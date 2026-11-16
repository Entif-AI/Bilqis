"""Immutable learner-relative evidence and generated-grade proposal contracts."""
from __future__ import annotations
from dataclasses import dataclass, field, fields
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


_INPUT_ISSUER = object()


@dataclass(frozen=True)
class GeneratedGradeInputs:
    learner: AcceptedLearnerFoot
    candidate_evidence: tuple[CandidateDevelopmentEvidence, ...]
    policy: GeneratedGradePolicy
    a09_progress_sha256: str | None
    a09_status: str
    a09_handoff_sha256: str | None
    a09_proposal_sha256: str | None
    input_sha256: str
    schema: str = "bilqis.generated-grade-inputs/v1"
    _issuance: object = field(init=False, default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if (self._issuance is not _INPUT_ISSUER
                or type(self.learner) is not AcceptedLearnerFoot
                or type(self.candidate_evidence) is not tuple
                or any(type(item) is not CandidateDevelopmentEvidence
                       for item in self.candidate_evidence)
                or type(self.policy) is not GeneratedGradePolicy
                or (self.a09_progress_sha256 is not None
                    and not _sha(self.a09_progress_sha256))
                or not self.a09_status
                or (self.a09_handoff_sha256 is not None
                    and not _sha(self.a09_handoff_sha256))
                or (self.a09_proposal_sha256 is not None
                    and not _sha(self.a09_proposal_sha256))
                or not _sha(self.input_sha256)
                or self.schema != "bilqis.generated-grade-inputs/v1"):
            _fail("BAMF_GENERATED_GRADE_INPUT_AUTHORITY_INVALID")

    def expected_digest(self) -> str:
        return hashlib.sha256(_bytes({
            "learner": self.learner,
            "candidate_evidence": self.candidate_evidence,
            "policy": self.policy,
            "a09_progress_sha256": self.a09_progress_sha256,
            "a09_status": self.a09_status,
            "a09_handoff_sha256": self.a09_handoff_sha256,
            "a09_proposal_sha256": self.a09_proposal_sha256,
            "schema": self.schema,
        })).hexdigest()


def _issue_inputs(**values) -> GeneratedGradeInputs:
    draft = object.__new__(GeneratedGradeInputs)
    for name, value in (*values.items(), ("_issuance", _INPUT_ISSUER)):
        object.__setattr__(draft, name, value)
    draft.__post_init__()
    if draft.input_sha256 != draft.expected_digest():
        _fail("BAMF_GENERATED_GRADE_INPUT_DIGEST_INVALID")
    return draft

@dataclass(frozen=True)
class GeneratedGradeProposal:
    snapshot_sha256: str
    closure_sha256: str
    current_release_sha256: str
    learner_foot_sha256: str
    learner_evidence_epoch: int
    policy_epoch: int
    policy_sha256: str
    input_sha256: str
    a09_progress_sha256: str | None
    a09_status: str
    a09_handoff_sha256: str | None
    a09_proposal_sha256: str | None
    member_semantic_ids: tuple[str, ...]
    decisions: tuple[CandidateGradeDecision, ...]
    source_holds: tuple[tuple[str, str, str], ...]
    proposal_sha256: str
    schema: str = "bilqis.generated-grade-proposal/v1"

    def expected_digest(self) -> str:
        return hashlib.sha256(_bytes({
            field.name: getattr(self, field.name)
            for field in fields(self) if field.name != "proposal_sha256"
        })).hexdigest()

    def verify(self) -> None:
        if (self.schema != "bilqis.generated-grade-proposal/v1"
                or not all(_sha(value) for value in (
                    self.snapshot_sha256, self.closure_sha256,
                    self.current_release_sha256, self.learner_foot_sha256,
                    self.policy_sha256, self.input_sha256,
                    self.proposal_sha256))
                or (self.a09_progress_sha256 is not None
                    and not _sha(self.a09_progress_sha256))
                or not self.a09_status
                or (self.a09_handoff_sha256 is not None
                    and not _sha(self.a09_handoff_sha256))
                or (self.a09_proposal_sha256 is not None
                    and not _sha(self.a09_proposal_sha256))
                or self.member_semantic_ids != tuple(dict.fromkeys(self.member_semantic_ids))
                or self.decisions != tuple(sorted(self.decisions, key=lambda item: item.semantic_id))
                or self.source_holds != tuple(sorted(set(self.source_holds)))
                or self.proposal_sha256 != self.expected_digest()):
            _fail("BAMF_GENERATED_GRADE_PROPOSAL_INVALID")

    def manifest(self) -> dict:
        return {
            "schema": self.schema,
            "snapshot_sha256": self.snapshot_sha256,
            "closure_sha256": self.closure_sha256,
            "current_release_sha256": self.current_release_sha256,
            "learner_foot_sha256": self.learner_foot_sha256,
            "learner_evidence_epoch": self.learner_evidence_epoch,
            "policy_epoch": self.policy_epoch,
            "policy_sha256": self.policy_sha256,
            "input_sha256": self.input_sha256,
            "a09_progress_sha256": self.a09_progress_sha256,
            "a09_status": self.a09_status,
            "a09_handoff_sha256": self.a09_handoff_sha256,
            "a09_proposal_sha256": self.a09_proposal_sha256,
            "member_semantic_ids": list(self.member_semantic_ids),
            "decisions": [_decision_manifest(item) for item in self.decisions],
            "source_holds": [list(item) for item in self.source_holds],
            "proposal_sha256": self.proposal_sha256,
        }

    @classmethod
    def from_manifest(cls, payload: dict) -> "GeneratedGradeProposal":
        try:
            decisions = tuple(CandidateGradeDecision(
                **{
                    **item,
                    "compiled_capability_ids": tuple(item["compiled_capability_ids"]),
                    "source_anchor_ids": tuple(item["source_anchor_ids"]),
                    "family_ids": tuple(item["family_ids"]),
                    "prerequisite_ids": tuple(item["prerequisite_ids"]),
                    "unmet_prerequisite_ids": tuple(item["unmet_prerequisite_ids"]),
                    "required_semantic_ids": tuple(item["required_semantic_ids"]),
                    "coverage_factors": tuple(item["coverage_factors"]),
                    "a09_statuses": tuple(item["a09_statuses"]),
                    "a09_reason_receipts": tuple(
                        tuple(value) for value in item["a09_reason_receipts"]),
                    "qualified_transfer_savings": (
                        None if item["qualified_transfer_savings"] is None else
                        tuple(tuple(value) for value in item["qualified_transfer_savings"])
                    ),
                    "source_evidence_sha256s": tuple(item["source_evidence_sha256s"]),
                    "reason_codes": tuple(item["reason_codes"]),
                    "cost_status": CostEvidenceKind(item["cost_status"]),
                }
            ) for item in payload["decisions"])
            result = cls(
                **{key: payload[key] for key in (
                    "snapshot_sha256", "closure_sha256", "current_release_sha256",
                    "learner_foot_sha256", "learner_evidence_epoch", "policy_epoch",
                    "policy_sha256", "input_sha256", "a09_progress_sha256",
                    "a09_status", "a09_handoff_sha256", "a09_proposal_sha256",
                    "proposal_sha256", "schema")},
                member_semantic_ids=tuple(payload["member_semantic_ids"]),
                decisions=decisions,
                source_holds=tuple(tuple(item) for item in payload["source_holds"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            _fail("BAMF_GENERATED_GRADE_MANIFEST_INVALID")
        result.verify()
        return result

def _decision_manifest(item: CandidateGradeDecision) -> dict:
    result = {field.name: getattr(item, field.name) for field in fields(item)}
    result["cost_status"] = item.cost_status.value
    for key in (
        "compiled_capability_ids", "source_anchor_ids", "family_ids",
        "prerequisite_ids", "unmet_prerequisite_ids",
        "required_semantic_ids", "coverage_factors", "source_evidence_sha256s",
        "reason_codes", "a09_statuses", "a09_reason_receipts",
    ):
        result[key] = list(result[key])
    result["qualified_transfer_savings"] = (
        None if result["qualified_transfer_savings"] is None else
        [list(value) for value in result["qualified_transfer_savings"]]
    )
    return result

def _sha(value: object) -> bool:
    return (type(value) is str and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))

def _canonical_ids(values: tuple[str, ...]) -> bool:
    return (type(values) is tuple and values == tuple(sorted(set(values)))
            and all(type(value) is str and value for value in values))
