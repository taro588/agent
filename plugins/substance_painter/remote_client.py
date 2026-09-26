"""Official Adobe Substance 3D Painter Remote Scripting client.

This client does not automate the UI. It talks to Painter's documented
/run.json remote-scripting endpoint and asks the installed GameArt plugin to
execute one allow-listed command through Painter's official Python API.
"""
from __future__ import annotations

import base64
import json
from http.client import HTTPConnection
from typing import Any


class PainterRemoteError(RuntimeError):
    pass


class PainterRemote:
    def __init__(self, host: str = "127.0.0.1", port: int = 60041, timeout: int = 3600):
        self.host = host
        self.port = port
        self.timeout = timeout

    def _post_python(self, script: str) -> str:
        payload = json.dumps({
            "python": base64.b64encode(script.encode("utf-8")).decode("ascii")
        }).encode("utf-8")
        connection = HTTPConnection(self.host, self.port, timeout=self.timeout)
        try:
            connection.request(
                "POST",
                "/run.json",
                payload,
                {"Content-Type": "application/json", "Accept": "application/json"},
            )
            response = connection.getresponse()
            body = response.read().decode("utf-8", errors="replace")
            if response.status >= 400:
                raise PainterRemoteError(f"Painter remote scripting HTTP {response.status}: {body}")
            return body
        finally:
            connection.close()

    def dispatch(self, command: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = json.dumps({
            "command": command,
            "arguments": arguments or {},
        }, ensure_ascii=False)
        script = (
            "import json\n"
            "import sys\n"
            "sys.path.insert(0, r'')\n"
            "import gameart_ai_toolkit\n"
            f"print(gameart_ai_toolkit.dispatch_json({payload!r}))\n"
        )
        raw = self._post_python(script)
        # Painter can return a trailing newline around print() output.
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            raise PainterRemoteError("Painter returned an empty response.")
        try:
            result = json.loads(lines[-1])
        except json.JSONDecodeError as exc:
            raise PainterRemoteError(f"Invalid Painter plugin response: {raw}") from exc
        if not result.get("ok"):
            raise PainterRemoteError(result.get("error", "Painter command failed."))
        return result
