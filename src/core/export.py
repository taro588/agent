"""Export contracts independent of Maya/3ds Max."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

@dataclass
class ExportResult:
    ok: bool
    format: str
    path: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

def validate_export_path(path: str | Path, allowed_suffixes: tuple[str, ...] = (".fbx",".usd",".usda",".usdc")) -> Path:
    target = Path(path).expanduser()
    if not target.name: raise ValueError("Export path must contain a filename.")
    if target.suffix.lower() not in allowed_suffixes: raise ValueError(f"Unsupported export format: {target.suffix}")
    return target

def safe_export(exporter: Callable[[], Any], path: str | Path, format_name: str) -> ExportResult:
    try:
        target=validate_export_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        result=exporter()
        if not target.exists():
            return ExportResult(
                False, format_name, str(target),
                "Exporter completed but did not create the requested output file.",
                {"result": result},
            )
        return ExportResult(True, format_name, str(target), metadata={"result": result})
    except Exception as exc:
        return ExportResult(False, format_name, str(path), f"{type(exc).__name__}: {exc}")
