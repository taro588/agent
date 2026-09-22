"""3ds Max DCC adapter. PyMXS is imported lazily so the toolkit can run independently."""
from __future__ import annotations
from typing import Any
from src.dcc.base import DCCAdapter

class MaxAdapter(DCCAdapter):
    name = "3ds_max"
    def _rt(self):
        try:
            import pymxs
            return pymxs.runtime
        except Exception:
            return None
    def is_available(self) -> bool:
        return self._rt() is not None
    def scene_info(self) -> dict[str, Any]:
        rt = self._rt()
        if rt is None:
            raise RuntimeError("3ds Max PyMXS API is unavailable")
        return {"scene": str(rt.maxFilePath) if rt.maxFilePath else "", "objects": int(rt.objects.count), "selection": int(rt.selection.count)}
    def ping(self) -> dict[str, Any]:
        return {"ok": self.is_available(), "dcc": self.name}
