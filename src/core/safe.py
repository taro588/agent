"""Shared failure-isolation helpers for optional integrations."""
from __future__ import annotations
import logging
from typing import Callable, TypeVar

T = TypeVar("T")
log = logging.getLogger("gameart.safe")

def safe_call(callback: Callable[[], T], fallback: T, *, context: str = "") -> T:
    """Run an optional integration without allowing exceptions to escape."""
    try:
        return callback()
    except Exception:
        log.exception("Optional integration failed%s", f" ({context})" if context else "")
        return fallback
