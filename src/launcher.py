"""GameArt Toolkit launcher and diagnostics."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os, platform

from .dcc.manager import DCCManager
from .dcc.session import DCCSession
from .maya.adapter import MayaAdapter
from .max.adapter import MaxAdapter
from .core.plugins import PluginRegistry
from .core.installer import ToolkitInstaller
from .core.plugin_installer import PluginInstaller
from .core.plugin_loader import PluginLoader


@dataclass
class DCCInstallation:
    name: str
    version: str
    path: Path


@dataclass
class LauncherConfig:
    install_root: Path
    config_root: Path


class Launcher:
    def __init__(self, config=None):
        home = Path.home()
        self.config = config or LauncherConfig(
            home / "GameArtAI" / "Toolkit",
            home / "GameArtAI" / "Config",
        )
        self.dcc = DCCManager()
        self.dcc.register("maya", DCCSession(MayaAdapter()))
        self.dcc.register("3ds_max", DCCSession(MaxAdapter()))
        self.plugins = PluginRegistry()
        self.installer = ToolkitInstaller(self.config.install_root)
        self.plugin_installer = PluginInstaller(self.config.install_root)
        self.plugin_loader = PluginLoader(self.config.install_root)

    def health_check(self):
        root = self.config.install_root
        return {
            "installed": root.exists(),
            "install_root": str(root),
            "config_root": str(self.config.config_root),
            "writable": self._writable(root),
        }

    def _writable(self, root):
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return True
        except OSError:
            return False

    def detect_dcc(self):
        found = []
        for name, env in (("Maya", "MAYA_LOCATION"), ("3ds Max", "ADSK_3DSMAX_ROOT")):
            value = os.environ.get(env)
            if value:
                path = Path(value).expanduser()
                found.append(
                    DCCInstallation(
                        name,
                        "detected" if path.exists() else "environment_only",
                        path,
                    )
                )
        return found

    def dcc_status(self):
        self.dcc.connect_all()
        return self.dcc.status()

    def doctor(self):
        dcc_api = self.dcc_status()
        environment = self.detect_dcc()
        health = self.health_check()

        storage_failed = not health["writable"]
        dcc_failures = []
        dcc_warnings = []
        for name, info in dcc_api.items():
            if info.get("connected"):
                continue
            # No native DCC is expected when the launcher runs standalone.
            # Only report it as a failure when that DCC is actually detected
            # in the environment or its adapter reported a real error.
            detected = any(
                item.name.lower().replace(" ", "_") == name.replace("_max", "_max")
                for item in environment
            )
            error = info.get("error")
            if detected or (error and error != "DCC API is not available"):
                dcc_failures.append(name)
            else:
                dcc_warnings.append(name)

        failures = list(dcc_failures)
        if storage_failed:
            failures.append("toolkit_storage")

        return {
            "status": "degraded" if failures else "ready",
            "toolkit": "GameArt AI Toolkit",
            "version": "0.1.0-alpha",
            "python": platform.python_version(),
            "platform": platform.platform(),
            "launcher": health,
            "environment_detection": [
                {"name": d.name, "version": d.version, "path": str(d.path)}
                for d in environment
            ],
            "dcc_api": dcc_api,
            "dcc_failures": failures,
            "dcc_warnings": dcc_warnings,
            "plugins": [h.__dict__ for h in self.plugins.health()],
            "installed_plugins": self.plugin_installer.installed(),
            "plugin_discovery": self.plugin_loader.discover(),
        }

    def repair(self):
        result = self.installer.repair().__dict__
        if result.get("ok"):
            try:
                self.config.config_root.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                result.update(ok=False, error=f"{type(exc).__name__}: {exc}")
        return result

    def start(self):
        return {"status": "ready", **self.health_check()}
