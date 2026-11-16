"""Core neural-inert Factory release contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode()).hexdigest()


def _sha256(value: str, code: str) -> str:
    if (not isinstance(value, str) or len(value) != 64 or
            any(char not in "0123456789abcdef" for char in value)):
        raise ValueError(code)
    return value


class AssessmentClass(str, Enum):
    ROUTINE = "ROUTINE"
    PROMOTION = "PROMOTION"
    GENERALIZATION = "GENERALIZATION"


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


__all__ = (
    "AssessmentClass",
    "CapabilityDefinition",
    "ConstructionProgram",
    "CoveragePlan",
    "GradeDefinition",
    "SemanticRelease",
    "SourceAdapter",
    "TeachingOption",
    "_digest",
    "_sha256",
)
