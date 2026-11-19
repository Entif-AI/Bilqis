"""Retained candidate state and B13 rehydration."""
from __future__ import annotations
from dataclasses import dataclass, field
import mlx.core as mx
import numpy as np
from bilqis_mlx.learning.atlas_engram import INITIAL_MOTIF_CAPACITY
from bilqis_mlx.learning.atlas_engram_transaction import MotifAllocationSnapshot
from bilqis_mlx.learning.atlas_plasticity import (
    PlasticityPolicy, apply_promotion_transition,
)
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
from .common import RETAINED_STATE_ISSUER, STATE_SCHEMA, invalid, is_digest
from .proofs import CandidateStepProof
from bilqis_mlx.learning._retention._atlas_candidate.identity import (
    LEGACY_IDENTITY_SCHEME, RAW_IDENTITY_SCHEME, require_identity_scheme,
)
from .identity_binding import (
    mark_candidate_state_unbindable, protect_candidate_state,
)

def _is_genesis_allocations(snapshot: MotifAllocationSnapshot) -> bool:
    return (type(snapshot) is MotifAllocationSnapshot
            and not snapshot.manifest.slots
            and snapshot.manifest.capacity == INITIAL_MOTIF_CAPACITY
            and not snapshot.observed_uses and not snapshot.pending_keys
            and not snapshot.aliases)

def _current_objective_ref() -> str:
    from bilqis_mlx.runtime.training_objective import (
        current_training_objective,
    )
    return current_training_objective().ref


def _current_objective_digest() -> str:
    from bilqis_mlx.runtime.training_objective import (
        current_training_objective,
    )
    return current_training_objective().digest


@dataclass(frozen=True)
class CandidateCustodyIdentity:
    """The published identity of one accepted generation.

    A candidate step may only be authorised against this identity, so
    provenance issued for another run, generation, manifest, topology or
    extents state cannot update this candidate.
    """

    run_id: str
    generation: int
    manifest_sha256: str | None
    topology_digest: str
    extents_digest: str
    training_objective_ref: str | None = field(default_factory=_current_objective_ref)
    training_objective_digest: str | None = field(
        default_factory=_current_objective_digest)

    def __post_init__(self) -> None:
        if (not isinstance(self.run_id, str) or not self.run_id
                or type(self.generation) is not int or self.generation < 0
                or (self.manifest_sha256 is not None
                    and not is_digest(self.manifest_sha256))
                or not is_digest(self.topology_digest)
                or not is_digest(self.extents_digest)
                or ((self.training_objective_ref is None)
                    != (self.training_objective_digest is None))
                or (self.training_objective_ref is not None
                    and (not isinstance(self.training_objective_ref, str)
                         or not self.training_objective_ref
                         or not is_digest(self.training_objective_digest)))):
            invalid()


@dataclass(frozen=True)
class CandidateState:
    """The inseparable proposed optimizer, allocation and policy state."""

    optimizer: AdamWStateTree
    policy: PlasticityPolicy
    allocations: MotifAllocationSnapshot
    optimizer_step: int
    custody: CandidateCustodyIdentity | None = None
    step_proofs: tuple = ()
    schema_version: str = STATE_SCHEMA
    identity_scheme: str = RAW_IDENTITY_SCHEME
    _issuance: object = field(init=False, default=None, repr=False, compare=False)

    def __post_init__(self):
        require_identity_scheme(self.identity_scheme)
        if (type(self.optimizer) is not AdamWStateTree
                or type(self.policy) is not PlasticityPolicy
                or type(self.allocations) is not MotifAllocationSnapshot
                or type(self.optimizer_step) is not int or self.optimizer_step < 0
                or (self.custody is not None
                    and type(self.custody) is not CandidateCustodyIdentity)
                or type(self.step_proofs) is not tuple
                or any(type(proof) is not CandidateStepProof for proof in self.step_proofs)
                or any(proof.step_index != index + 1
                       for index, proof in enumerate(self.step_proofs))
                or self.schema_version != STATE_SCHEMA):
            invalid()
        self.optimizer.validate_structure()
        self.policy.validate()
        self.allocations.__post_init__()
        if (not _is_genesis_allocations(self.allocations)
                and getattr(self, '_issuance', None) is not RETAINED_STATE_ISSUER):
            invalid()
        for row in self.policy.row_ages:
            count = self.optimizer.update_counts.get(f'identity.bank.{row.bank_index}')
            if count is None or count.ndim != 1 or row.row_index >= count.shape[0]:
                invalid()


