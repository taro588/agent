"""Dependency-free asset inspection and validation primitives."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Issue:
    code: str
    severity: str
    message: str
    field: str | None = None

@dataclass
class InspectionReport:
    asset_name: str
    issues: list[Issue] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    ok: bool = True

    def add(self, code: str, severity: str, message: str, field: str | None = None):
        normalized = str(severity).lower()
        self.issues.append(Issue(code, normalized, message, field))
        if normalized == "error":
            self.ok = False

    def to_dict(self):
        return {"asset": self.asset_name, "ok": self.ok, "metrics": dict(self.metrics), "issues": [i.__dict__ for i in self.issues]}

def inspect_asset(data: dict[str, Any]) -> InspectionReport:
    if not isinstance(data, dict):
        raise TypeError("Asset inspection data must be a dictionary.")
    name = str(data.get("name") or "UnnamedAsset")
    report = InspectionReport(name)
    if not data.get("name"):
        report.add("ASSET_NAME_MISSING", "warning", "Asset name is missing.", "name")
    objects = data.get("objects")
    if objects is not None:
        try:
            count = int(objects)
            report.metrics["objects"] = count
            if count < 0:
                report.add("OBJECT_COUNT_INVALID", "error", "Object count cannot be negative.", "objects")
        except (TypeError, ValueError):
            report.add("OBJECT_COUNT_INVALID", "error", "Object count must be numeric.", "objects")
    return report
