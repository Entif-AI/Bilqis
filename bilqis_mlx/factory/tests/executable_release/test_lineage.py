from dataclasses import replace
import json
import unittest

from bilqis_mlx.curriculum import BINARY, BOOLEAN_OPERATORS
from bilqis_mlx.factory.adapters import (
    RegisteredSourceAdapter, SourceAdapterRegistry,
)
from bilqis_mlx.factory.answers import (
    AnswerModality, AnswerModalityRegistry, RegisteredAnswerModality,
    fixed_domain,
)
from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.executable_release import (
    ExecutableFactoryRelease, compile_executable_factory_release,
)
from bilqis_mlx.factory.execution import CurriculumProfile
from bilqis_mlx.factory.execution import (
    CapabilityProfile, GradeProfile, PlanLineage,
)
from bilqis_mlx.factory.model import SourceAdapter
from bilqis_mlx.factory.tests.test_execution_plan import (
    _synthetic_boolean_course, _synthetic_course, _synthetic_registry,
)


def _answers():
    return AnswerModalityRegistry((
        RegisteredAnswerModality(
            AnswerModality("binary", "answer.binary/v1", "a" * 64),
            fixed_domain(BINARY),
            lambda value: {
                "FALSE": "cogal.value.false",
                "TRUE": "cogal.value.true",
            }[value]),
    ))


def _boolean_answers():
    return AnswerModalityRegistry((
        RegisteredAnswerModality(
            AnswerModality("binary", "answer.binary/v1", "a" * 64),
            fixed_domain(BINARY),
            lambda value: {
                "FALSE": "cogal.value.false",
                "TRUE": "cogal.value.true",
            }[value]),
        RegisteredAnswerModality(
            AnswerModality(
                "boolean_operator", "answer.boolean-operator/v1", "b" * 64),
            fixed_domain(BOOLEAN_OPERATORS),
            lambda value: "cogal.operator." + value),
    ))


from bilqis_mlx.factory.tests.executable_release.support import ReleaseTestSupport, _answers, _boolean_answers


