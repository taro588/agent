from src.core.plugin_installer import PluginInstaller

def test_verify_missing_plugin(tmp_path):
    result=PluginInstaller(tmp_path/"toolkit").verify("texture-importer")
    assert result["status"]=="needs_attention"
    assert any(not x["ok"] for x in result["checks"])

def test_verify_all_empty(tmp_path):
    assert PluginInstaller(tmp_path/"toolkit").verify_all()==[]
