import unittest

try:
    from src.installer_app import InstallerApp
except ModuleNotFoundError as exc:
    if exc.name != 'tkinter': raise
    InstallerApp = None

@unittest.skipIf(InstallerApp is None, 'tkinter is unavailable on this Linux runner')
def test_doctor_helpers(tmp_path):
    assert InstallerApp._path_writable(tmp_path / "x")
    assert not InstallerApp._path_writable(tmp_path / "x" / "file" / "child")
