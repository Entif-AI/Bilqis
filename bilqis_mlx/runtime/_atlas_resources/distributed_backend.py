"""MLX distributed backend capability inspection without group initialization."""
from __future__ import annotations

from dataclasses import dataclass

from .contracts import _invalid
from .distributed_contracts import (
    DISTRIBUTED_BACKENDS, DistributedPartition, DistributedStepManifest,
)


BACKENDS = tuple(sorted(DISTRIBUTED_BACKENDS))


def _mlx_core():
    """Return MLX when present without making the portable facade MLX-dependent."""
    try:
        import mlx.core as mx
    except ModuleNotFoundError as exc:
        if exc.name != "mlx" and not str(exc.name).startswith("mlx."):
            raise
        return None
    return mx


@dataclass(frozen=True)
class DistributedBackendCapability:
    backend: str
    available: bool

    def __post_init__(self) -> None:
        if self.backend not in BACKENDS or type(self.available) is not bool:
            _invalid("BAMF_C08_DISTRIBUTED_BACKEND_CAPABILITY_INVALID")


def core_backend_name(backend: str) -> str:
    """Normalize launcher aliases without initializing a distributed group."""
    if not isinstance(backend, str) or not backend:
        _invalid("BAMF_C08_DISTRIBUTED_BACKEND_INVALID")
    normalized = "jaccl" if backend == "jaccl-ring" else backend
    if normalized not in BACKENDS:
        _invalid("BAMF_C08_DISTRIBUTED_BACKEND_INVALID")
    return normalized


def inspect_distributed_backends() -> tuple[DistributedBackendCapability, ...]:
    """Return host capabilities using MLX's side-effect-free availability API."""
    mx = _mlx_core()
    return tuple(
        DistributedBackendCapability(
            backend,
            bool(mx is not None and mx.distributed.is_available(backend)),
        )
        for backend in BACKENDS
    )


def require_distributed_backend(backend: str) -> str:
    normalized = core_backend_name(backend)
    mx = _mlx_core()
    if mx is None or not bool(mx.distributed.is_available(normalized)):
        _invalid("BAMF_C08_DISTRIBUTED_BACKEND_UNAVAILABLE")
    return normalized


def validate_distributed_resume(
    manifest: DistributedStepManifest,
    *,
    world_size: int,
    backend: str,
    device_families: tuple[str, ...],
    mlx_version: str,
) -> None:
    """Validate execution topology on cold resume without changing model identity."""
    if type(manifest) is not DistributedStepManifest:
        _invalid("BAMF_C08_DISTRIBUTED_RESUME_MANIFEST_REQUIRED")
    manifest.__post_init__()
    normalized = core_backend_name(backend)
    expected_devices = tuple(worker.device_family for worker in manifest.workers)
    if (world_size != manifest.world_size
            or normalized != manifest.backend
            or device_families != expected_devices
            or mlx_version != manifest.mlx_version):
        _invalid("BAMF_C08_DISTRIBUTED_RESUME_TOPOLOGY_DRIFT")


def validate_runtime_rank(
        manifest: DistributedStepManifest, partition: DistributedPartition,
        group, *, backend: str, device_family: str, mlx_version: str,
        numeric_precision: str = "fp32") -> None:
    """Bind declared rank metadata to the initialized MLX process before compute."""
    if (type(manifest) is not DistributedStepManifest
            or type(partition) is not DistributedPartition
            or group is None or not isinstance(device_family, str)
            or not device_family or not isinstance(mlx_version, str)
            or not mlx_version):
        _invalid("BAMF_C08_DISTRIBUTED_RUNTIME_RANK_INVALID")
    rank = group.rank()
    if (group.size() != manifest.world_size
            or rank != partition.rank
            or manifest.workers[rank].device_family != device_family
            or core_backend_name(backend) != manifest.backend
            or mlx_version != manifest.mlx_version
            or numeric_precision != manifest.numeric_precision):
        _invalid("BAMF_C08_DISTRIBUTED_RUNTIME_RANK_DRIFT")


__all__ = (
    "BACKENDS", "DistributedBackendCapability", "core_backend_name",
    "inspect_distributed_backends", "require_distributed_backend",
    "validate_distributed_resume", "validate_runtime_rank",
)
