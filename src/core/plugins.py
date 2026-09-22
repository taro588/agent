"""Failure-safe third-party plugin registry with compatibility checks."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PluginSpec:
    name: str
    path: Path
    host: str = "shared"
    optional: bool = True
    min_host_version: str | None = None
    max_host_version: str | None = None


@dataclass(frozen=True)
class PluginHealth:
    name: str
    state: str
    path: str
    reason: str = ""


def _version_tuple(value):
    if not value:
        return ()
    try:
        return tuple(int(x) for x in str(value).split(".") if x != "")
    except ValueError:
        return ()


class PluginRegistry:
    def __init__(self, specs: Iterable[PluginSpec] = ()):
        self._specs = {s.name: s for s in specs}
        self._disabled: dict[str, str] = {}

    def register(self, spec, *, replace=False):
        if not spec.name:
            raise ValueError("Plugin name cannot be empty.")
        if spec.name in self._specs and not replace:
            raise KeyError(f"Plugin already registered: {spec.name}")
        self._specs[spec.name] = spec

    def disable(self, name, reason=""):
        if name not in self._specs:
            raise KeyError(name)
        self._disabled[name] = str(reason or "Plugin is quarantined/disabled.")

    def enable(self, name):
        self._disabled.pop(name, None)

    def compatible(self, name, host_version):
        spec = self._specs[name]
        v = _version_tuple(host_version)
        if spec.min_host_version and v and v < _version_tuple(spec.min_host_version):
            return False
        if spec.max_host_version and v and v > _version_tuple(spec.max_host_version):
            return False
        return True

    def health(self, host_versions=None):
        result = []
        host_versions = host_versions or {}
        for spec in self._specs.values():
            if spec.name in self._disabled:
                result.append(
                    PluginHealth(
                        spec.name,
                        "disabled",
                        str(spec.path),
                        self._disabled[spec.name],
                    )
                )
                continue
            try:
                if spec.host in host_versions and not self.compatible(
                    spec.name, host_versions[spec.host]
                ):
                    result.append(
                        PluginHealth(
                            spec.name,
                            "incompatible",
                            str(spec.path),
                            "Host version is outside plugin compatibility range.",
                        )
                    )
                    continue
                exists = spec.path.exists()
                result.append(
                    PluginHealth(
                        spec.name,
                        "available" if exists else "missing",
                        str(spec.path),
                        "" if exists else "Plugin path does not exist.",
                    )
                )
            except OSError as exc:
                result.append(
                    PluginHealth(
                        spec.name,
                        "error",
                        str(spec.path),
                        f"{type(exc).__name__}: {exc}",
                    )
                )
        return sorted(result, key=lambda x: x.name)

    def names(self):
        return sorted(self._specs)
