"""Maya DCC adapter. Imports Maya APIs lazily so the toolkit remains usable outside Maya."""
from __future__ import annotations
from typing import Any
from src.dcc.base import DCCAdapter

class MayaAdapter(DCCAdapter):
    name = "maya"
    def _cmds(self):
        try:
            import maya.cmds as cmds
            return cmds
        except Exception:
            return None
    def is_available(self) -> bool:
        return self._cmds() is not None
    def scene_info(self) -> dict[str, Any]:
        cmds = self._cmds()
        if cmds is None:
            raise RuntimeError("Maya Python API is unavailable")
        return {"scene": cmds.file(query=True, sceneName=True) or "", "objects": len(cmds.ls(dag=True, long=True) or []), "meshes": len(cmds.ls(type="mesh", long=True) or []), "selection": cmds.ls(selection=True, long=True) or []}
    def ping(self) -> dict[str, Any]:
        return {"ok": self.is_available(), "dcc": self.name}
