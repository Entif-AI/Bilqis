"""Immutable Model Forensics contracts with lazy registry/schema convenience exports."""
from importlib import import_module

__all__ = ("ALL_RECORD_TYPES", "RECORD_BY_SCHEMA", "JSON_SCHEMA_DIALECT", "record_schema", "schema_bundle")


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(name)
    module = "registry" if name in {"ALL_RECORD_TYPES", "RECORD_BY_SCHEMA"} else "schema"
    return getattr(import_module(f".{module}", __name__), name)
