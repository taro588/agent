"""3ds Max integration helpers for the GameArt Toolkit.

This module only generates explicit launcher scripts. It never imports or
executes third-party plugin code during Python startup.
"""
from __future__ import annotations
from pathlib import Path
import json
import re

def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_") or "Plugin"

def build_plugin_launcher(plugin_name: str, plugin_path: str | Path, candidates: list[str]) -> str:
    root = Path(plugin_path).resolve()
    safe = _safe_name(plugin_name)
    candidate_lines = [f'local p = @"{str((root / rel).resolve()).replace(chr(92), chr(92)*2)}"' for rel in candidates]
    joined = "\n".join(candidate_lines)
    return f'''/* GameArt AI Toolkit explicit launcher: {plugin_name}
   This MacroScript is intentionally manual. Review the upstream plugin before running it. */
macroScript GameArt_{safe}
    category:"GameArt AI Toolkit"
    tooltip:"GameArt AI Toolkit - {plugin_name}"
    buttonText:"{plugin_name}"
(
    on execute do
    (
        local base = @"{str(root).replace(chr(92), chr(92)*2)}"
        local candidates = #(
{",
".join([f'            @"{str((root / rel).resolve()).replace(chr(92), chr(92)*2)}"' for rel in candidates])}
        )
        local found = false
        for p in candidates do
        (
            if doesFileExist p then
            (
                found = true
                local answer = queryBox ("Run plugin script?\n\n" + p) title:"GameArt AI Toolkit"
                if answer then
                (
                    try(fileIn p)catch(messageBox ("Plugin failed to run:\n" + p) title:"GameArt AI Toolkit")
                )
                exit
            )
        )
        if not found then
            messageBox ("No configured entry script was found in:\n" + base) title:"GameArt AI Toolkit"
    )
)
'''
