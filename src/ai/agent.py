"""Dependency-free AI Agent orchestration contracts.

The agent layer plans work; it never imports Maya, 3ds Max, plugin SDKs, or
provider SDKs. Execution is delegated to registered structured tools.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from src.core.pipeline_guard import PipelineGuard

@dataclass(frozen=True)
class AgentStep:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    required: bool = True

@dataclass
class AgentPlan:
    intent: str
    steps: list[AgentStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentRunResult:
    ok: bool
    intent: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

class AgentPlanner:
    def plan(self, intent: str, steps: list[AgentStep], **metadata: Any) -> AgentPlan:
        if not str(intent).strip():
            raise ValueError("Agent intent cannot be empty.")
        return AgentPlan(str(intent), list(steps), dict(metadata))

class AgentExecutor:
    def __init__(self, tools: dict[str, Callable[..., Any]] | None = None):
        self.tools = dict(tools or {})
        self.guard = PipelineGuard()

    def register(self, name: str, callback: Callable[..., Any], *, replace: bool = False) -> None:
        if not name:
            raise ValueError("Tool name cannot be empty.")
        if name in self.tools and not replace:
            raise KeyError(f"Tool already registered: {name}")
        self.tools[name] = callback

    def run(self, plan: AgentPlan) -> AgentRunResult:
        results = []
        for step in plan.steps:
            callback = self.tools.get(step.tool)
            if callback is None:
                result = {"tool": step.tool, "ok": False, "error": "Tool is not registered."}
            else:
                guarded = self.guard.execute(
                    step.tool,
                    lambda cb=callback, args=dict(step.arguments): cb(**args),
                )
                result = {
                    "tool": step.tool,
                    "ok": guarded.ok,
                    "result": guarded.data.get("result") if guarded.ok else None,
                    "error": None if guarded.ok else guarded.message,
                }
            results.append(result)
            if not result["ok"] and step.required:
                return AgentRunResult(False, plan.intent, results, result["error"])
        return AgentRunResult(True, plan.intent, results)

class AgentReviewer:
    def review(self, run: AgentRunResult) -> dict[str, Any]:
        failed = [step for step in run.steps if not step.get("ok")]
        return {"ok": run.ok and not failed, "failed_steps": failed, "step_count": len(run.steps)}
