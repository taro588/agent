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
                            version, _, _ = winreg.EnumKey(root, i)
                            i += 1
                        except OSError:
                            break
                        if not re.fullmatch(r"20\d{2}", version):
                            continue
                        try:
                            with winreg.OpenKey(root, version) as key:
                                vals = {}
                                j = 0
                                while True:
                                    try:
                                        name, value, _ = winreg.EnumValue(key, j)
                                        vals[name.lower()] = str(value)
                                        j += 1
                                    except OSError:
                                        break
                            path = next((vals[k] for k in ("installpath", "installdir", "installdirectory", "path") if vals.get(k)), "")
                            if path and Path(path).exists():
                                found.append(DCCInstallation(host, version, path, "registry"))
                        except OSError:
                            continue
            except OSError:
                continue
    return found

def _scan_common_paths(host):
    roots = [Path(os.environ.get("ProgramFiles", r"C:\Program Files"))]
    if os.environ.get("ProgramFiles(x86)"):
        roots.append(Path(os.environ["ProgramFiles(x86)"]))
    found = []
    names = {
        "maya": ("Autodesk", "Maya"),
        "3ds_max": ("Autodesk", "3ds Max"),
    }
    base = names[host]
    for root in roots:
        parent = root / base[0] / base[1]
        if not parent.is_dir():
            continue
        for child in parent.iterdir():
            if child.is_dir() and re.fullmatch(r"20\d{2}", child.name):
                found.append(DCCInstallation(host, child.name, str(child), "filesystem"))
    return found

def detect_dcc():
    result = {"maya": [], "3ds_max": []}
    for host, prefix in (
        ("maya", r"SOFTWARE\Autodesk\Maya"),
        ("3ds_max", r"SOFTWARE\Autodesk\3dsMax"),
    ):
        found = _scan_registry(prefix, host)
        seen = {(x.version, x.path.lower()) for x in found}
        for item in _scan_common_paths(host):
            if (item.version, item.path.lower()) not in seen:
                found.append(item)
        result[host] = sorted(found, key=lambda x: x.version, reverse=True)
    return result

def compatibility(host, version):
    return version in SUPPORTED_POLICY.get(host, set())
