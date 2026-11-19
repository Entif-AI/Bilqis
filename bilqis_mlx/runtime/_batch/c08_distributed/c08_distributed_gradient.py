"""C08.4 owner for executor-only rank gradients and one logical reduction."""
from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Callable, Mapping

import mlx.core as mx

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.runtime.atlas_model import BamfGradientExecution
from bilqis_mlx.runtime.atlas_resources import (
    BatchPlan, DistributedPartition, DistributedStepManifest,
    partition_logical_batch,
)

from .c08_gradient_accumulation import (
    DistributedLogicalBatchMetadata, LogicalBatchGradientExecution,
    _add_b11_observation, _invalid,
    _logical_batch_result, _scale_tree, _sum_tree,
)
from .c08_distributed_evidence import issue_distributed_b11_evidence


_RANK_ISSUER = object()


@dataclass(frozen=True, init=False)
class DistributedRankGradientExecution:
    """Owner-issued rank-local FP32 mean gradient; never optimizer authority."""
    manifest_digest: str
    rank: int
    row_indices: tuple[int, ...]
    evidence: tuple
    gradients: Mapping
    mean_loss: mx.array
    gradient_launches: int
    compute_seconds: float
    peak_memory_bytes: int
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("C08_DISTRIBUTED_RANK_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self) -> None:
        if (getattr(self, "_issuance", None) is not _RANK_ISSUER
                or not isinstance(self.manifest_digest, str)
                or len(self.manifest_digest) != SHA256_HEX_LENGTH
                or type(self.rank) is not int or self.rank < 0
                or type(self.row_indices) is not tuple or not self.row_indices
                or len(self.row_indices) != len(self.evidence)
                or not isinstance(self.gradients, Mapping) or not self.gradients
                or any(not isinstance(value, mx.array)
                       or value.dtype != mx.float32
                       for value in self.gradients.values())
                or not isinstance(self.mean_loss, mx.array)
                or self.mean_loss.dtype != mx.float32
                or self.mean_loss.size != 1
                or type(self.gradient_launches) is not int
                or self.gradient_launches != len(self.row_indices)
                or type(self.compute_seconds) is not float
                or self.compute_seconds < 0.0
                or type(self.peak_memory_bytes) is not int
                or self.peak_memory_bytes < 0):
            _invalid("C08_DISTRIBUTED_RANK_GRADIENT_INVALID")


def _fp32_tree(gradients: Mapping) -> dict:
    return {name: value.astype(mx.float32) for name, value in gradients.items()}


def execute_distributed_rank(
    plan: BatchPlan,
    manifest: DistributedStepManifest,
    partition: DistributedPartition,
    execute_row: Callable[[int], BamfGradientExecution],
    base_authority_for_row: Callable[[int], object] | None = None,
) -> DistributedRankGradientExecution:
    """Execute exactly one rank's assigned rows with existing B11 row kernels."""
    if not callable(execute_row):
        _invalid("C08_DISTRIBUTED_RANK_EXECUTOR_INVALID")
    partitions = partition_logical_batch(plan, manifest)
    if (type(partition) is not DistributedPartition
            or partition.rank >= len(partitions)
            or partition != partitions[partition.rank]):
        _invalid("C08_DISTRIBUTED_RANK_PARTITION_DRIFT")
    started = time.perf_counter()
    total = None
    loss = mx.array(0.0, dtype=mx.float32)
    evidence = []
    baseline_active = int(mx.get_active_memory())
    mx.reset_peak_memory()
    for index in partition.row_indices:
        execution = execute_row(index)
        if type(execution) is not BamfGradientExecution:
            _invalid("C08_DISTRIBUTED_B11_EXECUTION_REQUIRED")
        execution.__post_init__()
        if execution.execution.output.generation_binding != plan.generation_binding:
            _invalid("C08_DISTRIBUTED_GENERATION_DRIFT")
        total = _sum_tree(total, _fp32_tree(execution.gradients))
        loss = loss + execution.loss_total.astype(mx.float32)
        evidence_kwargs = {
            "manifest_digest": manifest.digest,
            "rank": partition.rank,
            "row_index": index,
            "row_id": plan.logical_row_ids[index],
        }
        if base_authority_for_row is not None:
            evidence_kwargs["base_training_authority"] = base_authority_for_row(index)
        evidence.append(issue_distributed_b11_evidence(
            execution.execution, **evidence_kwargs))
    gradients = _scale_tree(total, 1.0 / len(partition.row_indices))
    loss = loss / len(partition.row_indices)
    mx.eval(gradients, loss)
    result = object.__new__(DistributedRankGradientExecution)
    for name, value in (
        ("manifest_digest", manifest.digest),
        ("rank", partition.rank),
        ("row_indices", partition.row_indices),
        ("evidence", tuple(evidence)),
        ("gradients", gradients),
        ("mean_loss", loss),
        ("gradient_launches", len(partition.row_indices)),
        ("compute_seconds", float(time.perf_counter() - started)),
        ("peak_memory_bytes", max(
            baseline_active, int(mx.get_active_memory()), int(mx.get_peak_memory()))),
        ("_issuance", _RANK_ISSUER),
    ):
        object.__setattr__(result, name, value)
    result.__post_init__()
    return result


def reduce_distributed_rank_gradients(
    plan: BatchPlan,
    manifest: DistributedStepManifest,
    rank_results: tuple[DistributedRankGradientExecution, ...],
    *,
    communication_seconds: float = 0.0,
    collective_gradients=None,
    collective_loss=None,
) -> LogicalBatchGradientExecution:
    """Fail closed on rank drift, then issue the existing one-step C08 aggregate."""
    partitions = partition_logical_batch(plan, manifest)
    if (type(rank_results) is not tuple
            or len(rank_results) != manifest.world_size
            or any(type(item) is not DistributedRankGradientExecution
                   for item in rank_results)
            or type(communication_seconds) is not float
            or communication_seconds < 0.0):
        _invalid("C08_DISTRIBUTED_RESULT_SET_INCOMPLETE")
    by_rank = {}
    for result in rank_results:
        result.__post_init__()
        if result.rank in by_rank:
            _invalid("C08_DISTRIBUTED_DUPLICATE_RANK_RESULT")
        by_rank[result.rank] = result
    if set(by_rank) != set(range(manifest.world_size)):
        _invalid("C08_DISTRIBUTED_LOST_RANK_RESULT")
    aggregate = None
    weighted_loss = mx.array(0.0, dtype=mx.float32)
    evidence_by_row = {}
    b11_observation = {
        "b11_preflight_wall_seconds": 0.0,
        "b11_autodiff_wall_seconds": 0.0,
        "b11_provider_draw_count": 0,
        "b11_atlas_reload_count": 0,
    }
    total_rows = len(plan.logical_row_ids)
    for partition in partitions:
        result = by_rank[partition.rank]
        if (result.manifest_digest != manifest.digest
                or result.row_indices != partition.row_indices):
            _invalid("C08_DISTRIBUTED_STALE_OR_WRONG_PARTITION_RESULT")
        weight = len(partition.row_indices) / total_rows
        aggregate = _sum_tree(
            aggregate, _scale_tree(result.gradients, weight))
        weighted_loss = weighted_loss + result.mean_loss * weight
        for index, evidence in zip(
                result.row_indices, result.evidence, strict=True):
            if index in evidence_by_row:
                _invalid("C08_DISTRIBUTED_DUPLICATE_ROW_RESULT")
            if (evidence.row_index != index
                    or evidence.row_id != plan.logical_row_ids[index]
                    or evidence.manifest_digest != manifest.digest):
                _invalid("C08_DISTRIBUTED_EVIDENCE_ROW_DRIFT")
            evidence_by_row[index] = evidence
    if set(evidence_by_row) != set(range(total_rows)):
        _invalid("C08_DISTRIBUTED_ROW_COVERAGE_DRIFT")
    mx.eval(aggregate, weighted_loss)
    if (collective_gradients is None) != (collective_loss is None):
        _invalid("C08_DISTRIBUTED_COLLECTIVE_RESULT_INCOMPLETE")
    if collective_gradients is not None:
        from .c08_distributed_collective import (
            require_collective_matches_reference,
        )
        require_collective_matches_reference(
            aggregate, weighted_loss, collective_gradients, collective_loss)
        aggregate = collective_gradients
        weighted_loss = collective_loss
    result = _logical_batch_result(
        plan, aggregate, weighted_loss,
        [evidence_by_row[index] for index in range(total_rows)],
        sum(item.gradient_launches for item in rank_results),
        0, total_rows,
        max(item.compute_seconds for item in rank_results) + communication_seconds,
        b11_observation,
    )
    object.__setattr__(result, "distributed_metadata", DistributedLogicalBatchMetadata(
        manifest=manifest,
        compute_seconds_per_worker=tuple(
            by_rank[rank].compute_seconds for rank in range(manifest.world_size)),
        communication_seconds=communication_seconds,
        peak_memory_per_worker=tuple(
            by_rank[rank].peak_memory_bytes for rank in range(manifest.world_size))))
    result.__post_init__()
    return result


__all__ = (
    "DistributedRankGradientExecution", "execute_distributed_rank",
    "reduce_distributed_rank_gradients",
)
