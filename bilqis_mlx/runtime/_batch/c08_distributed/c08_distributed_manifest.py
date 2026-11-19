"""Owner derivation of one C08.4 execution manifest from authoritative state."""
from __future__ import annotations

from bilqis_mlx.runtime.atlas_resources import (
    BatchPlan, DistributedExecutionProfile, DistributedStepManifest,
)
from bilqis_mlx.runtime.atlas_training_contracts import BamfTrainingBatch

from .c08_gradient_accumulation import _invalid


def issue_distributed_step_manifest(
        parent, training_batch: BamfTrainingBatch, plan: BatchPlan,
        profile: DistributedExecutionProfile) -> DistributedStepManifest:
    """Bind topology intent to exact retained, source, and curriculum authority."""
    custody = getattr(getattr(parent, "retained_state", parent), "custody", None)
    if custody is None:
        custody = getattr(parent, "custody", None)
    if (type(training_batch) is not BamfTrainingBatch
            or type(plan) is not BatchPlan
            or type(profile) is not DistributedExecutionProfile
            or custody is None):
        _invalid("C08_DISTRIBUTED_MANIFEST_AUTHORITY_REQUIRED")
    training_batch.__post_init__()
    plan.__post_init__()
    profile.__post_init__()
    if (training_batch.generation_binding != plan.generation_binding
            or tuple(row.provenance.row_id for row in training_batch.rows)
               != plan.logical_row_ids):
        _invalid("C08_DISTRIBUTED_MANIFEST_BATCH_DRIFT")
    return DistributedStepManifest(
        retained_generation=custody.generation,
        retained_manifest_sha256=custody.manifest_sha256,
        curriculum_release=training_batch.release_sha256,
        source_release=plan.source_digest,
        logical_batch_digest=plan.digest,
        partition_seed=profile.partition_seed,
        world_size=len(profile.workers), workers=profile.workers,
        mlx_version=profile.mlx_version, backend=profile.backend,
        numeric_precision=profile.numeric_precision,
        reduction_policy=profile.reduction_policy)


__all__ = ("issue_distributed_step_manifest",)
