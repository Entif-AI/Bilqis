from dataclasses import replace
import hashlib
import json
import unittest

from bilqis_mlx.curriculum import AnswerFamily, BINARY, Capability, Course, Grade
from bilqis_mlx.factory.adapters import RegisteredSourceAdapter, SourceAdapterRegistry
from bilqis_mlx.factory.model import AssessmentClass, FactoryRelease, SourceAdapter
from bilqis_mlx.factory.release import compile_factory_release
from bilqis_mlx.factory.tests.support import synthetic_release_inputs
from bilqis_mlx.compatibility.factory_release_v1 import decode_sealed_factory_release_v1


class FactoryReleaseTests(unittest.TestCase):
    def setUp(self):
        self.course, self.registry = synthetic_release_inputs()

    def test_release_binds_semantics_adapters_and_three_assessment_classes(self):
        release = compile_factory_release(self.course, self.registry)
        release.verify()
        self.assertEqual(
            release.release_sha256,
            "8337cedd486511409d1476b9fe0d63e5715c4b40251b5977540ddd23788801a8")
        self.assertEqual(tuple(item.capability_id for item in release.capabilities),
                         tuple(cap.id for cap in self.course.grades[0].capabilities))
        self.assertEqual({plan.assessment_class for plan in release.assessments},
                         set(AssessmentClass))
        self.assertEqual(
            tuple(item.capability_id for item in release.construction_programs),
            tuple(cap.id for cap in self.course.grades[0].capabilities))
        self.assertTrue(all(plan.require_fresh_seed for plan in release.coverage_plans))
        self.assertTrue(all(item.source_grounded for item in release.teaching_options))
        generalization = [plan for plan in release.assessments
                          if plan.assessment_class is AssessmentClass.GENERALIZATION][0]
        self.assertTrue(generalization.fresh_on_decision)
        self.assertTrue(generalization.burn_after_failure)
        promotion = [plan for plan in release.assessments
                     if plan.assessment_class is AssessmentClass.PROMOTION][0]
        self.assertTrue(promotion.reusable_after_failure)
        self.assertFalse(promotion.fresh_on_decision)

    def test_missing_source_adapter_blocks_release(self):
        with self.assertRaisesRegex(ValueError, "FACTORY_SOURCE_ADAPTER_MISSING"):
            compile_factory_release(self.course, SourceAdapterRegistry())

    def test_oracle_mismatch_blocks_release(self):
        wrong = SourceAdapter("fixture.adapter/v2", "fixture.generator/v1",
                              ("other.oracle/v1",), "e" * 64)
        registry = SourceAdapterRegistry((RegisteredSourceAdapter(
            wrong, lambda **_: (), lambda row, **_: False),))
        with self.assertRaisesRegex(ValueError, "FACTORY_SOURCE_ORACLE_NOT_ADAPTER_OWNED"):
            compile_factory_release(self.course, registry)

    def test_source_adapters_cannot_omit_or_repeat_generalization_axes(self):
        for axes in ((), ("fresh-seed", "fresh-seed"), ("",), (1,)):
            with self.subTest(axes=axes), self.assertRaisesRegex(ValueError, "VARIATION_AXES"):
                replace(self.registry.descriptors_for(self.course)[0], variation_axes=axes)

    def test_release_digest_detects_tampering(self):
        release = compile_factory_release(self.course, self.registry)
        tampered = replace(release, release_sha256="f" * 64)
        with self.assertRaisesRegex(ValueError, "FACTORY_RELEASE_CONTENT_DRIFT"):
            tampered.verify()

    def test_release_roundtrips_without_reconstructing_a_grade_provider(self):
        release = compile_factory_release(self.course, self.registry)
        payload = json.loads(json.dumps(release.manifest()))
        restored = FactoryRelease.from_manifest(payload, release.release_sha256)
        self.assertEqual(restored, release)
        payload["course"]["grades"][0]["capabilities"][0]["prerequisites"] = ["unknown"]
        with self.assertRaises(ValueError):
            FactoryRelease.from_manifest(payload, release.release_sha256)

    def test_sealed_v1_manifest_survives_later_optional_adapter_fields(self):
        release = compile_factory_release(self.course, self.registry)
        payload = json.loads(json.dumps(release.manifest()))
        for adapter in payload["source_adapters"]:
            adapter.pop("profile_dimensions", None)
        import hashlib
        digest = hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False).encode()).hexdigest()

        restored = decode_sealed_factory_release_v1(payload, digest)

        self.assertEqual(restored.course, release.course)
        self.assertEqual(
            restored.semantic_release.course_sha256,
            release.semantic_release.course_sha256)
        self.assertTrue(all(
            adapter.profile_dimensions == ()
            for adapter in restored.source_adapters))

    def test_prior_v1_release_without_added_adapter_field_preserves_original_digest(self):
        release = compile_factory_release(self.course, self.registry)
        payload = json.loads(json.dumps(release.manifest()))
        for adapter in payload["source_adapters"]:
            self.assertEqual(adapter.pop("profile_dimensions"), [])
        prior_digest = hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False).encode("utf-8")).hexdigest()
        restored = FactoryRelease.from_manifest(payload, prior_digest)
        self.assertEqual(restored.course, release.course)
        self.assertEqual(restored.expected_digest(), prior_digest)
        self.assertEqual(json.loads(json.dumps(restored.manifest())), payload)
        restored.verify()
        payload["course"]["grades"][0]["capabilities"][0]["prerequisites"] = ["fake"]
        with self.assertRaises(ValueError):
            FactoryRelease.from_manifest(payload, prior_digest)

    def test_rehashed_incomplete_or_inconsistent_release_is_rejected(self):
        release = compile_factory_release(self.course, self.registry)
        mutations = (
            {"assessments": ()},
            {"assessments": (replace(release.assessments[0],
                                     fresh_on_decision=False), *release.assessments[1:])},
            {"grades": (replace(release.grades[0], teaching_stages=(("A.C0",),)),)},
            {"semantic_release": replace(release.semantic_release, ast_sha256="e" * 64)},
            {"capabilities": (replace(release.capabilities[0], prerequisites=("missing",)),
                              *release.capabilities[1:])},
            {"construction_programs": (replace(release.construction_programs[0],
                                                generator_id="other.generator"),
                                        *release.construction_programs[1:])},
            {"coverage_plans": (replace(release.coverage_plans[0], minimum_specimens=0),
                                 *release.coverage_plans[1:])},
            {"teaching_options": (replace(release.teaching_options[0], source_grounded=False),
                                   *release.teaching_options[1:])},
        )
        for changes in mutations:
            with self.subTest(changes=tuple(changes)):
                candidate = replace(release, **changes)
                candidate = replace(candidate, release_sha256=candidate.expected_digest())
                with self.assertRaisesRegex(ValueError, "FACTORY_RELEASE_"):
                    candidate.verify()


if __name__ == "__main__":
    unittest.main()
