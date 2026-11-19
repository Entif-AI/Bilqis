"""Speculative candidate transactions and accepted-state resolution."""
from __future__ import annotations
from dataclasses import dataclass, field
import mlx.core as mx
from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.learning.atlas_engram import MotifBudget
from bilqis_mlx.learning.atlas_engram_transaction import (
    MotifAllocationSnapshot,
)
from bilqis_mlx.learning.atlas_plasticity import advance_candidate_policy, next_update_mode
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
from .common import (
    RETAINED_STATE_ISSUER, STATE_SCHEMA, TRANSACTION_ISSUER,
    TRANSACTION_SCHEMA, invalid,
)
from .proofs import CandidateStepProof
from bilqis_mlx.learning._retention._atlas_candidate.identity import RAW_IDENTITY_SCHEME
from .identity_binding import protect_candidate_state
from .state import CandidateState, _is_genesis_allocations
from .motif_transition import (
    CandidateMotifAllocationTransition,
    _require_candidate_motif_allocation_transition,
    _stage_candidate_motif_allocation,
)


def _parent_object_guard(parent: CandidateState) -> tuple:
    """Cheap process-local proof that the accepted parent objects are unchanged."""
    optimizer = parent.optimizer
    groups = []
    for group in ("parameters", "m", "v", "update_counts"):
        values = getattr(optimizer, group)
        groups.append((
            group, id(values),
            tuple((name, id(value)) for name, value in sorted(values.items())),
        ))
    return (
        id(parent), id(optimizer), parent.optimizer_step,
        id(parent.policy), id(parent.allocations), tuple(groups),
    )


@dataclass(frozen=True, init=False)
class CandidateTransaction:
    """One speculative branch; no method mutates or publishes its parent."""

    parent: CandidateState
    optimizer: AdamWStateTree
    allocations: MotifAllocationSnapshot
    teacher_requests_full: bool
    update_steps: int = 0
    step_proofs: tuple = ()
    training_authorities: tuple = ()
    motif_transition: CandidateMotifAllocationTransition | None = None
    training_objective_ref: str = field(init=False)
    training_objective_digest: str = field(init=False)
    schema_version: str = TRANSACTION_SCHEMA
    _parent_identity_sha256: str = field(init=False, repr=False, compare=False)
    _parent_guard: tuple = field(init=False, repr=False, compare=False)
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        # Public construction/replacement cannot assert a completed transition.
        invalid()

    def __post_init__(self):
        if getattr(self, '_issuance', None) is not TRANSACTION_ISSUER:
            invalid()
        if (type(self.parent) is not CandidateState
                or type(self.optimizer) is not AdamWStateTree
                or type(self.allocations) is not MotifAllocationSnapshot
                or type(self.teacher_requests_full) is not bool
                or type(self.update_steps) is not int or self.update_steps < 0
                or type(self.step_proofs) is not tuple
                or len(self.step_proofs) != self.update_steps
                or type(self.training_authorities) is not tuple
                or len(self.training_authorities) != self.update_steps
                or any(type(proof) is not CandidateStepProof for proof in self.step_proofs)
                or any(proof.step_index != index + 1
                       for index, proof in enumerate(self.step_proofs))
                or (self.motif_transition is not None
                    and type(self.motif_transition) is not CandidateMotifAllocationTransition)
                or not isinstance(self.training_objective_ref, str)
                or not self.training_objective_ref
                or not isinstance(self.training_objective_digest, str)
                or len(self.training_objective_digest) != SHA256_HEX_LENGTH
                or not isinstance(self._parent_identity_sha256, str)
                or len(self._parent_identity_sha256) != SHA256_HEX_LENGTH
                or _parent_object_guard(self.parent) != self._parent_guard
                or self.schema_version != TRANSACTION_SCHEMA):
            invalid()
        from bilqis_mlx.runtime.training_objective import (
            require_training_objective_digest,
        )
        require_training_objective_digest(self.training_objective_digest)
        custody = self.parent.custody
        if (custody is not None
                and (custody.training_objective_ref != self.training_objective_ref
                     or custody.training_objective_digest
                     != self.training_objective_digest)):
            invalid()
        self.parent.__post_init__()
        self.optimizer.validate_structure()
        self.allocations.__post_init__()
        if self.motif_transition is None:
            if (self.allocations is not self.parent.allocations
                    or set(self.optimizer.parameters) != set(self.parent.optimizer.parameters)):
                invalid()
        else:
            _require_candidate_motif_allocation_transition(self.motif_transition)
            transition = self.motif_transition
            if (self.update_steps < 1
                    or self.parent.custody is None
                    or transition.parent_manifest_sha256
                    != self.parent.custody.manifest_sha256
                    or transition.parent_extents_sha256
                    != self.parent.custody.extents_digest
                    or transition.parent_allocation_sha256 != self.parent.allocations.digest
                    or transition.candidate_allocation_sha256 != self.allocations.digest):
                invalid()
        count_checks = []
        for name, count in self.optimizer.update_counts.items():
            previous = self.parent.optimizer.update_counts.get(name)
            if previous is None:
                if self.motif_transition is None or not name.startswith("motif.page."):
                    invalid()
                continue
            if (self.optimizer.parameters[name].shape != self.parent.optimizer.parameters[name].shape
                    or count.shape != previous.shape):
                invalid()
            count_checks.extend((
                mx.all(count >= previous),
                mx.all(count - previous <= self.update_steps),
            ))
        if count_checks:
            counts_valid = mx.all(mx.stack(tuple(count_checks)))
            mx.eval(counts_valid)
            if not bool(counts_valid):
                invalid()

    @property
    def update_mode(self) -> str:
        return next_update_mode(self.parent.policy, teacher_requests_full=self.teacher_requests_full)


