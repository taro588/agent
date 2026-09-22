"""3ds Max bootstrap: initialize GameArt Toolkit safely."""
from src.dcc.bootstrap import safe_bootstrap
from src.dcc.detector import compatibility

def start(version=None):
    def _start():
        if version is not None and not compatibility("3ds_max", str(version)):
            return {"status":"unsupported_3ds_max","version":str(version)}
        from src.core.plugin_loader import PluginLoader
        return {"status":"max_bootstrap_ready","plugins":PluginLoader(__import__("os").environ.get("GAMEART_TOOLKIT_ROOT", ".")).discover()}
    return safe_bootstrap(_start)
