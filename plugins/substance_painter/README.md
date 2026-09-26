# Substance Painter installation

GameArt AI Toolkit installs the Python plugin using Adobe's documented user
plugin location on Windows 7.2+:

%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Painter\python\plugins\

The installer does not modify the Painter installation directory.

Remote control is launched with Adobe's documented:
--enable-remote-scripting

and uses the documented local endpoint:
http://127.0.0.1:60041/run.json

The plugin can also be managed through Painter's Python plugin system. Adobe
documents an additional plugin root via SUBSTANCE_PAINTER_PLUGINS_PATH when a
separate Toolkit-managed root is preferred.
