"""Semantic, runtime, memory, teacher, generation, and resource read models."""
from __future__ import annotations

from dataclasses import dataclass

from .model import (
    DataValue, RecordMeta, WireRecord, is_name, is_sha256, is_wire_integer, require,
)


@dataclass(frozen=True)
class SemanticAtlasSnapshot(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.semantic-atlas-snapshot/v1"
    meta: RecordMeta
    atlas_bundle_id: str
    atlas_release_sha256: str
    source_bundle_id: str
    active_concepts: DataValue
    source_eligible: DataValue
    source_held: DataValue

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_sha256(self.atlas_bundle_id)
                and is_sha256(self.source_bundle_id), "ATLAS_ID")
        require(is_sha256(self.atlas_release_sha256), "ATLAS_RELEASE")
        require(all(type(item) is DataValue for item in (
            self.active_concepts, self.source_eligible, self.source_held)), "ATLAS_VALUES")


@dataclass(frozen=True)
class NeuralRuntimeSample(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.neural-runtime-sample/v1"
    meta: RecordMeta
    optimizer_step: int
    step_duration_ms: DataValue
    active_parameters: DataValue
    refinement_fraction: DataValue

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_wire_integer(self.optimizer_step) and self.optimizer_step >= 0,
                "RUNTIME_STEP")
        require(all(type(item) is DataValue for item in (
            self.step_duration_ms, self.active_parameters,
            self.refinement_fraction)), "RUNTIME_VALUES")


@dataclass(frozen=True)
class MemorySnapshot(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.memory-snapshot/v1"
    meta: RecordMeta
    used_bytes: DataValue
    budget_bytes: DataValue
    hits: DataValue
    misses: DataValue
    requalifications: DataValue

    def __post_init__(self) -> None:
        super().__post_init__()
        require(all(type(item) is DataValue for item in (
            self.used_bytes, self.budget_bytes, self.hits,
            self.misses, self.requalifications)), "MEMORY_VALUES")


@dataclass(frozen=True)
class TeacherSnapshot(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.teacher-snapshot/v1"
    meta: RecordMeta
    teacher_identity: str
    teacher_epoch: int
    strategy_id: str
    attempts: DataValue
    accepted: DataValue
    rejected: DataValue

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_name(self.teacher_identity) and is_name(self.strategy_id), "TEACHER_ID")
        require(is_wire_integer(self.teacher_epoch) and self.teacher_epoch >= 0,
                "TEACHER_EPOCH")
        require(all(type(item) is DataValue for item in (
            self.attempts, self.accepted, self.rejected)), "TEACHER_VALUES")


@dataclass(frozen=True)
class GenerationManifest(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.generation-manifest/v1"
    meta: RecordMeta
    checkpoint_sha256: str
    student_sha256: str
    optimizer_state_sha256: str
    parent_manifest_sha256: str | None
    status: str

    def __post_init__(self) -> None:
        super().__post_init__()
        require(all(is_sha256(item) for item in (
            self.checkpoint_sha256, self.student_sha256,
            self.optimizer_state_sha256)), "GENERATION_DIGEST")
        require(self.parent_manifest_sha256 is None
                or is_sha256(self.parent_manifest_sha256), "PARENT_MANIFEST")
        require(is_name(self.status), "GENERATION_STATUS")


@dataclass(frozen=True)
class ResourceSample(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.resource-sample/v1"
    meta: RecordMeta
    memory_used_bytes: DataValue
    memory_budget_bytes: DataValue
    disk_used_bytes: DataValue
    step_rate_per_minute: DataValue

    def __post_init__(self) -> None:
        super().__post_init__()
        require(all(type(item) is DataValue for item in (
            self.memory_used_bytes, self.memory_budget_bytes,
            self.disk_used_bytes, self.step_rate_per_minute)), "RESOURCE_VALUES")
