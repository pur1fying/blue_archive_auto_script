"""Versioned plugin host. Third-party Python is trusted code, never a sandbox."""

from .errors import PluginError

__all__ = ["PluginError", "PluginManager"]


def __getattr__(name):
    if name == "PluginManager":
        from .manager import PluginManager
        return PluginManager
    raise AttributeError(name)
