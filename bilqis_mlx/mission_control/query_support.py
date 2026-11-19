"""Pure CP03 selection, cursor, and page mechanics."""
from __future__ import annotations

import hashlib
import json
from types import MappingProxyType

from .contracts.trainer import (
    TrainerObservation, TrainerObservationV2, TrainerObservationV3,
    TrainerObservationV4, TrainerObservationV5, TrainerObservationV6, TrainerObservationV7,
)
from .contracts.codec import encode_record
from .contracts.dossier import CapabilityDossier
from .contracts.envelopes import (
    PartialEnvelope, StaleEnvelope, UnavailableEnvelope, UnavailableReason,
)
from .contracts.events import (
    CandidateDecision, CorrectionEvent, FrameCompileReceipt, LearningEpisode,
    SalienceEvent,
)
from .contracts.model import CoverageState, WireRecord, is_wire_integer, require
from .contracts.registry import ALL_RECORD_TYPES
from .contracts.observability import (
    GenerationManifest, MemorySnapshot, NeuralRuntimeSample, ResourceSample,
    SemanticAtlasSnapshot, TeacherSnapshot,
)
from .query_contracts import (
    MAX_PAGE_ROWS_BYTES, QUERY_PAGE_SCHEMA, QueryFamily, QueryMode, QueryPage,
    QueryRequest, QueryState,
)
from .contracts.snapshots import (
    CapabilitySnapshot, CurriculumFrontier, OperatorView, RunContext,
    SchoolSnapshot,
)
from .semantic import (
    SemanticBankSnapshot, SemanticConceptSnapshot, SemanticGenerationState,
    SemanticHeldMappingSnapshot, SemanticSimilaritySnapshot,
)


FAMILY_TYPES = MappingProxyType({
    QueryFamily.RECORD: ALL_RECORD_TYPES,
    QueryFamily.RUN: (
        RunContext, OperatorView, TrainerObservation, TrainerObservationV2,
        TrainerObservationV3, TrainerObservationV4, TrainerObservationV5,
        TrainerObservationV6, TrainerObservationV7),
    QueryFamily.SCHOOL: (SchoolSnapshot, CurriculumFrontier),
    QueryFamily.CAPABILITY: (CapabilitySnapshot, CapabilityDossier),
    QueryFamily.EPISODE: (LearningEpisode, CandidateDecision),
    QueryFamily.GENERATION: (GenerationManifest,),
    QueryFamily.SEMANTIC: (
        SemanticAtlasSnapshot, SemanticConceptSnapshot, SemanticGenerationState,
        SemanticBankSnapshot, SemanticHeldMappingSnapshot, SemanticSimilaritySnapshot,
    ),
    QueryFamily.FRAME: (FrameCompileReceipt,),
    QueryFamily.NEURAL: (NeuralRuntimeSample,),
    QueryFamily.MEMORY: (MemorySnapshot,),
    QueryFamily.TEACHER: (TeacherSnapshot,),
    QueryFamily.SALIENCE: (SalienceEvent,),
    QueryFamily.CORRECTION: (CorrectionEvent,),
    QueryFamily.RESOURCE: (ResourceSample,),
})


def _forensic_refs(record: WireRecord) -> set[str]:
    refs = {
        record.meta.record_id,
        *record.meta.source_refs,
        *record.meta.evidence_refs,
        *record.meta.receipt_refs,
    }
    for name in (
        "capability_id", "episode_id", "candidate_id", "visit_id", "semantic_id",
        "frame_id", "correction_id", "target_ref", "salience_id", "teacher_identity",
        "strategy_id", "operation_id", "request_id", "request_sha256",
    ):
        value = getattr(record, name, None)
        if isinstance(value, str):
            refs.add(value)
    for name in ("capability_ids", "frame_schema_refs", "source_loci"):
        value = getattr(record, name, ())
        if isinstance(value, tuple):
            refs.update(item for item in value if isinstance(item, str))
    checkpoint = getattr(record, "checkpoint_sha256", None)
    if isinstance(checkpoint, str):
        refs.add(f"checkpoint:{checkpoint}")
        refs.add(checkpoint)
    for name in (
        "student_sha256", "optimizer_state_sha256", "source_frame_sha256",
        "compiled_frame_sha256", "old_digest", "new_digest",
    ):
        value = getattr(record, name, None)
        if isinstance(value, str):
            refs.add(value)
    return refs


def record_sort_key(record: WireRecord):
    run = record.meta.run
    return (
        "" if run is None else run.run_id,
        -1 if run is None else run.generation,
        -1 if record.meta.as_of is None else record.meta.as_of,
        record.schema_version,
        record.meta.record_id,
    )


