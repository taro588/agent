"""Target-specific game pipeline profiles."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class PipelineProfile:
    name: str
    triangle_budget: int | None = None
    texture_resolution: int | None = None
    lod_count: int = 0
    texture_formats: tuple[str, ...] = ()
    required_outputs: tuple[str, ...] = ()
    rules: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors=[]
        if self.triangle_budget is not None and self.triangle_budget < 0: errors.append("triangle_budget must be >= 0")
        if self.texture_resolution is not None and self.texture_resolution <= 0: errors.append("texture_resolution must be > 0")
        if self.lod_count < 0: errors.append("lod_count must be >= 0")
        return errors

DEFAULT_PROFILES = {
    "UE5_PC": PipelineProfile("UE5_PC", triangle_budget=100000, texture_resolution=4096, lod_count=3, texture_formats=("png","tga","exr"), required_outputs=("fbx",)),
    "UE5_MOBILE": PipelineProfile("UE5_MOBILE", triangle_budget=30000, texture_resolution=2048, lod_count=3, texture_formats=("png","tga"), required_outputs=("fbx",)),
    "Unity_Mobile": PipelineProfile("Unity_Mobile", triangle_budget=30000, texture_resolution=2048, lod_count=3, texture_formats=("png","tga"), required_outputs=("fbx",)),
}

def get_profile(name: str) -> PipelineProfile:
    try: return DEFAULT_PROFILES[name]
    except KeyError as exc: raise KeyError(f"Unknown pipeline profile: {name}") from exc
