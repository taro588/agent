"""Windows Substance 3D Painter installer integration.

Uses documented Adobe locations and launch flags. It never patches the Painter
installation directory and never edits Painter binaries.
"""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

PAINTER_DOCUMENTS_ROOT = Path.home() / "Documents" / "Adobe" / "Adobe Substance 3D Painter"
PAINTER_PLUGIN_ROOT = PAINTER_DOCUMENTS_ROOT / "python"
PAINTER_PLUGIN_DIR = PAINTER_PLUGIN_ROOT / "plugins"
PAINTER_STARTUP_DIR = PAINTER_PLUGIN_ROOT / "startup"
PAINTER_MODULES_DIR = PAINTER_PLUGIN_ROOT / "modules"
REMOTE_PORT = 60041
REMOTE_FLAG = "--enable-remote-scripting"

class PainterInstaller:
    plugin_module = "gameart_ai_toolkit"

    def __init__(self, source_root: str | Path):
        self.source_root = Path(source_root).resolve()
        self.installed_plugin = self.source_root / "plugins" / "substance_painter"

    def user_plugin_root(self) -> Path:
        return PAINTER_PLUGIN_ROOT

    def detect_executables(self) -> list[Path]:
        candidates = []
        for env_name in ("SUBSTANCE_PAINTER_EXE", "ADOBE_SUBSTANCE_PAINTER_EXE"):
            value = os.getenv(env_name)
            if value:
                candidates.append(Path(value))
        roots = [
            Path(os.environ.get("PROGRAMFILES", r"C:Program Files")) / "Adobe",
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:Program Files (x86)")) / "Adobe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Adobe",
        ]
        for root in roots:
            if root.is_dir():
                candidates.extend(root.glob("Adobe Substance 3D Painter*/Adobe Substance 3D painter.exe"))
                candidates.extend(root.glob("Adobe Substance 3D Painter*/resources/bin/Adobe Substance 3D painter.exe"))
        result=[]
        seen=set()
        for p in candidates:
            p=p.resolve()
            if p.is_file() and str(p).lower() not in seen:
                seen.add(str(p).lower()); result.append(p)
        return result

    def install(self) -> dict[str, Any]:
        source = self.installed_plugin / "gameart_ai_toolkit.py"
        if not source.is_file():
            raise FileNotFoundError(f"Painter plugin source not found: {source}")
        for folder in (PAINTER_PLUGIN_ROOT, PAINTER_PLUGIN_DIR, PAINTER_STARTUP_DIR, PAINTER_MODULES_DIR):
            folder.mkdir(parents=True, exist_ok=True)
        target = PAINTER_PLUGIN_DIR / source.name
        shutil.copy2(source, target)
        return {
            "ok": True,
            "target": str(target),
            "plugin_module": self.plugin_module,
            "documents_root": str(PAINTER_DOCUMENTS_ROOT),
            "remote_port": REMOTE_PORT,
        }

    def uninstall(self) -> dict[str, Any]:
        target = PAINTER_PLUGIN_DIR / "gameart_ai_toolkit.py"
        if target.exists():
            target.unlink()
        return {"ok": True, "removed": str(target)}

    def verify(self) -> dict[str, Any]:
        target = PAINTER_PLUGIN_DIR / "gameart_ai_toolkit.py"
        exe = self.detect_executables()
        return {
            "ok": target.is_file(),
            "plugin": str(target),
            "painter_executables": [str(x) for x in exe],
            "remote_port": REMOTE_PORT,
            "remote_flag": REMOTE_FLAG,
        }

    def launch_remote(self, executable: str | Path | None = None) -> subprocess.Popen:
        exe = Path(executable) if executable else (self.detect_executables()[0] if self.detect_executables() else None)
        if exe is None or not exe.is_file():
            raise FileNotFoundError("Substance 3D Painter executable was not detected.")
        self.install()
        return subprocess.Popen([str(exe), REMOTE_FLAG], cwd=str(exe.parent))

    def command_line(self, executable: str | Path | None = None) -> list[str]:
        exe = Path(executable) if executable else (self.detect_executables()[0] if self.detect_executables() else None)
        if exe is None:
            raise FileNotFoundError("Substance 3D Painter executable was not detected.")
        return [str(exe), REMOTE_FLAG]
