"""High-level structured tools over DCC sessions."""
from __future__ import annotations
from typing import Any
from src.dcc.manager import DCCManager
from src.mcp.tools import ToolRegistry, ToolSpec

def build_dcc_tool_registry(manager: DCCManager) -> ToolRegistry:
    registry = ToolRegistry()

    def scene_get_info(dcc: str) -> dict[str, Any]:
        session = manager.get(dcc)
        if session is None:
            return {"ok": False, "dcc": dcc, "error": f"Unknown DCC: {dcc}"}
        return session.info()

    def scene_ping(dcc: str) -> dict[str, Any]:
        return manager.execute(dcc, "ping")

    registry.register(ToolSpec(
        "scene.get_info",
        "Get lightweight scene information from a connected DCC.",
        scene_get_info,
        {"type": "object", "required": ["dcc"]},
    ))
    registry.register(ToolSpec(
        "scene.ping",
        "Check whether a DCC adapter is responsive.",
        scene_ping,
        {"type": "object", "required": ["dcc"]},
    ))
    return registry
