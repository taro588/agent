"""Preflight and failure-safe execution guard for pipelines."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class GuardResult:
    ok: bool
    stage: str
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)

class PipelineGuard:
    def preflight(self, required: dict[str, Any]) -> GuardResult:
        missing = [k for k, v in required.items() if v in (None, "", False)]
        if missing:
            return GuardResult(False, "preflight", "Required inputs are missing.", {"missing": missing})
        return GuardResult(True, "preflight", "Preflight passed.")

    def execute(self, stage: str, callback: Callable[[], Any]) -> GuardResult:
        try:
            value = callback()
            return GuardResult(True, stage, "Stage completed.", {"result": value})
        except Exception as exc:
            return GuardResult(False, stage, f"{type(exc).__name__}: {exc}")

    def run(self, stages: list[tuple[str, Callable[[], Any]]]) -> list[GuardResult]:
        results = []
        for stage, callback in stages:
            result = self.execute(stage, callback)
            results.append(result)
            if not result.ok:
                break
        return results
