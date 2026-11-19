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
    def test_v2_release_roundtrips_complete_executable_authority(self):
        release = self.compile()
        release.verify()
        self.assertEqual(release.schema, "bilqis.mlx.factory-release/v2")
        self.assertEqual(
            release.execution_plan.curriculum_sha256,
            self.curriculum.digest())
        self.assertEqual(
            release.execution_plan.source_binding_sha256,
            self.bindings.digest())
        self.assertEqual(
            release.semantic_catalog_sha256,
            release.verification.semantic_catalog_sha256)
        self.assertEqual(
            tuple(item.kind for item in release.answer_modalities),
            ("binary",))
        self.assertEqual(
            tuple(item.capability_id for item in release.verification.capabilities),
            tuple(item.capability_id for item in release.execution_plan.capabilities))
        self.assertEqual(
            release.foundation_capability_ids,
            release.execution_plan.active_capability_inventory)
        self.assertEqual(
            tuple(release.manifest()["foundation_capability_ids"]),
            release.execution_plan.active_capability_inventory)
        self.assertEqual(
            tuple(item.grade_id for item in release.verification.assessments),
            ("Z",))

        payload = json.loads(json.dumps(release.manifest()))
        restored = ExecutableFactoryRelease.from_manifest(
            payload, release.release_sha256)
        self.assertEqual(restored, release)
        restored.verify_semantic_catalog(self.graph)
        self.assertEqual(
            restored.foundation_capability_ids,
            release.foundation_capability_ids)

    def test_foundation_capability_identity_is_signed_release_authority(self):
        release = self.compile()
        foundation = release.execution_plan.active_capability_inventory
        self.assertTrue(foundation)
        self.assertEqual(release.foundation_capability_ids, foundation)

        altered = (*foundation[:-1], "FOREIGN.CAPABILITY")
        candidate = replace(
            release, foundation_capability_ids=altered,
            release_sha256="0" * 64)
        candidate = replace(
            candidate, release_sha256=candidate.expected_digest())
        self.assertNotEqual(candidate.release_sha256, release.release_sha256)
        with self.assertRaisesRegex(
                ValueError,
                "FACTORY_EXECUTABLE_RELEASE_FOUNDATION_CAPABILITY_DRIFT"):
            candidate.verify()

    def test_foundation_capability_identity_rejects_noncanonical_variants(self):
        release = self.compile()
        foundation = release.execution_plan.active_capability_inventory
        variants = (
            (),
            (foundation[0], *foundation),
            tuple(reversed(foundation)),
            foundation[:-1],
            (*foundation[:-1], "FOREIGN.CAPABILITY"),
        )
        for variant in variants:
            with self.subTest(variant=variant):
                candidate = replace(
                    release, foundation_capability_ids=variant,
                    release_sha256="0" * 64)
                candidate = replace(
                    candidate, release_sha256=candidate.expected_digest())
                with self.assertRaisesRegex(
                        ValueError,
                        "FACTORY_EXECUTABLE_RELEASE_FOUNDATION_CAPABILITY_DRIFT"):
                    candidate.verify()

    def test_grade_label_changes_do_not_change_active_capability_inventory(self):
        release = self.compile()
        renamed = replace(
            release.execution_plan,
            grades=tuple(
                replace(grade, grade_id=f"RENAMED-{index}")
                for index, grade in enumerate(release.execution_plan.grades)),
        )
        self.assertEqual(
            renamed.active_capability_inventory,
            release.foundation_capability_ids)

    def test_twelve_capability_release_roundtrips_without_legacy_course(self):
        names = tuple(f"Z.C{i}" for i in range(12))
        release = self.compile_twelve()
        payload = json.loads(json.dumps(release.manifest()))
        self.assertEqual(payload["schema"], "bilqis.mlx.factory-release/v2")
        restored = ExecutableFactoryRelease.from_manifest(payload, release.release_sha256)
        restored.verify()
        restored.verify_semantic_catalog(self.graph)
        self.assertEqual(restored, release)
        self.assertEqual(restored.release_sha256, release.release_sha256)
        self.assertEqual(tuple(item.capability_id for item in restored.verification.capabilities), names)
        self.assertEqual(restored.verification.assessments[0].cumulative_scope, names)
        self.assertEqual(tuple(item.specimen_count for item in restored.verification.capabilities),
                         (4,) * 12)
        seal = restored.verification.assessments[0]
        self.assertEqual(len(seal.capability_receipt_sha256s), 12)
        self.assertEqual(restored.answer_heads[0].kind, "binary")
        self.assertEqual(restored.answer_heads[0].values, ("FALSE", "TRUE"))
        self.assertEqual(restored.answer_heads[0].token_ids, (1, 2))
        incomplete_seal = replace(seal, cumulative_scope=names[:-1],
                                  capability_receipt_sha256s=seal.capability_receipt_sha256s[:-1])
        incomplete_seal = replace(incomplete_seal, seal_sha256=incomplete_seal.expected_digest())
        mutations = (
            (replace(restored.verification, capabilities=restored.verification.capabilities[:-1]),
             "FACTORY_EXECUTABLE_RELEASE_VERIFICATION_DRIFT"),
            (replace(restored.verification, assessments=(incomplete_seal,)),
             "FACTORY_EXECUTABLE_RELEASE_ASSESSMENT_DRIFT"),
        )
        for verification, error in mutations:
            with self.subTest(error=error):
                candidate = replace(restored, verification=verification)
                candidate = replace(candidate, release_sha256=candidate.expected_digest())
                with self.assertRaisesRegex(ValueError, f"^{error}$"):
                    candidate.verify()

    def test_twelve_capability_successors_preserve_existing_lineage_contract(self):
        predecessor = self.compile_twelve()
        variants = (
            (self.graph, "UNCHANGED"),
            ({"tokens": [*self.graph["tokens"], "fixture.appended"]}, "APPEND_ONLY_EXPANSION"),
        )
        for graph, geometry in variants:
            with self.subTest(geometry=geometry):
                successor = compile_executable_factory_release(
                    predecessor.curriculum, predecessor.source_bindings,
                    CurriculumProfile("fixture.successor"), self.registry, self.answers,
                    source_root=None, graph=graph, verification_seed=18, predecessor=predecessor)
                successor.verify_successor_of(predecessor)
                self.assertEqual(successor.predecessor_release_sha256, predecessor.release_sha256)
                delta = successor.transition
                self.assertEqual(delta.semantic_geometry, geometry)
                self.assertEqual(delta.previous_plan_sha256, predecessor.execution_plan.digest())
                self.assertEqual(delta.next_plan_sha256, successor.execution_plan.digest())
                self.assertEqual(delta.previous_curriculum_sha256, predecessor.curriculum.digest())
                self.assertEqual(delta.next_curriculum_sha256, predecessor.curriculum.digest())
                self.assertEqual(delta.previous_source_binding_sha256, predecessor.source_bindings.digest())
                self.assertEqual(delta.next_source_binding_sha256, predecessor.source_bindings.digest())
                self.assertEqual(delta.added_capabilities, ())
                self.assertEqual(delta.removed_capabilities, ())
                restored = ExecutableFactoryRelease.from_manifest(
                    json.loads(json.dumps(successor.manifest())), successor.release_sha256)
                restored.verify_successor_of(predecessor)
                self.assertEqual(restored.transition, delta)

    def test_v2_release_rejects_rehashed_plan_profile_mismatch(self):
        release = self.compile()
        mismatched = replace(
            release.execution_plan, profile_id="different-profile")
        candidate = replace(
            release, execution_plan=mismatched, release_sha256="0" * 64)
        candidate = replace(
            candidate, release_sha256=candidate.expected_digest())
        with self.assertRaisesRegex(
                ValueError, "FACTORY_EXECUTABLE_RELEASE_PROFILE_DRIFT"):
            candidate.verify()

    def test_v2_release_rejects_rehashed_provider_implementation_drift(self):
        release = self.compile()
        descriptor = release.source_adapters[0]
        changed = replace(descriptor, implementation_sha256="e" * 64)
        candidate = replace(
            release,
            source_adapters=(changed,),
            release_sha256="0" * 64)
        candidate = replace(
            candidate, release_sha256=candidate.expected_digest())
        with self.assertRaisesRegex(
                ValueError, "FACTORY_EXECUTABLE_RELEASE_PROVIDER_DRIFT"):
            candidate.verify()

    def test_v2_release_rejects_rehashed_verification_receipt_drift(self):
        release = self.compile()
        receipt = release.verification.capabilities[0]
        changed = replace(receipt, specimen_count=receipt.specimen_count + 1)
        verification = replace(
            release.verification,
            capabilities=(changed, *release.verification.capabilities[1:]))
        candidate = replace(
            release, verification=verification, release_sha256="0" * 64)
        candidate = replace(
            candidate, release_sha256=candidate.expected_digest())
        with self.assertRaisesRegex(
                ValueError, "FACTORY_EXECUTABLE_RELEASE_VERIFICATION_DRIFT"):
            candidate.verify()
