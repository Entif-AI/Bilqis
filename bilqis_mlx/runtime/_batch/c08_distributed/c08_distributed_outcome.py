"""Portable coordinator outcome for one completed distributed logical step."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Mapping

import mlx.core as mx

from bilqis_mlx.runtime._atlas_resources.distributed_contracts import _sha
from .c08_distributed_evidence import DistributedB11Evidence
from .c08_gradient_accumulation import _invalid


@dataclass(frozen=True)
class DistributedRuntimeAttestation:
    manifest_digest: str
    rank: int
    worker_id: str
    device_family: str
    mlx_version: str
    backend: str
    numeric_precision: str

    def __post_init__(self) -> None:
        if (not _sha(self.manifest_digest)
                or type(self.rank) is not int or self.rank < 0
                or any(not isinstance(value, str) or not value for value in (
                    self.worker_id, self.device_family, self.mlx_version,
                    self.backend, self.numeric_precision))):
            _invalid("C08_DISTRIBUTED_RUNTIME_ATTESTATION_INVALID")


def all_gather_runtime_attestation(
        local: DistributedRuntimeAttestation, group,
) -> tuple[DistributedRuntimeAttestation, ...]:
    local.__post_init__()
    payload = json.dumps(asdict(local), sort_keys=True, separators=(",", ":")).encode()
    lengths = mx.distributed.all_gather(
        mx.array([len(payload)], dtype=mx.int32), group=group)
    mx.eval(lengths)
    sizes = tuple(int(value) for value in lengths.tolist())
    width = max(sizes)
    padded = payload + b"\0" * (width - len(payload))
    gathered = mx.distributed.all_gather(
        mx.array(list(padded), dtype=mx.uint8), group=group)
    mx.eval(gathered)
    raw = bytes(gathered.tolist())
    result = []
    for rank, size in enumerate(sizes):
        try:
            item = DistributedRuntimeAttestation(
                **json.loads(raw[rank * width:rank * width + size].decode()))
        except (json.JSONDecodeError, TypeError, ValueError):
            _invalid("C08_DISTRIBUTED_RUNTIME_ATTESTATION_INVALID")
        item.__post_init__()
        result.append(item)
    return tuple(result)


@dataclass(frozen=True)
class DistributedStepOutcome:
    manifest_digest: str
    evidence: tuple[DistributedB11Evidence, ...]
    runtime_attestations: tuple[DistributedRuntimeAttestation, ...]
    gradients: Mapping
    weighted_mean_loss: mx.array
    compute_seconds_per_worker: tuple[float, ...]
    communication_seconds: float
    peak_memory_per_worker: tuple[int, ...]

    def __post_init__(self) -> None:
        ranks = tuple(item.rank for item in self.evidence)
        if (not _sha(self.manifest_digest)
                or type(self.evidence) is not tuple or not self.evidence
                or any(type(item) is not DistributedB11Evidence
                       for item in self.evidence)
                or type(self.runtime_attestations) is not tuple
                or not self.runtime_attestations
                or any(type(item) is not DistributedRuntimeAttestation
                       for item in self.runtime_attestations)
                or not isinstance(self.gradients, Mapping) or not self.gradients
                or any(not isinstance(value, mx.array) or value.dtype != mx.float32
                       for value in self.gradients.values())
                or not isinstance(self.weighted_mean_loss, mx.array)
                or self.weighted_mean_loss.dtype != mx.float32
                or self.weighted_mean_loss.size != 1
                or type(self.compute_seconds_per_worker) is not tuple
                or not self.compute_seconds_per_worker
                or any(type(value) is not float or value < 0.0
                       for value in self.compute_seconds_per_worker)
                or type(self.communication_seconds) is not float
                or self.communication_seconds < 0.0
                or type(self.peak_memory_per_worker) is not tuple
                or len(self.peak_memory_per_worker)
                   != len(self.compute_seconds_per_worker)
                or any(type(value) is not int or value < 0
                       for value in self.peak_memory_per_worker)
                or any(item.manifest_digest != self.manifest_digest
                       for item in self.evidence)
                or any(item.manifest_digest != self.manifest_digest
                       for item in self.runtime_attestations)
                or any(rank < 0 for rank in ranks)):
            _invalid("C08_DISTRIBUTED_OUTCOME_INVALID")


__all__ = (
    "DistributedRuntimeAttestation", "DistributedStepOutcome",
    "all_gather_runtime_attestation",
)
