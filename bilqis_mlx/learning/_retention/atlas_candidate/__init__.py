"""Public B12.2 candidate custody surface."""
from bilqis_mlx.learning.atlas_plasticity import PlasticityPolicy
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree

from .._atlas_candidate.common import LEGACY_STEP_PROOF_SCHEMA, STEP_PROOF_SCHEMA
from .._atlas_candidate.proofs import CandidateStepProof
from .._atlas_candidate.state import (
    CandidateCustodyIdentity, CandidateState,
    _issue_parameter_extension_state,
    _issue_promotion_transition_state,
    _load_retained_candidate_state_with_parts,
)
from .._atlas_candidate.transaction import (
    CandidateTransaction, _begin_candidate_with_parent_identity,
    begin_candidate, resolve_candidate,
)
from .._atlas_candidate.step import candidate_step


def issue_parameter_extension_state(
        parent: CandidateState, optimizer: AdamWStateTree,
        policy: PlasticityPolicy) -> CandidateState:
    """Public B12 owner seam for a staged non-training parameter extension."""
    return _issue_parameter_extension_state(parent, optimizer, policy)


def issue_promotion_transition_state(parent: CandidateState, receipt) -> CandidateState:
    """Public B12 seam for a neural-inert B09 promotion transition."""
    return _issue_promotion_transition_state(parent, receipt)

__all__ = (
    "CandidateCustodyIdentity", "CandidateState", "CandidateStepProof",
    "CandidateTransaction", "LEGACY_STEP_PROOF_SCHEMA", "STEP_PROOF_SCHEMA",
    "begin_candidate", "candidate_step", "resolve_candidate",
    "issue_parameter_extension_state", "issue_promotion_transition_state",
    "_load_retained_candidate_state_with_parts",
)
