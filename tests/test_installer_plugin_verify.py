import unittest

try:
    from src.installer_app import InstallerApp
except ModuleNotFoundError as exc:
    if exc.name != 'tkinter': raise
    InstallerApp = None

@unittest.skipIf(InstallerApp is None, 'tkinter is unavailable on this Linux runner')
def test_install_app_source_contains_plugin_verification():
    import inspect
    source=inspect.getsource(InstallerApp.install_all)
    assert "verify_all" in source
    assert "plugin_verify" in source
