"""GameArt AI Toolkit for Adobe Substance 3D Painter.

All scene/material/texture mutations are performed through Adobe's official
Substance 3D Painter Python API. No UI automation or private APIs are used.
"""
from __future__ import annotations

import json
from typing import Any

import substance_painter as sp
import substance_painter.project
import substance_painter.textureset
import substance_painter.layerstack
import substance_painter.export
import substance_painter.colormanagement
import substance_painter.ui

PLUGIN_NAME = "GameArt AI Toolkit"
PLUGIN_VERSION = "2.1.13"
plugin_widgets = []


def _active_stack():
    if not substance_painter.project.is_open():
        raise RuntimeError("No Substance 3D Painter project is open.")
    return substance_painter.textureset.get_active_stack()


def _color(value: Any):
    if isinstance(value, str):
        text = value.strip().lstrip("#")
        if len(text) != 6:
            raise ValueError("Color must be a 6-digit hex value such as #FF8800.")
        rgb = [int(text[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        return substance_painter.colormanagement.Color(
            rgb[0], rgb[1], rgb[2]
        )
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return substance_painter.colormanagement.Color(
            float(value[0]), float(value[1]), float(value[2])
        )
    raise ValueError("Color must be #RRGGBB or [r,g,b].")


def project_info() -> dict[str, Any]:
    if not substance_painter.project.is_open():
        return {"open": False}
    return {
        "open": True,
        "version": PLUGIN_VERSION,
        "painter_version": str(substance_painter.application.version()),
        "project": substance_painter.project.file_path(),
    }


def texture_sets() -> list[dict[str, Any]]:
    stack = _active_stack()
    return [{"name": stack.material().name(), "uid": stack.uid()}]


def layers() -> list[dict[str, Any]]:
    stack = _active_stack()
    nodes = substance_painter.layerstack.get_nodes(stack)
    result = []
    for node in nodes:
        result.append({
            "name": node.get_name(),
            "uid": node.uid(),
            "type": type(node).__name__,
        })
    return result


def selected_layers() -> list[dict[str, Any]]:
    stack = _active_stack()
    return [{
        "name": node.get_name(),
        "uid": node.uid(),
        "type": type(node).__name__,
    } for node in substance_painter.layerstack.get_selected_nodes(stack)]


def set_selected_fill_basecolor(color: Any) -> dict[str, Any]:
    stack = _active_stack()
    selected = substance_painter.layerstack.get_selected_nodes(stack)
    target = _color(color)
    changed = []
    for node in selected:
        if isinstance(node, substance_painter.layerstack.FillLayerNode):
            source = node.get_source(substance_painter.textureset.ChannelType.BaseColor)
            source.set_color(target)
            changed.append(node.get_name())
    if not changed:
        raise RuntimeError("No selected Fill Layer with a BaseColor source.")
    return {"changed": changed, "color": color}


def create_fill_color(name: str, color: Any) -> dict[str, Any]:
    stack = _active_stack()
    position = substance_painter.layerstack.InsertPosition.from_textureset_stack(stack)
    fill = substance_painter.layerstack.insert_fill(position)
    fill.set_name(str(name))
    fill.set_source(
        substance_painter.textureset.ChannelType.BaseColor,
        _color(color),
    )
    substance_painter.layerstack.set_selected_nodes([fill])
    return {"name": fill.get_name(), "uid": fill.uid(), "color": color}


def save_project() -> dict[str, Any]:
    if not substance_painter.project.is_open():
        raise RuntimeError("No project is open.")
    substance_painter.project.save()
    return {"saved": True, "project": substance_painter.project.file_path()}


def export_textures(config: dict[str, Any]) -> dict[str, Any]:
    _active_stack()
    substance_painter.export.export_project_textures(config)
    return {"export_started": True, "config": config}


COMMANDS = {
    "project.info": project_info,
    "texture_sets.list": texture_sets,
    "layers.list": layers,
    "layers.selected": selected_layers,
    "layer.selected_fill_basecolor.set": set_selected_fill_basecolor,
    "layer.fill_color.create": create_fill_color,
    "project.save": save_project,
    "textures.export": export_textures,
}


def dispatch(command: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    if command not in COMMANDS:
        raise ValueError(f"Unsupported GameArt command: {command}")
    result = COMMANDS[command](**dict(arguments or {}))
    return {"ok": True, "command": command, "result": result}


def dispatch_json(payload: str) -> str:
    try:
        data = json.loads(payload)
        return json.dumps(
            dispatch(data["command"], data.get("arguments")),
            ensure_ascii=False,
        )
    except Exception as exc:
        return json.dumps(
            {"ok": False, "error": f"{type(exc).__name__}: {exc}"},
            ensure_ascii=False,
        )


def _show_project_info():
    try:
        info = project_info()
        substance_painter.ui.display_message(
            f"{PLUGIN_NAME} {PLUGIN_VERSION} | "
            f"Painter {info.get('painter_version', 'unknown')} | "
            f"Project open: {info.get('open', False)}"
        )
    except Exception as exc:
        substance_painter.ui.display_error(str(exc))


def start_plugin():
    action = substance_painter.ui.create_action(
        PLUGIN_NAME,
        triggered=_show_project_info,
    )
    substance_painter.ui.add_action(
        substance_painter.ui.ApplicationMenu.Plugins,
        action,
    )
    plugin_widgets.append(action)


def close_plugin():
    for widget in plugin_widgets:
        substance_painter.ui.delete_ui_element(widget)
    plugin_widgets.clear()


if __name__ == "__main__":
    start_plugin()
