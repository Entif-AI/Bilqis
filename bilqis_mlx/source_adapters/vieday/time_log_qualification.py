"""Public-fixture-only qualification fragment for the VieDay time-log stratum."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

from bilqis_mlx.source_adapters.evidence.evidence_types import (
    EvidenceRights,
    PUBLIC_FIXTURE,
    SourceSpan,
)
from .time_log_contracts import (
    PARSER_REVISION,
    PUBLIC_FIXTURE_CLAIM,
    TemporalRelation,
    TimeLogHold,
    TimeLogRecord,
    TimeLogSemanticAuthority,
    TimeLogStratumManifest,
    _fail,
)
from .time_log_parser import parse_time_log_line


def _source_rows(source_text: str):
    offset = 0
    for line_number, raw in enumerate(source_text.splitlines(keepends=True), start=1):
        line = raw.rstrip("\r\n")
        width = len(line)
        if line:
            yield line_number, line, SourceSpan(offset, offset + width)
        offset += len(raw)


def _relations(records: tuple[TimeLogRecord, ...]) -> tuple[TemporalRelation, ...]:
    ordered = sorted(records, key=lambda row: (row.start_minute, row.end_minute, row.record_id))
    relations = []
    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            overlap = min(left.end_minute, right.end_minute) - right.start_minute
            if overlap <= 0:
                continue
            relations.append(TemporalRelation(
                left.record_id, right.record_id, "OVERLAP", overlap,
                left.status, right.status))
    if ordered:
        frontier = ordered[0]
        frontier_end = frontier.end_minute
        for right in ordered[1:]:
            if right.start_minute > frontier_end:
                relations.append(TemporalRelation(
                    frontier.record_id, right.record_id, "GAP",
                    right.start_minute - frontier_end,
                    frontier.status, right.status))
            if right.end_minute > frontier_end:
                frontier, frontier_end = right, right.end_minute
    return tuple(relations)


def _relation_ambiguities(
    records: tuple[TimeLogRecord, ...],
) -> tuple[tuple[TimeLogHold, ...], frozenset[str]]:
    holds = []
    ambiguous_ids = set()
    for index, left in enumerate(records):
        for right in records[index + 1:]:
            ambiguous = (
                left.day_rollover and right.start_minute < left.start_minute
            ) or (
                right.day_rollover and left.start_minute < right.start_minute
            )
            if not ambiguous:
                continue
            ambiguous_ids.update((left.record_id, right.record_id))
            holds.append(TimeLogHold(
                SourceSpan(
                    min(left.source_span.start, right.source_span.start),
                    max(left.source_span.end, right.source_span.end)),
                "TEMPORAL_RELATION",
                "RELATION_DAY_CONTEXT_AMBIGUOUS",
            ))
    unique = {
        (hold.source_span.start, hold.source_span.end, hold.reason): hold
        for hold in holds
    }
    return (
        tuple(unique[key] for key in sorted(unique)),
        frozenset(ambiguous_ids),
    )


def _mark_overlaps(
    records: tuple[TimeLogRecord, ...], relations: tuple[TemporalRelation, ...],
) -> tuple[TimeLogRecord, ...]:
    overlapping = {
        record_id
        for relation in relations if relation.kind == "OVERLAP"
        for record_id in (relation.left_record_id, relation.right_record_id)
    }
    return tuple(
        replace(row, conflicts=tuple(dict.fromkeys((*row.conflicts, "INTERVAL_OVERLAP"))))
        if row.record_id in overlapping else row
        for row in records)


def qualify_public_time_log_source(
    source_text: str, *, rights: EvidenceRights,
    authority: TimeLogSemanticAuthority, expected_semantic_release: str,
) -> TimeLogStratumManifest:
    """Parse only PUBLIC_FIXTURE rows; #327 must own later PRIVATE_REAL intake."""
    if (type(source_text) is not str or not source_text
            or type(rights) is not EvidenceRights
            or rights.regime != PUBLIC_FIXTURE
            or not rights.public_export_allowed
            or rights.allowed_training):
        _fail("VIEDAY_TIME_LOG_PUBLIC_FIXTURE_REQUIRED")
    if authority.semantic_release != expected_semantic_release:
        rows = tuple(_source_rows(source_text))
        holds = tuple(TimeLogHold(span, "SEMANTIC_RELEASE", "SEMANTIC_RELEASE_STALE")
                      for _, _, span in rows)
        return _manifest(
            source_text, rights, authority, expected_semantic_release,
            (), holds, ())
    parsed = tuple(
        parse_time_log_line(
            line, span=span, record_id=f"time-log-{line_number:04d}",
            authority=authority)
        for line_number, line, span in _source_rows(source_text)
    )
    records = tuple(row for row in parsed if type(row) is TimeLogRecord)
    holds = tuple(row for row in parsed if type(row) is TimeLogHold)
    duplicate_spans = {
        span for span in (row.source_span for row in records)
        if sum(candidate.source_span == span for candidate in records) > 1
    }
    if duplicate_spans:
        records = tuple(row for row in records if row.source_span not in duplicate_spans)
        holds = (*holds, *(TimeLogHold(span, "DUPLICATE_SOURCE_SPAN", "DUPLICATE_SOURCE_SPAN")
                           for span in sorted(duplicate_spans, key=lambda item: item.start)))
    relation_holds, ambiguous_ids = _relation_ambiguities(records)
    holds = (*holds, *relation_holds)
    relation_records = tuple(
        row for row in records if row.record_id not in ambiguous_ids)
    relations = _relations(relation_records)
    records = _mark_overlaps(records, relations)
    return _manifest(
        source_text, rights, authority, expected_semantic_release,
        records, holds, relations)


def _manifest(source_text, rights, authority, expected_semantic_release,
              records, holds, relations):
    qualified_shapes = tuple(sorted({row.template_shape for row in records}))
    held_shapes = tuple(sorted({row.template_shape for row in holds}))
    status = ("HELD" if not records else
              "STRUCTURAL_PARTIAL" if holds else "STRUCTURAL_PASS")
    return TimeLogStratumManifest(
        source_digest=sha256(source_text.encode("utf-8")).hexdigest(),
        semantic_release=authority.semantic_release,
        expected_semantic_release=expected_semantic_release,
        parser_revision=PARSER_REVISION,
        claim=PUBLIC_FIXTURE_CLAIM,
        publication_class=rights.regime,
        allowed_training=rights.allowed_training,
        status=status,
        qualified_template_shapes=qualified_shapes,
        held_template_shapes=held_shapes,
        records=tuple(records),
        holds=tuple(holds),
        relations=tuple(relations),
    )
