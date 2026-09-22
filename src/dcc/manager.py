from __future__ import annotations

from typing import Any

from .session import DCCSession


class DCCManager:
    """Registry for independent DCC sessions with failure isolation."""

    def __init__(self) -> None:
        self._sessions: dict[str, DCCSession] = {}

    def register(self, name: str, session: DCCSession, *, replace: bool = False) -> None:
        if not name:
            raise ValueError("DCC name cannot be empty.")
        if name in self._sessions and not replace:
            raise KeyError(f"DCC already registered: {name}")
        self._sessions[name] = session

    def get(self, name: str) -> DCCSession | None:
        """Return a registered session without exposing the internal mapping."""
        return self._sessions.get(name)

    def connect_all(self) -> dict[str, bool]:
        result = {}
        for name, session in self._sessions.items():
            try:
                result[name] = session.connect()
            except Exception as exc:
                session.connected = False
                session.last_error = f"{type(exc).__name__}: {exc}"
                result[name] = False
        return result

    def execute(self, name: str, operation: str, **kwargs: Any) -> dict[str, Any]:
        session = self._sessions.get(name)
        if session is None:
            return {"ok": False, "dcc": name, "operation": operation, "error": "DCC is not registered"}
        try:
            result = session.execute(operation, **kwargs)
            result["dcc"] = name
            return result
        except Exception as exc:
            return {"ok": False, "dcc": name, "operation": operation, "error": f"{type(exc).__name__}: {exc}"}

    def status(self) -> dict[str, dict]:
        result = {}
        for name, session in self._sessions.items():
            try:
                result[name] = session.info()
            except Exception as exc:
                result[name] = {
                    "dcc": name,
                    "available": False,
                    "connected": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
        return result
