from src.installer_app import InstallerApp

def test_install_app_source_contains_plugin_verification():
    import inspect
    source=inspect.getsource(InstallerApp.install_all)
    assert "verify_all" in source
    assert "plugin_verify" in source
