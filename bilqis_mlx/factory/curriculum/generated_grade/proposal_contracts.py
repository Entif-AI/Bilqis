"""Authority-issued generated-grade input and proposal contracts."""
from __future__ import annotations
from dataclasses import dataclass, field, fields
import hashlib
from bilqis_mlx.factory.atlas_frontier_contracts import _bytes, _fail
from .evidence_contracts import (
    AcceptedLearnerFoot, CandidateDevelopmentEvidence, CandidateGradeDecision,
    CostEvidenceKind, GeneratedGradePolicy, _sha,
)

_INPUT_ISSUER = object()
GENERATED_GRADE_INPUTS_V1 = "bilqis.generated-grade-inputs/v1"
GENERATED_GRADE_INPUTS_V2 = "bilqis.generated-grade-inputs/v2"
GENERATED_GRADE_PROPOSAL_V1 = "bilqis.generated-grade-proposal/v1"
GENERATED_GRADE_PROPOSAL_V2 = "bilqis.generated-grade-proposal/v2"


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
    predecessor_certification_sha256: str | None = None
    schema: str = GENERATED_GRADE_INPUTS_V1
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
                or self.schema not in {
                    GENERATED_GRADE_INPUTS_V1, GENERATED_GRADE_INPUTS_V2}
                or (self.schema == GENERATED_GRADE_INPUTS_V1
                    and self.predecessor_certification_sha256 is not None)
                or (self.schema == GENERATED_GRADE_INPUTS_V2
                    and not _sha(self.predecessor_certification_sha256))):
            _fail("BAMF_GENERATED_GRADE_INPUT_AUTHORITY_INVALID")

    def expected_digest(self) -> str:
        payload = {
            "learner": self.learner,
            "candidate_evidence": self.candidate_evidence,
            "policy": self.policy,
            "a09_progress_sha256": self.a09_progress_sha256,
            "a09_status": self.a09_status,
            "a09_handoff_sha256": self.a09_handoff_sha256,
            "a09_proposal_sha256": self.a09_proposal_sha256,
            "schema": self.schema,
        }
        if self.schema == GENERATED_GRADE_INPUTS_V2:
            payload["predecessor_certification_sha256"] = (
                self.predecessor_certification_sha256)
        return hashlib.sha256(_bytes(payload)).hexdigest()


def _issue_inputs(**values) -> GeneratedGradeInputs:
    draft = object.__new__(GeneratedGradeInputs)
    values.setdefault("predecessor_certification_sha256", None)
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
    predecessor_certification_sha256: str | None = None
    schema: str = GENERATED_GRADE_PROPOSAL_V1

    def expected_digest(self) -> str:
        payload = {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if field.name not in {
                "proposal_sha256", "predecessor_certification_sha256"}
        }
        if self.schema == GENERATED_GRADE_PROPOSAL_V2:
            payload["predecessor_certification_sha256"] = (
                self.predecessor_certification_sha256)
        return hashlib.sha256(_bytes(payload)).hexdigest()

    def verify(self) -> None:
        if (self.schema not in {
                    GENERATED_GRADE_PROPOSAL_V1, GENERATED_GRADE_PROPOSAL_V2}
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
                or (self.schema == GENERATED_GRADE_PROPOSAL_V1
                    and self.predecessor_certification_sha256 is not None)
                or (self.schema == GENERATED_GRADE_PROPOSAL_V2
                    and not _sha(self.predecessor_certification_sha256))
                or self.member_semantic_ids != tuple(dict.fromkeys(self.member_semantic_ids))
                or self.decisions != tuple(sorted(self.decisions, key=lambda item: item.semantic_id))
                or self.source_holds != tuple(sorted(set(self.source_holds)))
                or self.proposal_sha256 != self.expected_digest()):
            _fail("BAMF_GENERATED_GRADE_PROPOSAL_INVALID")

    def manifest(self) -> dict:
        result = {
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
        if self.schema == GENERATED_GRADE_PROPOSAL_V2:
            result["predecessor_certification_sha256"] = (
                self.predecessor_certification_sha256)
        return result

    @classmethod
    def from_manifest(cls, payload: dict) -> "GeneratedGradeProposal":
        try:
            if not isinstance(payload, dict):
                raise TypeError
            base_keys = {
                "schema", "snapshot_sha256", "closure_sha256",
                "current_release_sha256", "learner_foot_sha256",
                "learner_evidence_epoch", "policy_epoch", "policy_sha256",
                "input_sha256", "a09_progress_sha256", "a09_status",
                "a09_handoff_sha256", "a09_proposal_sha256",
                "member_semantic_ids", "decisions", "source_holds",
                "proposal_sha256",
            }
            schema = payload["schema"]
            expected_keys = (
                base_keys
                if schema == GENERATED_GRADE_PROPOSAL_V1 else
                base_keys | {"predecessor_certification_sha256"}
                if schema == GENERATED_GRADE_PROPOSAL_V2 else
                set()
            )
            if not expected_keys or set(payload) != expected_keys:
                raise ValueError
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
                predecessor_certification_sha256=(
                    None if schema == GENERATED_GRADE_PROPOSAL_V1
                    else payload["predecessor_certification_sha256"]),
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
