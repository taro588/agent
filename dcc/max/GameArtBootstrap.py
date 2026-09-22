"""Failure-safe 3ds Max bootstrap entry point."""
from src.dcc.bootstrap import safe_bootstrap

def start():
    return safe_bootstrap(lambda: {"status": "max_bootstrap_ready"})
