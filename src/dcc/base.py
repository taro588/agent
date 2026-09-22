"""DCC adapter contracts for GameArt AI Toolkit.

The core layer talks to DCCs through this small, dependency-free interface.
Maya/3ds Max implementations may use their native Python APIs when available.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DCCAdapter(ABC):
    name = "unknown"

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the native DCC API is available in this process."""

    @abstractmethod
    def scene_info(self) -> dict[str, Any]:
        """Return lightweight information about the current scene."""

    def status(self) -> dict[str, Any]:
        return {"dcc": self.name, "available": self.is_available()}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        method = getattr(self, operation, None)
        if method is None or not callable(method):
            raise ValueError(f"Unsupported DCC operation: {operation}")
        return method(**kwargs)
