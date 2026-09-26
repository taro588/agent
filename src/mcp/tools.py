"""Structured tool registry and OpenAI function-tool bridge."""
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
    def __init__(self, tools=None):
        self._tools={}
        for tool in tools or []: self.register(tool)

    def register(self, tool, *, replace=False):
        if not tool.name: raise ValueError("Tool name cannot be empty.")
        if tool.name in self._tools and not replace: raise KeyError(f"Tool already registered: {tool.name}")
        self._tools[tool.name]=tool

    def names(self): return sorted(self._tools)

    def describe(self):
        return [{"name":t.name,"description":t.description,"input_schema":dict(t.input_schema)}
                for t in sorted(self._tools.values(),key=lambda x:x.name)]

    def openai_tools(self):
        return [{"type":"function","name":t.name,"description":t.description,
                 "parameters":dict(t.input_schema or {"type":"object","properties":{},
                 "additionalProperties":False}),"strict":True} for t in self._tools.values()]

    def handlers(self): return {name:t.handler for name,t in self._tools.items()}

    def call(self,name,**arguments):
        tool=self._tools.get(name)
        if tool is None: return {"ok":False,"tool":name,"error":"Tool is not registered."}
        try: return {"ok":True,"tool":name,"result":tool.handler(**arguments)}
        except Exception as exc: return {"ok":False,"tool":name,"error":f"{type(exc).__name__}: {exc}"}
