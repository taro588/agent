"""Offline contract checks for the Painter integration."""
import json
from plugins.substance_painter.remote_client import ALLOWED_COMMANDS

with open("plugins/substance_painter/tool_schema.json", encoding="utf-8") as f:
    schema = json.load(f)

schema_commands = set(schema["operations"])
assert schema_commands == ALLOWED_COMMANDS
assert schema["policy"]["arbitrary_python"] is False
assert schema["policy"]["ui_automation"] is False
assert schema["policy"]["private_api"] is False

print(f"Painter tool contract OK: {len(ALLOWED_COMMANDS)} commands")