def _freshness_key(record: WireRecord):
    meta = record.meta
    return (
        -1 if meta.as_of is None else meta.as_of,
        -1 if meta.observed_at is None else meta.observed_at,
        meta.materialized_at,
        meta.record_id,
    )


def _current_identity(record: WireRecord):
    run = record.meta.run
    if run is None:
        return None
    record_type = (
        TrainerObservation if isinstance(record, TrainerObservation)
        else type(record))
    base = (run.run_id, record_type)
    if isinstance(record, TrainerObservation):
        return (*base, record.observation_id)
    if type(record) is CapabilitySnapshot:
        return (*base, record.capability_id)
    if type(record) is SemanticGenerationState:
        return (*base, record.semantic_id)
    if type(record) is SemanticBankSnapshot:
        return (*base, record.bank)
    if type(record) is SemanticSimilaritySnapshot:
        return (*base, record.source_semantic_id, record.target_semantic_id, record.basis_ref)
    if type(record) in {
        RunContext, OperatorView, SchoolSnapshot, CurriculumFrontier,
        GenerationManifest, SemanticAtlasSnapshot, NeuralRuntimeSample,
        MemorySnapshot, TeacherSnapshot, ResourceSample,
    }:
        return base
    if type(record) is SemanticConceptSnapshot:
        return (type(record), record.atlas_release_sha256, record.semantic_id)
    if type(record) is SemanticHeldMappingSnapshot:
        return (type(record), record.atlas_release_sha256,
                record.domain, record.table, record.key)
    return None


def matches_identity(
        item: WireRecord, request: QueryRequest, *, match_record_id: bool = True) -> bool:
    if isinstance(item, TrainerObservation) and (
            request.mode is not QueryMode.CURRENT or request.generation is not None
            or request.as_of is not None or request.frontier_id is not None):
        return False
    if request.schema_version is not None and item.schema_version != request.schema_version:
        return False
    if request.run_id is not None:
        if item.meta.run is None or item.meta.run.run_id != request.run_id:
            return False
    if match_record_id and request.record_id is not None:
        if item.meta.record_id != request.record_id:
            return False
    if request.generation is not None:
        if item.meta.run is None or item.meta.run.generation != request.generation:
            return False
    if request.as_of is not None and item.meta.as_of != request.as_of:
        return False
    if request.frontier_id is not None:
        if type(item) is not CurriculumFrontier or item.frontier_id != request.frontier_id:
            return False
    if (request.family is QueryFamily.RECORD and request.reference is not None
            and request.reference not in _forensic_refs(item)):
        return False
    return True


def select_current(rows: list[WireRecord]) -> list[WireRecord]:
    generations = {}
    for item in rows:
        run = item.meta.run
        if run is not None and not isinstance(item, TrainerObservation):
            generations[run.run_id] = max(
                run.generation, generations.get(run.run_id, -1))
    if generations:
        rows = [
            item for item in rows
            if isinstance(item, TrainerObservation) or item.meta.run is None
            or item.meta.run.generation == generations[item.meta.run.run_id]
        ]
    newest = {}
    passthrough = []
    for item in rows:
        identity = _current_identity(item)
        if identity is None:
            passthrough.append(item)
            continue
        incumbent = newest.get(identity)
        if incumbent is None or _freshness_key(item) > _freshness_key(incumbent):
            newest[identity] = item
    return [*passthrough, *newest.values()]


def _rows_digest(rows) -> str:
    payload = [
        encode_record(item) if isinstance(item, WireRecord) else item.to_record()
        for item in rows
    ]
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _cursor(request: QueryRequest, rows, offset: int) -> str:
    return f"cp03:{request.query_id}:{_rows_digest(rows)}:{offset}"


def _offset(request: QueryRequest, rows) -> int:
    if request.cursor is None:
        return 0
    prefix = f"cp03:{request.query_id}:"
    require(request.cursor.startswith(prefix), "QUERY_CURSOR_IDENTITY")
    parts = request.cursor[len(prefix):].split(":")
    require(
        len(parts) == 2 and len(parts[0]) == 64
        and all(char in "0123456789abcdef" for char in parts[0]),
        "QUERY_CURSOR_DIGEST",
    )
    require(parts[0] == _rows_digest(rows), "QUERY_CURSOR_STALE")
    require(parts[1].isdigit() and len(parts[1]) <= 16, "QUERY_CURSOR_OFFSET")
    offset = int(parts[1])
    require(is_wire_integer(offset) and offset >= 0, "QUERY_CURSOR_OFFSET")
    require(bool(rows) and offset < len(rows), "QUERY_CURSOR_RANGE")
    return offset


