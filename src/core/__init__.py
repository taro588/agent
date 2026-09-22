"""GameArt AI Toolkit core package.

Core modules must remain usable without Maya, 3ds Max, AI providers,
third-party plugins, or network access.
"""
from .safe import safe_call

__all__ = ["safe_call"]
