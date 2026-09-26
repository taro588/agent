"""Offline checks for documented Painter installation paths."""
from pathlib import Path
from plugins.substance_painter.installer import PAINTER_PLUGIN_DIR, REMOTE_FLAG, REMOTE_PORT

assert PAINTER_PLUGIN_DIR == Path.home() / "Documents" / "Adobe" / "Adobe Substance 3D Painter" / "python" / "plugins"
assert REMOTE_FLAG == "--enable-remote-scripting"
assert REMOTE_PORT == 60041
print("Painter installation contract OK")
