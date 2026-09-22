"""Transactional third-party plugin installer.

Plugins are installed outside the DCC installation. The installer clones an
upstream Git repository into a Toolkit-owned directory, writes a local manifest,
and only publishes the plugin after the clone succeeds.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import os
import shutil
import stat
import subprocess
import tempfile
from urllib.parse import urlparse
import platform
from .host_integration import HostIntegrator

@dataclass(frozen=True)
class PluginInstallResult:
    ok: bool
    name: str
    path: str
    error: str | None = None
    source: str | None = None

KNOWN_PLUGINS = {
    "texture-importer": {
        "host": "maya",
        "url": "https://github.com/beatreichenbach/texture-importer.git",
    },
    "totex": {
        "host": "3ds_max",
        "url": "https://github.com/svenfraeys/totex.git",
    },
    "MayaToPainter": {
        "host": "maya",
        "url": "https://github.com/pramberg/MayaToPainter.git",
    },
    "SubstancePainterToMaya": {
        "host": "maya",
        "url": "https://github.com/Strangenoise/SubstancePainterToMaya.git",
    },
    "rename-lowhigh-proximity": {
        "host": "3ds_max",
        "url": "https://github.com/Khanzino3d/maxscript-rename-lowhigh-proximity.git",
    },
    "fal-texture-pbr-generator": {
        "host": "shared",
        "url": "https://github.com/lovisdotio/fal-texture-pbr-generator.git",
    },
    "Procedural-PBR": {
        "host": "shared",
        "url": "https://github.com/Whappens/Procedural-PBR.git",
    },
    "SubstanceDesignerTools": {
        "host": "shared",
        "url": "https://github.com/Gil-1/SubstanceDesignerTools.git",
    },
}

class PluginInstaller:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.plugin_root = self.root / "plugins"
        self.manifest_root = self.root / "plugin-manifests"
        self.host = HostIntegrator(self.root)

    def _owned(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Refusing to operate outside Toolkit root.") from exc
        return target

    def _validate_source(self, source: str) -> str:
        parsed = urlparse(source)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Plugin source must be an HTTPS repository URL.")
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise ValueError("Only GitHub HTTPS repositories are supported.")
        return source

    def _git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def resolve(self, name: str) -> dict:
        spec = KNOWN_PLUGINS.get(name)
        if spec is None:
            raise KeyError(f"Unknown plugin: {name}")
        return {"name": name, **spec}

    def install(
        self,
        name: str,
        source: str | None = None,
        *,
        host: str | None = None,
        branch: str | None = None,
    ) -> PluginInstallResult:
        try:
            spec = self.resolve(name)
            source = self._validate_source(source or spec["url"])
            host = host or spec["host"]
            destination = self._owned(self.plugin_root / host / name)
            if destination.exists():
                raise ValueError(f"Plugin is already installed: {name}")

            self.plugin_root.mkdir(parents=True, exist_ok=True)
            self.manifest_root.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(prefix=".plugin-", dir=self.root))
            checkout = staging / "checkout"
            try:
                args = ["clone", "--depth", "1"]
                if branch:
                    args += ["--branch", branch]
                args += [source, str(checkout)]
                result = self._git(*args)
                if result.returncode != 0:
                    detail = (result.stderr or result.stdout).strip()
                    raise RuntimeError(f"git clone failed: {detail or 'unknown error'}")

                if not checkout.is_dir() or not any(checkout.iterdir()):
                    raise RuntimeError("Git clone completed but the plugin directory is empty.")

                # Installed plugins are payloads, not working Git checkouts.
                # Removing .git keeps credentials/config metadata out of the
                # Toolkit and makes Windows uninstall deterministic.
                git_metadata = checkout / ".git"
                if git_metadata.exists():
                    self._remove_tree(git_metadata)

                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(checkout, destination)
                manifest = {
                    "name": name,
                    "state": "installed",
                    "host": host,
                    "source": source,
                    "branch": branch,
                    "path": str(destination),
                    "entrypoints": self._detect_entrypoints(destination),
                }
                manifest_path = self._owned(self.manifest_root / f"{name}.json")
                tmp_manifest = self._owned(self.manifest_root / f".{name}.tmp")
                tmp_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                os.replace(tmp_manifest, manifest_path)
                self.generate_host_loaders()
                if host == "maya":
                    integration = self.host.register_maya()
                elif host == "3ds_max":
                    integration = self.host.register_max()
                else:
                    integration = None
                if integration is not None and not integration.ok:
                    raise RuntimeError(f"Host registration failed: {integration.error}")
                return PluginInstallResult(True, name, str(destination), source=source)
            finally:
                shutil.rmtree(staging, ignore_errors=True)
        except Exception as exc:
            try:
                if "destination" in locals() and destination.exists():
                    self._remove_tree(destination)
            except OSError:
                pass
            return PluginInstallResult(
                False,
                name,
                str(self.plugin_root),
                f"{type(exc).__name__}: {exc}",
                source,
            )



    def _detect_entrypoints(self, root: Path) -> list[dict[str, str]]:
        """Detect entry points without importing or executing plugin code."""
        result = []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = str(path.relative_to(root))
            if path.suffix.lower() == ".py":
                result.append({"type": "python", "path": rel})
            elif path.suffix.lower() == ".mel":
                result.append({"type": "maya_script", "path": rel})
            elif path.suffix.lower() in {".ms", ".mcr"}:
                result.append({"type": "maxscript", "path": rel})
        return result[:100]
    def generate_host_loaders(self) -> list[str]:
        """Generate Toolkit-owned host loader files; never modify DCC installs."""
        generated = []
        for host in ("maya", "3ds_max"):
            host_root = self._owned(self.root / "host-loaders" / host)
            host_root.mkdir(parents=True, exist_ok=True)
            if host == "maya":
                content = '''# GameArt Toolkit Maya loader.
# Installed by the Toolkit; does not modify Maya installation files.
import os
from pathlib import Path

TOOLKIT_ROOT = Path(os.environ.get("GAMEART_TOOLKIT_ROOT", "")).expanduser()
if TOOLKIT_ROOT:
    os.environ.setdefault("GAMEART_TOOLKIT_ROOT", str(TOOLKIT_ROOT))
'''
                target = host_root / "gameart_loader.py"
            else:
                content = '''-- GameArt Toolkit 3ds Max loader.
-- This file is generated inside the Toolkit and must be explicitly
-- registered through the Toolkit/host integration layer.
'''
                target = host_root / "gameart_loader.ms"
            target.write_text(content, encoding="utf-8")
            generated.append(str(target))
        return generated

    @staticmethod
    def _remove_tree(path: Path) -> None:
        def onerror(func, target, exc_info):
            try:
                os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
            except OSError:
                pass
            func(target)

        shutil.rmtree(path, onerror=onerror)

    def uninstall(self, name: str) -> PluginInstallResult:
        try:
            spec = self.resolve(name)
            host = spec["host"]
            destination = self._owned(self.plugin_root / host / name)
            manifest = self._owned(self.manifest_root / f"{name}.json")
            if destination.exists():
                self._remove_tree(destination)
            if manifest.exists():
                manifest.unlink()
            if host == "maya":
                self.host.unregister_maya()
            elif host == "3ds_max":
                self.host.unregister_max()
            return PluginInstallResult(True, name, str(destination))
        except Exception as exc:
            return PluginInstallResult(False, name, str(self.plugin_root), f"{type(exc).__name__}: {exc}")

    def installed(self) -> list[dict]:
        result = []
        if not self.manifest_root.exists():
            return result
        for path in sorted(self.manifest_root.glob("*.json")):
            try:
                result.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                result.append({"name": path.stem, "state": "invalid_manifest"})
        return result
