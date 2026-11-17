"""Core typed contracts for the legacy FactoryRelease facade.

These types remain implementation-neutral and carry no runtime learner authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

def _sha256(value: str, code: str) -> str:
    if (not isinstance(value, str) or len(value) != 64 or
            any(char not in "0123456789abcdef" for char in value)):
        raise ValueError(code)
    return value


class AssessmentClass(str, Enum):
    ROUTINE = "ROUTINE"
    PROMOTION = "PROMOTION"
    GENERALIZATION = "GENERALIZATION"


class ProviderDimensionError(str, Enum):
    POLICY_INVALID = "FACTORY_PROVIDER_DIMENSION_POLICY_INVALID"
    SELECTION_MODE_INVALID = "FACTORY_PROVIDER_DIMENSION_SELECTION_MODE_INVALID"
    TRIGGER_INVALID = "FACTORY_PROVIDER_DIMENSION_TRIGGER_INVALID"
    ANSWER_FAMILY_INVALID = "FACTORY_PROVIDER_DIMENSION_ANSWER_FAMILY_INVALID"
    CHANGE_FLAGS_INVALID = "FACTORY_PROVIDER_DIMENSION_CHANGE_FLAGS_INVALID"
    ANSWER_CHANGE_INVALID = "FACTORY_PROVIDER_DIMENSION_ANSWER_CHANGE_INVALID"
    POLICY_BINDING_INVALID = "FACTORY_PROVIDER_DIMENSION_POLICY_BINDING_INVALID"
    DOMAIN_INVALID = "FACTORY_PROVIDER_DIMENSION_DOMAIN_INVALID"
    PROVIDER_AMBIGUOUS = "FACTORY_PROVIDER_DIMENSION_PROVIDER_AMBIGUOUS"
    POLICY_REQUIRED = "FACTORY_PROVIDER_DIMENSION_POLICY_REQUIRED"
    PROVIDER_REQUIRED = "FACTORY_PROVIDER_DIMENSION_PROVIDER_REQUIRED"
    VALUE_OUTSIDE_DOMAIN = "FACTORY_PROVIDER_DIMENSION_VALUE_OUTSIDE_DOMAIN"
    SELECTION_EMPTY = "FACTORY_PROVIDER_DIMENSION_SELECTION_EMPTY"
    SELECTION_DRIFT = "FACTORY_PROVIDER_DIMENSION_SELECTION_DRIFT"
    PROGRESS_STATE_INVALID = "FACTORY_PROVIDER_DIMENSION_PROGRESS_STATE_INVALID"
    ANSWER_STATE_DRIFT = "FACTORY_PROVIDER_DIMENSION_ANSWER_STATE_DRIFT"
    RELEASE_REQUIRED = "FACTORY_PROVIDER_DIMENSION_RELEASE_REQUIRED"
    EXECUTION_REQUIRED = "FACTORY_PROVIDER_DIMENSION_EXECUTION_REQUIRED"
    EXECUTION_DRIFT = "FACTORY_PROVIDER_DIMENSION_EXECUTION_DRIFT"
    GEOMETRY_OWNER_REQUIRED = "FACTORY_PROVIDER_DIMENSION_GEOMETRY_OWNER_REQUIRED"
    POLICY_DRIFT = "FACTORY_PROVIDER_DIMENSION_POLICY_DRIFT"
    MEMBERSHIP_OWNER_REQUIRED = "FACTORY_PROVIDER_DIMENSION_MEMBERSHIP_OWNER_REQUIRED"
    SUCCESSOR_DRIFT = "FACTORY_PROVIDER_DIMENSION_SUCCESSOR_DRIFT"
    PROJECTION_DRIFT = "FACTORY_PROVIDER_DIMENSION_PROJECTION_DRIFT"
    AUTO_POLICY_AMBIGUOUS = "FACTORY_PROVIDER_DIMENSION_AUTO_POLICY_AMBIGUOUS"


@dataclass(frozen=True)
class SemanticRelease:
    version: str
    course_sha256: str
    ast_sha256: str
    source_attestation_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.version, str) or not self.version:
            raise ValueError("FACTORY_SEMANTIC_RELEASE_VERSION_REQUIRED")
        _sha256(self.course_sha256, "FACTORY_SEMANTIC_RELEASE_COURSE_DIGEST_INVALID")
        _sha256(self.ast_sha256, "FACTORY_SEMANTIC_RELEASE_AST_DIGEST_INVALID")
        _sha256(self.source_attestation_sha256,
                "FACTORY_SEMANTIC_RELEASE_SOURCE_DIGEST_INVALID")


@dataclass(frozen=True)
class CapabilityDefinition:
    capability_id: str
    grade_id: str
    prerequisites: tuple[str, ...]
    source_adapter_id: str
    oracle_id: str
    answer_kinds: tuple[str, ...]


@dataclass(frozen=True)
class GradeDefinition:
    grade_id: str
    capabilities: tuple[str, ...]
    teaching_stages: tuple[tuple[str, ...], ...]
    assessment_sha256: str


@dataclass(frozen=True)
class ConstructionProgram:
    capability_id: str
    source_adapter_id: str
    generator_id: str
    oracle_id: str
    prerequisites: tuple[str, ...]


@dataclass(frozen=True)
class CoveragePlan:
    capability_id: str
    variation_axes: tuple[str, ...]
    minimum_specimens: int
    require_counterbalanced_gold: bool = True
    require_fresh_seed: bool = True


@dataclass(frozen=True)
class TeachingOption:
    option_id: str
    capability_id: str
    construction_program_id: str
    source_grounded: bool
    supervised_gold_allowed: bool


@dataclass(frozen=True)
class SourceAdapter:
    """Release-time identity of one genuine source construction boundary."""

    adapter_id: str
    generator_id: str
    accepted_oracle_ids: tuple[str, ...]
    implementation_sha256: str
    cohort_generator_id: str | None = None
    cohort_releases: tuple[tuple[str, str], ...] = ()
    variation_axes: tuple[str, ...] = ("source-valid", "balanced-gold", "fresh-seed")
    teaching_option_ids: tuple[str, ...] = ()
    profile_dimensions: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def __post_init__(self) -> None:
        if (not self.adapter_id or not self.generator_id or
                not self.accepted_oracle_ids or
                any(not isinstance(item, str) or not item
                    for item in self.accepted_oracle_ids)):
            raise ValueError("FACTORY_SOURCE_ADAPTER_IDENTITY_INVALID")
        _sha256(self.implementation_sha256,
                "FACTORY_SOURCE_ADAPTER_IMPLEMENTATION_DIGEST_INVALID")
        if self.cohort_generator_id is not None and not self.cohort_generator_id:
            raise ValueError("FACTORY_SOURCE_ADAPTER_COHORT_GENERATOR_INVALID")
        if (not self.variation_axes or
                any(not isinstance(axis, str) or not axis for axis in self.variation_axes) or
                len(set(self.variation_axes)) != len(self.variation_axes)):
            raise ValueError("FACTORY_SOURCE_ADAPTER_VARIATION_AXES_INVALID")
        seen = set()
        for release, digest in self.cohort_releases:
            if (not release or release in seen):
                raise ValueError("FACTORY_SOURCE_ADAPTER_COHORT_RELEASE_INVALID")
            seen.add(release)
            _sha256(digest, "FACTORY_SOURCE_ADAPTER_COHORT_RELEASE_DIGEST_INVALID")
        if (len(set(self.teaching_option_ids)) != len(self.teaching_option_ids) or
                any(not isinstance(item, str) or not item
                    for item in self.teaching_option_ids)):
            raise ValueError("FACTORY_SOURCE_ADAPTER_TEACHING_OPTIONS_INVALID")
        names = tuple(name for name, _ in self.profile_dimensions)
        if (len(set(names)) != len(names) or
                any(not isinstance(name, str) or not name or
                    not values or len(set(values)) != len(values) or
                    any(not isinstance(value, str) or not value for value in values)
                    for name, values in self.profile_dimensions)):
            raise ValueError("FACTORY_SOURCE_ADAPTER_PROFILE_DIMENSIONS_INVALID")

    @property
    def cohort_generator(self) -> str:
        return self.cohort_generator_id or self.generator_id

    def cohort_code_sha256(self, release: str) -> str:
        mapping = dict(self.cohort_releases)
        return mapping.get(release, self.implementation_sha256)

    def validate_profile_parameters(
            self, parameters: tuple[tuple[str, tuple[str, ...]], ...]) -> None:
        declared = dict(self.profile_dimensions)
        supplied = dict(parameters)
        if set(supplied) - set(declared):
            raise ValueError(
                "FACTORY_PROFILE_PROVIDER_DIMENSION_UNDECLARED:" + self.adapter_id)
        for name, values in parameters:
            domain = declared[name]
            if (not set(values) <= set(domain) or
                    values != tuple(value for value in domain if value in values)):
                raise ValueError(
                    "FACTORY_PROFILE_PROVIDER_VALUES_NOT_CANONICAL_SUBSET:"
                    + self.adapter_id + ":" + name)


@dataclass(frozen=True)
class ProviderDimensionPolicy:
    """Provider-owned progression contract for one already-admitted dimension."""

    provider_id: str
    dimension_id: str
    parameter_name: str
    progression_values: tuple[str, ...]
    selection_mode: str
    step_mode: str
    advance_trigger: str
    terminal_value: str
    source_constraint: str
    admission_constraint: str
    telemetry_projection: str
    answer_family_kind: str | None = None
    changes_semantic_geometry: bool = False
    changes_source_projection: bool = True
    changes_assessment_scope: bool = False
    changes_answer_domain: bool = False

    def __post_init__(self) -> None:
        identifiers = (
            self.provider_id, self.dimension_id, self.parameter_name,
            self.telemetry_projection)
        if (any(not isinstance(value, str) or not value for value in identifiers) or
                not re.fullmatch(r"[A-Za-z0-9._-]+", self.dimension_id) or
                not self.progression_values or
                len(set(self.progression_values)) != len(self.progression_values) or
                any(not isinstance(value, str) or not value
                    for value in self.progression_values)):
            raise ValueError(ProviderDimensionError.POLICY_INVALID.value)
        if (self.step_mode != "ADJACENT" or
                self.terminal_value != self.progression_values[-1] or
                self.source_constraint != "SAME_PROVIDER_BINDING" or
                self.admission_constraint != "EXISTING_CAPABILITY_PROFILE"):
            raise ValueError(ProviderDimensionError.POLICY_INVALID.value)
        if self.selection_mode != "CANONICAL_PREFIX":
            raise ValueError(ProviderDimensionError.SELECTION_MODE_INVALID.value)
        if self.advance_trigger not in ("DEVELOPMENTAL_BOUNDARY", "EXPLICIT"):
            raise ValueError(ProviderDimensionError.TRIGGER_INVALID.value)
        if (self.answer_family_kind is not None and
                (not isinstance(self.answer_family_kind, str) or
                 not self.answer_family_kind)):
            raise ValueError(ProviderDimensionError.ANSWER_FAMILY_INVALID.value)
        flags = (
            self.changes_semantic_geometry, self.changes_source_projection,
            self.changes_assessment_scope, self.changes_answer_domain)
        if any(type(value) is not bool for value in flags):
            raise ValueError(ProviderDimensionError.CHANGE_FLAGS_INVALID.value)
        if self.changes_answer_domain != (self.answer_family_kind is not None):
            raise ValueError(ProviderDimensionError.ANSWER_CHANGE_INVALID.value)


@dataclass(frozen=True)
class AssessmentPlan:
    grade_id: str
    assessment_class: AssessmentClass
    lifecycle: str
    fresh_on_decision: bool
    reusable_after_failure: bool
    burn_after_failure: bool


def assessment_plans(grade_ids) -> tuple[AssessmentPlan, ...]:
    from ...generated_assessment import (
        GENERALIZATION_LIFECYCLE, PROMOTION_ATTEMPT_LIFECYCLE, ROUTINE_EVAL_LIFECYCLE,
    )
    return tuple(
        AssessmentPlan(grade, kind, lifecycle, fresh, reusable, burn)
        for grade in grade_ids
        for kind, lifecycle, fresh, reusable, burn in (
            (AssessmentClass.ROUTINE, ROUTINE_EVAL_LIFECYCLE, True, False, False),
            (AssessmentClass.PROMOTION, PROMOTION_ATTEMPT_LIFECYCLE, False, True, False),
            (AssessmentClass.GENERALIZATION, GENERALIZATION_LIFECYCLE, True, False, True)))
