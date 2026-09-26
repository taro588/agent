# GameArt AI Toolkit — Substance 3D Painter

This integration uses Adobe Substance 3D Painter official Python API only for
Painter-side operations.

Execution path:
AI request -> structured GameArt command -> allow-listed dispatcher ->
Adobe Substance 3D Painter Python API -> validation/result.

No mouse/keyboard automation, screen scraping, private Painter APIs, or simulated
UI clicks are used.

Windows Painter 7.2+ Python plugin location:
%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Painter\python\plugins\

Supported commands:
- project.info
- texture_sets.list
- layers.list
- layers.selected
- layer.selected_fill_basecolor.set
- layer.fill_color.create
- project.save
- textures.export

Adobe documents Python plugins under python/plugins and documents Remote Scripting
on port 60041 using the /run.json endpoint when Painter is started with
--enable-remote-scripting.

The external agent should call only dispatch_json() with an allow-listed command.
It must never expose arbitrary Python execution to the AI.
