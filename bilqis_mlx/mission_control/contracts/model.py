"""Shared immutable vocabulary for BAMF Model Forensics view contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import math
import re
from typing import ClassVar, TypeAlias


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SCHEMA = re.compile(r"bilqis\.bamf\.mission-control\.[a-z0-9-]+/v[1-9][0-9]*\Z")
MAX_WIRE_INTEGER = (1 << 53) - 1
Scalar: TypeAlias = str | int | float | bool


class ContractErrorCode(StrEnum):
    INVALID_RECORD = "MISSION_CONTROL_RECORD_INVALID"
    SCHEMA_MISSING = "MISSION_CONTROL_SCHEMA_MISSING"
    SCHEMA_UNSUPPORTED = "MISSION_CONTROL_SCHEMA_UNSUPPORTED"
    SCHEMA_TYPE_MISMATCH = "MISSION_CONTROL_SCHEMA_TYPE_MISMATCH"
    PAYLOAD_INVALID = "MISSION_CONTROL_PAYLOAD_INVALID"


class MissionControlContractError(ValueError):
    """Deterministic public boundary error; details never change the identity."""

    def __init__(self, code: ContractErrorCode, detail: str | None = None):
        self.code = code
        self.detail = detail
        super().__init__(code.value if detail is None else f"{code.value}:{detail}")


def invalid(detail: str) -> None:
    raise MissionControlContractError(ContractErrorCode.INVALID_RECORD, detail)


def require(condition: bool, detail: str) -> None:
    if not condition:
        invalid(detail)


def is_text(value: object) -> bool:
    return (isinstance(value, str)
            and all(not 0xD800 <= ord(char) <= 0xDFFF for char in value))


def is_name(value: object) -> bool:
    return is_text(value) and bool(value.strip()) and "\n" not in value


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def is_time(value: object) -> bool:
    return is_wire_integer(value) and value >= 0


def is_wire_integer(value: object) -> bool:
    return type(value) is int and -MAX_WIRE_INTEGER <= value <= MAX_WIRE_INTEGER


def is_names(value: object, *, allow_empty: bool = True) -> bool:
    return (type(value) is tuple and (allow_empty or bool(value))
            and all(is_name(item) for item in value)
            and len(value) == len(set(value)))


class CoverageState(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AuthorityClass(StrEnum):
    SOURCE_AUTHORITATIVE = "SOURCE_AUTHORITATIVE"
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"


class ValueState(StrEnum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"
    DENIED = "DENIED"
    UNAVAILABLE = "UNAVAILABLE"


class ValueOrigin(StrEnum):
    SOURCE_AUTHORITATIVE = "SOURCE_AUTHORITATIVE"
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"


@dataclass(frozen=True)
class RunRef:
    run_id: str
    run_identity_sha256: str
    generation: int
    generation_manifest_sha256: str
    candidate_identity_sha256: str
    factory_release_sha256: str
    semantic_release_sha256: str
    topology_sha256: str

    def __post_init__(self) -> None:
        require(is_name(self.run_id), "RUN_ID")
        require(is_wire_integer(self.generation) and self.generation >= 0, "GENERATION")
        require(all(is_sha256(item) for item in (
            self.run_identity_sha256, self.generation_manifest_sha256,
            self.candidate_identity_sha256, self.factory_release_sha256,
            self.semantic_release_sha256, self.topology_sha256,
        )), "RUN_DIGEST")


@dataclass(frozen=True)
class RecordMeta:
    record_id: str
    run: RunRef | None
    materialized_at: int
    observed_at: int | None
    as_of: int | None
    coverage: CoverageState
    authority: AuthorityClass
    source_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    receipt_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require(is_name(self.record_id), "RECORD_ID")
        require(self.run is None or type(self.run) is RunRef, "RUN_REF")
        require(is_time(self.materialized_at), "MATERIALIZED_AT")
        for label, value in (("OBSERVED_AT", self.observed_at), ("AS_OF", self.as_of)):
            require(value is None or is_time(value), label)
            require(value is None or value <= self.materialized_at, label + "_FUTURE")
        require(type(self.coverage) is CoverageState, "COVERAGE")
        require(type(self.authority) is AuthorityClass, "AUTHORITY")
        require(is_names(self.source_refs), "SOURCE_REFS")
        require(is_names(self.evidence_refs), "EVIDENCE_REFS")
        require(is_names(self.receipt_refs), "RECEIPT_REFS")


@dataclass(frozen=True)
class DataValue:
    state: ValueState
    origin: ValueOrigin | None
    value: Scalar | None
    units: str | None = None

    def __post_init__(self) -> None:
        require(type(self.state) is ValueState, "VALUE_STATE")
        require(self.origin is None or type(self.origin) is ValueOrigin, "VALUE_ORIGIN")
        require(self.units is None or is_name(self.units), "VALUE_UNITS")
        if self.state is ValueState.PRESENT:
            require(self.origin is not None and self.value is not None, "VALUE_PRESENT")
            require(type(self.value) in (str, int, float, bool), "VALUE_TYPE")
            if type(self.value) is str:
                require(is_text(self.value), "VALUE_TEXT")
            if type(self.value) is int:
                require(is_wire_integer(self.value), "VALUE_INTEGER")
            if type(self.value) is float:
                require(math.isfinite(self.value), "VALUE_FINITE")
        else:
            require(self.origin is None and self.value is None, "VALUE_ABSENT")


class WireRecord:
    """Marker for versioned CP02 records; subclasses are frozen dataclasses."""

    SCHEMA: ClassVar[str]
    RUN_BOUND: ClassVar[bool] = True
    meta: RecordMeta

    @property
    def schema_version(self) -> str:
        return self.SCHEMA

    def __post_init__(self) -> None:
        require(_SCHEMA.fullmatch(self.SCHEMA) is not None, "SCHEMA_ID")
        require(type(self.meta) is RecordMeta, "META")
        require(not self.RUN_BOUND or self.meta.run is not None, "RUN_REQUIRED")
