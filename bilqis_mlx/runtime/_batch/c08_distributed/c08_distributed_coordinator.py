"""Coordinator reconstruction of one portable distributed C08 outcome."""
from __future__ import annotations

from bilqis_mlx.runtime.atlas_resources import (
    BatchPlan, DistributedStepManifest, partition_logical_batch,
)

from .c08_distributed_outcome import DistributedStepOutcome
from .c08_gradient_accumulation import (
    DistributedLogicalBatchMetadata, LogicalBatchGradientExecution,
    _invalid, _logical_batch_result,
)


def logical_batch_from_distributed_outcome(
        plan: BatchPlan, manifest: DistributedStepManifest,
        outcome: DistributedStepOutcome) -> LogicalBatchGradientExecution:
    """Validate portable rank evidence and issue the canonical C08 logical result."""
    if type(outcome) is not DistributedStepOutcome:
        _invalid("C08_DISTRIBUTED_OUTCOME_REQUIRED")
    outcome.__post_init__()
    partitions = partition_logical_batch(plan, manifest)
    if (outcome.manifest_digest != manifest.digest
            or len(outcome.compute_seconds_per_worker) != manifest.world_size):
        _invalid("C08_DISTRIBUTED_OUTCOME_MANIFEST_DRIFT")
    attestations = {item.rank: item for item in outcome.runtime_attestations}
    if (len(attestations) != manifest.world_size
            or set(attestations) != set(range(manifest.world_size))):
        _invalid("C08_DISTRIBUTED_RUNTIME_ATTESTATION_COVERAGE_DRIFT")
    for worker in manifest.workers:
        attestation = attestations[worker.rank]
        if (attestation.worker_id != worker.worker_id
                or attestation.device_family != worker.device_family
                or attestation.mlx_version != manifest.mlx_version
                or attestation.backend != manifest.backend
                or attestation.numeric_precision != manifest.numeric_precision):
            _invalid("C08_DISTRIBUTED_RUNTIME_ATTESTATION_DRIFT")
    by_row = {}
    rows_by_rank = {partition.rank: partition.row_indices for partition in partitions}
    for item in outcome.evidence:
        if (item.rank not in rows_by_rank
                or item.row_index not in rows_by_rank[item.rank]
                or item.row_id != plan.logical_row_ids[item.row_index]
                or item.row_index in by_row):
            _invalid("C08_DISTRIBUTED_OUTCOME_COVERAGE_DRIFT")
        by_row[item.row_index] = item
    if set(by_row) != set(range(len(plan.logical_row_ids))):
        _invalid("C08_DISTRIBUTED_OUTCOME_COVERAGE_DRIFT")
    result = _logical_batch_result(
        plan, outcome.gradients, outcome.weighted_mean_loss,
        [by_row[index] for index in range(len(plan.logical_row_ids))],
        len(plan.logical_row_ids), 0, len(plan.logical_row_ids),
        max(outcome.compute_seconds_per_worker) + outcome.communication_seconds,
        {"b11_preflight_wall_seconds": 0.0,
         "b11_autodiff_wall_seconds": 0.0,
         "b11_provider_draw_count": 0,
         "b11_atlas_reload_count": 0})
    object.__setattr__(result, "distributed_metadata", DistributedLogicalBatchMetadata(
        manifest=manifest,
        compute_seconds_per_worker=outcome.compute_seconds_per_worker,
        communication_seconds=outcome.communication_seconds,
        peak_memory_per_worker=outcome.peak_memory_per_worker))
    result.__post_init__()
    return result


__all__ = ("logical_batch_from_distributed_outcome",)
