"""Strict structural parser for rights-cleared VieDay time-log fixtures."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re

from bilqis_mlx.source_adapters.evidence.evidence_types import SourceSpan
from .time_log_contracts import (
    DurationAssertion,
    TimeLogHold,
    TimeLogRecord,
    TimeLogSemanticAuthority,
)


_CLOCK = re.compile(r"(?P<hour>[01]\d|2[0-3]):(?P<minute>[0-5]\d)\Z")
_DURATION = re.compile(r"(?P<decimal>\d+(?:\.\d+)?) (?P<unit>h|min)\Z")
_BASE_KEYS = ("interval", "activity", "category", "status", "duration")
_WITH_AGGREGATE = (*_BASE_KEYS, "aggregate")


def _shape(fields: dict[str, str]) -> str:
    return "+".join(fields) if fields else "EMPTY"


def _duration(raw: str) -> DurationAssertion | None:
    match = _DURATION.fullmatch(raw)
    if match is None:
        return None
    try:
        Decimal(match.group("decimal"))
    except InvalidOperation:
        return None
    return DurationAssertion(raw, match.group("decimal"), match.group("unit"))


def _clock(raw: str) -> int | None:
    match = _CLOCK.fullmatch(raw)
    if match is None:
        return None
    return int(match.group("hour")) * 60 + int(match.group("minute"))


def _interval(raw: str):
    rollover = raw.endswith("+1d")
    core = raw[:-3] if rollover else raw
    if core.count("-") != 1:
        return None
    start, end = core.split("-", 1)
    start_minute, end_minute = _clock(start), _clock(end)
    if start_minute is None or end_minute is None:
        return None
    if end_minute < start_minute and not rollover:
        return (start, end, False, None, "AMBIGUOUS_DAY_ROLLOVER")
    if rollover:
        end_minute += 1440
    return (start, end, rollover, end_minute - start_minute, None)


def parse_time_log_line(
    line: str, *, span: SourceSpan, record_id: str,
    authority: TimeLogSemanticAuthority,
) -> TimeLogRecord | TimeLogHold:
    fields: dict[str, str] = {}
    try:
        for part in line.split("; "):
            key, value = part.split("=", 1)
            if key in fields:
                raise ValueError
            fields[key] = value
    except ValueError:
        return TimeLogHold(span, _shape(fields), "MALFORMED_KEY_VALUE_ROW")
    shape = _shape(fields)
    if tuple(fields) not in {_BASE_KEYS, _WITH_AGGREGATE}:
        reason = "MISSING_CATEGORY" if "category" not in fields else "UNSUPPORTED_TEMPLATE_SHAPE"
        return TimeLogHold(span, shape, reason)
    if not fields["activity"]:
        return TimeLogHold(span, shape, "ACTIVITY_PHRASE_EMPTY")
    if fields["status"] not in {"planned", "occurred"}:
        return TimeLogHold(span, shape, "STATUS_UNSUPPORTED")
    interval = _interval(fields["interval"])
    if interval is None:
        return TimeLogHold(span, shape, "INTERVAL_MALFORMED")
    start, end, rollover, calculated, interval_hold = interval
    if interval_hold is not None:
        return TimeLogHold(span, shape, interval_hold)
    category_ref = authority.resolve(fields["category"])
    if category_ref is None:
        return TimeLogHold(span, shape, "CATEGORY_MAPPING_UNKNOWN")
    reported = _duration(fields["duration"])
    if reported is None:
        return TimeLogHold(span, shape, "REPORTED_DURATION_MALFORMED")
    aggregate = None
    if "aggregate" in fields:
        aggregate = _duration(fields["aggregate"])
        if aggregate is None:
            return TimeLogHold(span, shape, "AGGREGATE_DURATION_MALFORMED")
    conflicts = ()
    if reported.minutes != Decimal(calculated):
        conflicts = ("REPORTED_CALCULATED_DURATION_MISMATCH",)
    return TimeLogRecord(
        record_id=record_id,
        source_span=span,
        template_shape=shape,
        raw_interval_text=fields["interval"],
        start_time=start,
        end_time=end,
        day_rollover=rollover,
        raw_activity_phrase=fields["activity"],
        raw_category_label=fields["category"],
        category_ref=category_ref,
        status=fields["status"].upper(),
        reported_duration=reported,
        calculated_duration_minutes=calculated,
        aggregate_notation=aggregate,
        conflicts=conflicts,
    )
