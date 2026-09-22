"""Core asset model. Dependency-free and safe to use outside any DCC."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Asset:
    name: str
    source_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "source_path": self.source_path, "metadata": dict(self.metadata)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Asset":
        if not isinstance(data, dict):
            raise TypeError("Asset data must be a dictionary.")
        return cls(str(data.get("name") or "UnnamedAsset"), data.get("source_path"), dict(data.get("metadata") or {}))
