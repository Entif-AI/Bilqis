"""JSON Schema projection generated from the typed CP02 record family."""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import types
from typing import get_args, get_origin, get_type_hints, Union

from .model import MAX_WIRE_INTEGER, RunRef, WireRecord


JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_BUNDLE_VERSION = "bilqis.bamf.mission-control.schema-bundle/v1"
_VARIADIC_TUPLE_ARITY = 2
_SHA256_PATTERN = "^[0-9a-f]{64}$"
_SHA256_FIELDS = (
    "atlas_bundle_id", "source_bundle_id", "old_digest", "new_digest",
    "atlas_release_sha256",
)
_FREE_STRING_FIELDS = ("value",)


def _string_schema(field_name: str | None) -> dict:
    schema = {"type": "string", "x-bilqis-unicode-domain": "scalar-values"}
    if field_name and (field_name.endswith("_sha256") or field_name in _SHA256_FIELDS):
        schema["pattern"] = _SHA256_PATTERN
    elif field_name not in _FREE_STRING_FIELDS:
        schema.update({"minLength": 1, "pattern": "\\S", "not": {"pattern": "\\n"}})
    return schema


def _tuple_schema(args, field_name: str | None) -> dict:
    if len(args) == _VARIADIC_TUPLE_ARITY and args[1] is Ellipsis:
        schema = {
            "type": "array",
            "items": _schema_for_type(args[0], field_name=field_name),
            "uniqueItems": True,
        }
        if field_name == "parameters":
            schema["x-bilqis-unique-by"] = "key"
        return schema
    return {
        "type": "array",
        "prefixItems": [
            _schema_for_type(option, field_name=field_name) for option in args
        ],
        "minItems": len(args),
        "maxItems": len(args),
    }


def _datavalue_constraints() -> list[dict]:
    return [{
        "if": {"properties": {"state": {"const": "PRESENT"}}, "required": ["state"]},
        "then": {"properties": {
            "origin": {"not": {"type": "null"}},
            "value": {"not": {"type": "null"}},
        }},
        "else": {"properties": {
            "origin": {"type": "null"},
            "value": {"type": "null"},
        }},
    }]


def _stream_position_constraints() -> list[dict]:
    return [{
        "if": {"properties": {"ordinal": {"const": 0}}, "required": ["ordinal"]},
        "then": {"properties": {"previous_cursor_sha256": {"type": "null"}}},
        "else": {"properties": {"previous_cursor_sha256": {
            "type": "string", "pattern": _SHA256_PATTERN,
        }}},
    }]


def _dataclass_schema(expected) -> dict:
    hints = get_type_hints(expected)
    properties = {
        field.name: _schema_for_type(hints[field.name], field_name=field.name)
        for field in fields(expected)
    }
    schema = {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }
    if expected.__name__ == "DataValue":
        schema["allOf"] = _datavalue_constraints()
    if expected.__name__ == "StreamPosition":
        schema["allOf"] = _stream_position_constraints()
    return schema


def _integer_schema(field_name: str | None) -> dict:
    schema = {
        "type": "integer",
        "maximum": MAX_WIRE_INTEGER,
        "minimum": -MAX_WIRE_INTEGER,
    }
    if field_name != "value":
        schema["minimum"] = 0
    return schema


def _schema_for_type(expected, *, field_name: str | None = None):
    origin = get_origin(expected)
    args = get_args(expected)
    if origin in (types.UnionType, Union):
        return {"anyOf": [
            _schema_for_type(option, field_name=field_name) for option in args
        ]}
    if origin is tuple:
        return _tuple_schema(args, field_name)
    if expected is type(None):
        return {"type": "null"}
    if isinstance(expected, type) and issubclass(expected, Enum):
        return {"type": "string", "enum": [item.value for item in expected]}
    if isinstance(expected, type) and is_dataclass(expected):
        return _dataclass_schema(expected)
    if expected is str:
        return _string_schema(field_name)
    if expected is int:
        return _integer_schema(field_name)
    if expected is float:
        return {"type": "number"}
    if expected is bool:
        return {"type": "boolean"}
    raise TypeError


def record_schema(record_type: type[WireRecord]) -> dict:
    if not isinstance(record_type, type) or not issubclass(record_type, WireRecord):
        raise TypeError
    body = _schema_for_type(record_type)
    properties = {
        "schema_version": {"type": "string", "const": record_type.SCHEMA},
        **body["properties"],
    }
    schema = {
        "$schema": JSON_SCHEMA_DIALECT,
        "$id": record_type.SCHEMA,
        "title": record_type.__name__,
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
        "x-bilqis-runtime-validator": "bilqis_mlx.mission_control.codec.decode_record",
    }
    if record_type.RUN_BOUND:
        properties["meta"]["properties"]["run"] = _schema_for_type(RunRef)
    if record_type.__name__ == "UnavailableEnvelope":
        properties["meta"]["properties"]["coverage"] = {
            "type": "string", "const": "UNKNOWN",
        }
        schema["allOf"] = [{
            "if": {"properties": {"reason": {"const": "DENIED"}},
                   "required": ["reason"]},
            "then": {"properties": {"meta": {"properties": {
                "run": {"type": "null"},
                "source_refs": {"maxItems": 0},
                "evidence_refs": {"maxItems": 0},
                "receipt_refs": {"maxItems": 0},
            }}}},
        }]
    elif record_type.__name__ == "PartialEnvelope":
        properties["meta"]["properties"]["coverage"] = {
            "type": "string", "const": "PARTIAL",
        }
        properties["missing_fields"]["minItems"] = 1
    elif record_type.__name__ == "StaleEnvelope":
        schema["x-bilqis-runtime-invariants"] = [
            "meta.as_of == stale_as_of",
            "stale_as_of < requested_as_of",
            "requested_as_of <= meta.materialized_at",
        ]
    elif record_type.__name__ == "EventEnvelope":
        schema["x-bilqis-runtime-invariants"] = [
            "position.cursor_sha256 is the CP02 cursor digest over position, event and payload identity",
        ]
    elif record_type.__name__ in {"OperatorActionReceipt", "OperatorActionReceiptV2"}:
        schema["x-bilqis-runtime-invariants"] = [
            "COMPLETED requires postcondition_ref and receipt_refs",
            "REJECTED/FAILED require error_ref",
            "non-terminal states carry neither postcondition_ref nor error_ref",
        ]
    return schema


def schema_bundle() -> dict:
    from .registry import ALL_RECORD_TYPES
    return {
        "schema_version": SCHEMA_BUNDLE_VERSION,
        "records": {
            record_type.SCHEMA: record_schema(record_type)
            for record_type in ALL_RECORD_TYPES
        },
    }
