from pathlib import Path
from src.core.host_integration import HostIntegrator

def test_maya_loader_includes_plugin_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("GAMEART_MAYA_USER_SCRIPTS", str(tmp_path/"maya"))
    root=tmp_path/"toolkit"; (root/"plugin-manifests").mkdir(parents=True)
    p=root/"plugins"/"maya"/"demo"; p.mkdir(parents=True)
    (root/"plugin-manifests"/"demo.json").write_text('{"name":"demo","host":"maya","path":"'+str(p).replace("\\","/")+'"}', encoding="utf-8")
    out=HostIntegrator(root).register_maya()
    assert out.ok
    assert str(p) in Path(out.path).read_text(encoding="utf-8")

def test_max_loader_includes_plugin_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("GAMEART_MAX_USER_STARTUP", str(tmp_path/"max"))
    root=tmp_path/"toolkit"; (root/"host-loaders"/"3ds_max").mkdir(parents=True)
    (root/"plugin-manifests").mkdir(parents=True)
    p=root/"plugins"/"3ds_max"/"demo"; p.mkdir(parents=True)
    (root/"plugin-manifests"/"demo.json").write_text('{"name":"demo","host":"3ds_max","path":"'+str(p).replace("\\","/")+'"}', encoding="utf-8")
    out=HostIntegrator(root).register_max()
    assert out.ok
    assert "pathConfig.appendPath" in Path(out.path).read_text(encoding="utf-8")
