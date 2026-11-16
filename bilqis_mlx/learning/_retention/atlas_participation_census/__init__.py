"""Validate B09 group classification against the B01 topology ledger.

This checks structure only; execution participation and row ages still require
an accepted upstream owner before masks can authorize production updates.
"""
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, ParameterGroup, expected_bamf_shapes,
)


def validate_group_census(eligibility, spec, extents):
    from bilqis_mlx.learning.atlas_plasticity import GroupEligibility

    if (type(eligibility) is not GroupEligibility
            or type(spec) is not ModelTopologySpecV2
            or type(extents) is not GenerationExtents):
        ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)
    eligibility.__post_init__()
    declared = expected_bamf_shapes(spec, extents)
    if eligibility.mode == "FAST":
        eligible = {item.name for item in declared if item.group is ParameterGroup.FAST}
    else:
        eligible = {item.name for item in declared}
    frozen = {item.name for item in declared} - eligible
    if (set(eligibility.eligible_parameter_names) != eligible
            or set(eligibility.frozen_parameter_names) != frozen
            or any(bank >= extents.semantic_bank_count
                   for bank, _ in eligibility.admitted_identity_rows)):
        ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)
