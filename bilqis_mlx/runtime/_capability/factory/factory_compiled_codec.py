"""Strict JSON codec for generation-independent C05 compiled semantic state."""
from __future__ import annotations

import base64
from dataclasses import fields, is_dataclass
from enum import Enum
import importlib
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL


_DATACLASS = "dataclass"
_ENUM = "enum"
_TUPLE = "tuple"
_SET = "set"
_FROZENSET = "frozenset"
_BYTES = "bytes"
_PATH = "path"
_DICT = "dict"
_TYPE_KEY = "__c05_type__"
_SEMANTIC_PREFIX = "bilqis_mlx.semantics"
_KEY_VALUE_WIDTH = 2


def _invalid(reason):
    ErrorBus.raise_(SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID, reason=reason)


def _type_name(value) -> str:
    cls = type(value)
    return f"{cls.__module__}:{cls.__qualname__}"


def encode_compiled_value(value):
    """Encode only deterministic semantic/compiler records into JSON values."""
    if value is None or type(value) in (bool, int, float, str):
        return value
    if isinstance(value, Enum):
        return {_TYPE_KEY: _ENUM, "type": _type_name(value), "name": value.name}
    if is_dataclass(value) and type(value).__module__.startswith(_SEMANTIC_PREFIX):
        return {
            _TYPE_KEY: _DATACLASS,
            "type": _type_name(value),
            "fields": {
                item.name: encode_compiled_value(getattr(value, item.name))
                for item in fields(value) if item.init
            },
        }
    if type(value) is tuple:
        return {_TYPE_KEY: _TUPLE, "items": [encode_compiled_value(item) for item in value]}
    if type(value) is list:
        return [encode_compiled_value(item) for item in value]
    if type(value) is dict:
        return {
            _TYPE_KEY: _DICT,
            "items": [[encode_compiled_value(key), encode_compiled_value(item)]
                      for key, item in value.items()],
        }
    if type(value) is set:
        return {_TYPE_KEY: _SET, "items": [encode_compiled_value(item)
                                             for item in sorted(value, key=repr)]}
    if type(value) is frozenset:
        return {_TYPE_KEY: _FROZENSET, "items": [encode_compiled_value(item)
                                                   for item in sorted(value, key=repr)]}
    if type(value) is bytes:
        return {_TYPE_KEY: _BYTES, "value": base64.b64encode(value).decode("ascii")}
    if type(value) is Path:
        return {_TYPE_KEY: _PATH, "value": str(value)}
    _invalid(f"BAMF_C05_COMPILED_CACHE_UNSUPPORTED_TYPE:{_type_name(value)}")


def _resolve_type(name: str):
    if not isinstance(name, str) or ":" not in name:
        _invalid("BAMF_C05_COMPILED_CACHE_TYPE_INVALID")
    module_name, qualname = name.split(":", 1)
    if not module_name.startswith(_SEMANTIC_PREFIX) or "<locals>" in qualname:
        _invalid("BAMF_C05_COMPILED_CACHE_TYPE_FORBIDDEN")
    value = importlib.import_module(module_name)
    for component in qualname.split("."):
        value = getattr(value, component)
    return value


def decode_compiled_value(value):
    """Decode only the allowlisted semantic/compiler record family."""
    if value is None or type(value) in (bool, int, float, str):
        return value
    if type(value) is list:
        return [decode_compiled_value(item) for item in value]
    if type(value) is not dict:
        _invalid("BAMF_C05_COMPILED_CACHE_VALUE_INVALID")
    kind = value.get(_TYPE_KEY)
    if kind == _ENUM and set(value) == {_TYPE_KEY, "type", "name"}:
        cls = _resolve_type(value["type"])
        if not issubclass(cls, Enum):
            _invalid("BAMF_C05_COMPILED_CACHE_ENUM_INVALID")
        return cls[value["name"]]
    if kind == _DATACLASS and set(value) == {_TYPE_KEY, "type", "fields"}:
        cls = _resolve_type(value["type"])
        if not is_dataclass(cls) or not isinstance(value["fields"], dict):
            _invalid("BAMF_C05_COMPILED_CACHE_DATACLASS_INVALID")
        allowed = {item.name for item in fields(cls) if item.init}
        if set(value["fields"]) != allowed:
            _invalid("BAMF_C05_COMPILED_CACHE_DATACLASS_FIELDS_INVALID")
        return cls(**{
            key: decode_compiled_value(item)
            for key, item in value["fields"].items()
        })
    if kind in (_TUPLE, _SET, _FROZENSET) and set(value) == {_TYPE_KEY, "items"}:
        if not isinstance(value["items"], list):
            _invalid("BAMF_C05_COMPILED_CACHE_SEQUENCE_INVALID")
        items = [decode_compiled_value(item) for item in value["items"]]
        return (tuple(items) if kind == _TUPLE else
                set(items) if kind == _SET else frozenset(items))
    if kind == _DICT and set(value) == {_TYPE_KEY, "items"}:
        if (not isinstance(value["items"], list)
                or any(not isinstance(item, list) or len(item) != _KEY_VALUE_WIDTH
                       for item in value["items"])):
            _invalid("BAMF_C05_COMPILED_CACHE_DICT_INVALID")
        return {decode_compiled_value(key): decode_compiled_value(item)
                for key, item in value["items"]}
    if kind == _BYTES and set(value) == {_TYPE_KEY, "value"}:
        return base64.b64decode(value["value"], validate=True)
    if kind == _PATH and set(value) == {_TYPE_KEY, "value"}:
        return Path(value["value"])
    _invalid("BAMF_C05_COMPILED_CACHE_VALUE_INVALID")


__all__ = ("decode_compiled_value", "encode_compiled_value")
