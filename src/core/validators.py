"""Safe, extensible validators for mesh/UV/material/pipeline metadata."""
from __future__ import annotations
from typing import Any, Callable
from .asset_inspector import InspectionReport

Validator = Callable[[dict[str, Any], InspectionReport], None]

def validate_mesh(data: dict[str, Any], report: InspectionReport) -> None:
    tris = data.get("triangles")
    if tris is not None:
        try:
            tris = int(tris)
            report.metrics["triangles"] = tris
            if tris < 0:
                report.add("TRIANGLES_INVALID", "error", "Triangle count cannot be negative.", "triangles")
        except (TypeError, ValueError):
            report.add("TRIANGLES_INVALID", "error", "Triangle count must be numeric.", "triangles")

def validate_uv(data: dict[str, Any], report: InspectionReport) -> None:
    uv_sets = data.get("uv_sets")
    if uv_sets is not None:
        if not isinstance(uv_sets, (list, tuple)):
            report.add("UV_SETS_INVALID", "error", "UV sets must be a list.", "uv_sets")
        elif len(uv_sets) == 0:
            report.add("UV_SET_MISSING", "warning", "No UV set is reported.", "uv_sets")
        else:
            report.metrics["uv_sets"] = len(uv_sets)

def validate_material(data: dict[str, Any], report: InspectionReport) -> None:
    materials = data.get("materials")
    if materials is not None:
        if not isinstance(materials, (list, tuple)):
            report.add("MATERIALS_INVALID", "error", "Materials must be a list.", "materials")
        else:
            report.metrics["materials"] = len(materials)
            if not materials:
                report.add("MATERIAL_MISSING", "warning", "No material is reported.", "materials")

def run_validators(data: dict[str, Any], validators: list[Validator] | None = None) -> InspectionReport:
    if not isinstance(data, dict):
        raise TypeError("Validator input must be a dictionary.")
    report = InspectionReport(str(data.get("name") or "UnnamedAsset"))
    for validator in validators or [validate_mesh, validate_uv, validate_material]:
        try:
            validator(data, report)
        except Exception as exc:
            report.add("VALIDATOR_FAILED", "error", f"{getattr(validator, '__name__', 'validator')} failed: {type(exc).__name__}: {exc}")
    return report
