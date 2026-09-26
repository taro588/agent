# Substance 3D Painter Official API Integration

Architecture:
User -> OpenAI Responses API / Agent -> structured function call ->
GameArt command dispatcher -> Adobe Remote Scripting ->
Substance 3D Painter Python plugin -> official substance_painter API ->
Project / Texture Set / Layer / Material / Export.

Rule:
All actual Substance Painter operations must terminate in documented Adobe APIs.
UI automation is not an execution layer.

Current API operations:
- Project state and saving: substance_painter.project
- Texture sets: substance_painter.textureset
- Layer inspection and selection: substance_painter.layerstack
- Fill source/color: substance_painter.source.SourceUniformColor
- Color management: substance_painter.colormanagement.Color
- Texture export: substance_painter.export
- Plugin UI: substance_painter.ui

Remote control:
Adobe official Remote Scripting:
Adobe Substance 3D painter.exe --enable-remote-scripting
POST http://localhost:60041/run.json

The remote script should import the installed plugin and call its allow-listed
dispatcher. The AI never receives arbitrary Python execution.

GameArt AI Toolkit version: 2.1.13
