"""User-level DCC host integration without modifying DCC installations."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import shutil

MARKER = "# GameArt Toolkit managed block"

@dataclass(frozen=True)
class HostIntegrationResult:
    ok: bool
    host: str
    action: str
    path: str
    error: str | None = None

class HostIntegrator:
    def __init__(self, toolkit_root: str | Path):
        self.root = Path(toolkit_root).expanduser().resolve()
        self.loaders = self.root / "host-loaders"

    def _maya_scripts(self) -> Path:
        override = os.environ.get("GAMEART_MAYA_USER_SCRIPTS")
        return Path(override).expanduser().resolve() if override else (Path.home() / "Documents" / "maya" / "scripts").resolve()

    def _max_startup(self) -> Path:
        override = os.environ.get("GAMEART_MAX_USER_STARTUP")
        return Path(override).expanduser().resolve() if override else (Path.home() / "Documents" / "3ds Max" / "scripts" / "startup").resolve()

    def _write_maya_user_setup(self, scripts: Path, enabled: bool) -> Path:
        scripts.mkdir(parents=True, exist_ok=True)
        setup = scripts / "userSetup.py"
        current = setup.read_text(encoding="utf-8") if setup.exists() else ""
        begin, end = f"{MARKER} BEGIN", f"{MARKER} END"
        kept, inside = [], False
        for line in current.splitlines():
            if line.strip() == begin:
                inside = True
                continue
            if line.strip() == end:
                inside = False
                continue
            if not inside:
                kept.append(line)
        block = []
        if enabled:
            block = [
                begin,
                "import sys as _gameart_sys",
                f"_gameart_root = {str(self.root)!r}",
                "if _gameart_root not in _gameart_sys.path: _gameart_sys.path.insert(0, _gameart_root)",
                "try:",
                "    from src.core.plugin_loader import PluginLoader as _GameArtPluginLoader",
                "except Exception:",
                "    _GameArtPluginLoader = None",
                end,
            ]
        setup.write_text("\n".join(kept + block).rstrip() + "\n", encoding="utf-8")
        return setup

    def register_maya(self):
        try:
            p=self._write_maya_user_setup(self._maya_scripts(), True)
            return HostIntegrationResult(True,"maya","register",str(p))
        except Exception as exc:
            return HostIntegrationResult(False,"maya","register",str(self._maya_scripts()),f"{type(exc).__name__}: {exc}")

    def unregister_maya(self):
        try:
            p=self._write_maya_user_setup(self._maya_scripts(), False)
            return HostIntegrationResult(True,"maya","unregister",str(p))
        except Exception as exc:
            return HostIntegrationResult(False,"maya","unregister",str(self._maya_scripts()),f"{type(exc).__name__}: {exc}")

    def register_max(self):
        try:
            startup=self._max_startup()
            startup.mkdir(parents=True, exist_ok=True)
            target=startup/"GameArtToolkitStartup.ms"
            source=self.loaders/"3ds_max"/"gameart_loader.ms"
            if not source.is_file():
                raise FileNotFoundError(f"Toolkit Max loader not found: {source}")
            shutil.copy2(source,target)
            return HostIntegrationResult(True,"3ds_max","register",str(target))
        except Exception as exc:
            return HostIntegrationResult(False,"3ds_max","register",str(self._max_startup()),f"{type(exc).__name__}: {exc}")

    def unregister_max(self):
        try:
            target=self._max_startup()/"GameArtToolkitStartup.ms"
            if target.exists(): target.unlink()
            return HostIntegrationResult(True,"3ds_max","unregister",str(target))
        except Exception as exc:
            return HostIntegrationResult(False,"3ds_max","unregister",str(self._max_startup()),f"{type(exc).__name__}: {exc}")
