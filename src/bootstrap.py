"""Host-safe Toolkit bootstrap entry point.

This module is intentionally dependency-light. It never imports Maya, 3ds Max,
third-party plugins, or AI providers during import.
"""
from __future__ import annotations
import logging
from typing import Any, Callable

log = logging.getLogger("gameart.bootstrap")

def bootstrap(start_callback: Callable[[], Any] | None = None) -> Any:
    if start_callback is None:
        return {"status": "ready", "mode": "standalone"}
    try:
        return start_callback()
    except Exception as exc:
        log.exception("Toolkit bootstrap failed; host application remains available.")
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
