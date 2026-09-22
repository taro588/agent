import unittest

try:
    from src.installer_app import InstallerApp
except ModuleNotFoundError as exc:
    if exc.name != 'tkinter': raise
    InstallerApp = None

@unittest.skipIf(InstallerApp is None, 'tkinter is unavailable on this Linux runner')
def test_doctor_and_repair_methods_exist():
    assert callable(InstallerApp.doctor)
    assert callable(InstallerApp.auto_repair)
