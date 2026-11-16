"""FactoryRelease serialization and contract validation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ...curriculum import AnswerFamily, Capability, Course, Grade
from .assessment import AssessmentPlan, assessment_plans
from .contracts import (
    AssessmentClass,
    CapabilityDefinition,
    ConstructionProgram,
    CoveragePlan,
    GradeDefinition,
    SemanticRelease,
    SourceAdapter,
    TeachingOption,
    _digest,
    _sha256,
)


@dataclass(frozen=True)
class FactoryRelease:
    """Only release artifact from which a production grade may be executed."""

    semantic_release: SemanticRelease
    course: Course
    capabilities: tuple[CapabilityDefinition, ...]
    grades: tuple[GradeDefinition, ...]
    source_adapters: tuple[SourceAdapter, ...]
    construction_programs: tuple[ConstructionProgram, ...]
    coverage_plans: tuple[CoveragePlan, ...]
    teaching_options: tuple[TeachingOption, ...]
    assessments: tuple[AssessmentPlan, ...]
    release_sha256: str
    # The original v1 wire contract predates the optional profile_dimensions
    # descriptor. Preserve its exact signed form on legacy readback, rather
    # than accidentally minting a different hash from dataclass defaults.
    _legacy_adapter_wire: bool = field(default=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        _sha256(self.release_sha256, "FACTORY_RELEASE_DIGEST_INVALID")

    @property
    def source_adapter_map(self) -> dict[str, SourceAdapter]:
        return {adapter.adapter_id: adapter for adapter in self.source_adapters}

    @property
    def assessment_rubric_sha256s(self) -> tuple[str, ...]:
        """Expose signed v1 assessment identities without leaking Course traversal."""
        return tuple(grade.assessment_sha256 for grade in self.course.grades)

    def expected_digest(self) -> str:
        return _digest(self.manifest())

    def manifest(self) -> dict:
        adapters = [asdict(item) for item in self.source_adapters]
        if self._legacy_adapter_wire:
            for adapter in adapters:
                if adapter["profile_dimensions"]:
                    raise ValueError("FACTORY_RELEASE_LEGACY_ADAPTER_SCOPE_DRIFT")
                del adapter["profile_dimensions"]
        return {
            "semantic_release": asdict(self.semantic_release),
            "course": asdict(self.course),
            "course_sha256": self.course.digest(),
            "capabilities": [asdict(item) for item in self.capabilities],
            "grades": [asdict(item) for item in self.grades],
            "source_adapters": adapters,
            "construction_programs": [asdict(item) for item in self.construction_programs],
            "coverage_plans": [asdict(item) for item in self.coverage_plans],
            "teaching_options": [asdict(item) for item in self.teaching_options],
            "assessments": [
                {**asdict(item), "assessment_class": item.assessment_class.value}
                for item in self.assessments],
        }

    @classmethod
    def _decode_manifest(cls, payload: dict, release_sha256: str) -> FactoryRelease:
        """Decode manifest shape without assigning a digest verification policy."""
        def tuples(value):
            return tuple(tuples(item) for item in value) if isinstance(value, list) else value

        def record(record_type, value):
            return record_type(**{key: tuples(item) for key, item in value.items()})

        try:
            declared = payload["course"]
            adapters = payload["source_adapters"]
            adapter_wire = tuple("profile_dimensions" in item for item in adapters)
            if adapter_wire and len(set(adapter_wire)) != 1:
                raise ValueError("FACTORY_RELEASE_ADAPTER_WIRE_MIXED")
            legacy_adapter_wire = bool(adapter_wire) and not adapter_wire[0]
            grades = []
            for grade in declared["grades"]:
                caps = tuple(record(Capability, {
                    **cap, "answer_families": tuple(record(AnswerFamily, family)
                                                   for family in cap["answer_families"]),
                }) for cap in grade["capabilities"])
                grades.append(record(Grade, {**grade, "capabilities": caps}))
            course = Course(**{**declared, "grades": tuple(grades)})
            return cls(
                semantic_release=record(SemanticRelease, payload["semantic_release"]),
                course=course,
                **{key: tuple(record(kind, value) for value in payload[key])
                   for key, kind in (
                       ("capabilities", CapabilityDefinition), ("grades", GradeDefinition),
                       ("source_adapters", SourceAdapter),
                       ("construction_programs", ConstructionProgram),
                       ("coverage_plans", CoveragePlan), ("teaching_options", TeachingOption))},
                assessments=tuple(record(AssessmentPlan, {
                    **value, "assessment_class": AssessmentClass(value["assessment_class"]),
                }) for value in payload["assessments"]),
                release_sha256=release_sha256,
                _legacy_adapter_wire=legacy_adapter_wire,
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError("FACTORY_RELEASE_MANIFEST_INVALID") from exc

    @classmethod
    def from_manifest(cls, payload: dict, release_sha256: str) -> FactoryRelease:
        """Decode a manifest minted by the current FactoryRelease serializer."""
        release = cls._decode_manifest(payload, release_sha256)
        if (_digest(payload) != release_sha256 or
                payload["course_sha256"] != release.course.digest()):
            raise ValueError("FACTORY_RELEASE_MANIFEST_CONTENT_DRIFT")
        release.verify()
        return release

    def verify_contract(self) -> None:
        """Verify semantic/source structure independently of serializer identity."""
        from ...curriculum_compiler import compile_ast

        if not self.course.executable:
            raise ValueError("FACTORY_RELEASE_COURSE_NOT_EXECUTABLE")
        if self.semantic_release.course_sha256 != self.course.digest():
            raise ValueError("FACTORY_RELEASE_COURSE_BINDING_DRIFT")
        if (self.semantic_release.version != self.course.version or
                self.semantic_release.ast_sha256 != compile_ast(self.course).digest() or
                self.semantic_release.source_attestation_sha256 !=
                self.course.source_attestation_sha256):
            raise ValueError("FACTORY_RELEASE_SEMANTIC_BINDING_DRIFT")
        grade_ids = tuple(grade.id for grade in self.course.grades)
        if tuple(item.grade_id for item in self.grades) != grade_ids:
            raise ValueError("FACTORY_RELEASE_GRADE_BINDING_DRIFT")
        for definition, grade in zip(self.grades, self.course.grades):
            if definition != GradeDefinition(
                    grade.id, tuple(cap.id for cap in grade.capabilities),
                    grade.teaching_stages, grade.assessment_sha256):
                raise ValueError("FACTORY_RELEASE_GRADE_CONTRACT_DRIFT")
        expected_caps = tuple(cap.id for grade in self.course.grades
                              for cap in grade.capabilities)
        if tuple(item.capability_id for item in self.capabilities) != expected_caps:
            raise ValueError("FACTORY_RELEASE_CAPABILITY_BINDING_DRIFT")
        for field, values in (
                ("construction", self.construction_programs),
                ("coverage", self.coverage_plans)):
            if tuple(item.capability_id for item in values) != expected_caps:
                raise ValueError("FACTORY_RELEASE_" + field.upper() + "_BINDING_DRIFT")
        self._verify_source_contracts(expected_caps)
        if self.assessments != assessment_plans(grade_ids):
            raise ValueError("FACTORY_RELEASE_ASSESSMENT_CONTRACT_DRIFT")

    def verify(self) -> None:
        if self.release_sha256 != self.expected_digest():
            raise ValueError("FACTORY_RELEASE_CONTENT_DRIFT")
        self.verify_contract()

    def _verify_source_contracts(self, expected_caps):
        teaching_by_capability = {
            capability: tuple(item for item in self.teaching_options
                              if item.capability_id == capability)
            for capability in expected_caps
        }
        if (any(not teaching_by_capability[capability] for capability in expected_caps) or
                {item.capability_id for item in self.teaching_options} != set(expected_caps) or
                any(not any(item.option_id == "source.direct/" + capability
                            for item in teaching_by_capability[capability])
                    for capability in expected_caps)):
            raise ValueError("FACTORY_RELEASE_TEACHING_BINDING_DRIFT")
        adapters = self.source_adapter_map
        if len(adapters) != len(self.source_adapters):
            raise ValueError("FACTORY_RELEASE_DUPLICATE_SOURCE_ADAPTER")
        for cap in self.capabilities:
            adapter = adapters.get(cap.source_adapter_id)
            if adapter is None or cap.oracle_id not in adapter.accepted_oracle_ids:
                raise ValueError("FACTORY_RELEASE_SOURCE_ORACLE_BINDING_INVALID")
            declared = self.course.capability_map[cap.capability_id]
            if (cap.grade_id != next(grade.id for grade in self.course.grades
                                    if declared in grade.capabilities) or
                    cap.prerequisites != declared.prerequisites or
                    cap.oracle_id != declared.independent_oracle or
                    cap.answer_kinds != tuple(f.kind for f in declared.answer_families) or
                    adapter.generator_id != declared.lesson_generator):
                raise ValueError("FACTORY_RELEASE_CAPABILITY_CONTRACT_DRIFT")
        for cap, program, coverage in zip(
                self.capabilities, self.construction_programs, self.coverage_plans):
            adapter = adapters[cap.source_adapter_id]
            if program != ConstructionProgram(
                    cap.capability_id, cap.source_adapter_id, adapter.generator_id,
                    cap.oracle_id, cap.prerequisites):
                raise ValueError("FACTORY_RELEASE_CONSTRUCTION_CONTRACT_DRIFT")
            counts = dict(next(grade.exam_item_counts for grade in self.course.grades
                               if grade.id == cap.grade_id))
            if (coverage.variation_axes != adapter.variation_axes or
                    coverage.minimum_specimens != counts[cap.capability_id] or
                    coverage.require_counterbalanced_gold !=
                    ("balanced-gold" in adapter.variation_axes) or
                    coverage.require_fresh_seed is not True):
                raise ValueError("FACTORY_RELEASE_COVERAGE_CONTRACT_DRIFT")
            expected_options = tuple(
                TeachingOption(option, cap.capability_id, cap.capability_id, True, True)
                for option in ("source.direct/" + cap.capability_id,
                               *adapter.teaching_option_ids))
            if teaching_by_capability[cap.capability_id] != expected_options:
                raise ValueError("FACTORY_RELEASE_TEACHING_CONTRACT_DRIFT")


__all__ = ("FactoryRelease",)
