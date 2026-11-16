"""Versioned CP03 query request, result, and stable-link contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from typing import Mapping

from .contracts.model import CoverageState, WireRecord, is_name, is_wire_integer, require


QUERY_REQUEST_SCHEMA = "bilqis.bamf.control-plane.query/v1"
QUERY_PAGE_SCHEMA = "bilqis.bamf.control-plane.query-page/v1"
DEFAULT_PAGE_SIZE = 8
MAX_PAGE_SIZE = 32
MAX_PAGE_ROWS_BYTES = 48 * 1024


class QueryFamily(StrEnum):
    RECORD = "record"
    RUN = "run"
    SCHOOL = "school"
    CAPABILITY = "capability"
    EPISODE = "episode"
    GENERATION = "generation"
    SEMANTIC = "semantic"
    FRAME = "frame"
    NEURAL = "neural"
    MEMORY = "memory"
    TEACHER = "teacher"
    SALIENCE = "salience"
    CORRECTION = "correction"
    RESOURCE = "resource"
    REFERENCE = "reference"
    LINKS = "links"


class QueryMode(StrEnum):
    CURRENT = "current"
    HISTORICAL = "historical"


class QueryState(StrEnum):
    PRESENT = "PRESENT"
    EMPTY = "EMPTY"
    MISSING = "MISSING"
    UNAVAILABLE = "UNAVAILABLE"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    DENIED = "DENIED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class QueryLink:
    relation: str
    source_record_id: str
    target_ref: str
    target_record_id: str | None = None

    def __post_init__(self) -> None:
        require(all(is_name(item) for item in (
            self.relation, self.source_record_id, self.target_ref)), "QUERY_LINK")
        require(
            self.target_record_id is None or is_name(self.target_record_id),
            "QUERY_LINK_TARGET",
        )

    def to_record(self) -> dict:
        return {
            "relation": self.relation,
            "source_record_id": self.source_record_id,
            "target_ref": self.target_ref,
            "target_record_id": self.target_record_id,
        }


@dataclass(frozen=True)
class QueryRequest:
    family: QueryFamily
    mode: QueryMode = QueryMode.CURRENT
    run_id: str | None = None
    record_id: str | None = None
    schema_version: str | None = None
    generation: int | None = None
    frontier_id: str | None = None
    as_of: int | None = None
    reference: str | None = None
    cursor: str | None = None
    limit: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        require(type(self.family) is QueryFamily, "QUERY_FAMILY")
        require(type(self.mode) is QueryMode, "QUERY_MODE")
        for label, value in (
            ("RUN", self.run_id), ("RECORD", self.record_id),
            ("SCHEMA", self.schema_version), ("FRONTIER", self.frontier_id),
            ("REFERENCE", self.reference), ("CURSOR", self.cursor),
        ):
            require(value is None or is_name(value), f"QUERY_{label}")
            require(value != "latest", f"QUERY_{label}_LATEST_FORBIDDEN")
        require(
            self.generation is None
            or (is_wire_integer(self.generation) and self.generation >= 0),
            "QUERY_GENERATION",
        )
        require(self.as_of is None or (
            is_wire_integer(self.as_of) and self.as_of >= 0), "QUERY_AS_OF")
        require(
            is_wire_integer(self.limit) and 1 <= self.limit <= MAX_PAGE_SIZE,
            "QUERY_LIMIT",
        )
        if self.mode is QueryMode.HISTORICAL:
            require(any(value is not None for value in (
                self.generation, self.frontier_id, self.as_of, self.record_id,
            )), "QUERY_HISTORICAL_IDENTITY_REQUIRED")
        if self.family is QueryFamily.REFERENCE:
            require(self.reference is not None, "QUERY_REFERENCE_REQUIRED")
        if self.family is QueryFamily.LINKS:
            require(self.record_id is not None, "QUERY_LINK_RECORD_REQUIRED")

    def identity_record(self) -> dict:
        return {
            "schema": QUERY_REQUEST_SCHEMA,
            "family": self.family.value,
            "mode": self.mode.value,
            "run_id": self.run_id,
            "record_id": self.record_id,
            "schema_version": self.schema_version,
            "generation": self.generation,
            "frontier_id": self.frontier_id,
            "as_of": self.as_of,
            "reference": self.reference,
            "limit": self.limit,
        }

    @property
    def query_id(self) -> str:
        raw = json.dumps(
            self.identity_record(), sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @classmethod
    def from_mapping(cls, payload: Mapping) -> "QueryRequest":
        expected = set(cls.__dataclass_fields__) | {"schema"}
        require(isinstance(payload, Mapping), "QUERY_REQUEST")
        require(set(payload) == expected, "QUERY_REQUEST_FIELDS")
        require(payload.get("schema") == QUERY_REQUEST_SCHEMA, "QUERY_REQUEST_SCHEMA")
        try:
            family = QueryFamily(payload["family"])
            mode = QueryMode(payload["mode"])
        except (KeyError, TypeError, ValueError):
            require(False, "QUERY_REQUEST_INVALID")
            raise AssertionError
        return cls(
            family=family,
            mode=mode,
            run_id=payload["run_id"],
            record_id=payload["record_id"],
            schema_version=payload["schema_version"],
            generation=payload["generation"],
            frontier_id=payload["frontier_id"],
            as_of=payload["as_of"],
            reference=payload["reference"],
            cursor=payload["cursor"],
            limit=payload["limit"],
        )

    def to_record(self) -> dict:
        return {**self.identity_record(), "cursor": self.cursor}


@dataclass(frozen=True)
class QueryPage:
    request: QueryRequest
    state: QueryState
    coverage: CoverageState
    total_matches: int
    records: tuple[WireRecord, ...] = ()
    markers: tuple[WireRecord, ...] = ()
    links: tuple[QueryLink, ...] = ()
    next_cursor: str | None = None

    def __post_init__(self) -> None:
        require(type(self.request) is QueryRequest, "QUERY_PAGE_REQUEST")
        require(type(self.state) is QueryState, "QUERY_PAGE_STATE")
        require(type(self.coverage) is CoverageState, "QUERY_PAGE_COVERAGE")
        require(
            is_wire_integer(self.total_matches) and self.total_matches >= 0,
            "QUERY_PAGE_TOTAL",
        )
        require(
            all(isinstance(item, WireRecord) for item in (*self.records, *self.markers)),
            "QUERY_PAGE_RECORDS",
        )
        require(
            all(type(item) is QueryLink for item in self.links), "QUERY_PAGE_LINKS")
        require(
            self.total_matches >= len(self.records) + len(self.links),
            "QUERY_PAGE_TOTAL",
        )
        require(
            self.next_cursor is None or is_name(self.next_cursor),
            "QUERY_PAGE_CURSOR",
        )

    @property
    def truncated(self) -> bool:
        return self.next_cursor is not None
