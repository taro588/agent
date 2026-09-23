"""Windows DCC installation/version detection for GameArt Toolkit."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import re
import sys

@dataclass(frozen=True)
class DCCInstallation:
    host: str
    version: str
    path: str
    detected_by: str

SUPPORTED_POLICY = {
    "maya": set(str(v) for v in range(2022, 2027)),
    "3ds_max": set(str(v) for v in range(2022, 2027)),
}

def _windows_registry():
    if sys.platform != "win32":
        return None
    try:
        import winreg
        return winreg
    except ImportError:
        return None

def _registry_values(root, subkey):
    winreg = _windows_registry()
    if winreg is None:
        return []
    values = []
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (getattr(winreg, "KEY_WOW64_64KEY", 0), getattr(winreg, "KEY_WOW64_32KEY", 0)):
            try:
                with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ | view) as key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            values.append((name, str(value)))
                            i += 1
                        except OSError:
                            break
            except OSError:
                continue
    return values

def _scan_registry(prefix, host):
    winreg = _windows_registry()
    if winreg is None:
        return []
    found = []
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (getattr(winreg, "KEY_WOW64_64KEY", 0), getattr(winreg, "KEY_WOW64_32KEY", 0)):
            try:
                with winreg.OpenKey(hive, prefix, 0, winreg.KEY_READ | view) as root:
                    i = 0
                    while True:
                        try:
                            version = winreg.EnumKey(root, i)
                            i += 1
                        except OSError:
                            break
                        match = re.search(r"(20\d{2})", version)
                        if not match:
                            continue
                        version = match.group(1)
                        try:
                            with winreg.OpenKey(root, winreg.EnumKey(root, i - 1)) as key:
                                vals = {}
                                j = 0
                                while True:
                                    try:
                                        name, value, _ = winreg.EnumValue(key, j)
                                        vals[name.lower()] = str(value)
                                        j += 1
                                    except OSError:
                                        break
                            path = next((vals[k] for k in ("installpath", "installdir", "installdirectory", "path", "location") if vals.get(k)), "")
                            if path and Path(path).exists():
                                found.append(DCCInstallation(host, version, path, "registry"))
                        except OSError:
                            continue
            except OSError:
                continue
    return found

def _candidate_roots():
    roots = []
    for key in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
        value = os.environ.get(key)
        if value:
            roots.append(Path(value))
    roots.extend([Path(r"C:\Program Files"), Path(r"C:\Program Files (x86)")])
    unique, seen = [], set()
    for root in roots:
        try: root = root.resolve()
        except OSError: continue
        key = str(root).lower()
        if key not in seen:
            seen.add(key); unique.append(root)
    return unique

def _scan_common_paths(host):
    found = []
    names = {"maya": ("Autodesk", "Maya"), "3ds_max": ("Autodesk", "3ds Max")}
    exe = {"maya": "maya.exe", "3ds_max": "3dsmax.exe"}[host]
    for root in _candidate_roots():
        parent = root / names[host][0] / names[host][1]
        if not parent.is_dir():
            continue
        for child in parent.iterdir():
            if child.is_dir():
                m = re.search(r"20\d{2}", child.name)
                if m and (child / exe).exists():
                    found.append(DCCInstallation(host, m.group(0), str(child), "filesystem"))
    return found

def _scan_autodesk_uninstall(host):
    winreg = _windows_registry()
    if winreg is None:
        return []
    found = []
    prefixes = {
        "maya": (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",),
        "3ds_max": (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",),
    }
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (getattr(winreg, "KEY_WOW64_64KEY", 0), getattr(winreg, "KEY_WOW64_32KEY", 0)):
            try:
                with winreg.OpenKey(hive, prefixes[host][0], 0, winreg.KEY_READ | view) as root:
                    i = 0
                    while True:
                        try: sub = winreg.EnumKey(root, i); i += 1
                        except OSError: break
                        try:
                            with winreg.OpenKey(root, sub) as key:
                                vals = {}
                                j = 0
                                while True:
                                    try:
                                        n,v,_ = winreg.EnumValue(key,j); vals[n.lower()] = str(v); j += 1
                                    except OSError: break
                            display = vals.get("displayname","")
                            if ("maya" not in display.lower() if host=="maya" else "3ds max" not in display.lower()):
                                continue
                            m = re.search(r"(20\d{2})", display)
                            if not m: continue
                            path = next((vals[k] for k in ("installlocation","installpath") if vals.get(k)), "")
                            if path and Path(path).exists():
                                found.append(DCCInstallation(host,m.group(1),path,"uninstall-registry"))
                        except OSError: continue
            except OSError: continue
    return found

def detect_dcc():
    result = {"maya": [], "3ds_max": []}
    prefixes = {"maya": r"SOFTWARE\Autodesk\Maya", "3ds_max": r"SOFTWARE\Autodesk\3dsMax"}
    for host in result:
        found = _scan_registry(prefixes[host], host)
        found += _scan_autodesk_uninstall(host)
        found += _scan_common_paths(host)
        unique = {}
        for item in found:
            unique[(item.version, item.path.lower())] = item
        result[host] = sorted(unique.values(), key=lambda x: x.version, reverse=True)
    return result

def compatibility(host, version):
    return version in SUPPORTED_POLICY.get(host, set())
