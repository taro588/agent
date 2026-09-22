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