def _load_retained_candidate_state_with_parts(
        bundle_root, *, expected_manifest_sha256: str):
    """Rehydrate retained state only from B13-validated immutable custody."""
    from bilqis_mlx.runtime.bamf_bundle.codec import _load_validated_bundle_parts

    parts = _load_validated_bundle_parts(
        bundle_root, expected_manifest_sha256=expected_manifest_sha256)
    proofs = tuple(CandidateStepProof.from_record(item)
                   for item in parts.records["step_proofs"]["proofs"])
    state = object.__new__(CandidateState)
    for name, value in (
            ('optimizer', parts.numerical), ('policy', parts.policy),
            ('identity_scheme', parts.manifest['optimizer'].get(
                'identity_scheme', LEGACY_IDENTITY_SCHEME)),
            ('allocations', parts.motif), ('optimizer_step', parts.optimizer_step),
            ('custody', CandidateCustodyIdentity(
                parts.manifest['run_id'], parts.manifest['generation'],
                expected_manifest_sha256,
                parts.spec.digest, parts.extents.digest,
                parts.manifest.get('training_objective_ref'),
                parts.manifest.get('training_objective_digest'))),
            ('step_proofs', proofs),
            ('schema_version', STATE_SCHEMA),
            ('_issuance', RETAINED_STATE_ISSUER)):
        object.__setattr__(state, name, value)
    state.__post_init__()
    protect_candidate_state(state)
    return state, parts


def _array_equal(left, right) -> bool:
    return np.array_equal(np.asarray(left), np.asarray(right))


def _identity_bank(name: str) -> int | None:
    if not name.startswith("identity.bank."):
        return None
    try:
        return int(name.rsplit(".", 1)[1])
    except ValueError:
        invalid()


def _admitted_rows_by_bank(
        new_rows: set[tuple[int, int]]) -> dict[int, set[int]]:
    allowed: dict[int, set[int]] = {}
    for bank, row in new_rows:
        allowed.setdefault(bank, set()).add(row)
    return allowed


def _require_zero_rows(array, rows: set[int]) -> None:
    if rows and np.any(np.asarray(array)[sorted(rows)] != 0):
        invalid()


def _require_zero_outside_rows(array, rows: set[int]) -> None:
    values = np.asarray(array)
    protected = [row for row in range(values.shape[0]) if row not in rows]
    if protected and np.any(values[protected] != 0):
        invalid()


def _validate_new_identity_parameter(
        optimizer: AdamWStateTree, name: str, admitted_rows: set[int]) -> None:
    for group in (optimizer.parameters, optimizer.m, optimizer.v,
                  optimizer.update_counts):
        _require_zero_outside_rows(group[name], admitted_rows)
    for group in (optimizer.m, optimizer.v, optimizer.update_counts):
        _require_zero_rows(group[name], admitted_rows)


def _validate_existing_parameter_group(
        before, after, admitted_rows: set[int], *, zero_admitted: bool) -> None:
    old_values = np.asarray(before)
    next_values = np.asarray(after)
    if old_values.shape != next_values.shape:
        invalid()
    if not admitted_rows:
        if not np.array_equal(old_values, next_values):
            invalid()
        return
    protected = [row for row in range(old_values.shape[0])
                 if row not in admitted_rows]
    if protected and not np.array_equal(old_values[protected], next_values[protected]):
        invalid()
    if zero_admitted:
        _require_zero_rows(next_values, admitted_rows)


def _validate_existing_parameter(
        old: AdamWStateTree, optimizer: AdamWStateTree, name: str,
        admitted_rows: set[int]) -> None:
    for old_group, next_group, zero_admitted in (
            (old.parameters, optimizer.parameters, False),
            (old.m, optimizer.m, True),
            (old.v, optimizer.v, True),
            (old.update_counts, optimizer.update_counts, True)):
        _validate_existing_parameter_group(
            old_group[name], next_group[name], admitted_rows,
            zero_admitted=zero_admitted)


