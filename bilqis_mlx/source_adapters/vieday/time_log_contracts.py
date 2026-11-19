"""Typed contracts for the bounded VieDay structured time-log stratum."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.source_adapters.evidence.evidence_types import SourceSpan


PARSER_REVISION = "vieday-time-log-structural/v1"
PUBLIC_FIXTURE_CLAIM = "PUBLIC_FIXTURE_ONLY_NOT_REAL_PILOT_EVIDENCE"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_STATUS = frozenset({"PLANNED", "OCCURRED"})
_RELATION = frozenset({"GAP", "OVERLAP"})
_CLOCK = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z")


def _fail(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.STATE.HISTORICAL_ARTIFACT_INVALID, reason=reason)


def _text(value: object) -> bool:
    return type(value) is str and bool(value)


@dataclass(frozen=True)
class CategoryMapping:
    raw_label: str
    category_ref: str

    def __post_init__(self) -> None:
        if not _text(self.raw_label) or not _text(self.category_ref):
            _fail("VIEDAY_TIME_LOG_CATEGORY_MAPPING_INVALID")


@dataclass(frozen=True)
class TimeLogSemanticAuthority:
    semantic_release: str
    category_mappings: tuple[CategoryMapping, ...]

    def __post_init__(self) -> None:
        if (not _SHA256.fullmatch(self.semantic_release)
                or type(self.category_mappings) is not tuple
                or not self.category_mappings
                or any(type(row) is not CategoryMapping for row in self.category_mappings)
                or len({row.raw_label for row in self.category_mappings})
                    != len(self.category_mappings)):
            _fail("VIEDAY_TIME_LOG_SEMANTIC_AUTHORITY_INVALID")

    def resolve(self, raw_label: str) -> str | None:
        return next((row.category_ref for row in self.category_mappings
                     if row.raw_label == raw_label), None)


@dataclass(frozen=True)
class DurationAssertion:
    raw_text: str
    decimal: str
    unit: str

    def __post_init__(self) -> None:
        try:
            Decimal(self.decimal)
        except InvalidOperation:
            _fail("VIEDAY_TIME_LOG_DURATION_INVALID")
        if (not _text(self.raw_text) or self.raw_text != f"{self.decimal} {self.unit}"
                or self.unit not in {"h", "min"}
                or Decimal(self.decimal) < 0):
            _fail("VIEDAY_TIME_LOG_DURATION_INVALID")

    @property
    def minutes(self) -> Decimal:
        value = Decimal(self.decimal)
        return value * 60 if self.unit == "h" else value


@dataclass(frozen=True)
class TimeLogRecord:
    record_id: str
    source_span: SourceSpan
    template_shape: str
    raw_interval_text: str
    start_time: str
    end_time: str
    day_rollover: bool
    raw_activity_phrase: str
    raw_category_label: str
    category_ref: str
    status: str
    reported_duration: DurationAssertion
    calculated_duration_minutes: int
    aggregate_notation: DurationAssertion | None
    conflicts: tuple[str, ...]

    def __post_init__(self) -> None:
        if (not _text(self.record_id) or type(self.source_span) is not SourceSpan
                or not _text(self.template_shape)
                or not all(_text(value) for value in (
                    self.raw_interval_text, self.start_time, self.end_time,
                    self.raw_activity_phrase, self.raw_category_label,
                    self.category_ref))
                or type(self.day_rollover) is not bool
                or self.status not in _STATUS
                or type(self.reported_duration) is not DurationAssertion
                or type(self.calculated_duration_minutes) is not int
                or self.calculated_duration_minutes < 0
                or (self.aggregate_notation is not None
                    and type(self.aggregate_notation) is not DurationAssertion)
                or type(self.conflicts) is not tuple
                or any(not _text(item) for item in self.conflicts)
                or len(set(self.conflicts)) != len(self.conflicts)):
            _fail("VIEDAY_TIME_LOG_RECORD_INVALID")
        if not _CLOCK.fullmatch(self.start_time) or not _CLOCK.fullmatch(self.end_time):
            _fail("VIEDAY_TIME_LOG_RECORD_INVALID")
        expected_duration = self.end_minute - self.start_minute
        if expected_duration < 0 or expected_duration != self.calculated_duration_minutes:
            _fail("VIEDAY_TIME_LOG_CALCULATED_DURATION_INVALID")

    @property
    def start_minute(self) -> int:
        hour, minute = (int(part) for part in self.start_time.split(":"))
        return hour * 60 + minute

    @property
    def end_minute(self) -> int:
        hour, minute = (int(part) for part in self.end_time.split(":"))
        return hour * 60 + minute + (1440 if self.day_rollover else 0)


@dataclass(frozen=True)
class TimeLogHold:
    source_span: SourceSpan
    template_shape: str
    reason: str

    def __post_init__(self) -> None:
        if (type(self.source_span) is not SourceSpan
                or not _text(self.template_shape) or not _text(self.reason)):
            _fail("VIEDAY_TIME_LOG_HOLD_INVALID")


@dataclass(frozen=True)
class TemporalRelation:
    left_record_id: str
    right_record_id: str
    kind: str
    minutes: int
    left_status: str
    right_status: str

    def __post_init__(self) -> None:
        if (not _text(self.left_record_id) or not _text(self.right_record_id)
                or self.kind not in _RELATION or type(self.minutes) is not int
                or self.minutes <= 0 or self.left_status not in _STATUS
                or self.right_status not in _STATUS):
            _fail("VIEDAY_TIME_LOG_RELATION_INVALID")


@dataclass(frozen=True)
class TimeLogStratumManifest:
    source_digest: str
    semantic_release: str
    expected_semantic_release: str
    parser_revision: str
    claim: str
    publication_class: str
    allowed_training: bool
    status: str
    qualified_template_shapes: tuple[str, ...]
    held_template_shapes: tuple[str, ...]
    records: tuple[TimeLogRecord, ...]
    holds: tuple[TimeLogHold, ...]
    relations: tuple[TemporalRelation, ...]

    def __post_init__(self) -> None:
        if (not _SHA256.fullmatch(self.source_digest)
                or not _SHA256.fullmatch(self.semantic_release)
                or not _SHA256.fullmatch(self.expected_semantic_release)
                or self.parser_revision != PARSER_REVISION
                or self.claim != PUBLIC_FIXTURE_CLAIM
                or self.publication_class != "PUBLIC_FIXTURE"
                or self.allowed_training is not False
                or self.status not in {"STRUCTURAL_PASS", "STRUCTURAL_PARTIAL", "HELD"}
                or any(type(item) is not TimeLogRecord for item in self.records)
                or any(type(item) is not TimeLogHold for item in self.holds)
                or any(type(item) is not TemporalRelation for item in self.relations)
                or len({(item.source_span.start, item.source_span.end)
                        for item in self.records}) != len(self.records)):
            _fail("VIEDAY_TIME_LOG_MANIFEST_INVALID")
        qualified_shapes = tuple(sorted({row.template_shape for row in self.records}))
        held_shapes = tuple(sorted({row.template_shape for row in self.holds}))
        expected_status = (
            "HELD" if not self.records else
            "STRUCTURAL_PARTIAL" if self.holds else "STRUCTURAL_PASS")
        record_ids = {row.record_id for row in self.records}
        by_id = {row.record_id: row for row in self.records}
        if (self.qualified_template_shapes != qualified_shapes
                or self.held_template_shapes != held_shapes
                or self.status != expected_status
                or any(relation.left_record_id not in record_ids
                       or relation.right_record_id not in record_ids
                       for relation in self.relations)
                or len({(relation.left_record_id, relation.right_record_id, relation.kind)
                        for relation in self.relations}) != len(self.relations)):
            _fail("VIEDAY_TIME_LOG_MANIFEST_DERIVATION_INVALID")
        for relation in self.relations:
            left = by_id[relation.left_record_id]
            right = by_id[relation.right_record_id]
            if relation.left_status != left.status or relation.right_status != right.status:
                _fail("VIEDAY_TIME_LOG_RELATION_DERIVATION_INVALID")
            overlap = min(left.end_minute, right.end_minute) - max(
                left.start_minute, right.start_minute)
            if relation.kind == "OVERLAP":
                expected_minutes = overlap
            elif left.end_minute <= right.start_minute:
                expected_minutes = right.start_minute - left.end_minute
            elif right.end_minute <= left.start_minute:
                expected_minutes = left.start_minute - right.end_minute
            else:
                expected_minutes = -1
            if expected_minutes <= 0 or relation.minutes != expected_minutes:
                _fail("VIEDAY_TIME_LOG_RELATION_DERIVATION_INVALID")
