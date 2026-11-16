"""Accepted learner evidence and generated-grade policy contracts."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib
from bilqis_mlx.factory.atlas_frontier_contracts import _bytes, _fail
from bilqis_mlx.factory.atlas_frontier_selection import A09_FRONTIER_COMPARATOR_ORDER

class CostEvidenceKind(str, Enum):
    MEASURED = "MEASURED"
    BOOTSTRAPPED = "BOOTSTRAPPED"
    UNKNOWN = "UNKNOWN"
@dataclass(frozen=True)
class AcquisitionCostEvidence:
    status: CostEvidenceKind
    measure: str
    units: int | None
    # ``None`` means no qualified causal-transfer estimate exists.  An empty
    # tuple means a qualified comparison found zero transferable effect.
    transfer_savings: tuple[tuple[str, int], ...] | None = None
    def __post_init__(self) -> None:
        known = self.status in {CostEvidenceKind.MEASURED, CostEvidenceKind.BOOTSTRAPPED}
        transfer = self.transfer_savings
        ids = () if transfer is None else tuple(identity for identity, _ in transfer)
        if (not isinstance(self.status, CostEvidenceKind) or not self.measure
                or (known and (type(self.units) is not int or self.units < 0))
                or (not known and self.units is not None)
                or ids != tuple(sorted(set(ids)))
                or (transfer is not None
                    and any(type(value) is not int for _, value in transfer))):
            _fail("BAMF_GENERATED_GRADE_COST_EVIDENCE_INVALID")

@dataclass(frozen=True)
class AcceptedLearnerFoot:
    checkpoint_sha256: str
    optimizer_step: int
    factory_release_sha256: str
    policy_epoch: int
    evidence_epoch: int
    baselined_semantic_ids: tuple[str, ...]
    mastered_capability_ids: tuple[str, ...]
    evidence_sha256: str

    def __post_init__(self) -> None:
        if (not _sha(self.checkpoint_sha256) or not _sha(self.factory_release_sha256)
                or not _sha(self.evidence_sha256)
                or type(self.optimizer_step) is not int or self.optimizer_step < 0
                or type(self.policy_epoch) is not int or self.policy_epoch < 0
                or type(self.evidence_epoch) is not int or self.evidence_epoch < 0
                or not _canonical_ids(self.baselined_semantic_ids)
                or not _canonical_ids(self.mastered_capability_ids)):
            _fail("BAMF_GENERATED_GRADE_LEARNER_FOOT_INVALID")

    def digest(self) -> str:
        return hashlib.sha256(_bytes(self)).hexdigest()

@dataclass(frozen=True)
class CandidateDevelopmentEvidence:
    semantic_id: str
    compiled_capability_ids: tuple[str, ...]
    source_anchor_ids: tuple[str, ...]
    neighborhood_id: str
    coverage_factors: tuple[str, ...]
    acquisition_cost: AcquisitionCostEvidence
    grounding_quality: int
    answer_modality_burden: int | None
    ast_burden: int | None
    entanglement: int | None
    reusable_constituent_value: int | None
    downstream_unlocks: int
    minimal_contrast_value: int | None
    transfer_breadth: int | None
    learning_progress: int | None
    fairness_age: int | None
    a09_prerequisite_slope: int
    a09_cursor_distance: int
    a09_statuses: tuple[str, ...]
    a09_reason_receipts: tuple[tuple[str, str, str, str, str], ...]
    planning_compute_units: int
    evidence_sha256: str

    def __post_init__(self) -> None:
        ordinal = (self.grounding_quality, self.downstream_unlocks,
                   self.a09_prerequisite_slope, self.a09_cursor_distance,
                   self.planning_compute_units)
        optional_ordinal = (
            self.answer_modality_burden, self.ast_burden, self.entanglement,
            self.reusable_constituent_value, self.minimal_contrast_value,
            self.transfer_breadth, self.learning_progress, self.fairness_age,
        )
        if (not self.semantic_id or not _canonical_ids(self.compiled_capability_ids)
                or not _canonical_ids(self.source_anchor_ids)
                or not self.neighborhood_id
                or not _canonical_ids(self.coverage_factors)
                or type(self.acquisition_cost) is not AcquisitionCostEvidence
                or any(type(item) is not int or item < 0 for item in ordinal)
                or any(item is not None and (type(item) is not int or item < 0)
                       for item in optional_ordinal)
                or self.a09_statuses != tuple(sorted(set(self.a09_statuses)))
                or any(not item for item in self.a09_statuses)
                or self.a09_reason_receipts != tuple(sorted(set(self.a09_reason_receipts)))
                or any(type(item) is not tuple
                       or tuple(type(part) for part in item)
                          != (str, str, str, str, str)
                       for item in self.a09_reason_receipts)
                or not _sha(self.evidence_sha256)):
            _fail("BAMF_GENERATED_GRADE_CANDIDATE_EVIDENCE_INVALID")

@dataclass(frozen=True)
class GeneratedGradePolicy:
    policy_id: str
    max_members: int
    max_unmet_prerequisites: int
    policy_epoch: int = 0
    comparator_order: tuple[str, ...] = A09_FRONTIER_COMPARATOR_ORDER
    pareto_dimensions: tuple[str, ...] = (
        "a09_prerequisite_slope", "cost_evidence_rank",
        "closure_acquisition_units",
        "answer_modality_burden",
        "ast_burden", "entanglement",
        "coverage_factor_count_desc", "reusable_constituent_value_desc",
        "downstream_unlocks_desc", "minimal_contrast_value_desc",
        "transfer_breadth_desc", "learning_progress_desc",
    )
    schema: str = "bilqis.generated-grade-policy/v1"

    def __post_init__(self) -> None:
        if (not self.policy_id or type(self.max_members) is not int
                or self.max_members < 1 or type(self.max_unmet_prerequisites) is not int
                or self.max_unmet_prerequisites < 0
                or type(self.policy_epoch) is not int or self.policy_epoch < 0
                or self.comparator_order != A09_FRONTIER_COMPARATOR_ORDER
                or self.pareto_dimensions != GeneratedGradePolicy.__dataclass_fields__[
                    "pareto_dimensions"].default
                or self.schema != "bilqis.generated-grade-policy/v1"):
            _fail("BAMF_GENERATED_GRADE_POLICY_INVALID")

    def digest(self) -> str:
        return hashlib.sha256(_bytes(self)).hexdigest()

@dataclass(frozen=True)
class CandidateGradeDecision:
    semantic_id: str
    compiled_capability_ids: tuple[str, ...]
    source_anchor_ids: tuple[str, ...]
    family_ids: tuple[str, ...]
    prerequisite_ids: tuple[str, ...]
    unmet_prerequisite_ids: tuple[str, ...]
    required_semantic_ids: tuple[str, ...]
    neighborhood_id: str
    coverage_factors: tuple[str, ...]
    cost_status: CostEvidenceKind
    cost_measure: str
    base_acquisition_units: int | None
    effective_acquisition_units: int | None
    closure_acquisition_units: int | None
    applied_transfer_savings: int
    qualified_transfer_savings: tuple[tuple[str, int], ...] | None
    grounding_quality: int
    answer_modality_burden: int | None
    ast_burden: int | None
    entanglement: int | None
    reusable_constituent_value: int | None
    downstream_unlocks: int
    minimal_contrast_value: int | None
    transfer_breadth: int | None
    learning_progress: int | None
    fairness_age: int | None
    a09_prerequisite_slope: int
    a09_cursor_distance: int
    a09_statuses: tuple[str, ...]
    a09_reason_receipts: tuple[tuple[str, str, str, str, str], ...]
    planning_compute_units: int
    source_evidence_sha256s: tuple[str, ...]
    development_evidence_sha256: str
    disposition: str
    reason_codes: tuple[str, ...]

def _sha(value: object) -> bool:
    return (type(value) is str and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))

def _canonical_ids(values: tuple[str, ...]) -> bool:
    return (type(values) is tuple and values == tuple(sorted(set(values)))
            and all(type(value) is str and value for value in values))
