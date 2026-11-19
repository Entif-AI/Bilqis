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
    def test_seal_rejects_a_source_true_unintroduced_constituent(self):
        binding = self.bindings.bindings[0]
        adapter = self.registry.require(binding.generator_id, binding.oracle_id)
        self.registry = SourceAdapterRegistry((replace(
            adapter, semantic_footprint=lambda row: ("future.root",)),))
        with self.assertRaisesRegex(
                ValueError, "FACTORY_INSTRUCTIONAL_CONSTITUENT_CLOSURE:Z.C0:future.root"):
            self.compile()

    def test_untyped_source_footprint_fails_closed(self):
        adapter = self.registry.require("fixture.z-generator/v1", "fixture.z-oracle/v1")
        self.registry = SourceAdapterRegistry((replace(adapter, semantic_footprint=lambda row: "z.op.0"),))
        with self.assertRaisesRegex(ValueError, "CLOSURE:Z.C0:SOURCE_FOOTPRINT_INVALID"):
            self.compile()

    def test_normal_v2_draw_checks_new_rows_after_safe_sealing(self):
        from bilqis_mlx.factory.generation import draw_executable_release_rows
        binding = self.bindings.bindings[0]
        adapter = self.registry.require(binding.generator_id, binding.oracle_id)
        self.registry = SourceAdapterRegistry((replace(adapter, semantic_footprint=lambda row:
            ("z.op." + row["capability"].partition(".C")[2],)),))
        release = self.compile()
        changed = SourceAdapterRegistry((replace(
            adapter, semantic_footprint=lambda row: ("future.root",)),))
        with self.assertRaisesRegex(
                ValueError, "FACTORY_INSTRUCTIONAL_CONSTITUENT_CLOSURE:Z.C0:future.root"):
            draw_executable_release_rows(None, self.graph, release, changed,
                                         seed=99, capability="Z.C0", each=4)

    def test_instructional_closure_uses_only_target_prior_grade_and_earlier_stage(self):
        original_grade = self.curriculum.grades[0]
        prior_cap = replace(original_grade.capabilities[0], capability_id="Y.C0",
                            taught_roots=("prior.root",), examined_roots=("prior.root",))
        prior = replace(original_grade, grade_id="Y", capabilities=(prior_cap,),
                        exam_item_counts=(("Y.C0", 4),))
        current = replace(original_grade, teaching_stages=(
            ("Z.C0",), tuple(cap.capability_id for cap in original_grade.capabilities[1:])))
        self.curriculum = replace(self.curriculum, grades=(prior, current))
        self.bindings = replace(self.bindings, bindings=(
            replace(self.bindings.bindings[0], capability_id="Y.C0"), *self.bindings.bindings))
        adapter = self.registry.require(self.bindings.bindings[0].generator_id,
                                        self.bindings.bindings[0].oracle_id)
        def roots(row):
            cap = row["capability"]
            if cap == "Y.C0":
                return ("prior.root",)
            if cap == "Z.C1":
                return ("prior.root", "z.op.0", "z.op.1")
            return ("z.op." + cap.partition(".C")[2],)
        self.registry = SourceAdapterRegistry((replace(adapter, semantic_footprint=roots),))
        self.compile().verify()
        for target in ("Z.C0", "Z.C2"):
            self.registry = SourceAdapterRegistry((replace(adapter, semantic_footprint=lambda row:
                ("z.op.1",) if row["capability"] == target else roots(row)),))
            with self.subTest(target=target), self.assertRaisesRegex(
                    ValueError, "CLOSURE:" + target + ":z.op.1"):
                self.compile()
        self.registry = SourceAdapterRegistry((replace(adapter, semantic_footprint=roots),))
        with self.assertRaisesRegex(ValueError, "CLOSURE:Z.C1:prior.root"):
            compile_executable_factory_release(
                self.curriculum, self.bindings, CurriculumProfile("no-prior", (
                    GradeProfile("Y", enabled_capabilities=()),)), self.registry, self.answers,
                source_root=None, graph=self.graph, verification_seed=17)

    def test_semantic_footprint_is_runtime_only_and_preserves_release_identity(self):
        from unittest.mock import Mock
        baseline = self.compile()
        payload = json.dumps(baseline.manifest(), sort_keys=True)
        binding = self.bindings.bindings[0]
        original = self.registry.require(binding.generator_id, binding.oracle_id)
        callback = Mock(side_effect=lambda row:
                        ("z.op." + row["capability"].partition(".C")[2],))
        registered = replace(original, semantic_footprint=callback)
        self.registry = SourceAdapterRegistry((registered,))
        resolved = self.registry.require(binding.generator_id, binding.oracle_id)
        row = {"query": {"kind": "fixture"}, "capability": "Z.C0"}
        self.assertEqual(resolved.semantic_footprint(row), ("z.op.0",))
        callback.assert_called_once_with(row)
        callback.reset_mock()
        compiled = self.compile()
        self.assertEqual(json.dumps(compiled.manifest(), sort_keys=True), payload)
        self.assertEqual(compiled.release_sha256, baseline.release_sha256)
        restored = ExecutableFactoryRelease.from_manifest(
            json.loads(payload), baseline.release_sha256)
        self.assertEqual(restored, compiled)
        self.assertEqual(registered.descriptor, original.descriptor)
        self.assertEqual(callback.call_count, 24)

    def test_historical_registration_reads_but_v2_requires_a_footprint(self):
        baseline = self.compile()
        binding = self.bindings.bindings[0]
        adapter = replace(self.registry.require(binding.generator_id, binding.oracle_id),
                          semantic_footprint=None)
        self.registry = SourceAdapterRegistry((adapter,))
        self.assertIsNone(adapter.semantic_footprint)
        self.assertEqual(ExecutableFactoryRelease.from_manifest(
            baseline.manifest(), baseline.release_sha256), baseline)
        with self.assertRaisesRegex(ValueError, "CLOSURE:Z.C0:SOURCE_FOOTPRINT_UNAVAILABLE"):
            self.compile()
        self.registry.descriptors_for(self.course)
        for invalid in (False, "callback", (), {}):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(
                    ValueError, "FACTORY_SOURCE_CONSTRUCTOR_AND_CHECKER_REQUIRED"):
                SourceAdapterRegistry((replace(adapter, semantic_footprint=invalid),))

    def test_full_graph_binding_rejects_same_catalog_substitution(self):
        from bilqis_mlx.factory.executable_release import _digest

        self.graph["nodes"] = [{"meaning": "é", "arity": 1}]
        release = self.compile()
        self.assertEqual(release.semantic_graph_sha256, _digest(self.graph))
        restored = ExecutableFactoryRelease.from_manifest(
            json.loads(json.dumps(release.manifest())), release.release_sha256)
        reordered = dict(reversed(tuple(self.graph.items())))
        restored.verify_semantic_catalog(reordered)
        changed = {**self.graph, "nodes": [{"meaning": "é", "arity": 2}]}
        with self.assertRaisesRegex(ValueError, "SEMANTIC_GRAPH_DRIFT"):
            restored.verify_semantic_catalog(changed)
        with self.assertRaisesRegex(ValueError, "SEMANTIC_GRAPH_INVALID"):
            replace(release, semantic_graph_sha256="invalid")

    def test_historical_v2_manifest_preserves_exact_hash_without_graph_field(self):
        from bilqis_mlx.factory.executable_release import _digest

        payload = json.loads(json.dumps(self.compile().manifest()))
        payload.pop("foundation_capability_ids", None)
        payload.pop("semantic_graph_sha256", None)
        payload.pop("provider_dimension_policies", None)
        historical_sha = "c37d62403c00e87b0cdd648764f5967eee9a58860941ddca694371f2544cf956"
        self.assertEqual(_digest(payload), historical_sha)
        restored = ExecutableFactoryRelease.from_manifest(payload, historical_sha)
        self.assertIsNone(restored.semantic_graph_sha256)
        self.assertIsNone(restored.foundation_capability_ids)
        with self.assertRaisesRegex(
                ValueError,
                "FACTORY_EXECUTABLE_RELEASE_FOUNDATION_CAPABILITY_IDS_REQUIRED"):
            restored.require_foundation_capability_ids()
        self.assertNotIn("foundation_capability_ids", restored.manifest())
        self.assertNotIn("semantic_graph_sha256", restored.manifest())
        self.assertNotIn("provider_dimension_policies", restored.manifest())
        self.assertEqual(json.loads(json.dumps(restored.manifest())), payload)
        self.assertEqual(restored.expected_digest(), historical_sha)

    def test_compilers_reject_deleted_legacy_course_keyword(self):
        from bilqis_mlx.factory.executable_release import compile_successor_profile_release

        release = self.compile()
        with self.assertRaisesRegex(TypeError, "legacy_course"):
            compile_executable_factory_release(
                self.curriculum, self.bindings, CurriculumProfile.full(),
                self.registry, self.answers, source_root=None, graph=self.graph,
                verification_seed=17, legacy_course=self.course)
        with self.assertRaisesRegex(TypeError, "legacy_course"):
            compile_successor_profile_release(
                release, CurriculumProfile.full(), self.registry, self.answers,
                source_root=None, graph=self.graph, verification_seed=17,
                legacy_course=self.course)
        successor = compile_successor_profile_release(
            release, CurriculumProfile.full(), self.registry, self.answers,
            source_root=None, graph=self.graph, verification_seed=20261019)
        self.assertEqual(successor.verification, release.verification)
        self.assertEqual(successor.predecessor_release_sha256, release.release_sha256)
