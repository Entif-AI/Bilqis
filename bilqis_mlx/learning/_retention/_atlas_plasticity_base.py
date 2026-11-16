"""B09.1a rank-eight residual adapters and retained identity-row ages.

This module defines numerical adapters and immutable eligibility proposals.
B09.1b owns cadence/mode transitions, B09.1c owns step participation masks,
and B12/B13/C own AdamW and accepted-generation publication.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, ParameterCensus,
    ParameterGroup, expected_bamf_shapes,
)


ADAPTER_SCHEMA = "bilqis.mlx.plastic-adapter/v1"
AGE_SCHEMA = "bilqis.mlx.identity-row-age/v1"
ELIGIBILITY_SCHEMA = "bilqis.mlx.plastic-group-eligibility/v1"
WIDTH = ModelTopologySpecV2.width
RANK = ModelTopologySpecV2.adapter_rank
GROUP_COUNT = ModelTopologySpecV2.depth_groups
ESTABLISHED_AGE = 8
UPDATE_MODES = frozenset({"FOUNDATION", "FAST", "FULL"})
ADAPTER_NAMES = ("norm", "A", "B")


def _invalid() -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


@dataclass(frozen=True)
class AdapterParameters:
    group_index: int
    norm: mx.array
    A: mx.array
    B: mx.array
    schema_version: str = ADAPTER_SCHEMA

    def __post_init__(self) -> None:
        if (type(self.group_index) is not int
                or not 0 <= self.group_index < GROUP_COUNT
                or not isinstance(self.norm, mx.array)
                or self.norm.shape != (WIDTH,)
                or not isinstance(self.A, mx.array)
                or self.A.shape != (RANK, WIDTH)
                or not isinstance(self.B, mx.array)
                or self.B.shape != (WIDTH, RANK)
                or any(value.dtype != mx.float32
                       or (host_tensor_validation_enabled()
                           and not bool(mx.all(mx.isfinite(value))))
                       for value in (self.norm, self.A, self.B))
                or self.schema_version != ADAPTER_SCHEMA):
            _invalid()


def adapter_parameter_view(
    parameters: Mapping[str, mx.array],
    *, spec: ModelTopologySpecV2, extents: GenerationExtents,
    group_index: int,
) -> AdapterParameters:
    """Borrow only the B01-owned tensors, without a second parameter ledger."""
    if (type(group_index) is not int or not 0 <= group_index < GROUP_COUNT
            or not isinstance(parameters, Mapping)
            or type(spec) is not ModelTopologySpecV2
            or type(extents) is not GenerationExtents):
        _invalid()
    declared = expected_bamf_shapes(spec, extents)
    if set(parameters) != {item.name for item in declared}:
        _invalid()
    for item in declared:
        tensor = parameters[item.name]
        if (not isinstance(tensor, mx.array)
                or tensor.shape != item.shape
                or tensor.dtype != mx.float32):
            _invalid()
    prefix = f"plastic.group.{group_index}."
    return AdapterParameters(
        group_index, *(mx.array(parameters[prefix + name])
                       for name in ADAPTER_NAMES))


def adapter_forward(hidden: mx.array, params: AdapterParameters) -> mx.array:
    """h + (1/8) B SiLU(A RMSNorm(h)), even when B starts at zero."""
    if (type(params) is not AdapterParameters
            or not isinstance(hidden, mx.array)
            or hidden.ndim != 3 or hidden.shape[2] != WIDTH
            or hidden.dtype != mx.float32
            or (host_tensor_validation_enabled()
                and not bool(mx.all(mx.isfinite(hidden))))):
        _invalid()
    params.__post_init__()
    normalized = mx.fast.rms_norm(
        hidden, params.norm, ModelTopologySpecV2.rms_norm_epsilon)
    projected = normalized @ params.A.T
    activated = projected * mx.sigmoid(projected)
    result = hidden + (activated @ params.B.T) / RANK
    if host_tensor_validation_enabled() and not bool(mx.all(mx.isfinite(result))):
        _invalid()
    return result


@dataclass(frozen=True, order=True)
class IdentityRowAge:
    bank_index: int
    row_index: int
    accepted_age: int
    schema_version: str = AGE_SCHEMA

    def __post_init__(self) -> None:
        if (type(self.bank_index) is not int or self.bank_index < 0
                or type(self.row_index) is not int
                or not 0 <= self.row_index < ModelTopologySpecV2.semantic_bank_rows
                or type(self.accepted_age) is not int
                or not 0 <= self.accepted_age <= ESTABLISHED_AGE
                or self.schema_version != AGE_SCHEMA):
            _invalid()

    @property
    def identity(self) -> tuple[int, int]:
        return self.bank_index, self.row_index


def _valid_ages(ages: object) -> bool:
    return (isinstance(ages, tuple)
            and all(type(item) is IdentityRowAge for item in ages)
            and tuple(item.identity for item in ages)
            == tuple(sorted({item.identity for item in ages})))


@dataclass(frozen=True)
class GroupEligibility:
    mode: str
    eligible_parameter_names: tuple[str, ...]
    frozen_parameter_names: tuple[str, ...]
    admitted_identity_rows: tuple[tuple[int, int], ...]
    fast_identity_rows: tuple[tuple[int, int], ...]
    established_identity_rows: tuple[tuple[int, int], ...]
    schema_version: str = ELIGIBILITY_SCHEMA

    def __post_init__(self) -> None:
        names = self.eligible_parameter_names + self.frozen_parameter_names
        admitted = set(self.admitted_identity_rows)
        fast = set(self.fast_identity_rows)
        established = set(self.established_identity_rows)
        if (self.mode not in UPDATE_MODES
                or type(self.eligible_parameter_names) is not tuple
                or type(self.frozen_parameter_names) is not tuple
                or len(names) != len(set(names))
                or any(not isinstance(name, str) or not name for name in names)
                or not _valid_identity_pairs(self.admitted_identity_rows)
                or not _valid_identity_pairs(self.fast_identity_rows)
                or not _valid_identity_pairs(self.established_identity_rows)
                or fast & established
                or fast | established != admitted
                or self.schema_version != ELIGIBILITY_SCHEMA):
            _invalid()


def _valid_identity_pairs(value: object) -> bool:
    return (type(value) is tuple
            and value == tuple(sorted(set(value)))
            and all(type(item) is tuple and len(item) == 2
                    and type(item[0]) is int and item[0] >= 0
                    and type(item[1]) is int
                    and 0 <= item[1] < ModelTopologySpecV2.semantic_bank_rows
                    for item in value))


def group_eligibility(
    mode: str, manifest: ParameterCensus,
    accepted_ages: tuple[IdentityRowAge, ...],
) -> GroupEligibility:
    """Static B01 group membership; participation is checked per step later."""
    if (mode not in UPDATE_MODES or type(manifest) is not ParameterCensus
            or not _valid_ages(accepted_ages)):
        _invalid()
    identity_banks = {
        int(item.name.rsplit(".", 1)[-1])
        for item in manifest.parameters
        if item.group is ParameterGroup.IDENTITY_ROW_AGE
        and item.name.startswith("identity.bank.")
    }
    if any(item.bank_index not in identity_banks for item in accepted_ages):
        _invalid()
    all_names = tuple(item.name for item in manifest.parameters)
    if mode in ("FOUNDATION", "FULL"):
        eligible = all_names
        frozen = ()
    else:
        eligible = tuple(item.name for item in manifest.parameters
                         if item.group is ParameterGroup.FAST)
        frozen = tuple(item.name for item in manifest.parameters
                       if item.group is not ParameterGroup.FAST)
    admitted = tuple(item.identity for item in accepted_ages)
    fast_rows = tuple(item.identity for item in accepted_ages
                      if item.accepted_age < ESTABLISHED_AGE)
    established = tuple(item.identity for item in accepted_ages
                        if item.accepted_age == ESTABLISHED_AGE)
    return GroupEligibility(
        mode, eligible, frozen, admitted, fast_rows, established)


def advance_accepted_row_ages(
    parent: tuple[IdentityRowAge, ...],
    participating_rows: tuple[tuple[int, int], ...],
    *, accepted: bool,
) -> tuple[IdentityRowAge, ...]:
    """One increment per *retained candidate*, not per internal AdamW step.

    The accepted flag must come from the retained-generation owner; this pure
    function neither decides acceptance nor changes the parent's checkpoint.
    """
    if (not _valid_ages(parent) or type(accepted) is not bool
            or not isinstance(participating_rows, tuple)
            or any(not isinstance(item, tuple) or len(item) != 2
                   or any(type(value) is not int for value in item)
                   for item in participating_rows)
            or participating_rows != tuple(sorted(set(participating_rows)))
            or not set(participating_rows).issubset({
                item.identity for item in parent})):
        _invalid()
    if not accepted:
        return parent
    active = set(participating_rows)
    return tuple(
        IdentityRowAge(
            item.bank_index, item.row_index,
            min(ESTABLISHED_AGE, item.accepted_age + int(item.identity in active)))
        for item in parent)
