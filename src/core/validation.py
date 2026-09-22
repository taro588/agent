"""Validation result primitives shared by pipeline and DCC adapters."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class ValidationIssue:
    code: str
    severity: str
    message: str
    field: str | None = None

@dataclass
class ValidationResult:
    ok: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def add(self, code: str, severity: str, message: str, field: str | None = None) -> None:
        self.issues.append(ValidationIssue(code, severity, message, field))
        if severity.lower() == "error":
            self.ok = False

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "issues": [i.__dict__ for i in self.issues], "metrics": dict(self.metrics)}

def run_validation(data: dict[str, Any], validators: list[Callable] | None = None) -> ValidationResult:
    result = ValidationResult()
    for validator in validators or []:
        try:
            validator(data, result)
        except Exception as exc:
            result.add("VALIDATOR_FAILED", "error",
                       f"{getattr(validator, '__name__', 'validator')} failed: {type(exc).__name__}: {exc}")
    return result
