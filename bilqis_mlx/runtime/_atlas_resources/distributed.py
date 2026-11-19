"""C08.4 deterministic logical-batch rank partitioning."""
from __future__ import annotations

import hashlib

from .contracts import BatchPlan, _invalid
from .distributed_contracts import (
    DistributedPartition, DistributedStepManifest,
)


def partition_logical_batch(
    plan: BatchPlan, manifest: DistributedStepManifest,
) -> tuple[DistributedPartition, ...]:
    """Partition exact logical rows deterministically with balanced rank load."""
    if type(plan) is not BatchPlan or type(manifest) is not DistributedStepManifest:
        _invalid("BAMF_C08_DISTRIBUTED_PARTITION_ARGUMENT_INVALID")
    plan.__post_init__()
    manifest.__post_init__()
    if manifest.logical_batch_digest != plan.digest:
        _invalid("BAMF_C08_DISTRIBUTED_MANIFEST_BATCH_DRIFT")
    if manifest.world_size > len(plan.logical_row_ids):
        _invalid("BAMF_C08_DISTRIBUTED_WORLD_EXCEEDS_ROWS")
    ordered = sorted(
        range(len(plan.logical_row_ids)),
        key=lambda index: hashlib.sha256(
            f"{manifest.partition_seed}:{index}:{plan.logical_row_ids[index]}".encode()
        ).digest(),
    )
    by_rank = [[] for _ in range(manifest.world_size)]
    for offset, index in enumerate(ordered):
        by_rank[offset % manifest.world_size].append(index)
    return tuple(
        DistributedPartition(
            manifest_digest=manifest.digest,
            rank=rank,
            row_indices=tuple(sorted(indices)),
            row_ids=tuple(plan.logical_row_ids[index] for index in sorted(indices)),
        )
        for rank, indices in enumerate(by_rank)
    )

__all__ = ("partition_logical_batch",)
