from pathlib import Path
from src.core.plugin_installer import PluginInstaller

def test_entrypoint_detection_is_conservative(tmp_path):
    root=tmp_path/"plugin"
    root.mkdir()
    (root/"main.py").write_text("print('library')", encoding="utf-8")
    (root/"userSetup.py").write_text("# maya startup", encoding="utf-8")
    (root/"tool.ms").write_text("-- max tool", encoding="utf-8")
    found=PluginInstaller(tmp_path/"toolkit")._detect_entrypoints(root)
    assert {"type":"maya_user_setup","path":"userSetup.py","load":"startup_candidate"} in found
    assert not any(x["path"]=="main.py" for x in found)
    assert not any(x["path"]=="tool.ms" for x in found)
