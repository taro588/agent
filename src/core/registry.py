"""Small dependency-free registry for core capabilities and adapters."""
from __future__ import annotations
from typing import Any

class Registry:
    def __init__(self) -> None:
        self._items: dict[str, Any] = {}

    def register(self, name: str, item: Any, *, replace: bool = False) -> None:
        if not name:
            raise ValueError("Registry name cannot be empty.")
        if name in self._items and not replace:
            raise KeyError(f"Already registered: {name}")
        self._items[name] = item

    def get(self, name: str, default: Any = None) -> Any:
        return self._items.get(name, default)

    def has(self, name: str) -> bool:
        return name in self._items

    def unregister(self, name: str) -> Any:
        return self._items.pop(name, None)

    def names(self) -> list[str]:
        return sorted(self._items)

    def clear(self) -> None:
        self._items.clear()

    def as_dict(self) -> dict[str, Any]:
        return dict(self._items)
