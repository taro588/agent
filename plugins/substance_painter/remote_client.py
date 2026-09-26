"""Official Adobe Substance 3D Painter Remote Scripting client."""
from __future__ import annotations
import base64
import json
from http.client import HTTPConnection
from typing import Any

ALLOWED_COMMANDS = {
    "project.info",
    "texture_sets.list",
    "texture_set.channel.add",
    "layers.list",
    "layers.selected",
    "layer.selected_fill_basecolor.set",
    "layer.fill_color.create",
    "layer.selected.mask.add",
    "layer.selected.smart_mask.add",
    "smart_material.add",
    "resource.search",
    "resource.import",
    "project.save",
    "textures.export",
    "textures.export.preview",
    "textures.export.presets.list",
    "bake.selected.start",
    "bake.highpoly.set",
}

class PainterRemoteError(RuntimeError):
    pass

class PainterRemote:
    def __init__(self, host="127.0.0.1", port=60041, timeout=3600):
        self.host, self.port, self.timeout = host, port, timeout

    def _post_python(self, script: str) -> str:
        payload = json.dumps({
            "python": base64.b64encode(script.encode("utf-8")).decode("ascii")
        }).encode("utf-8")
        connection = HTTPConnection(self.host, self.port, timeout=self.timeout)
        try:
            connection.request("POST", "/run.json", payload,
                               {"Content-Type": "application/json",
                                "Accept": "application/json"})
            response = connection.getresponse()
            body = response.read().decode("utf-8", errors="replace")
            if response.status >= 400:
                raise PainterRemoteError(
                    f"Painter remote scripting HTTP {response.status}: {body}"
                )
            return body
        finally:
            connection.close()

    def health(self) -> dict[str, Any]:
        return self.dispatch("project.info")

    def dispatch(self, command: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if command not in ALLOWED_COMMANDS:
            raise PainterRemoteError(f"Command is not allow-listed: {command}")
        payload = json.dumps({"command": command, "arguments": arguments or {}},
                             ensure_ascii=False)
        script = (
            "import gameart_ai_toolkit\n"
            f"print(gameart_ai_toolkit.dispatch_json({payload!r}))\n"
        )
        raw = self._post_python(script)
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
