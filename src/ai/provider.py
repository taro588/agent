"""Optional AI provider abstraction.

No provider SDK or API key is required to import the core toolkit.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol

class AIProvider(Protocol):
    name: str
    def generate(self, prompt: str, **kwargs: Any) -> Any: ...

@dataclass
class ProviderResult:
    ok: bool
    provider: str
    result: Any = None
    error: str | None = None

class NullProvider:
    name = "none"
    def generate(self, prompt: str, **kwargs: Any) -> ProviderResult:
        return ProviderResult(False, self.name, error="No AI provider is configured.")

def get_provider(name: str | None = None) -> AIProvider:
    normalized = (name or "none").strip().lower()
    if normalized in {"", "none", "null"}:
        return NullProvider()
    raise RuntimeError(f"AI provider '{normalized}' is not installed/configured.")
