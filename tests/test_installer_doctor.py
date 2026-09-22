from src.installer_app import InstallerApp

def test_doctor_helpers(tmp_path):
    assert InstallerApp._path_writable(tmp_path / "x")
    assert not InstallerApp._path_writable(tmp_path / "x" / "file" / "child")
