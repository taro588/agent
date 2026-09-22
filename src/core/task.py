"""Core task model. Tasks contain intent/data, not DCC-specific code."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class Task:
    name: str
    action: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Any = None
    error: str | None = None

    def succeed(self, result: Any = None) -> None:
        self.status, self.result, self.error = "completed", result, None

    def fail(self, error: str) -> None:
        self.status, self.error = "failed", str(error)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "action": self.action, "inputs": dict(self.inputs),
                "metadata": dict(self.metadata), "status": self.status,
                "result": self.result, "error": self.error}
