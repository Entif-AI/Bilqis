"""Persistent BAMF human-run operator entrypoint."""
from importlib import import_module


def __getattr__(name: str):
    if name not in {"BamfOperatorResult", "operate_bamf"}:
        raise AttributeError(name)
    value = getattr(import_module(".session", __name__), name)
    globals()[name] = value
    return value

__all__ = ("BamfOperatorResult", "operate_bamf")
