"""OpenAI Responses API provider with structured tool calling."""
from __future__ import annotations
import json, os
from dataclasses import dataclass
from typing import Any, Callable, Protocol

@dataclass
class ProviderResult:
    ok: bool
    provider: str
    result: Any = None
    error: str | None = None

class AIProvider(Protocol):
    name: str
    def run(self, prompt: str, tools: list[dict[str, Any]], handlers: dict[str, Callable[..., Any]], **kwargs: Any) -> ProviderResult: ...

class OpenAIResponsesProvider:
    name = "openai"
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.6")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

    def run(self, prompt, tools, handlers, **kwargs):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the official OpenAI Python SDK: pip install openai") from exc
        max_rounds = int(kwargs.pop("max_tool_rounds", 20))
        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(model=self.model, input=prompt, tools=tools, **kwargs)
        for _ in range(max_rounds):
            calls = [x for x in response.output if getattr(x, "type", None) == "function_call"]
            if not calls:
                return ProviderResult(True, self.name, response)
            outputs = []
            for call in calls:
                try:
                    handler = handlers.get(call.name)
                    if handler is None:
                        raise RuntimeError(f"Tool '{call.name}' is not registered.")
                    args = json.loads(call.arguments or "{}")
                    result = {"ok": True, "result": handler(**args)}
                except Exception as exc:
                    result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
                outputs.append({"type":"function_call_output","call_id":call.call_id,
                                "output":json.dumps(result,ensure_ascii=False)})
            response = client.responses.create(model=self.model, previous_response_id=response.id,
                                              input=outputs, tools=tools)
        return ProviderResult(False, self.name, error="Maximum tool-call rounds exceeded.")

class NoneProvider:
    name = "none"
    def run(self, prompt, tools, handlers, **kwargs):
        return ProviderResult(False, self.name, error="No AI provider is configured.")

def get_provider(name=None):
    normalized=(name or os.getenv("GAMEART_AI_PROVIDER","none")).strip().lower()
    if normalized=="openai": return OpenAIResponsesProvider()
    if normalized in {"","none","null"}: return NoneProvider()
    raise RuntimeError(f"AI provider '{normalized}' is not configured.")
