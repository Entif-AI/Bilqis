"""Project canonical Atlas data and explicit generation overlays for GUI07."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from ..contracts.model import (
    AuthorityClass, CoverageState, DataValue, RecordMeta, RunRef,
    ValueOrigin, ValueState, require,
)


DEFAULT_BANK_ROW_CAPACITY = 8192
from ..contracts.observability import SemanticAtlasSnapshot
from .records import (
    SemanticAdmissionState, SemanticBankSnapshot, SemanticConceptSnapshot,
    SemanticGenerationState, SemanticHeldMappingSnapshot, SemanticLabel,
    SemanticRealization, SemanticRelation, SemanticSimilaritySnapshot,
    SemanticSourceRow,
)


@dataclass(frozen=True)
class SimilarityInput:
    source_semantic_id: str
    target_semantic_id: str
    basis_ref: str
    value: float
    origin: ValueOrigin = ValueOrigin.DERIVED


def concept_record_id(release_sha256: str, semantic_id: str) -> str:
    return f"semantic-concept:{release_sha256}:{semantic_id}"


def state_record_id(run: RunRef, bank: int, row: int) -> str:
    return f"semantic-state:{run.run_id}:{run.generation}:{bank}:{row}"


def bank_record_id(run: RunRef, bank: int) -> str:
    return f"semantic-bank:{run.run_id}:{run.generation}:{bank}"


def _digest(*parts: str) -> str:
    return hashlib.sha256("\u001f".join(parts).encode("utf-8")).hexdigest()


def _source_meta(record_id: str, snapshot, materialized_at: int,
                 observed_at: int | None, as_of: int | None) -> RecordMeta:
    return RecordMeta(
        record_id=record_id, run=None, materialized_at=materialized_at,
        observed_at=observed_at, as_of=as_of, coverage=CoverageState.COMPLETE,
        authority=AuthorityClass.SOURCE_AUTHORITATIVE,
        source_refs=(f"atlas-bundle:{snapshot.bundle_id}",
                     f"semantic-release:{snapshot.release_sha256}"),
    )


def _generation_meta(record_id: str, run: RunRef, materialized_at: int,
                     observed_at: int | None, as_of: int | None,
                     *, authority=AuthorityClass.DERIVED) -> RecordMeta:
    return RecordMeta(
        record_id=record_id, run=run, materialized_at=materialized_at,
        observed_at=observed_at, as_of=as_of, coverage=CoverageState.COMPLETE,
        authority=authority,
        source_refs=(f"semantic-release:{run.semantic_release_sha256}",),
    )


def _validate_projection_inputs(
        snapshot, run, active_indices, newly_admitted_indices,
        recently_exercised_indices, requalification_affected_indices,
        similarities, frame_schema_refs, bank_row_capacity):
    required_snapshot_fields = (
        "bundle_id", "release_sha256", "source_bundle_id", "counts",
        "formal_domain_bindings", "concepts", "abi_entries", "withheld_rows",
    )
    require(all(hasattr(snapshot, name) for name in required_snapshot_fields),
            "SEMANTIC_PROJECTION_SNAPSHOT")
    require(type(run) is RunRef, "SEMANTIC_PROJECTION_RUN")
    require(run.semantic_release_sha256 == snapshot.release_sha256,
            "SEMANTIC_PROJECTION_RELEASE_MISMATCH")
    frame_schema_refs = {} if frame_schema_refs is None else frame_schema_refs
    require(type(bank_row_capacity) is int and bank_row_capacity > 0,
            "SEMANTIC_PROJECTION_BANK_CAPACITY")
    allocated = {entry.index for entry in snapshot.abi_entries}
    require(all(
        type(entry.index) is int and type(entry.bank) is int and type(entry.row) is int
        and entry.index == entry.bank * bank_row_capacity + entry.row
        and 0 <= entry.row < bank_row_capacity
        for entry in snapshot.abi_entries
    ), "SEMANTIC_PROJECTION_ABI_LAYOUT")
    active = set(active_indices)
    newly = set(newly_admitted_indices)
    exercised = set(recently_exercised_indices)
    requal = set(requalification_affected_indices)
    require(all(type(items) is tuple for items in (
        active_indices, newly_admitted_indices, recently_exercised_indices,
        requalification_affected_indices, similarities,
    )), "SEMANTIC_PROJECTION_COLLECTION")
    require(active <= allocated and newly <= active and exercised <= active
            and requal <= allocated, "SEMANTIC_PROJECTION_INDEX_SET")
    require(len(active) == len(active_indices) and len(newly) == len(newly_admitted_indices)
            and len(exercised) == len(recently_exercised_indices)
            and len(requal) == len(requalification_affected_indices),
            "SEMANTIC_PROJECTION_INDEX_DUPLICATE")
    return frame_schema_refs, active, newly, exercised, requal


def _capability_ids(snapshot) -> dict[str, set[str]]:
    capability_ids: dict[str, set[str]] = {}
    for binding in snapshot.formal_domain_bindings:
        for semantic_id in binding.semantic_ids:
            capability_ids.setdefault(semantic_id, set()).update(binding.capability_ids)
    return capability_ids


def _project_concepts(snapshot, materialized_at, observed_at, as_of,
                      frame_schema_refs, capability_ids):
    concept_records = []
    concept_ids = {}
    for frozen in snapshot.concepts:
        concept = frozen.concept
        record_id = concept_record_id(snapshot.release_sha256, concept.semantic_id)
        concept_ids[concept.semantic_id] = record_id
        concept_records.append(SemanticConceptSnapshot(
            meta=_source_meta(record_id, snapshot, materialized_at, observed_at, as_of),
            atlas_release_sha256=snapshot.release_sha256,
            semantic_id=concept.semantic_id,
            kind=concept.kind,
            types=concept.types,
            labels=tuple(SemanticLabel(item.role, item.value, item.language)
                         for item in concept.labels),
            realizations=tuple(SemanticRealization(
                item.value, item.datatype, item.language) for item in concept.realizations),
            source_loci=tuple(item.canonical for item in concept.source_loci),
            source_rows=tuple(SemanticSourceRow(item.domain, item.table, item.key)
                              for item in concept.source_rows),
            relations=tuple(SemanticRelation(item.predicate, item.target)
                            for item in concept.relations),
            abi_index=frozen.abi_index, abi_bank=frozen.abi_bank, abi_row=frozen.abi_row,
            implementation_status=frozen.implementation_status,
            teaching_candidate=frozen.teaching_candidate,
            teaching_reason=frozen.teaching_reason,
            frame_schema_refs=tuple(sorted(frame_schema_refs.get(concept.semantic_id, ()))),
            capability_ids=tuple(sorted(capability_ids.get(concept.semantic_id, ()))),
        ))
    return tuple(concept_records), concept_ids


def _project_states(snapshot, run, concept_ids, active, newly, exercised, requal,
                    materialized_at, observed_at, as_of):
    states = []
    for entry in snapshot.abi_entries:
        states.append(SemanticGenerationState(
            meta=_generation_meta(
                state_record_id(run, entry.bank, entry.row), run,
                materialized_at, observed_at, as_of),
            semantic_id=entry.semantic_id,
            concept_record_id=concept_ids.get(entry.semantic_id),
            abi_index=entry.index, abi_bank=entry.bank, abi_row=entry.row,
            admission_state=(SemanticAdmissionState.ACTIVE if entry.index in active
                             else SemanticAdmissionState.RESERVED_MASKED),
            newly_admitted=entry.index in newly,
            recently_exercised=entry.index in exercised,
            requalification_affected=entry.index in requal,
        ))
    return tuple(states)


def _project_banks(snapshot, run, active, newly, exercised, requal,
                   materialized_at, observed_at, as_of, bank_row_capacity):
    banks = []
    for bank in sorted({entry.bank for entry in snapshot.abi_entries}):
        rows = [entry for entry in snapshot.abi_entries if entry.bank == bank]
        indices = {entry.index for entry in rows}
        active_rows = len(indices & active)
        banks.append(SemanticBankSnapshot(
            meta=_generation_meta(bank_record_id(run, bank), run,
                                  materialized_at, observed_at, as_of),
            bank=bank, row_capacity=bank_row_capacity, allocated_rows=len(rows),
            active_rows=active_rows, masked_rows=len(rows) - active_rows,
            newly_admitted_rows=len(indices & newly),
            recently_exercised_rows=len(indices & exercised),
            requalification_affected_rows=len(indices & requal),
        ))
    return tuple(banks)


def _project_held(snapshot, materialized_at, observed_at, as_of):
    held = []
    for row in snapshot.withheld_rows:
        record_id = "semantic-held:" + snapshot.release_sha256 + ":" + _digest(
            row.domain, row.table, row.key)
        held.append(SemanticHeldMappingSnapshot(
            meta=_source_meta(record_id, snapshot, materialized_at, observed_at, as_of),
            atlas_release_sha256=snapshot.release_sha256,
            domain=row.domain, table=row.table, key=row.key, semantic_id=row.semantic_id,
            source_disposition=row.source_disposition,
            implementation_status=row.implementation_status,
            reason_code=row.reason_code, teaching_reason=row.teaching_reason, owner=row.owner,
        ))
    return tuple(held)


def _project_similarities(snapshot, run, similarities, materialized_at,
                          observed_at, as_of):
    similarities_out = []
    semantic_ids = {entry.semantic_id for entry in snapshot.abi_entries}
    for item in similarities:
        require(type(item) is SimilarityInput, "SEMANTIC_PROJECTION_SIMILARITY")
        require(item.source_semantic_id in semantic_ids and item.target_semantic_id in semantic_ids,
                "SEMANTIC_PROJECTION_SIMILARITY_ID")
        record_id = "semantic-similarity:" + _digest(
            run.run_id, str(run.generation), item.source_semantic_id,
            item.target_semantic_id, item.basis_ref)
        similarities_out.append(SemanticSimilaritySnapshot(
            meta=_generation_meta(record_id, run, materialized_at, observed_at, as_of,
                                  authority=AuthorityClass.DERIVED),
            source_semantic_id=item.source_semantic_id,
            target_semantic_id=item.target_semantic_id,
            basis_ref=item.basis_ref,
            similarity=DataValue(ValueState.PRESENT, item.origin, item.value, "similarity"),
        ))
    return tuple(similarities_out)


def _project_summary(snapshot, run, active, materialized_at, observed_at, as_of):
    summary = SemanticAtlasSnapshot(
        meta=_generation_meta(
            f"semantic-atlas:{run.run_id}:{run.generation}", run,
            materialized_at, observed_at, as_of),
        atlas_bundle_id=snapshot.bundle_id,
        atlas_release_sha256=snapshot.release_sha256,
        source_bundle_id=snapshot.source_bundle_id,
        active_concepts=DataValue(ValueState.PRESENT, ValueOrigin.DERIVED,
                                  len(active), "count"),
        source_eligible=DataValue(ValueState.PRESENT, ValueOrigin.SOURCE_AUTHORITATIVE,
                                  snapshot.counts.semantic_concepts, "count"),
        source_held=DataValue(ValueState.PRESENT, ValueOrigin.SOURCE_AUTHORITATIVE,
                              snapshot.counts.source_held, "count"),
    )
    return summary


def project_semantic_atlas_records(
    snapshot,
    run: RunRef,
    active_indices: tuple[int, ...],
    *,
    materialized_at: int,
    observed_at: int | None = None,
    as_of: int | None = None,
    newly_admitted_indices: tuple[int, ...] = (),
    recently_exercised_indices: tuple[int, ...] = (),
    requalification_affected_indices: tuple[int, ...] = (),
    similarities: tuple[SimilarityInput, ...] = (),
    frame_schema_refs: dict[str, tuple[str, ...]] | None = None,
    bank_row_capacity: int = DEFAULT_BANK_ROW_CAPACITY,
) -> tuple:
    """Return read-only GUI07 records; callers supply generation-local activation."""
    frame_schema_refs, active, newly, exercised, requal = _validate_projection_inputs(
        snapshot, run, active_indices, newly_admitted_indices,
        recently_exercised_indices, requalification_affected_indices,
        similarities, frame_schema_refs, bank_row_capacity)
    concept_records, concept_ids = _project_concepts(
        snapshot, materialized_at, observed_at, as_of,
        frame_schema_refs, _capability_ids(snapshot))
    states = _project_states(
        snapshot, run, concept_ids, active, newly, exercised, requal,
        materialized_at, observed_at, as_of)
    banks = _project_banks(
        snapshot, run, active, newly, exercised, requal,
        materialized_at, observed_at, as_of, bank_row_capacity)
    held = _project_held(snapshot, materialized_at, observed_at, as_of)
    similarities_out = _project_similarities(
        snapshot, run, similarities, materialized_at, observed_at, as_of)
    summary = _project_summary(
        snapshot, run, active, materialized_at, observed_at, as_of)
    return tuple((*concept_records, *held, summary, *banks, *states, *similarities_out))
