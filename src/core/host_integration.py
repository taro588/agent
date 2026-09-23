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

    def _maya_roots(self) -> list[Path]:
        override = os.environ.get("GAMEART_MAYA_USER_SCRIPTS")
        if override:
            return [Path(override).expanduser().resolve()]
        documents = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Documents"
        maya = documents / "maya"
        roots = [p / "scripts" for p in maya.iterdir() if p.is_dir()] if maya.is_dir() else []
        legacy = maya / "scripts"
        return roots or [legacy]

    def _maya_scripts(self) -> Path:
        return self._maya_roots()[0]

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
            paths = [self._write_maya_user_setup(p, True) for p in self._maya_roots()]
            return HostIntegrationResult(True,"maya","register",";".join(str(p) for p in paths))
        except Exception as exc:
            return HostIntegrationResult(False,"maya","register",str(self._maya_scripts()),f"{type(exc).__name__}: {exc}")

    def unregister_maya(self):
        try:
            paths = [self._write_maya_user_setup(p, False) for p in self._maya_roots()]
            return HostIntegrationResult(True,"maya","unregister",";".join(str(p) for p in paths))
        except Exception as exc:
            return HostIntegrationResult(False,"maya","unregister",str(self._maya_scripts()),f"{type(exc).__name__}: {exc}")

    def _max_startups(self) -> list[Path]:
        override = os.environ.get("GAMEART_MAX_USER_STARTUP")
        if override:
            return [Path(override).expanduser().resolve()]
        local = Path(os.environ.get("LOCALAPPDATA", "")) / "Autodesk" / "3dsMax"
        documents = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Documents" / "3ds Max"
        roots: list[Path] = []
        for base in (local, documents):
            if not base.is_dir():
                continue
            for version in base.iterdir():
                if not version.is_dir():
                    continue
                for candidate in (version / "ENU" / "scripts" / "startup",
                                  version / "scripts" / "startup",
                                  version / "ENU" / "scripts"):
                    if candidate not in roots:
                        roots.append(candidate)
        return roots or [local / "2025" / "ENU" / "scripts" / "startup"]

    def register_max(self):
        try:
            source = self.loaders / "3ds_max" / "gameart_loader.ms"
            if not source.is_file():
                raise FileNotFoundError(f"Toolkit Max loader not found: {source}")
            registered = []
            for startup in self._max_startups():
                startup.mkdir(parents=True, exist_ok=True)
                target = startup / "GameArtToolkitStartup.ms"
                shutil.copy2(source, target)
                registered.append(str(target))
            if not registered:
                raise RuntimeError("No 3ds Max user startup directory was found.")
            return HostIntegrationResult(True, "3ds_max", "register", ";".join(registered))
        except Exception as exc:
            return HostIntegrationResult(False, "3ds_max", "register", str(self._max_startups()[0]), f"{type(exc).__name__}: {exc}")

    def unregister_max(self):
        try:
            removed = []
            for startup in self._max_startups():
                target = startup / "GameArtToolkitStartup.ms"
                if target.exists():
                    target.unlink()
                    removed.append(str(target))
            return HostIntegrationResult(True, "3ds_max", "unregister", ";".join(removed) or str(self._max_startup()))
        except Exception as exc:
            return HostIntegrationResult(False, "3ds_max", "unregister", str(self._max_startup()), f"{type(exc).__name__}: {exc}")