def _state(records, markers, *, historical_missing: bool) -> QueryState:
    if any(type(item) is StaleEnvelope for item in markers):
        return QueryState.STALE
    if any(type(item) is PartialEnvelope for item in markers):
        return QueryState.PARTIAL
    unavailable = next((item for item in markers if type(item) is UnavailableEnvelope), None)
    if unavailable is not None:
        return {
            UnavailableReason.MISSING: QueryState.MISSING,
            UnavailableReason.DENIED: QueryState.DENIED,
            UnavailableReason.UNAVAILABLE: QueryState.UNAVAILABLE,
            UnavailableReason.UNKNOWN: QueryState.UNKNOWN,
        }[unavailable.reason]
    if any(item.meta.coverage is CoverageState.PARTIAL for item in records):
        return QueryState.PARTIAL
    if records:
        return QueryState.PRESENT
    return QueryState.MISSING if historical_missing else QueryState.EMPTY


def build_page(*, available: bool, request: QueryRequest, records, markers,
               links=(), exact_missing=False) -> QueryPage:
    rows = links if request.family in {QueryFamily.LINKS, QueryFamily.REFERENCE} else records
    offset = _offset(request, rows)
    page_rows = []
    rows_bytes = 2
    for row in rows[offset:offset + request.limit]:
        encoded = encode_record(row) if isinstance(row, WireRecord) else row.to_record()
        encoded_bytes = len(json.dumps(
            encoded, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        require(encoded_bytes <= MAX_PAGE_ROWS_BYTES, "QUERY_ROW_TOO_LARGE")
        if page_rows and rows_bytes + encoded_bytes + 1 > MAX_PAGE_ROWS_BYTES:
            break
        rows_bytes += encoded_bytes + (1 if page_rows else 0)
        page_rows.append(row)
    page_rows = tuple(page_rows)
    next_offset = offset + len(page_rows)
    next_cursor = _cursor(request, rows, next_offset) if next_offset < len(rows) else None
    page_records = tuple(page_rows) if rows is records else ()
    page_links = tuple(page_rows) if rows is links else ()
    page_ids = {item.meta.record_id for item in page_records}
    page_refs = {item.target_ref for item in page_links}
    page_sources = {item.source_record_id for item in page_links}
    relevant_ids = page_ids | page_refs | page_sources
    if request.reference is not None:
        relevant_ids.add(request.reference)
    page_markers = tuple(
        item for item in markers
        if ((type(item) is PartialEnvelope
             and item.partial_record_id in relevant_ids)
            or (type(item) is StaleEnvelope
                and (
                    item.stale_record_id in relevant_ids
                    or (request.family not in {QueryFamily.REFERENCE, QueryFamily.LINKS}
                        and not records)
                ))
            or (type(item) is UnavailableEnvelope
                and (not page_links
                     or item.resource in page_refs
                     or item.resource == request.reference)))
    )
    state = (
        QueryState.UNAVAILABLE if not available
        else _state(
            page_records, page_markers,
            historical_missing=(exact_missing or request.mode is QueryMode.HISTORICAL),
        )
    )
    if page_links and not page_markers:
        state = QueryState.PRESENT
    coverage = (
        CoverageState.UNKNOWN if state in {
            QueryState.MISSING, QueryState.UNAVAILABLE, QueryState.DENIED, QueryState.UNKNOWN,
        }
        else CoverageState.PARTIAL if (
            state in {QueryState.PARTIAL, QueryState.STALE} or next_cursor is not None)
        else CoverageState.COMPLETE
    )
    return QueryPage(
        request=request, state=state, coverage=coverage,
        total_matches=len(rows), records=page_records,
        markers=page_markers, links=page_links, next_cursor=next_cursor,
    )


def encode_query_page(page: QueryPage) -> dict:
    return {
        "schema": QUERY_PAGE_SCHEMA,
        "query_id": page.request.query_id,
        "request": page.request.to_record(),
        "family": page.request.family.value,
        "mode": page.request.mode.value,
        "state": page.state.value,
        "coverage": page.coverage.value,
        "total_matches": page.total_matches,
        "returned": len(page.records) + len(page.links),
        "truncated": page.truncated,
        "next_cursor": page.next_cursor,
        "records": [encode_record(item) for item in page.records],
        "markers": [encode_record(item) for item in page.markers],
        "links": [item.to_record() for item in page.links],
    }
