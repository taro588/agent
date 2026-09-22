"""Failure-safe Maya bootstrap entry point."""
from src.dcc.bootstrap import safe_bootstrap

def start():
    return safe_bootstrap(lambda: {"status": "maya_bootstrap_ready"})