def _issue_transaction(parent, optimizer, teacher_requests_full, update_steps=0,
                       step_proofs=(), training_authorities=(), *, allocations=None,
                       motif_transition=None, parent_identity_sha256=None,
                       parent_guard=None):
    """Continue one candidate; B07 allocation state is terminal when present."""
    candidate = object.__new__(CandidateTransaction)
    allocations = parent.allocations if allocations is None else allocations
    if parent_identity_sha256 is None:
        from ..atlas_acceptance import candidate_identity_digest
        parent_identity_sha256 = candidate_identity_digest(parent)
    parent_guard = _parent_object_guard(parent) if parent_guard is None else parent_guard
    custody = parent.custody
    if custody is None:
        from bilqis_mlx.runtime.training_objective import (
            current_training_objective,
        )
        objective = current_training_objective()
        objective_ref, objective_digest = objective.ref, objective.digest
    elif (custody.training_objective_ref is None
            or custody.training_objective_digest is None):
        invalid()
    else:
        from bilqis_mlx.runtime.training_objective import (
            require_training_objective_digest,
        )
        require_training_objective_digest(custody.training_objective_digest)
        objective_ref = custody.training_objective_ref
        objective_digest = custody.training_objective_digest
    for name, value in (
            ('parent', parent), ('optimizer', optimizer), ('allocations', allocations),
            ('teacher_requests_full', teacher_requests_full), ('update_steps', update_steps),
            ('step_proofs', tuple(step_proofs)),
            ('training_authorities', tuple(training_authorities)),
            ('motif_transition', motif_transition),
            ('training_objective_ref', objective_ref),
            ('training_objective_digest', objective_digest),
            ('_parent_identity_sha256', parent_identity_sha256),
            ('_parent_guard', parent_guard),
            ('schema_version', TRANSACTION_SCHEMA), ('_issuance', TRANSACTION_ISSUER)):
        object.__setattr__(candidate, name, value)
    candidate.__post_init__()
    return candidate


def begin_candidate(parent: CandidateState, *, budget=None,
                    teacher_requests_full: bool = False) -> CandidateTransaction:
    """Begin optimizer-only work from one validated retained parent."""
    if type(parent) is not CandidateState or type(teacher_requests_full) is not bool:
        invalid()
    parent.__post_init__()
    if budget is not None and type(budget) is not MotifBudget:
        invalid()
    return _issue_transaction(parent, parent.optimizer, teacher_requests_full)


def _begin_candidate_with_parent_identity(
        parent: CandidateState, parent_identity_sha256: str, *,
        teacher_requests_full: bool = False) -> CandidateTransaction:
    """Accepted-custody ingress that reuses an owner-issued immutable parent identity."""
    if (type(parent) is not CandidateState
            or not isinstance(parent_identity_sha256, str)
            or len(parent_identity_sha256) != SHA256_HEX_LENGTH
            or type(teacher_requests_full) is not bool):
        invalid()
    parent.__post_init__()
    return _issue_transaction(
        parent, parent.optimizer, teacher_requests_full,
        parent_identity_sha256=parent_identity_sha256)


def resolve_candidate(candidate: CandidateTransaction, *, accepted: bool) -> CandidateState:
    """Return all retained components together, or return the exact parent.

    accepted comes from the retention owner. This pure selection is neither a
    retention decision nor an accepted-generation/checkpoint publication grant.
    """
    if type(candidate) is not CandidateTransaction or type(accepted) is not bool:
        invalid()
    candidate.__post_init__()
    if not accepted or candidate.update_steps == 0:
        return candidate.parent
    rows = tuple(row.identity for row in candidate.parent.policy.row_ages
                 if bool(candidate.optimizer.update_counts[f'identity.bank.{row.bank_index}'][row.row_index]
                         > candidate.parent.optimizer.update_counts[f'identity.bank.{row.bank_index}'][row.row_index]))
    policy = advance_candidate_policy(
        candidate.parent.policy, teacher_requests_full=candidate.teacher_requests_full,
        accepted=True, participating_rows=rows)
    step = candidate.parent.optimizer_step + candidate.update_steps
    if _is_genesis_allocations(candidate.allocations):
        state = CandidateState(candidate.optimizer, policy, candidate.allocations, step,
                               candidate.parent.custody,
                               tuple(candidate.step_proofs),
                               identity_scheme=RAW_IDENTITY_SCHEME)
        protect_candidate_state(state)
        return state
    state = object.__new__(CandidateState)
    for name, value in (
            ('optimizer', candidate.optimizer), ('policy', policy),
            ('identity_scheme', RAW_IDENTITY_SCHEME),
            ('allocations', candidate.allocations), ('optimizer_step', step),
            ('custody', candidate.parent.custody),
            ('step_proofs', tuple(candidate.step_proofs)),
            ('schema_version', STATE_SCHEMA), ('_issuance', RETAINED_STATE_ISSUER)):
        object.__setattr__(state, name, value)
    state.__post_init__()
    protect_candidate_state(state)
    return state
