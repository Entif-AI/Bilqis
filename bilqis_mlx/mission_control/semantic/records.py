"""GUI07 semantic Atlas read models with explicit authority separation."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..contracts.model import (
    AuthorityClass, DataValue, RecordMeta, WireRecord, is_name, is_sha256,
    is_wire_integer, require,
)


class SemanticAdmissionState(StrEnum):
    ACTIVE = "ACTIVE"
    RESERVED_MASKED = "RESERVED_MASKED"


@dataclass(frozen=True, order=True)
class SemanticLabel:
    role: str
    value: str
    language: str | None = None

    def __post_init__(self) -> None:
        require(is_name(self.role) and is_name(self.value), "SEMANTIC_LABEL")
        require(self.language is None or is_name(self.language), "SEMANTIC_LABEL_LANGUAGE")


@dataclass(frozen=True, order=True)
class SemanticRealization:
    value: str
    datatype: str | None = None
    language: str | None = None

    def __post_init__(self) -> None:
        require(is_name(self.value), "SEMANTIC_REALIZATION")
        require(self.datatype is None or is_name(self.datatype), "SEMANTIC_DATATYPE")
        require(self.language is None or is_name(self.language), "SEMANTIC_LANGUAGE")


@dataclass(frozen=True, order=True)
class SemanticSourceRow:
    domain: str
    table: str
    key: str

    def __post_init__(self) -> None:
        require(all(is_name(value) for value in (self.domain, self.table, self.key)),
                "SEMANTIC_SOURCE_ROW")


@dataclass(frozen=True, order=True)
class SemanticRelation:
    predicate: str
    target_semantic_id: str

    def __post_init__(self) -> None:
        require(is_name(self.predicate) and is_name(self.target_semantic_id),
                "SEMANTIC_RELATION")


@dataclass(frozen=True)
class SemanticConceptSnapshot(WireRecord):
    """Source-authoritative concept identity; never a learned-neighborhood claim."""

    SCHEMA = "bilqis.bamf.mission-control.semantic-concept-snapshot/v1"
    RUN_BOUND = False
    meta: RecordMeta
    atlas_release_sha256: str
    semantic_id: str
    kind: str
    types: tuple[str, ...]
    labels: tuple[SemanticLabel, ...]
    realizations: tuple[SemanticRealization, ...]
    source_loci: tuple[str, ...]
    source_rows: tuple[SemanticSourceRow, ...]
    relations: tuple[SemanticRelation, ...]
    abi_index: int
    abi_bank: int
    abi_row: int
    implementation_status: str
    teaching_candidate: bool
    teaching_reason: str
    frame_schema_refs: tuple[str, ...] = ()
    capability_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        require(self.meta.run is None, "SEMANTIC_CONCEPT_RUN")
        require(self.meta.authority is AuthorityClass.SOURCE_AUTHORITATIVE,
                "SEMANTIC_CONCEPT_AUTHORITY")
        require(is_sha256(self.atlas_release_sha256), "SEMANTIC_RELEASE")
        require(is_name(self.semantic_id) and is_name(self.kind), "SEMANTIC_IDENTITY")
        require(all(is_name(item) for item in (*self.types, *self.source_loci,
                                                *self.frame_schema_refs,
                                                *self.capability_ids)), "SEMANTIC_NAMES")
        require(all(type(item) is SemanticLabel for item in self.labels), "SEMANTIC_LABELS")
        require(all(type(item) is SemanticRealization for item in self.realizations),
                "SEMANTIC_REALIZATIONS")
        require(all(type(item) is SemanticSourceRow for item in self.source_rows),
                "SEMANTIC_SOURCE_ROWS")
        require(all(type(item) is SemanticRelation for item in self.relations),
                "SEMANTIC_RELATIONS")
        require(all(is_wire_integer(item) and item >= 0
                    for item in (self.abi_index, self.abi_bank, self.abi_row)),
                "SEMANTIC_ABI")
        require(is_name(self.implementation_status) and is_name(self.teaching_reason),
                "SEMANTIC_STATUS")
        require(type(self.teaching_candidate) is bool, "SEMANTIC_TEACHING_CANDIDATE")


@dataclass(frozen=True)
class SemanticGenerationState(WireRecord):
    """Generation-local activation state projected onto stable semantic identity."""

    SCHEMA = "bilqis.bamf.mission-control.semantic-generation-state/v1"
    meta: RecordMeta
    semantic_id: str
    concept_record_id: str | None
    abi_index: int
    abi_bank: int
    abi_row: int
    admission_state: SemanticAdmissionState
    newly_admitted: bool
    recently_exercised: bool
    requalification_affected: bool

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_name(self.semantic_id), "SEMANTIC_STATE_ID")
        require(self.concept_record_id is None or is_name(self.concept_record_id),
                "SEMANTIC_STATE_CONCEPT")
        require(all(is_wire_integer(item) and item >= 0
                    for item in (self.abi_index, self.abi_bank, self.abi_row)),
                "SEMANTIC_STATE_ABI")
        require(type(self.admission_state) is SemanticAdmissionState,
                "SEMANTIC_ADMISSION_STATE")
        require(all(type(item) is bool for item in (
            self.newly_admitted, self.recently_exercised,
            self.requalification_affected,
        )), "SEMANTIC_STATE_FLAGS")


@dataclass(frozen=True)
class SemanticBankSnapshot(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.semantic-bank-snapshot/v1"
    meta: RecordMeta
    bank: int
    row_capacity: int
    allocated_rows: int
    active_rows: int
    masked_rows: int
    newly_admitted_rows: int
    recently_exercised_rows: int
    requalification_affected_rows: int

    def __post_init__(self) -> None:
        super().__post_init__()
        values = (
            self.bank, self.row_capacity, self.allocated_rows, self.active_rows,
            self.masked_rows, self.newly_admitted_rows,
            self.recently_exercised_rows, self.requalification_affected_rows,
        )
        require(all(is_wire_integer(item) and item >= 0 for item in values),
                "SEMANTIC_BANK_VALUES")
        require(self.row_capacity > 0 and self.allocated_rows <= self.row_capacity,
                "SEMANTIC_BANK_CAPACITY")
        require(self.active_rows + self.masked_rows == self.allocated_rows,
                "SEMANTIC_BANK_PARTITION")
        require(all(item <= self.allocated_rows for item in (
            self.newly_admitted_rows, self.recently_exercised_rows,
            self.requalification_affected_rows,
        )), "SEMANTIC_BANK_COUNTS")


@dataclass(frozen=True)
class SemanticHeldMappingSnapshot(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.semantic-held-mapping/v1"
    RUN_BOUND = False
    meta: RecordMeta
    atlas_release_sha256: str
    domain: str
    table: str
    key: str
    semantic_id: str | None
    source_disposition: str
    implementation_status: str
    reason_code: str
    teaching_reason: str
    owner: str

    def __post_init__(self) -> None:
        super().__post_init__()
        require(self.meta.run is None and
                self.meta.authority is AuthorityClass.SOURCE_AUTHORITATIVE,
                "SEMANTIC_HELD_AUTHORITY")
        require(is_sha256(self.atlas_release_sha256), "SEMANTIC_HELD_RELEASE")
        require(all(is_name(item) for item in (
            self.domain, self.table, self.key, self.source_disposition,
            self.implementation_status, self.reason_code, self.teaching_reason,
            self.owner,
        )), "SEMANTIC_HELD_FIELDS")
        require(self.semantic_id is None or is_name(self.semantic_id),
                "SEMANTIC_HELD_ID")


@dataclass(frozen=True)
class SemanticSimilaritySnapshot(WireRecord):
    """Learned/derived proximity that is forbidden from asserting equivalence."""

    SCHEMA = "bilqis.bamf.mission-control.semantic-similarity-snapshot/v1"
    meta: RecordMeta
    source_semantic_id: str
    target_semantic_id: str
    basis_ref: str
    similarity: DataValue
    canonical_equivalence: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        require(self.meta.authority is not AuthorityClass.SOURCE_AUTHORITATIVE,
                "SEMANTIC_SIMILARITY_AUTHORITY")
        require(all(is_name(item) for item in (
            self.source_semantic_id, self.target_semantic_id, self.basis_ref,
        )), "SEMANTIC_SIMILARITY_ID")
        require(self.source_semantic_id != self.target_semantic_id,
                "SEMANTIC_SIMILARITY_SELF")
        require(type(self.similarity) is DataValue, "SEMANTIC_SIMILARITY_VALUE")
        require(self.similarity.state.value == "PRESENT"
                and self.similarity.origin is not None
                and self.similarity.origin.value != "SOURCE_AUTHORITATIVE"
                and type(self.similarity.value) in (int, float)
                and 0 <= self.similarity.value <= 1,
                "SEMANTIC_SIMILARITY_RANGE")
        require(self.canonical_equivalence is False, "SEMANTIC_SIMILARITY_EQUIVALENCE")
