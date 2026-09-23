from src.dcc.detector import DCCInstallation, compatibility

def test_supported_versions():
    assert compatibility("maya","2022")
    assert compatibility("maya","2026")
    assert compatibility("3ds_max","2022")
    assert compatibility("3ds_max","2026")

def test_unknown_version_is_not_supported():
    assert not compatibility("maya","2021")
    assert not compatibility("3ds_max","2027")

def test_detection_model():
    item=DCCInstallation("maya","2025",r"C:\Program Files\Autodesk\Maya\2025","filesystem")
    assert item.host=="maya"
    assert item.version=="2025"


def test_registry_enumkey_returns_single_value(monkeypatch):
    from src.dcc.detector import _scan_registry
    class FakeWinreg:
        HKEY_LOCAL_MACHINE = 1
        HKEY_CURRENT_USER = 2
        KEY_READ = 0
        KEY_WOW64_64KEY = 0
        KEY_WOW64_32KEY = 0
        def OpenKey(self, *args): return self
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def EnumKey(self, root, index):
            if index == 0: return "2025"
            raise OSError()
        def EnumValue(self, key, index):
            if index == 0: return ("InstallPath", r"C:\\NotPresent", 1)
            raise OSError()
    monkeypatch.setattr("src.dcc.detector._windows_registry", lambda: FakeWinreg())
    assert _scan_registry(r"SOFTWARE\\Autodesk\\Maya", "maya") == []
