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

    def _max_roots(self) -> list[Path]:
        override = os.environ.get("GAMEART_MAX_USER_ROOT")
        if override:
            return [Path(override).expanduser().resolve()]
        roots: list[Path] = []
        local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        autodesk = local / "Autodesk" / "3dsMax"
        if autodesk.is_dir():
            roots.extend(sorted((p for p in autodesk.iterdir() if p.is_dir()), key=lambda p: p.name))
        # Keep the historical Documents path as a fallback for custom/legacy setups.
        roots.append(Path.home() / "Documents" / "3ds Max")
        unique = []
        seen = set()
        for root in roots:
            root = root.resolve()
            if str(root).lower() not in seen:
                seen.add(str(root).lower())
                unique.append(root)
        return unique

    def _max_startups(self) -> list[Path]:
        return [root / "ENU" / "scripts" / "startup" for root in self._max_roots()]

    def _max_startup(self) -> Path:
        startups = self._max_startups()
        return startups[0]

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
            return HostIntegrationResult(False, "3ds_max", "register", str(self._max_startup()), f"{type(exc).__name__}: {exc}")

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
