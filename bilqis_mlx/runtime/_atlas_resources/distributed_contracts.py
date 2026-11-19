"""C08.4 immutable execution-topology and rank-result contracts."""
from __future__ import annotations

from dataclasses import dataclass
import re

from .contracts import _digest, _invalid


DISTRIBUTED_STEP_MANIFEST_SCHEMA = "bilqis.c08.distributed-step-manifest/v1"
DISTRIBUTED_RANK_SCHEMA = "bilqis.c08.distributed-rank/v1"
DISTRIBUTED_PARTITION_SCHEMA = "bilqis.c08.distributed-partition/v1"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
DISTRIBUTED_BACKENDS = frozenset(("ring", "jaccl", "mpi", "nccl"))
_PRECISIONS = frozenset(("fp32",))
_REDUCTIONS = frozenset(("fp32_weighted_mean",))


def _sha(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value))


@dataclass(frozen=True)
class DistributedRank:
    rank: int
    worker_id: str
    device_family: str
    schema_version: str = DISTRIBUTED_RANK_SCHEMA

    def __post_init__(self) -> None:
        if (type(self.rank) is not int or self.rank < 0
                or not isinstance(self.worker_id, str) or not self.worker_id
                or not isinstance(self.device_family, str) or not self.device_family
                or self.schema_version != DISTRIBUTED_RANK_SCHEMA):
            _invalid("BAMF_C08_DISTRIBUTED_RANK_INVALID")


@dataclass(frozen=True)
class DistributedExecutionProfile:
    partition_seed: int
    workers: tuple[DistributedRank, ...]
    mlx_version: str
    backend: str
    numeric_precision: str = "fp32"
    reduction_policy: str = "fp32_weighted_mean"

    def __post_init__(self) -> None:
        if (type(self.partition_seed) is not int or self.partition_seed < 0
                or type(self.workers) is not tuple or not self.workers
                or any(type(worker) is not DistributedRank for worker in self.workers)
                or tuple(worker.rank for worker in self.workers)
                   != tuple(range(len(self.workers)))
                or not isinstance(self.mlx_version, str) or not self.mlx_version
                or self.backend not in DISTRIBUTED_BACKENDS
                or self.numeric_precision not in _PRECISIONS
                or self.reduction_policy not in _REDUCTIONS):
            _invalid("BAMF_C08_DISTRIBUTED_PROFILE_INVALID")


@dataclass(frozen=True)
class DistributedStepManifest:
    retained_generation: int
    retained_manifest_sha256: str
    curriculum_release: str
    source_release: str
    logical_batch_digest: str
    partition_seed: int
    world_size: int
    workers: tuple[DistributedRank, ...]
    mlx_version: str
    backend: str
    numeric_precision: str
    reduction_policy: str = "fp32_weighted_mean"
    schema_version: str = DISTRIBUTED_STEP_MANIFEST_SCHEMA

    def __post_init__(self) -> None:
        if (type(self.retained_generation) is not int
                or self.retained_generation < 0
                or not _sha(self.retained_manifest_sha256)
                or not isinstance(self.curriculum_release, str)
                or not self.curriculum_release
                or not isinstance(self.source_release, str)
                or not self.source_release
                or not _sha(self.logical_batch_digest)
                or type(self.partition_seed) is not int
                or self.partition_seed < 0
                or type(self.world_size) is not int
                or self.world_size < 1
                or type(self.workers) is not tuple
                or len(self.workers) != self.world_size
                or any(type(worker) is not DistributedRank for worker in self.workers)
                or tuple(worker.rank for worker in self.workers)
                   != tuple(range(self.world_size))
                or len({worker.worker_id for worker in self.workers})
                   != self.world_size
                or not isinstance(self.mlx_version, str)
                or not self.mlx_version
                or self.backend not in DISTRIBUTED_BACKENDS
                or self.numeric_precision not in _PRECISIONS
                or self.reduction_policy not in _REDUCTIONS
                or self.schema_version != DISTRIBUTED_STEP_MANIFEST_SCHEMA):
            _invalid("BAMF_C08_DISTRIBUTED_MANIFEST_INVALID")

    @property
    def digest(self) -> str:
        return _digest({
            "retained_generation": self.retained_generation,
            "retained_manifest_sha256": self.retained_manifest_sha256,
            "curriculum_release": self.curriculum_release,
            "source_release": self.source_release,
            "logical_batch_digest": self.logical_batch_digest,
            "partition_seed": self.partition_seed,
            "world_size": self.world_size,
            "workers": tuple(
                (w.rank, w.worker_id, w.device_family) for w in self.workers),
            "mlx_version": self.mlx_version,
            "backend": self.backend,
            "numeric_precision": self.numeric_precision,
            "reduction_policy": self.reduction_policy,
            "schema_version": self.schema_version,
        })


@dataclass(frozen=True)
class DistributedPartition:
    manifest_digest: str
    rank: int
    row_indices: tuple[int, ...]
    row_ids: tuple[str, ...]
    schema_version: str = DISTRIBUTED_PARTITION_SCHEMA

    def __post_init__(self) -> None:
        if (not _sha(self.manifest_digest)
                or type(self.rank) is not int or self.rank < 0
                or type(self.row_indices) is not tuple or not self.row_indices
                or any(type(index) is not int or index < 0
                       for index in self.row_indices)
                or len(set(self.row_indices)) != len(self.row_indices)
                or type(self.row_ids) is not tuple
                or len(self.row_ids) != len(self.row_indices)
                or any(not isinstance(row_id, str) or not row_id
                       for row_id in self.row_ids)
                or self.schema_version != DISTRIBUTED_PARTITION_SCHEMA):
            _invalid("BAMF_C08_DISTRIBUTED_PARTITION_INVALID")


__all__ = (
    "DISTRIBUTED_BACKENDS",
    "DistributedExecutionProfile", "DistributedPartition", "DistributedRank",
    "DistributedStepManifest",
)
