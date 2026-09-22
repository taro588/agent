from src.installer_app import InstallerApp

def test_doctor_and_repair_methods_exist():
    assert callable(InstallerApp.doctor)
    assert callable(InstallerApp.auto_repair)
