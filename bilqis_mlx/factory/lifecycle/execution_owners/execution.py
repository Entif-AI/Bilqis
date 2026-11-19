"""Compile semantic curriculum plus source bindings into one execution plan.

Canonical curriculum meaning is independent from source/provider implementation.
Legacy ``Course`` remains an input only through a compatibility projection while
callers migrate to ``CurriculumDefinition`` and ``SourceBindingSet``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json

from ..curriculum import AnswerFamily, Course
from .adapters import SourceAdapterRegistry
from .curriculum_definition import (
    CurriculumDefinition, SourceBindingSet, from_legacy_course,
    validate_curriculum_definition, validate_source_bindings,
)


@dataclass(frozen=True)
class CapabilityProfile:
    capability_id: str
    provider_parameters: tuple[tuple[str, tuple[str, ...]], ...] = ()
    answer_family_values: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.capability_id, str) or not self.capability_id:
            raise ValueError("FACTORY_PROFILE_CAPABILITY_ID_REQUIRED")
        object.__setattr__(self, "provider_parameters", _pairs(self.provider_parameters))
        object.__setattr__(self, "answer_family_values", _pairs(self.answer_family_values))

@dataclass(frozen=True)
class GradeProfile:
    grade_id: str
    enabled_capabilities: tuple[str, ...] | None = None
    capabilities: tuple[CapabilityProfile, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.grade_id, str) or not self.grade_id:
            raise ValueError("FACTORY_PROFILE_GRADE_ID_REQUIRED")
        if self.enabled_capabilities is not None and (
                len(set(self.enabled_capabilities)) != len(self.enabled_capabilities) or
                any(not isinstance(item, str) or not item
                    for item in self.enabled_capabilities)):
            raise ValueError("FACTORY_PROFILE_ENABLED_CAPABILITIES_INVALID")
        ids = tuple(item.capability_id for item in self.capabilities)
        if len(set(ids)) != len(ids):
            raise ValueError("FACTORY_PROFILE_DUPLICATE_CAPABILITY_OVERRIDE")

@dataclass(frozen=True)
class CurriculumProfile:
    profile_id: str
    grades: tuple[GradeProfile, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not self.profile_id:
            raise ValueError("FACTORY_PROFILE_ID_REQUIRED")
        ids = tuple(item.grade_id for item in self.grades)
        if len(set(ids)) != len(ids):
            raise ValueError("FACTORY_PROFILE_DUPLICATE_GRADE_OVERRIDE")

    @classmethod
    def full(cls) -> "CurriculumProfile":
        return cls("full")

@dataclass(frozen=True)
class CapabilityExecution:
    capability_id: str
    grade_id: str
    stage: int
    prerequisites: tuple[str, ...]
    composed_of: tuple[str, ...]
    source_anchor: str
    provider_id: str
    provider_implementation_sha256: str
    oracle_id: str
    construction_program_id: str
    provider_parameters: tuple[tuple[str, tuple[str, ...]], ...]
    variation_axes: tuple[str, ...]
    teaching_option_ids: tuple[str, ...]
    answer_families: tuple[AnswerFamily, ...]
    exam_item_count: int

@dataclass(frozen=True)
class GradeExecution:
    grade_id: str
    capabilities: tuple[str, ...]
    teaching_stages: tuple[tuple[str, ...], ...]
    cumulative_scope: tuple[str, ...]
    assessment_blueprint_sha256: str

@dataclass(frozen=True)
class ProjectionDigests:
    roster: str
    schedule: str
    assessment: str
    source: str
    answer_schema: str
    coverage: str
    teaching: str

@dataclass(frozen=True)
class CapabilityProjectionDigests:
    capability_id: str
    schedule: str
    assessment: str
    source: str
    answer_schema: str
    coverage: str
    teaching: str

@dataclass(frozen=True)
class ExecutionPlan:
    profile_id: str
    curriculum_sha256: str
    source_binding_sha256: str
    grades: tuple[GradeExecution, ...]
    capabilities: tuple[CapabilityExecution, ...]
    projection_digests: ProjectionDigests
    capability_projection_digests: tuple[CapabilityProjectionDigests, ...]

    @property
    def capability_map(self) -> dict[str, CapabilityExecution]:
        return {item.capability_id: item for item in self.capabilities}

    @property
    def active_capability_inventory(self) -> tuple[str, ...]:
        """Canonical executable capability inventory in plan order."""
        return tuple(item.capability_id for item in self.capabilities)

    @property
    def grade_map(self) -> dict[str, GradeExecution]:
        return {item.grade_id: item for item in self.grades}

    @property
    def course_sha256(self) -> str:
        """Compatibility alias for pre-split callers only."""
        return self.curriculum_sha256

    def digest(self) -> str:
        return _digest(asdict(self))

class SemanticGeometryChange(str, Enum):
    UNCHANGED = "UNCHANGED"
    APPEND_ONLY_EXPANSION = "APPEND_ONLY_EXPANSION"
    INCOMPATIBLE = "INCOMPATIBLE"

@dataclass(frozen=True)
class PlanLineage:
    previous_curriculum_sha256: str
    next_curriculum_sha256: str
    semantic_geometry: SemanticGeometryChange

    def __post_init__(self) -> None:
        for value in (
                self.previous_curriculum_sha256,
                self.next_curriculum_sha256):
            if (not isinstance(value, str) or len(value) != 64 or
                    any(c not in "0123456789abcdef" for c in value)):
                raise ValueError("FACTORY_PLAN_LINEAGE_CURRICULUM_DIGEST_INVALID")

    @classmethod
    def from_semantic_catalogs(
            cls, previous: ExecutionPlan, current: ExecutionPlan,
            previous_tokens: tuple[str, ...], current_tokens: tuple[str, ...]):
        if (not previous_tokens or not current_tokens or
                len(set(previous_tokens)) != len(previous_tokens) or
                len(set(current_tokens)) != len(current_tokens)):
            raise ValueError("FACTORY_PLAN_LINEAGE_SEMANTIC_CATALOG_INVALID")
        if current_tokens == previous_tokens:
            geometry = SemanticGeometryChange.UNCHANGED
        elif current_tokens[:len(previous_tokens)] == previous_tokens:
            geometry = SemanticGeometryChange.APPEND_ONLY_EXPANSION
        else:
            geometry = SemanticGeometryChange.INCOMPATIBLE
        return cls(
            previous.curriculum_sha256, current.curriculum_sha256, geometry)

@dataclass(frozen=True)
class CurriculumDelta:
    previous_plan_sha256: str
    next_plan_sha256: str
    previous_curriculum_sha256: str
    next_curriculum_sha256: str
    previous_source_binding_sha256: str
    next_source_binding_sha256: str
    added_grades: tuple[str, ...]
    removed_grades: tuple[str, ...]
    revised_grades: tuple[str, ...]
    added_capabilities: tuple[str, ...]
    removed_capabilities: tuple[str, ...]
    changed_capabilities: tuple[str, ...]
    projection_changes: tuple[str, ...]
    semantic_geometry: str

from ._execution.common import (
    _digest, _pairs,
)
from ._execution.lineage import (
    _verify_lineage_curriculum, diff_execution_plans,
)
from ._execution.profiling import (
    _profile_maps, _answer_families, _stages, _enabled_for_grade, _profiled_grade, _compile_profiled_grades,
)
from ._execution.projections import (
    _projection_digests, _capability_projection_digests,
)
from ._execution.compilation import (
    _normalize_inputs, compile_execution_plan,
)

# Preserve the historical public identity of imported functions.
for _function in (
    _digest, _pairs,
    _verify_lineage_curriculum, diff_execution_plans,
    _profile_maps, _answer_families, _stages, _enabled_for_grade, _profiled_grade, _compile_profiled_grades,
    _projection_digests, _capability_projection_digests,
    _normalize_inputs, compile_execution_plan,
):
    _function.__module__ = __name__
del _function