def _validate_parameter_extension_optimizer(
        parent: CandidateState, optimizer: AdamWStateTree,
        new_rows: set[tuple[int, int]]) -> None:
    """Permit only source-admitted identity rows to differ from the parent."""
    old = parent.optimizer
    old_names = set(old.parameters)
    next_names = set(optimizer.parameters)
    if not old_names <= next_names:
        invalid()
    allowed_by_bank = _admitted_rows_by_bank(new_rows)
    for name in next_names - old_names:
        bank = _identity_bank(name)
        if bank not in allowed_by_bank:
            invalid()
    for name in next_names:
        bank = _identity_bank(name)
        admitted_rows = allowed_by_bank.get(bank, set()) if bank is not None else set()
        if name not in old_names:
            _validate_new_identity_parameter(optimizer, name, admitted_rows)
            continue
        _validate_existing_parameter(old, optimizer, name, admitted_rows)


def _issue_parameter_extension_state(
        parent: CandidateState, optimizer: AdamWStateTree,
        policy: PlasticityPolicy) -> CandidateState:
    """Issue neural-inert state for an admitted append-only parameter extension.

    The accepted parent's motif allocation, optimizer step, custody identity and
    proof history remain exact. New policy rows must begin at age zero. A
    separate admission binding is still required before publication.
    """
    if (type(parent) is not CandidateState
            or type(optimizer) is not AdamWStateTree
            or type(policy) is not PlasticityPolicy):
        invalid()
    parent_rows = {row.identity: row.accepted_age for row in parent.policy.row_ages}
    next_rows = {row.identity: row.accepted_age for row in policy.row_ages}
    new_rows = set(next_rows) - set(parent_rows)
    if (any(next_rows.get(identity) != age
            for identity, age in parent_rows.items())
            or any(identity not in parent_rows and age != 0
                   for identity, age in next_rows.items())
            or policy.mode != parent.policy.mode
            or policy.accepted_fast_since_full
            != parent.policy.accepted_fast_since_full
            or policy.policy_version != parent.policy.policy_version
            or policy.schema_version != parent.policy.schema_version
            or policy.mode_transition != parent.policy.mode_transition):
        invalid()
    _validate_parameter_extension_optimizer(parent, optimizer, new_rows)
    state = object.__new__(CandidateState)
    for name, value in (
            ('optimizer', optimizer), ('policy', policy),
            ('identity_scheme', RAW_IDENTITY_SCHEME if new_rows else parent.identity_scheme),
            ('allocations', parent.allocations),
            ('optimizer_step', parent.optimizer_step),
            ('custody', parent.custody), ('step_proofs', parent.step_proofs),
            ('schema_version', STATE_SCHEMA), ('_issuance', RETAINED_STATE_ISSUER)):
        object.__setattr__(state, name, value)
    state.__post_init__()
    mark_candidate_state_unbindable(state, "CALLER_OWNED_NUMERICAL_STATE")
    return state


def _issue_promotion_transition_state(parent: CandidateState, receipt) -> CandidateState:
    """Persist one B09 cadence transition without changing neural state."""
    from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
    from bilqis_mlx.runtime.plasticity_promotion import (
        require_accepted_promotion_transition,
    )

    if type(parent) is not CandidateState:
        invalid()
    require_accepted_promotion_transition(receipt)
    custody = parent.custody
    if (custody is None
            or receipt.run_id != custody.run_id
            or receipt.parent_generation != custody.generation
            or receipt.candidate_generation != custody.generation + 1
            or receipt.parent_manifest_sha256 != custody.manifest_sha256
            or receipt.candidate_identity_sha256 != candidate_identity_digest(parent)
            or receipt.optimizer_step != parent.optimizer_step):
        invalid()
    policy = apply_promotion_transition(parent.policy, receipt)
    state = object.__new__(CandidateState)
    for name, value in (
            ('optimizer', parent.optimizer), ('policy', policy),
            ('identity_scheme', parent.identity_scheme),
            ('allocations', parent.allocations),
            ('optimizer_step', parent.optimizer_step),
            ('custody', parent.custody), ('step_proofs', parent.step_proofs),
            ('schema_version', STATE_SCHEMA), ('_issuance', RETAINED_STATE_ISSUER)):
        object.__setattr__(state, name, value)
    state.__post_init__()
    mark_candidate_state_unbindable(state, "CALLER_OWNED_NUMERICAL_STATE")
    return state
