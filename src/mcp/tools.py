"""Structured MCP-style tool registry.

No MCP SDK is required by the core. A transport adapter can expose these
contracts later without coupling the toolkit to a particular SDK.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., Any]
    input_schema: dict[str, Any] = field(default_factory=dict)

class ToolRegistry:
    def __init__(self, tools: list[ToolSpec] | None = None):
        self._tools: dict[str, ToolSpec] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: ToolSpec, *, replace: bool = False) -> None:
        if not tool.name:
            raise ValueError("Tool name cannot be empty.")
        if tool.name in self._tools and not replace:
            raise KeyError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def names(self) -> list[str]:
        return sorted(self._tools)

    def describe(self) -> list[dict[str, Any]]:
        return [
            {"name": tool.name, "description": tool.description, "input_schema": dict(tool.input_schema)}
            for tool in sorted(self._tools.values(), key=lambda item: item.name)
        ]

    def call(self, name: str, **arguments: Any) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            return {"ok": False, "tool": name, "error": "Tool is not registered."}
        try:
            return {"ok": True, "tool": name, "result": tool.handler(**arguments)}
        except Exception as exc:
            return {"ok": False, "tool": name, "error": f"{type(exc).__name__}: {exc}"}
