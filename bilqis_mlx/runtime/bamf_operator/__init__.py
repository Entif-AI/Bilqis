"""Persistent BAMF human-run operator entrypoint."""
from importlib import import_module


def __getattr__(name: str):
    if name == "read_latest_run_stop_receipt":
        value = getattr(import_module(".session_parts.stop_receipt", __name__), name)
        globals()[name] = value
        return value
    if name not in {"BamfOperatorResult", "operate_bamf"}:
        raise AttributeError(name)
    value = getattr(import_module(".session", __name__), name)
    globals()[name] = value
    return value

__all__ = (
    "BamfOperatorResult", "operate_bamf", "read_latest_run_stop_receipt",
)
