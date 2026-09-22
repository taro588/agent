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
import urllib.request
import zipfile
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

PLUGIN_PROFILES = {
    "texture-importer": {"host":"maya","entry_mode":"path_only","note":"Python package; load through sys.path, no blanket execution."},
    "totex": {"host":"3ds_max","entry_mode":"manual_script","note":"MaxScript/MZP tool; expose files and provide explicit launcher from the Toolkit manager."},
    "MayaToPainter": {"host":"maya","entry_mode":"path_only","note":"Maya integration; inspect upstream startup files before enabling."},
    "SubstancePainterToMaya": {"host":"maya","entry_mode":"path_only","note":"Maya integration; inspect upstream startup files before enabling."},
    "rename-lowhigh-proximity": {"host":"3ds_max","entry_mode":"manual_script","note":"MAXScript utility; provide explicit launcher from the Toolkit manager."},
    "fal-texture-pbr-generator": {"host":"shared","entry_mode":"manual","note":"External/AI workflow; never auto-execute network code at DCC startup."},
    "Procedural-PBR": {"host":"shared","entry_mode":"manual","note":"Procedural PBR workflow; manual activation."},
    "SubstanceDesignerTools": {"host":"shared","entry_mode":"manual","note":"Substance Designer tooling; not a Maya/Max startup plugin."},
}

KNOWN_PLUGINS = {
    "texture-importer": {"host":"maya","url":"https://github.com/beatreichenbach/texture-importer.git","install":"manual_launcher","entry_candidates":["setup_maya.mel","setup_max.ms"]},
    "totex": {"host":"3ds_max","url":"https://github.com/svenfraeys/totex.git","install":"mzp_or_script","entry_candidates":["mzpInstall.ms","totex.ms","ToTex"]},
    "MayaToPainter": {"host":"maya","url":"https://github.com/pramberg/MayaToPainter.git","install":"manual_launcher","entry_candidates":[]},
    "SubstancePainterToMaya": {"host":"maya","url":"https://github.com/Strangenoise/SubstancePainterToMaya.git","install":"path_and_shelf","entry_candidates":["main.py"]},
    "rename-lowhigh-proximity": {"host":"3ds_max","url":"https://github.com/Khanzino3d/maxscript-rename-lowhigh-proximity.git","install":"manual_script","entry_candidates":[]},
    "fal-texture-pbr-generator": {"host":"shared","url":"https://github.com/lovisdotio/fal-texture-pbr-generator.git","install":"web_app","entry_candidates":[]},
    "Procedural-PBR": {"host":"shared","url":"https://github.com/Whappens/Procedural-PBR.git","install":"cli","entry_candidates":["generate_brick_pbr.py","generate_grass_pbr.py","generate_clouds_pbr.py","generate_liquid_pbr.py","generate_water_pbr.py","generate_snow_pbr.py","generate_ice_pbr.py"]},
    "SubstanceDesignerTools": {"host":"shared","url":"https://github.com/Gil-1/SubstanceDesignerTools.git","install":"substance_sbs","entry_candidates":["Simple_Triplanar_Texturer.sbs"]},
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

    def _download_zip(self, source: str, destination: Path, branch: str | None = None) -> None:
        parsed = urlparse(source)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) != 2 or parts[0] == "users":
            raise ValueError("Plugin source must be a GitHub repository URL.")
        owner, repo = parts
        if repo.endswith(".git"):
            repo = repo[:-4]
        ref = f"/{branch}" if branch else ""
        url = f"https://api.github.com/repos/{owner}/{repo}/zipball{ref}"
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "GameArtToolkit"},
        )
        archive = destination.parent / (destination.name + ".zip")
        try:
            with urllib.request.urlopen(request, timeout=30) as response, archive.open("wb") as out:
                shutil.copyfileobj(response, out)
            with zipfile.ZipFile(archive) as zf:
                root = destination
                root.mkdir(parents=True, exist_ok=True)
                for member in zf.infolist():
                    name = member.filename.replace("\\", "/")
                    if name.startswith("/") or any(part == ".." for part in name.split("/")):
                        raise ValueError(f"Unsafe archive path: {member.filename}")
                    target = (root / Path(name)).resolve()
                    target.relative_to(root.resolve())
                    if member.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, target.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
        finally:
            archive.unlink(missing_ok=True)
        children = [p for p in destination.iterdir() if p.is_dir()]
        files = [p for p in destination.iterdir() if p.is_file()]
        if len(children) == 1 and not files:
            nested = children[0]
            for item in nested.iterdir():
                os.replace(item, destination / item.name)
            nested.rmdir()

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
                self._download_zip(source, checkout, branch)
                if not checkout.is_dir() or not any(checkout.iterdir()):
                    raise RuntimeError("GitHub archive completed but the plugin directory is empty.")

                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(checkout, destination)
                profile = PLUGIN_PROFILES.get(name, {"host": host, "entry_mode": "manual", "note": "No automatic startup policy."})
                verified = KNOWN_PLUGINS.get(name, {})
                manifest = {
                    "name": name,
                    "state": "installed",
                    "host": host,
                    "source": source,
                    "branch": branch,
                    "path": str(destination),
                    "entry_mode": profile["entry_mode"],
                    "install_mode": verified.get("install", "manual"),
                    "entry_candidates": verified.get("entry_candidates", []),
                    "note": profile["note"],
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
        """Classify likely host entry points without importing or executing code."""
        result = []
        startup_names = {
            "usersetup.py": "maya_user_setup",
            "package.py": "maya_package",
            "module-info.json": "maya_module",
            "gamearttoolkitstartup.ms": "max_startup",
        }
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = str(path.relative_to(root)).replace("\\", "/")
            lower = path.name.lower()
            suffix = path.suffix.lower()
            if lower in startup_names:
                result.append({"type": startup_names[lower], "path": rel, "load": "startup_candidate"})
            elif suffix in {".mll", ".pyd", ".dll"}:
                result.append({"type": "native_binary", "path": rel, "load": "manual_only"})
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


    def verify(self, name: str) -> dict:
        """Verify an installed plugin without importing or executing it."""
        spec = self.resolve(name)
        destination = self._owned(self.plugin_root / spec["host"] / name)
        manifest_path = self._owned(self.manifest_root / f"{name}.json")
        checks = [{"check": "directory", "ok": destination.is_dir()},
                  {"check": "manifest", "ok": manifest_path.is_file()}]
        manifest = {}
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                checks.append({"check": "manifest_json", "ok": False})
        if manifest:
            checks.append({"check": "manifest_path", "ok": Path(manifest.get("path","")).resolve() == destination})
            for rel in manifest.get("entry_candidates", []):
                checks.append({"check": f"candidate:{rel}", "ok": (destination / rel).is_file()})
        entrypoints = self._detect_entrypoints(destination) if destination.is_dir() else []
        checks.append({"check": "entrypoint_scan", "ok": True, "count": len(entrypoints)})
        failed = [c for c in checks if not c.get("ok")]
        return {"name": name, "status": "ok" if not failed else "needs_attention",
                "checks": checks, "manifest": manifest}

    def verify_all(self) -> list[dict]:
        return [self.verify(item["name"]) for item in self.installed() if item.get("name")]

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
