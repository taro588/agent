from dcc.maya.GameArtBootstrap import start as maya_start
from dcc.max.GameArtBootstrap import start as max_start

def test_maya_supported():
    r=maya_start("2025")
    assert r["status"]=="maya_bootstrap_ready"

def test_maya_unsupported():
    r=maya_start("2021")
    assert r["status"]=="unsupported_maya"

def test_max_supported():
    r=max_start("2025")
    assert r["status"]=="max_bootstrap_ready"

def test_max_unsupported():
    r=max_start("2021")
    assert r["status"]=="unsupported_3ds_max"
