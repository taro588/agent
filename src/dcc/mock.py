"""Mock adapter used by tests and headless development."""
from __future__ import annotations

from typing import Any

from .base import DCCAdapter


class MockAdapter(DCCAdapter):
    name = "mock"

    def is_available(self) -> bool:
        return True

    def scene_info(self) -> dict[str, Any]:
        return {"scene": "mock", "objects": 0}

    def ping(self) -> dict[str, Any]:
        return {"ok": True, "dcc": self.name}
