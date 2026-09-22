from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import DCCAdapter


@dataclass
class DCCSession:
    """Failure boundary around one DCC adapter.

    Native DCC/plugin exceptions are converted to structured results so a
    broken capability cannot terminate the Toolkit process.
    """

    adapter: DCCAdapter
    connected: bool = False
    last_error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def connect(self) -> bool:
        try:
            self.connected = bool(self.adapter.is_available())
            self.last_error = None if self.connected else "DCC API is not available"
        except Exception as exc:
            self.connected = False
            self.last_error = f"{type(exc).__name__}: {exc}"
        return self.connected

    def info(self) -> dict[str, Any]:
        try:
            result = self.adapter.status()
        except Exception as exc:
            result = {
                "dcc": getattr(self.adapter, "name", "unknown"),
                "available": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
        result.update({"connected": self.connected, "error": self.last_error})
        if self.connected:
            try:
                result["scene"] = self.adapter.scene_info()
            except Exception as exc:
                result["scene_error"] = f"{type(exc).__name__}: {exc}"
        return result

    def execute(self, operation: str, **kwargs: Any) -> dict[str, Any]:
        """Execute one DCC operation without letting its exception escape."""
        if not self.connected:
            return {
                "ok": False,
                "operation": operation,
                "error": self.last_error or "DCC session is not connected",
            }
        try:
            return {"ok": True, "operation": operation, "result": self.adapter.execute(operation, **kwargs)}
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            return {"ok": False, "operation": operation, "error": self.last_error}
