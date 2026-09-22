"""Dependency-free pipeline orchestration primitives."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class PipelineStage:
    name: str
    action: Callable[[], Any]
    required: bool = True

@dataclass
class Pipeline:
    name: str
    stages: list[PipelineStage] = field(default_factory=list)

    def add_stage(self, name: str, action: Callable[[], Any], required: bool = True) -> "Pipeline":
        if not name or not callable(action):
            raise ValueError("Pipeline stage requires a non-empty name and callable action.")
        self.stages.append(PipelineStage(name, action, required))
        return self

    def run(self) -> dict[str, Any]:
        results = []
        for stage in self.stages:
            try:
                value = stage.action()
                results.append({"stage": stage.name, "ok": True, "result": value})
            except Exception as exc:
                results.append({"stage": stage.name, "ok": False,
                                "error": f"{type(exc).__name__}: {exc}"})
                if stage.required:
                    return {"pipeline": self.name, "ok": False, "stages": results}
        return {"pipeline": self.name, "ok": True, "stages": results}
