"""Compatibility facade for generated-grade contracts."""
from .evidence_contracts import (
    AcceptedLearnerFoot, AcquisitionCostEvidence, CandidateDevelopmentEvidence,
    CandidateGradeDecision, CostEvidenceKind, GeneratedGradePolicy,
)
from .proposal_contracts import (
    GeneratedGradeInputs, GeneratedGradeProposal, _issue_inputs,
)

for _contract in (
    AcceptedLearnerFoot, AcquisitionCostEvidence, CandidateDevelopmentEvidence,
    CandidateGradeDecision, CostEvidenceKind, GeneratedGradeInputs,
    GeneratedGradePolicy, GeneratedGradeProposal,
):
    _contract.__module__ = __name__

__all__ = (
    "AcceptedLearnerFoot", "AcquisitionCostEvidence",
    "CandidateDevelopmentEvidence", "CandidateGradeDecision",
    "CostEvidenceKind", "GeneratedGradeInputs", "GeneratedGradePolicy",
    "GeneratedGradeProposal",
)
