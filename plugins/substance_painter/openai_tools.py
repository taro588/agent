"""Bridge registered Painter commands into the GameArt tool registry."""
from __future__ import annotations
from typing import Any
from src.mcp.tools import ToolRegistry, ToolSpec
from plugins.substance_painter.remote_client import PainterRemote

def painter_registry(remote: PainterRemote | None = None) -> ToolRegistry:
    remote = remote or PainterRemote()
    return ToolRegistry([
        ToolSpec("sp.project.info","Read current Substance Painter project state.",remote.dispatch,
                 {"type":"object","properties":{"command":{"type":"string"}},"required":[],"additionalProperties":False}),
    ])

def build_painter_tools(remote: PainterRemote | None = None) -> ToolRegistry:
    remote = remote or PainterRemote()
    def call(command):
        return lambda **args: remote.dispatch(command,args)
    specs = [
        ("sp.project.info","Read current Substance Painter project state.",{}, "project.info"),
        ("sp.texture_sets.list","List Substance Painter texture sets.",{}, "texture_sets.list"),
        ("sp.layers.list","List layers in the active texture set.",{}, "layers.list"),
        ("sp.layers.selected","List selected Painter layers.",{}, "layers.selected"),
        ("sp.layer.basecolor.set","Set BaseColor on selected Fill Layers.",{"color":{"type":"string","description":"#RRGGBB color"}},"layer.selected_fill_basecolor.set"),
        ("sp.layer.fill.create","Create a Fill Layer with BaseColor.",{"name":{"type":"string"},"color":{"type":"string"}},"layer.fill_color.create"),
        ("sp.layer.mask.add","Add a mask to selected layers.",{"background":{"type":"string","enum":["Black","White"]}},"layer.selected.mask.add"),
        ("sp.smart_mask.add","Apply a Smart Mask resource to selected layers.",{"resource_query":{"type":"string"}},"layer.selected.smart_mask.add"),
        ("sp.smart_material.add","Insert a Smart Material from the Painter resource shelf.",{"resource_query":{"type":"string"}},"smart_material.add"),
        ("sp.resource.search","Search Painter resources.",{"query":{"type":"string"},"limit":{"type":"integer","minimum":1,"maximum":100}},"resource.search"),
        ("sp.resource.import","Import a resource into the project.",{"path":{"type":"string"},"usage":{"type":"string"},"name":{"type":["string","null"]}},"resource.import"),
        ("sp.channel.add","Add a Texture Set channel.",{"channel_type":{"type":"string"}},"texture_set.channel.add"),
        ("sp.bake.start","Start baking selected texture sets.",{}, "bake.selected.start"),
        ("sp.bake.highpoly.set","Set High Poly mesh for a texture set.",{"texture_set_name":{"type":"string"},"highpoly_path":{"type":"string"}},"bake.highpoly.set"),
        ("sp.export.preview","Preview Painter texture export.",{"config":{"type":"object"}},"textures.export.preview"),
        ("sp.export","Export Painter textures.",{"config":{"type":"object"}},"textures.export"),
        ("sp.project.save","Save the active Painter project.",{}, "project.save"),
    ]
    tools=[]
    for name,desc,props,command in specs:
        schema={"type":"object","properties":props,"required":list(props),"additionalProperties":False}
        tools.append(ToolSpec(name,desc,call(command),schema))
    return ToolRegistry(tools)
