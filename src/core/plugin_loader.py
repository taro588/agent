"""Failure-safe runtime plugin discovery and loading.

Discovery never executes plugin code. Loading is explicit and isolated at the
Python import boundary; a failed optional plugin is reported as quarantined.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import importlib.util
import json
import sys
from typing import Any

@dataclass(frozen=True)
class PluginLoadResult:
    ok: bool
    name: str
    state: str
    error: str | None = None

class PluginLoader:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.plugin_root = self.root / "plugins"
        self.manifest_root = self.root / "plugin-manifests"

    def discover(self) -> list[dict[str, Any]]:
        result=[]
        if not self.manifest_root.exists():
            return result
        for path in sorted(self.manifest_root.glob("*.json")):
            try:
                data=json.loads(path.read_text(encoding="utf-8"))
                plugin_path=Path(data["path"]).expanduser().resolve()
                plugin_path.relative_to(self.root)
                data["exists"]=plugin_path.is_dir()
                data["state"]="installed" if data["exists"] else "missing"
            except Exception as exc:
                data={"name":path.stem,"state":"invalid_manifest","error":f"{type(exc).__name__}: {exc}"}
            result.append(data)
        return result

    def load_python(self, name: str, module_file: str = "__init__.py") -> PluginLoadResult:
        manifest_path=self.manifest_root/f"{name}.json"
        try:
            data=json.loads(manifest_path.read_text(encoding="utf-8"))
            root=Path(data["path"]).expanduser().resolve()
            root.relative_to(self.root)
            target=(root/module_file).resolve()
            target.relative_to(root)
            if not target.is_file():
                raise FileNotFoundError(f"Python entry point not found: {target}")
            module_name=f"gameart_plugin_{name.replace('-', '_')}"
            spec=importlib.util.spec_from_file_location(module_name,target)
            if spec is None or spec.loader is None:
                raise ImportError(f"Unable to create import spec for {target}")
            module=importlib.util.module_from_spec(spec)
            sys.modules[module_name]=module
            try:
                spec.loader.exec_module(module)
            except Exception:
                sys.modules.pop(module_name,None)
                raise
            return PluginLoadResult(True,name,"loaded")
        except Exception as exc:
            return PluginLoadResult(False,name,"quarantined",f"{type(exc).__name__}: {exc}")

    def load_maya_script(self, name: str, script_file: str) -> PluginLoadResult:
        """Validate a Maya script entry point without executing it."""
        manifest_path = self.manifest_root / f"{name}.json"
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            root = Path(data["path"]).expanduser().resolve()
            root.relative_to(self.root)
            target = (root / script_file).resolve()
            target.relative_to(root)
            if not target.is_file():
                raise FileNotFoundError(f"Maya script entry point not found: {target}")
            return PluginLoadResult(True, name, "ready")
        except Exception as exc:
            return PluginLoadResult(False, name, "quarantined", f"{type(exc).__name__}: {exc}")

    def run_maxscript(self, name: str, script_file: str) -> PluginLoadResult:
        """MAXScript requires an explicit host bridge and is never auto-executed."""
        return PluginLoadResult(
            False, name, "quarantined",
            "MAXScript execution requires an explicit 3ds Max host bridge.",
        )
