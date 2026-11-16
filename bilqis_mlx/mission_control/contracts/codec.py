"""Exact JSON-shaped encoding and decoding for CP02 records."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
import json
import types
from typing import get_args, get_origin, get_type_hints, Union

from .model import (
    ContractErrorCode, MissionControlContractError, WireRecord, is_text, is_wire_integer,
)


_VARIADIC_TUPLE_ARITY = 2


def _fail(code: ContractErrorCode, detail: str | None = None):
    raise MissionControlContractError(code, detail)


def _encode(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _encode(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_encode(item) for item in value]
    if type(value) is str:
        if not is_text(value):
            _fail(ContractErrorCode.PAYLOAD_INVALID, "unicode-scalar")
        return value
    if value is None or type(value) in (int, float, bool):
        return value
    _fail(ContractErrorCode.PAYLOAD_INVALID, type(value).__name__)


def encode_record(record: WireRecord) -> dict:
    if not isinstance(record, WireRecord) or not is_dataclass(record):
        _fail(ContractErrorCode.PAYLOAD_INVALID, "record")
    payload = _encode(record)
    return {"schema_version": record.schema_version, **payload}


def canonical_json(record: WireRecord) -> bytes:
    try:
        return (json.dumps(
            encode_record(record), sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        _fail(ContractErrorCode.PAYLOAD_INVALID, "json")
        raise AssertionError from exc


def _decode_dataclass(expected, value):
    if not isinstance(value, Mapping):
        _fail(ContractErrorCode.PAYLOAD_INVALID, expected.__name__)
    type_hints = get_type_hints(expected)
    expected_fields = tuple(field.name for field in fields(expected))
    if set(value) != set(expected_fields):
        _fail(ContractErrorCode.PAYLOAD_INVALID, expected.__name__ + ".fields")
    decoded = {
        name: _decode(type_hints[name], value[name])
        for name in expected_fields
    }
    try:
        return expected(**decoded)
    except (TypeError, ValueError) as exc:
        if isinstance(exc, MissionControlContractError):
            raise
        _fail(ContractErrorCode.PAYLOAD_INVALID, expected.__name__)


def _decode_tuple(args, value):
    if type(value) not in (list, tuple):
        _fail(ContractErrorCode.PAYLOAD_INVALID, "tuple")
    if len(args) == _VARIADIC_TUPLE_ARITY and args[1] is Ellipsis:
        return tuple(_decode(args[0], item) for item in value)
    if len(value) != len(args):
        _fail(ContractErrorCode.PAYLOAD_INVALID, "tuple-length")
    return tuple(_decode(kind, item) for kind, item in zip(args, value))


def _decode_integer(value):
    if type(value) is int:
        if is_wire_integer(value):
            return value
        _fail(ContractErrorCode.PAYLOAD_INVALID, "int")
    if type(value) is float and value.is_integer():
        converted = int(value)
        if is_wire_integer(converted):
            return converted
    _fail(ContractErrorCode.PAYLOAD_INVALID, "int")


def _decode_primitive(expected, value):
    if expected is int:
        return _decode_integer(value)
    if type(value) is not expected:
        _fail(ContractErrorCode.PAYLOAD_INVALID, expected.__name__)
    if expected is str and not is_text(value):
        _fail(ContractErrorCode.PAYLOAD_INVALID, "unicode-scalar")
    return value


def _union_options(args, value):
    """Prefer the literal JSON scalar type before any compatible coercion."""
    exact = tuple(
        option for option in args
        if option in (str, int, float, bool) and type(value) is option
    )
    return exact + tuple(option for option in args if option not in exact)


def _decode(expected, value):
    origin = get_origin(expected)
    args = get_args(expected)
    if origin in (types.UnionType, Union):
        for option in _union_options(args, value):
            try:
                return _decode(option, value)
            except MissionControlContractError:
                continue
        _fail(ContractErrorCode.PAYLOAD_INVALID, "union")
    if origin is tuple:
        return _decode_tuple(args, value)
    if expected is type(None):
        if value is not None:
            _fail(ContractErrorCode.PAYLOAD_INVALID, "null")
        return None
    if isinstance(expected, type) and issubclass(expected, Enum):
        try:
            return expected(value)
        except (TypeError, ValueError):
            _fail(ContractErrorCode.PAYLOAD_INVALID, expected.__name__)
    if isinstance(expected, type) and is_dataclass(expected):
        return _decode_dataclass(expected, value)
    if expected in (str, int, float, bool):
        return _decode_primitive(expected, value)
    _fail(ContractErrorCode.PAYLOAD_INVALID, str(expected))


def decode_record(payload: Mapping) -> WireRecord:
    if not isinstance(payload, Mapping):
        _fail(ContractErrorCode.PAYLOAD_INVALID, "root")
    schema = payload.get("schema_version")
    if schema is None:
        _fail(ContractErrorCode.SCHEMA_MISSING)
    if type(schema) is not str:
        _fail(ContractErrorCode.SCHEMA_UNSUPPORTED, "non-string")
    from .registry import RECORD_BY_SCHEMA
    record_type = RECORD_BY_SCHEMA.get(schema)
    if record_type is None:
        _fail(ContractErrorCode.SCHEMA_UNSUPPORTED, schema)
    body = {key: value for key, value in payload.items() if key != "schema_version"}
    try:
        return _decode_dataclass(record_type, body)
    except MissionControlContractError:
        raise
    except (TypeError, ValueError):
        _fail(ContractErrorCode.SCHEMA_TYPE_MISMATCH, schema)


def decode_json(payload: bytes | str) -> WireRecord:
    def reject_constant(_value: str):
        _fail(ContractErrorCode.PAYLOAD_INVALID, "json-constant")

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                _fail(ContractErrorCode.PAYLOAD_INVALID, "duplicate-key")
            result[key] = value
        return result

    try:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        parsed = json.loads(
            payload,
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
        _fail(ContractErrorCode.PAYLOAD_INVALID, "json")
    return decode_record(parsed)
