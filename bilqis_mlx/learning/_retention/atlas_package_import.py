"""B12 package-import state custody, distinct from native training candidates."""
from __future__ import annotations

from bilqis_mlx.learning._retention.candidate_identity import RAW_IDENTITY_SCHEME

from collections.abc import Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from types import MappingProxyType

import mlx.core as mx
import numpy as np

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.atlas_candidate import CandidateState
from bilqis_mlx.learning._retention._atlas_candidate.common import (
    RETAINED_STATE_ISSUER, STATE_SCHEMA,
)
from bilqis_mlx.learning.atlas_plasticity import IdentityRowAge, PlasticityPolicy
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree


RESET_POLICY_SCHEMA = "bilqis.mlx.package-import-reset-policy/v1"
TRANSACTION_SCHEMA = "bilqis.mlx.package-import-transaction/v1"
RESET_POLICY = MappingProxyType({
    "schema": RESET_POLICY_SCHEMA,
    "parameters": "IMPORT_DECLARED_SLICES_ONLY",
    "moments": "ZERO_CHANGED_ELEMENTS",
    "update_counts": "ZERO_NATIVE_COUNT_CELLS",
    "identity_row_ages": "ZERO_CHANGED_ROWS",
    "accepted_fast_since_full": "ZERO",
    "mode": "PRESERVE",
    "allocations": "PRESERVE",
    "optimizer_step": "PRESERVE",
})
RESET_POLICY_SHA256 = sha256(json.dumps(
    dict(RESET_POLICY), sort_keys=True, separators=(",", ":"), ensure_ascii=False,
).encode("utf-8")).hexdigest()
_TRANSACTION_ISSUER = object()


def _invalid():
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


@dataclass(frozen=True, order=True)
class ImportSlice:
    parameter_name: str
    start: int
    stop: int

    def __post_init__(self):
        if (type(self.parameter_name) is not str or not self.parameter_name
                or type(self.start) is not int or type(self.stop) is not int
                or not 0 <= self.start < self.stop):
            _invalid()


@dataclass(frozen=True, init=False)
class PackageImportTransaction:
    """One B12-owned import proposal; publication remains B13-owned."""

    parent: CandidateState
    candidate: CandidateState
    changed_slices: tuple[ImportSlice, ...]
    changed_identity_rows: tuple[tuple[int, int], ...]
    reset_policy_sha256: str
    schema_version: str = TRANSACTION_SCHEMA
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid()

    def __post_init__(self):
        if (getattr(self, "_issuance", None) is not _TRANSACTION_ISSUER
                or type(self.parent) is not CandidateState
                or type(self.candidate) is not CandidateState
                or self.changed_slices != _canonical_slices(self.changed_slices)
                or self.changed_identity_rows != tuple(sorted(set(self.changed_identity_rows)))
                or self.reset_policy_sha256 != RESET_POLICY_SHA256
                or self.schema_version != TRANSACTION_SCHEMA):
            _invalid()
        self.parent.__post_init__()
        self.candidate.__post_init__()
        if (self.candidate.allocations is not self.parent.allocations
                or self.candidate.optimizer_step != self.parent.optimizer_step
                or self.candidate.policy.mode != self.parent.policy.mode
                or self.candidate.policy.accepted_fast_since_full != 0):
            _invalid()


def _canonical_slices(value) -> tuple[ImportSlice, ...]:
    if (type(value) is not tuple or not value
            or any(type(item) is not ImportSlice for item in value)):
        _invalid()
    ordered = tuple(sorted(value))
    previous = {}
    for item in ordered:
        item.__post_init__()
        stop = previous.get(item.parameter_name, -1)
        if item.start < stop:
            _invalid()
        previous[item.parameter_name] = item.stop
    return ordered


def _validate_parameters(parent: CandidateState, parameters: Mapping[str, mx.array]):
    if not isinstance(parameters, Mapping) or set(parameters) != set(parent.optimizer.parameters):
        _invalid()
    for name, old in parent.optimizer.parameters.items():
        new = parameters[name]
        if (not isinstance(new, mx.array) or new.dtype != mx.float32
                or new.shape != old.shape or not bool(mx.all(mx.isfinite(new)))):
            _invalid()


