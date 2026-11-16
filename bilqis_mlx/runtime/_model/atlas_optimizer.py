"""Private numerical AdamW counts; full-model candidate custody remains separate.

No durable student, participation policy, clipping policy, generation publication
or historical optimizer migration is implemented by this numerical seam.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping

import mlx.core as mx
import numpy as np

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.mlx_parity import clip_gradients
from bilqis_mlx.runtime.optimizer_count_geometry import declared_update_count_shape
from bilqis_mlx.runtime.optimizer_step import (
    adamw_leaf_update, adamw_selected_rows_update, optimizer_parent_witness_matches,
)


DENSE_COUNT_RANK = 0
ROW_COUNT_RANK = 1
ROW_SELECTION_PARTS = 2
ADAM_MOMENT_COUNT = 2
UINT64_MAX = int(np.iinfo(np.uint64).max)
STATE_SCHEMA = "bilqis.mlx.adamw-count-state/provisional-v1"


def _invalid():
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


def _finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


@dataclass(frozen=True)
class AdamWHyperparameters:
    """Exact supplied teacher values; this record makes no policy selection."""

    learning_rate: float
    betas: tuple[float, float]
    eps: float
    weight_decay: float

    def __post_init__(self):
        if (not _finite_number(self.learning_rate) or self.learning_rate <= 0 or
                type(self.betas) is not tuple or len(self.betas) != ADAM_MOMENT_COUNT or
                any(not _finite_number(beta) or not 0 <= beta < 1 for beta in self.betas) or
                not _finite_number(self.eps) or self.eps <= 0 or
                not _finite_number(self.weight_decay) or self.weight_decay < 0):
            _invalid()


@dataclass(frozen=True)
class AdamWStateTree:
    """One exact numerical tree; dense counts are scalar, table counts per row.

    uint64 scalar counts give whole-tensor participation. A uint64 vector whose
    length equals the parameter's leading extent gives per-row participation.
    The normative runtime/model_topology_v2.py parameter ledger, row admission
    and serialization must be bound by the complete-model and candidate
    transaction owners before this fixture tree becomes candidate state.
    """

    parameters: Mapping[str, mx.array]
    m: Mapping[str, mx.array]
    v: Mapping[str, mx.array]
    update_counts: Mapping[str, mx.array]
    schema_version: str = STATE_SCHEMA

    def __post_init__(self):
        self.validate()
        for name in ("parameters", "m", "v", "update_counts"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

    def validate_structure(self):
        """Validate CPU-visible schema, tree, shape and dtype invariants only."""
        trees = (self.parameters, self.m, self.v, self.update_counts)
        if (self.schema_version != STATE_SCHEMA or any(not isinstance(tree, Mapping) for tree in trees) or
                not self.parameters or any(type(name) is not str or not name for name in self.parameters) or
                any(set(tree) != set(self.parameters) for tree in trees)):
            _invalid()
        for name, parameter in self.parameters.items():
            if (not isinstance(parameter, mx.array) or parameter.dtype != mx.float32 or
                    parameter.size < 1):
                _invalid()
            for moment in (self.m[name], self.v[name]):
                if not isinstance(moment, mx.array) or moment.shape != parameter.shape or moment.dtype != mx.float32:
                    _invalid()
            count = self.update_counts[name]
            if (not isinstance(count, mx.array) or count.dtype != mx.uint64 or
                    not (count.shape == () or (parameter.ndim >= ROW_COUNT_RANK and
                                              count.shape == (parameter.shape[0],)))):
                _invalid()

    def validate(self):
        """Validate structure plus one aggregated device-visible numerical predicate."""
        self.validate_structure()
        checks = []
        for name, parameter in self.parameters.items():
            checks.extend((
                mx.all(mx.isfinite(parameter)),
                mx.all(mx.isfinite(self.m[name])),
                mx.all(mx.isfinite(self.v[name])),
                mx.all(self.v[name] >= 0),
            ))
        valid = mx.all(mx.stack(tuple(checks)))
        mx.eval(valid)
        if not bool(valid):
            _invalid()


def reconcile_b01_optimizer_manifest(
        state: AdamWStateTree, spec, extents) -> Mapping[str, bool]:
    """Validate one optimizer tree against B01 and return its decay manifest.

    B01 owns the complete parameter names, shapes, initializers and decay flags.
    B12 adds moments/counts but cannot invent a parallel tree or caller-authored
    decay policy. Order is checked as well as membership so serialization and
    optimizer custody consume the same expanded ParameterSpec sequence.
    """
    from bilqis_mlx.runtime.model_topology_v2 import (
        GenerationExtents, ModelTopologySpecV2, expected_bamf_shapes,
        validate_bamf_parameters,
    )

    if (type(state) is not AdamWStateTree
            or type(spec) is not ModelTopologySpecV2
            or type(extents) is not GenerationExtents):
        _invalid()
    state.validate_structure()
    validate_bamf_parameters(spec, extents, state.parameters)
    declared = expected_bamf_shapes(spec, extents)
    names = tuple(item.name for item in declared)
    if any(tuple(tree) != names for tree in (
            state.parameters, state.m, state.v, state.update_counts)):
        _invalid()
    for item in declared:
        if (state.parameters[item.name].shape != item.shape
                or state.m[item.name].shape != item.shape
                or state.v[item.name].shape != item.shape
                or state.update_counts[item.name].shape
                != declared_update_count_shape(item)):
            _invalid()
    return MappingProxyType({item.name: item.decay for item in declared})


def _validate_step_inputs(parent, gradients, participation):
    if (type(parent) is not AdamWStateTree or
            any(not isinstance(tree, Mapping) or set(tree) != set(parent.parameters)
                for tree in (gradients, participation))):
        _invalid()
    parent.validate_structure()
    checks = []
    for name, parameter in parent.parameters.items():
        gradient, mask = gradients[name], participation[name]
        if (not isinstance(gradient, mx.array) or gradient.shape != parameter.shape
                or gradient.dtype != mx.float32
                or not isinstance(mask, mx.array) or mask.dtype != mx.bool_ or
                mask.shape != parent.update_counts[name].shape):
            _invalid()
        checks.append(mx.all(mx.isfinite(gradient)))
    return checks


def _participation_authority_checks(parent, participation, authority):
    """Validate owner-issued row selections and bind them to device masks."""
    if authority is None:
        return []
    if not isinstance(authority, Mapping) or set(authority) != set(parent.parameters):
        _invalid()
    checks = []
    for name, count in parent.update_counts.items():
        selection = authority[name]
        if type(selection) is not tuple or len(selection) != ROW_SELECTION_PARTS:
            _invalid()
        whole, rows = selection
        if (type(whole) is not bool or type(rows) is not tuple
                or any(type(row) is not int or row < 0 for row in rows)
                or rows != tuple(sorted(set(rows)))
                or (whole and rows)):
            _invalid()
        mask = participation[name]
        if count.ndim == DENSE_COUNT_RANK:
            if rows:
                _invalid()
            expected = mx.array(whole, dtype=mx.bool_)
        else:
            if any(row >= count.shape[0] for row in rows):
                _invalid()
            expected = mx.ones_like(mask) if whole else mx.zeros_like(mask)
            if rows:
                expected[mx.array(rows, dtype=mx.uint32)] = True
        checks.append(mx.all(mask == expected))
    return checks


def _preflight(parent, gradients, participation, hyperparameters, decay, loss_bearing,
               participation_authority=None):
    checks = _validate_step_inputs(parent, gradients, participation)
    if (type(hyperparameters) is not AdamWHyperparameters or type(loss_bearing) is not bool or
            not isinstance(decay, Mapping) or set(decay) != set(parent.parameters) or
            any(type(value) is not bool for value in decay.values())):
        _invalid()
    hyperparameters.__post_init__()
    checks.extend(_participation_authority_checks(
        parent, participation, participation_authority))
    if loss_bearing:
        maximum = mx.array(np.array(UINT64_MAX, dtype=np.uint64))
        checks.extend(
            ~mx.any(participation[name] & (count == maximum))
            for name, count in parent.update_counts.items())
    any_participation = mx.any(mx.stack(tuple(
        mx.any(mask) for mask in participation.values())))
    valid = mx.all(mx.stack(tuple(checks)))
    mx.eval(valid, any_participation)
    if not bool(valid):
        _invalid()
    return bool(any_participation)


def _masked_clipped_gradients(parent, gradients, participation, *, max_norm):
    """Mask supplied participation before the existing global FP32 norm clip.

    This numerical adapter does not attest that masks came from actual model
    execution. The full-model owner must supply that independent provenance.
    """
    if not _finite_number(max_norm) or max_norm <= 0:
        _invalid()
    masked = {}
    for name, gradient in gradients.items():
        mask = participation[name]
        if mask.ndim == ROW_COUNT_RANK:
            mask = mask.reshape((-1,) + (1,) * (gradient.ndim - 1))
        masked[name] = mx.where(mask, gradient, mx.zeros_like(gradient))
    clipped, norm = clip_gradients(mx, masked, max_norm=max_norm)
    finite_norm = mx.isfinite(norm)
    mx.eval(finite_norm)
    if not bool(finite_norm):
        _invalid()
    return clipped, norm


def _adamw_update(parent: AdamWStateTree, gradients: Mapping[str, mx.array],
                  participation: Mapping[str, mx.array], hyperparameters: AdamWHyperparameters, *,
                  decay: Mapping[str, bool], loss_bearing: bool = True,
                  max_norm: float | None = None, parent_witness=None,
                  participation_authority=None) -> AdamWStateTree:
    """Apply native AdamW only to selected numerical leaves/rows, without publication.

    max_norm uses the existing global clip after participation masking. When
    omitted, supplied gradients must already follow the clipping contract.
    Masks are explicit Boolean scalars or row vectors, never inferred from
    nonzero gradients. Selected zero gradients still advance moments/counts.
    No-loss and wholly frozen steps return the original state object.
    """
    # Numerical validation belongs to this exact consumption boundary.  A
    # witness may attest object ownership, but MLX leaves remain mutable, so it
    # must never substitute for validating the state at the instant it is used.
    if parent_witness is not None and not optimizer_parent_witness_matches(parent_witness, parent):
        _invalid()
    parent.validate()
    any_participation = _preflight(
        parent, gradients, participation, hyperparameters, decay, loss_bearing,
        participation_authority)
    if max_norm is not None and (not _finite_number(max_norm) or max_norm <= 0):
        _invalid()
    if not loss_bearing or not any_participation:
        return parent
    if max_norm is not None:
        gradients, _ = _masked_clipped_gradients(parent, gradients, participation, max_norm=max_norm)
    parameters, first, second, counts = (dict(tree) for tree in
                                         (parent.parameters, parent.m, parent.v, parent.update_counts))
    for name, parameter in parent.parameters.items():
        mask = participation[name]
        count = parent.update_counts[name]
        authority = None if participation_authority is None else participation_authority[name]
        if authority is not None and not authority[0] and not authority[1]:
            continue
        kwargs = dict(
            learning_rate=hyperparameters.learning_rate,
            betas=hyperparameters.betas,
            eps=hyperparameters.eps,
            weight_decay=hyperparameters.weight_decay if decay[name] else 0.,
        )
        if authority is not None and authority[1]:
            updated, next_first, next_second, next_count = adamw_selected_rows_update(
                parameter, parent.m[name], parent.v[name], count, gradients[name],
                mask, authority[1], **kwargs)
        else:
            updated, next_first, next_second, next_count = adamw_leaf_update(
                parameter, parent.m[name], parent.v[name], count,
                gradients[name], mask, **kwargs)
        parameters[name] = updated
        first[name] = next_first
        second[name] = next_second
        counts[name] = next_count
    return AdamWStateTree(parameters, first, second, counts)


def _create_unbound_bamf_optimizer(spec, extents, *, run_seed):
    """Reuse the complete topology owner's disposable initialization verbatim.

    This fresh UNBOUND state has no admitted source rows or production caller.
    It is not a historical optimizer migration or a checkpoint-generation grant.
    Count geometry follows declared table initializers; vector seeds and dense
    matrices retain scalar counts. Decay flags come only from the same ledger.
    """
    from bilqis_mlx.runtime.model_topology_v2 import (
        create_unbound_bamf_state, expected_bamf_shapes,
    )

    parameters, native, manifest = create_unbound_bamf_state(spec, extents, run_seed=run_seed)
    declared = expected_bamf_shapes(spec, extents)
    counts = {
        item.name: mx.zeros(declared_update_count_shape(item), dtype=mx.uint64)
        for item in declared
    }
    state = AdamWStateTree(parameters, {item.name: native[item.name]["m"] for item in declared},
                           {item.name: native[item.name]["v"] for item in declared}, counts)
    decay = reconcile_b01_optimizer_manifest(state, spec, extents)
    return state, decay, manifest
