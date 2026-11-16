"""CP05 guarded operator command lifecycle."""

from .model import CommandMode

__all__ = ("CommandManager", "CommandMode")


def __getattr__(name: str):
    if name == "CommandManager":
        from .manager import CommandManager
        return CommandManager
    raise AttributeError(name)
