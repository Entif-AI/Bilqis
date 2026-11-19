"""C08.4 scaling observations and topology comparison records."""
from __future__ import annotations

from dataclasses import dataclass
import math

from .contracts import _invalid
from .distributed_contracts import _sha


_TOPOLOGIES = frozenset((
    "single_fastest", "synchronous_pair", "trainer_auxiliary",
))


def _finite_nonnegative(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _finite(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


@dataclass(frozen=True)
class DistributedStepTelemetry:
    manifest_digest: str
    logical_examples: int
    logical_positions: int
    compute_seconds_per_worker: tuple[float, ...]
    communication_seconds: float
    wall_seconds: float
    attempted_steps: int
    peak_memory_per_worker: tuple[int, ...]
    world_size: int
    single_worker_reference_seconds: float | None = None
    schema_version: str = "bilqis.c08.distributed-step-telemetry/v1"

    def __post_init__(self) -> None:
        if (not _sha(self.manifest_digest)
                or type(self.logical_examples) is not int
                or self.logical_examples < 1
                or type(self.logical_positions) is not int
                or self.logical_positions < 0
                or type(self.compute_seconds_per_worker) is not tuple
                or len(self.compute_seconds_per_worker) != self.world_size
                or any(not _finite_nonnegative(value)
                       for value in self.compute_seconds_per_worker)
                or not _finite_nonnegative(self.communication_seconds)
                or not _finite_nonnegative(self.wall_seconds)
                or self.wall_seconds <= 0
                or type(self.attempted_steps) is not int
                or self.attempted_steps < 1
                or type(self.peak_memory_per_worker) is not tuple
                or len(self.peak_memory_per_worker) != self.world_size
                or any(type(value) is not int or value < 0
                       for value in self.peak_memory_per_worker)
                or type(self.world_size) is not int or self.world_size < 1
                or (self.single_worker_reference_seconds is not None
                    and (not _finite_nonnegative(self.single_worker_reference_seconds)
                         or self.single_worker_reference_seconds <= 0))
                or self.schema_version
                   != "bilqis.c08.distributed-step-telemetry/v1"):
            _invalid("BAMF_C08_DISTRIBUTED_TELEMETRY_INVALID")

    @property
    def examples_per_second(self) -> float:
        return self.logical_examples / self.wall_seconds

    @property
    def positions_per_second(self) -> float:
        return self.logical_positions / self.wall_seconds

    @property
    def attempted_steps_per_hour(self) -> float:
        return self.attempted_steps * 3600.0 / self.wall_seconds

    @property
    def scaling_efficiency(self) -> float | None:
        if self.single_worker_reference_seconds is None:
            return None
        speedup = self.single_worker_reference_seconds / self.wall_seconds
        return speedup / self.world_size


@dataclass(frozen=True)
class TopologyObservation:
    topology: str
    retained_capability_gain: float
    wall_seconds: float
    source_contract_digest: str
    evaluation_contract_digest: str
    worker_generations: tuple[str, ...]
    memory_bandwidth_gbps: tuple[float, ...]
    compute_throughput: tuple[float, ...]
    interconnect_gbps: tuple[float, ...]

    def __post_init__(self) -> None:
        if (self.topology not in _TOPOLOGIES
                or not _finite(self.retained_capability_gain)
                or not _finite_nonnegative(self.wall_seconds)
                or self.wall_seconds <= 0
                or not _sha(self.source_contract_digest)
                or not _sha(self.evaluation_contract_digest)
                or type(self.worker_generations) is not tuple
                or not self.worker_generations
                or any(not isinstance(value, str) or not value
                       for value in self.worker_generations)
                or any(type(values) is not tuple
                       or len(values) != len(self.worker_generations)
                       or any(not _finite_nonnegative(value) for value in values)
                       for values in (self.memory_bandwidth_gbps,
                                      self.compute_throughput,
                                      self.interconnect_gbps))):
            _invalid("BAMF_C08_TOPOLOGY_OBSERVATION_INVALID")

    @property
    def retained_capability_gain_per_hour(self) -> float:
        return self.retained_capability_gain * 3600.0 / self.wall_seconds


@dataclass(frozen=True)
class TopologyUnavailable:
    topology: str
    reason: str

    def __post_init__(self) -> None:
        if (self.topology != "synchronous_pair"
                or not isinstance(self.reason, str) or not self.reason.strip()):
            _invalid("BAMF_C08_TOPOLOGY_UNAVAILABLE_INVALID")


def best_topology(
    observations: tuple[TopologyObservation, ...],
    unavailable: tuple[TopologyUnavailable, ...] = (),
) -> TopologyObservation:
    """Compare only observations under the exact same source/evaluation contract."""
    if (type(observations) is not tuple
            or any(type(item) is not TopologyObservation for item in observations)
            or type(unavailable) is not tuple
            or any(type(item) is not TopologyUnavailable for item in unavailable)):
        _invalid("BAMF_C08_TOPOLOGY_COMPARISON_INVALID")
    measured = {item.topology for item in observations}
    unavailable_names = {item.topology for item in unavailable}
    if (len(measured) != len(observations)
            or len(unavailable_names) != len(unavailable)
            or measured & unavailable_names
            or not {"single_fastest", "trainer_auxiliary"} <= measured
            or measured | unavailable_names != _TOPOLOGIES):
        _invalid("BAMF_C08_TOPOLOGY_COVERAGE_INCOMPLETE")
    source = {item.source_contract_digest for item in observations}
    evaluation = {item.evaluation_contract_digest for item in observations}
    if len(source) != 1 or len(evaluation) != 1:
        _invalid("BAMF_C08_TOPOLOGY_CONTRACT_DRIFT")
    return max(
        observations,
        key=lambda item: item.retained_capability_gain_per_hour,
    )


__all__ = (
    "DistributedStepTelemetry", "TopologyObservation", "TopologyUnavailable",
    "best_topology",
)