class ExecutableFactoryReleaseTests(ReleaseTestSupport):
    def test_profile_transition_binds_unchanged_geometry_and_new_assessment_seal(self):
        course, registry = _synthetic_boolean_course()
        curriculum, bindings = from_legacy_course(course)
        answers = _boolean_answers()
        graph = {
            "tokens": [
                "fixture.padding",
                "cogal.value.false",
                "cogal.value.true",
                *(f"cogal.operator.{value}" for value in BOOLEAN_OPERATORS),
            ],
        }
        full = compile_executable_factory_release(
            curriculum, bindings, CurriculumProfile.full(),
            registry, answers, source_root=None, graph=graph,
            verification_seed=17)
        reduced_profile = CurriculumProfile(
            "boolean-kernel/and-iff",
            grades=(GradeProfile(
                "B",
                enabled_capabilities=(
                    "B.AND", "B.IFF", "B.COMPOSITE", "B.IDBOOLOPS"),
                capabilities=(
                    CapabilityProfile(
                        "B.COMPOSITE",
                        provider_parameters=(("operators", ("AND", "IFF")),)),
                    CapabilityProfile(
                        "B.IDBOOLOPS",
                        provider_parameters=(("operators", ("AND", "IFF")),),
                        answer_family_values=(
                            ("boolean_operator", ("AND", "IFF")),)),
                ),
            ),),
        )
        reduced = compile_executable_factory_release(
            curriculum, bindings, reduced_profile,
            registry, answers, source_root=None, graph=graph,
            verification_seed=17,
            predecessor=full)

        self.assertEqual(reduced.predecessor_release_sha256, full.release_sha256)
        self.assertEqual(reduced.transition.semantic_geometry, "UNCHANGED")
        self.assertEqual(
            reduced.transition.previous_curriculum_sha256,
            reduced.transition.next_curriculum_sha256)
        full_b = full.verification.assessments[-1]
        reduced_b = reduced.verification.assessments[-1]
        self.assertNotEqual(full_b.seal_sha256, reduced_b.seal_sha256)
        self.assertEqual(
            {item.provider_id for item in reduced.execution_plan.capabilities
             if item.grade_id == "B"},
            {"fixture.b-adapter/v1"})

    def test_source_oracle_failure_cannot_mint_verified_release(self):
        descriptor = self.registry.require(
            "fixture.z-generator/v1", "fixture.z-oracle/v1").descriptor
        failing_registry = SourceAdapterRegistry((
            RegisteredSourceAdapter(
                descriptor,
                self.registry.require(
                    "fixture.z-generator/v1", "fixture.z-oracle/v1").draw,
                lambda row, **_: False),
        ))
        with self.assertRaisesRegex(
                ValueError, "SOURCE_ORACLE_DISAGREEMENT"):
            compile_executable_factory_release(
                self.curriculum, self.bindings, CurriculumProfile.full(),
                failing_registry, self.answers,
                source_root=None, graph=self.graph,
                verification_seed=20261019)

    def test_incompatible_semantic_geometry_cannot_be_admitted(self):
        predecessor = self.compile()
        grade = self.course.grades[0]
        changed_capability = replace(
            grade.capabilities[-1],
            taught_roots=("fixture.changed",),
            examined_roots=("fixture.changed",))
        changed_course = replace(
            self.course,
            grades=(replace(
                grade,
                capabilities=(*grade.capabilities[:-1], changed_capability)),),
        )
        curriculum, bindings = from_legacy_course(changed_course)
        incompatible_graph = {
            "tokens": [
                "fixture.padding",
                "cogal.value.true",
                "cogal.value.false",
            ],
        }
        with self.assertRaisesRegex(
                ValueError, "INCOMPATIBLE_GEOMETRY"):
            compile_executable_factory_release(
                curriculum, bindings, CurriculumProfile.full(),
                self.registry_with_revised_roots({"Z.C5": "fixture.changed"}), self.answers,
                source_root=None, graph=incompatible_graph,
                verification_seed=20261019,
                predecessor=predecessor)

    def test_append_only_semantic_geometry_is_carried_by_successor_release(self):
        predecessor = self.compile()
        grade = self.course.grades[0]
        new_capability = replace(
            grade.capabilities[-1],
            id="Z.C6",
            taught_roots=("fixture.op.6",),
            examined_roots=("fixture.op.6",))
        expanded_grade = replace(
            grade,
            capabilities=(*grade.capabilities, new_capability),
            exam_item_counts=(*grade.exam_item_counts, ("Z.C6", 4)))
        expanded_course = replace(self.course, grades=(expanded_grade,))
        curriculum, bindings = from_legacy_course(expanded_course)
        expanded_graph = {
            "tokens": [*self.graph["tokens"], "fixture.appended.identity"],
        }
        successor = compile_executable_factory_release(
            curriculum, bindings, CurriculumProfile.full(),
            self.registry_with_revised_roots({"Z.C6": "fixture.op.6"}), self.answers,
            source_root=None, graph=expanded_graph,
            verification_seed=20261019,
            predecessor=predecessor)

        self.assertEqual(
            successor.transition.semantic_geometry,
            "APPEND_ONLY_EXPANSION")
        self.assertEqual(
            successor.predecessor_release_sha256,
            predecessor.release_sha256)
        self.assertIn("Z.C6", successor.transition.added_capabilities)
        self.assertNotIn("Z.C6", predecessor.foundation_capability_ids)
        self.assertIn("Z.C6", successor.foundation_capability_ids)
        self.assertEqual(
            predecessor.foundation_capability_ids,
            predecessor.execution_plan.active_capability_inventory)
        self.assertEqual(
            successor.foundation_capability_ids,
            successor.execution_plan.active_capability_inventory)

    def test_rehashed_modality_descriptor_drift_is_rejected(self):
        release = self.compile()
        changed = replace(
            release.answer_modalities[0],
            implementation_sha256="f" * 64)
        candidate = replace(
            release,
            answer_modalities=(changed,),
            release_sha256="0" * 64)
        candidate = replace(
            candidate, release_sha256=candidate.expected_digest())
        with self.assertRaisesRegex(
                ValueError, "FACTORY_EXECUTABLE_RELEASE_ANSWER_HEAD_DRIFT"):
            candidate.verify()

    def test_rehashed_semantic_catalog_binding_drift_is_rejected(self):
        release = self.compile()
        candidate = replace(
            release,
            semantic_catalog_sha256="f" * 64,
            release_sha256="0" * 64)
        candidate = replace(
            candidate, release_sha256=candidate.expected_digest())
        with self.assertRaisesRegex(
                ValueError, "FACTORY_EXECUTABLE_RELEASE_CATALOG_DRIFT"):
            candidate.verify()
