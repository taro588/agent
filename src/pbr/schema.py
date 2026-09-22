"""Dependency-free PBR texture schema."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

CHANNELS = ("base_color", "normal", "roughness", "metallic", "height", "ao")

@dataclass
class PBRTextureSet:
    name: str
    channels: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors = []
        for channel, path in self.channels.items():
            if channel not in CHANNELS:
                errors.append(f"Unsupported PBR channel: {channel}")
            elif not isinstance(path, str) or not path.strip():
                errors.append(f"Texture path for {channel} is empty.")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "channels": dict(self.channels), "metadata": dict(self.metadata)}
