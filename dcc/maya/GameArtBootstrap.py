"""Maya bootstrap: initialize GameArt Toolkit without executing third-party code blindly."""
from src.dcc.bootstrap import safe_bootstrap
from src.dcc.detector import compatibility

def start(version=None):
    def _start():
        if version is not None and not compatibility("maya", str(version)):
            return {"status":"unsupported_maya","version":str(version)}
        from src.core.plugin_loader import PluginLoader
        return {"status":"maya_bootstrap_ready","plugins":PluginLoader(__import__("os").environ.get("GAMEART_TOOLKIT_ROOT", ".")).discover()}
    return safe_bootstrap(_start)