def _slice_masks(parent: CandidateState, parameters, slices):
    _validate_parameters(parent, parameters)
    masks = {name: np.zeros(value.size, dtype=np.bool_)
             for name, value in parent.optimizer.parameters.items()}
    for item in slices:
        if item.parameter_name not in masks or item.stop > masks[item.parameter_name].size:
            _invalid()
        masks[item.parameter_name][item.start:item.stop] = True
    for name, mask in masks.items():
        before = np.asarray(parent.optimizer.parameters[name]).reshape(-1).view(np.uint32)
        after = np.asarray(parameters[name]).reshape(-1).view(np.uint32)
        if not np.array_equal(before[~mask], after[~mask]):
            _invalid()
    return masks


def _reset_counts(count, parameter, mask):
    reset = np.asarray(count).copy()
    if not bool(mask.any()):
        return count, ()
    if count.ndim == 0:
        reset[...] = 0
        return mx.array(reset, dtype=mx.uint64), ()
    row_width = parameter.size // parameter.shape[0]
    rows = tuple(int(value) for value in np.unique(np.flatnonzero(mask) // row_width))
    reset[list(rows)] = 0
    return mx.array(reset, dtype=mx.uint64), rows


def _reset_state(parent: CandidateState, parameters, slices):
    masks = _slice_masks(parent, parameters, slices)
    first, second, counts = {}, {}, {}
    changed_identity_rows = []
    age_ids = {row.identity for row in parent.policy.row_ages}
    for name, parameter in parent.optimizer.parameters.items():
        mask = masks[name]
        shape = tuple(parameter.shape)
        for target, source in ((first, parent.optimizer.m), (second, parent.optimizer.v)):
            if bool(mask.any()):
                raw = np.asarray(source[name]).copy().reshape(-1)
                raw[mask] = 0.0
                target[name] = mx.array(raw.reshape(shape), dtype=mx.float32)
            else:
                target[name] = source[name]
        counts[name], rows = _reset_counts(parent.optimizer.update_counts[name], parameter, mask)
        if name.startswith("identity.bank.") and rows:
            try:
                bank = int(name.rsplit(".", 1)[1])
            except ValueError:
                _invalid()
            identities = tuple((bank, row) for row in rows)
            if not set(identities).issubset(age_ids):
                _invalid()
            changed_identity_rows.extend(identities)
    changed = set(changed_identity_rows)
    ages = tuple(IdentityRowAge(row.bank_index, row.row_index,
                                0 if row.identity in changed else row.accepted_age)
                 for row in parent.policy.row_ages)
    policy = PlasticityPolicy(
        mode=parent.policy.mode, accepted_fast_since_full=0, row_ages=ages,
        policy_version=parent.policy.policy_version,
        schema_version=parent.policy.schema_version,
        mode_transition=parent.policy.mode_transition)
    optimizer = AdamWStateTree(parameters, first, second, counts)
    candidate = object.__new__(CandidateState)
    for name, value in (
            ("optimizer", optimizer), ("policy", policy),
            ("identity_scheme", RAW_IDENTITY_SCHEME),
            ("allocations", parent.allocations), ("optimizer_step", parent.optimizer_step),
            ("custody", parent.custody), ("step_proofs", parent.step_proofs),
            ("schema_version", STATE_SCHEMA), ("_issuance", RETAINED_STATE_ISSUER)):
        object.__setattr__(candidate, name, value)
    candidate.__post_init__()
    return candidate, tuple(sorted(changed))


def _issue_transaction(parent, candidate, slices, changed_identity_rows):
    transaction = object.__new__(PackageImportTransaction)
    for name, value in (
            ("parent", parent), ("candidate", candidate), ("changed_slices", slices),
            ("changed_identity_rows", changed_identity_rows),
            ("reset_policy_sha256", RESET_POLICY_SHA256),
            ("schema_version", TRANSACTION_SCHEMA), ("_issuance", _TRANSACTION_ISSUER)):
        object.__setattr__(transaction, name, value)
    transaction.__post_init__()
    return transaction


def prepare_package_import(
        parent: CandidateState, parameters: Mapping[str, mx.array],
        changed_slices: tuple[ImportSlice, ...],
) -> PackageImportTransaction:
    """Prepare the reset imported state without deciding retention or publishing it."""
    if type(parent) is not CandidateState:
        _invalid()
    parent.__post_init__()
    slices = _canonical_slices(changed_slices)
    candidate, changed_rows = _reset_state(parent, parameters, slices)
    return _issue_transaction(parent, candidate, slices, changed_rows)
