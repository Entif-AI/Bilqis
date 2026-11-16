"""Immutable A09.1a snapshot value contracts and canonical encoding."""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
import re

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.semantics.atlas_projection import CorpusCoverageRow

from .model import LearningEvidence
from .skos_curriculum import FamilyObligation

SNAPSHOT_SCHEMA = "bilqis.factory-curriculum-snapshot/v1"
EDGE_SCHEMA = "bilqis.factory-source-prerequisite-edge/v1"
BUDGET_SCHEMA = "bilqis.factory-planner-budget/v1"
SNAPSHOT_STATUS = "SOURCE_PROPOSAL_NOT_ADMITTED"
_SHA = re.compile(r"[0-9a-f]{64}\Z")


def _fail(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.STATE.HISTORICAL_ARTIFACT_INVALID, reason=reason)


def _canonical(value: object) -> object:
    if type(value) in (str, int, bool) or value is None:
        return value
    if isinstance(value, Enum):
        return _canonical(value.value)
    if type(value) is tuple:
        return [_canonical(item) for item in value]
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            _fail("BAMF_PLANNER_SNAPSHOT_NONCANONICAL")
        return {key: _canonical(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _canonical(getattr(value, field.name))
                for field in fields(value)}
    _fail("BAMF_PLANNER_SNAPSHOT_NONCANONICAL")


def _bytes(value: object) -> bytes:
    return (json.dumps(
        _canonical(value), sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


@dataclass(frozen=True, order=True)
class PrerequisiteEdge:
    semantic_id: str
    prerequisite_semantic_id: str
    source_evidence_sha256: str
    status: str = "SOURCE_DECLARED_UNVERIFIED"
    schema: str = EDGE_SCHEMA

    def __post_init__(self) -> None:
        if (type(self.semantic_id) is not str or not self.semantic_id
                or type(self.prerequisite_semantic_id) is not str
                or not self.prerequisite_semantic_id
                or self.semantic_id == self.prerequisite_semantic_id
                or type(self.source_evidence_sha256) is not str
                or not _SHA.fullmatch(self.source_evidence_sha256)
                or self.status not in {
                    "SOURCE_DECLARED_UNVERIFIED",
                    "FRONTIER_HYPOTHESIS_UNVERIFIED",
                }
                or self.schema != EDGE_SCHEMA):
            _fail("BAMF_PLANNER_PREREQUISITE_EDGE_INVALID")


@dataclass(frozen=True)
class PlannerBudget:
    max_candidates: int
    max_identity_rows: int
    max_compute_units: int
    schema: str = BUDGET_SCHEMA

    def __post_init__(self) -> None:
        if (any(type(item) is not int or item < 0
                for item in (
                    self.max_candidates, self.max_identity_rows,
                    self.max_compute_units))
                or self.schema != BUDGET_SCHEMA):
            _fail("BAMF_PLANNER_BUDGET_INVALID")


@dataclass(frozen=True)
class CurriculumSnapshot:
    semantic_release: str
    atlas_bundle_id: str
    source_bundle_id: str
    source_coverage_sha256: str
    frozen_census_sha256: str
    source_eligible_concept_ids: tuple[str, ...]
    required_source_family_ids: tuple[str, ...]
    coverage_rows: tuple[FamilyObligation, ...]
    source_held_rows: tuple[CorpusCoverageRow, ...]
    source_ir_only_rows: tuple[CorpusCoverageRow, ...]
    pending_nonconcept_rows: tuple[
        tuple[CorpusCoverageRow, tuple[str, ...]], ...]
    prerequisite_edges: tuple[PrerequisiteEdge, ...]
    candidate_frontier_sha256: str
    ready_candidate_ids: tuple[str, ...]
    staged_factory_release_sha256s: tuple[str, ...]
    admitted_factory_release_sha256: str | None
    admission_receipt_sha256: str | None
    unverified_exposed_capability_ids: tuple[str, ...]
    unverified_qualified_capability_ids: tuple[str, ...]
    retained_evidence: tuple[LearningEvidence, ...]
    retained_mastery_debt: tuple[str, ...]
    retained_debt_source_sha256: str | None
    unverified_learning_claims_sha256: str
    rights_epoch: int
    correction_generation: int
    policy_epoch: int
    teacher_epoch: int
    qualification_epoch: int
    budget: PlannerBudget
    grade_labels: tuple[str, ...]
    cursor: int
    event_generation: int
    predecessor_sha256: str | None
    snapshot_sha256: str
    status: str = SNAPSHOT_STATUS
    schema: str = SNAPSHOT_SCHEMA

    def __post_init__(self) -> None:
        digests = (
            self.semantic_release, self.atlas_bundle_id,
            self.source_bundle_id, self.source_coverage_sha256,
            self.frozen_census_sha256, self.candidate_frontier_sha256,
            self.unverified_learning_claims_sha256,
            self.snapshot_sha256)
        if (any(type(item) is not str or not _SHA.fullmatch(item)
                for item in digests)
                or any(type(item) is not str or not _SHA.fullmatch(item)
                       for item in self.staged_factory_release_sha256s)
                or (self.admitted_factory_release_sha256 is not None
                    and (type(self.admitted_factory_release_sha256) is not str
                         or not _SHA.fullmatch(self.admitted_factory_release_sha256)))
                or (self.admission_receipt_sha256 is not None
                    and (type(self.admission_receipt_sha256) is not str
                         or not _SHA.fullmatch(self.admission_receipt_sha256)))
                or (self.predecessor_sha256 is not None
                    and (type(self.predecessor_sha256) is not str
                         or not _SHA.fullmatch(self.predecessor_sha256)))
                or (self.retained_debt_source_sha256 is not None
                    and (type(self.retained_debt_source_sha256) is not str
                         or not _SHA.fullmatch(self.retained_debt_source_sha256)))
                or any(type(item) is not int or item < 0
                       for item in (
                           self.rights_epoch, self.correction_generation,
                           self.policy_epoch, self.teacher_epoch,
                           self.qualification_epoch, self.cursor,
                           self.event_generation))
                or type(self.budget) is not PlannerBudget
                or self.status != SNAPSHOT_STATUS or self.schema != SNAPSHOT_SCHEMA):
            _fail("BAMF_PLANNER_SNAPSHOT_INVALID")
        if not _snapshot_rows_valid(self):
            _fail("BAMF_PLANNER_SNAPSHOT_ROWS_INVALID")
        if not _snapshot_order_valid(self):
            _fail("BAMF_PLANNER_SNAPSHOT_ORDER_INVALID")

    def canonical_bytes(self) -> bytes:
        return _bytes(self)

    def digest_bytes(self) -> bytes:
        """Canonical bytes covered by ``snapshot_sha256``."""
        return _bytes({
            field.name: getattr(self, field.name)
            for field in fields(self) if field.name != "snapshot_sha256"
        })

    def expected_digest(self) -> str:
        return hashlib.sha256(self.digest_bytes()).hexdigest()

    def verify(self) -> None:
        if self.snapshot_sha256 != self.expected_digest():
            _fail("BAMF_PLANNER_SNAPSHOT_DIGEST_MISMATCH")


def _evidence_key(item: LearningEvidence) -> tuple:
    return (
        item.checkpoint_sha256, item.cohort_sha256,
        item.optimizer_step, item.assessment_class.value,
        item.passed, item.contaminated_for_qualification,
    )


def _snapshot_rows_valid(snapshot: CurriculumSnapshot) -> bool:
    text_groups = (
        snapshot.source_eligible_concept_ids,
        snapshot.required_source_family_ids, snapshot.ready_candidate_ids,
        snapshot.unverified_exposed_capability_ids,
        snapshot.unverified_qualified_capability_ids, snapshot.grade_labels,
    )
    return not (
        any(type(item) is not str or not item for group in text_groups for item in group)
        or any(type(row) is not FamilyObligation for row in snapshot.coverage_rows)
        or any(type(row) is not CorpusCoverageRow
               or row.source_disposition != "SOURCE_HELD"
               or not row.reason_code or not row.owner
               for row in snapshot.source_held_rows)
        or any(type(row) is not CorpusCoverageRow
               or row.source_disposition != "SOURCE_IR_ONLY"
               for row in snapshot.source_ir_only_rows)
        or any(type(pair) is not tuple or len(pair) != 2
               or type(pair[0]) is not CorpusCoverageRow
               or pair[0].source_disposition != "SOURCE_EMITTED_NON_CONCEPT"
               or type(pair[1]) is not tuple
               or any(type(item) is not str or not item for item in pair[1])
               for pair in snapshot.pending_nonconcept_rows)
        or any(type(item) is not PrerequisiteEdge for item in snapshot.prerequisite_edges)
        or any(type(item) is not LearningEvidence for item in snapshot.retained_evidence)
        or any(type(item) is not str or not item for item in snapshot.retained_mastery_debt)
        or (bool(snapshot.retained_mastery_debt)
            and snapshot.retained_debt_source_sha256 is None)
    )


def _snapshot_order_valid(snapshot: CurriculumSnapshot) -> bool:
    return not (
        snapshot.source_eligible_concept_ids
        != tuple(sorted(set(snapshot.source_eligible_concept_ids)))
        or snapshot.required_source_family_ids
        != tuple(sorted(set(snapshot.required_source_family_ids)))
        or snapshot.coverage_rows != tuple(sorted(
            snapshot.coverage_rows, key=lambda item: (item.semantic_id, item.family_id)))
        or snapshot.prerequisite_edges != tuple(sorted(set(snapshot.prerequisite_edges)))
        or snapshot.ready_candidate_ids != tuple(sorted(set(snapshot.ready_candidate_ids)))
        or snapshot.staged_factory_release_sha256s
        != tuple(sorted(set(snapshot.staged_factory_release_sha256s)))
        or snapshot.unverified_exposed_capability_ids
        != tuple(sorted(set(snapshot.unverified_exposed_capability_ids)))
        or snapshot.unverified_qualified_capability_ids
        != tuple(sorted(set(snapshot.unverified_qualified_capability_ids)))
        or snapshot.grade_labels != tuple(sorted(set(snapshot.grade_labels)))
        or snapshot.retained_mastery_debt != tuple(sorted(set(snapshot.retained_mastery_debt)))
        or snapshot.retained_evidence != tuple(sorted(snapshot.retained_evidence, key=_evidence_key))
        or (snapshot.admitted_factory_release_sha256 is None)
        != (snapshot.admission_receipt_sha256 is None)
    )
