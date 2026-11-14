from dataclasses import replace
from types import SimpleNamespace
import unittest

from bilqis_mlx.curriculum import BOOLEAN_OPERATORS
from bilqis_mlx.factory.adapters import (
    RegisteredSourceAdapter, SourceAdapterRegistry,
)
from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.executable_release import (
    answer_heads_from_executable_release,
    compile_executable_factory_release,
)
from bilqis_mlx.factory.execution import (
    CapabilityProfile, CurriculumProfile, GradeProfile,
)
from bilqis_mlx.factory.generation import (
    _is_1324082_rollback_adapter_pair, draw_executable_release_rows,
    runtime_adapter_for_release,
)
from bilqis_mlx.factory.model import SourceAdapter
from bilqis_mlx.factory.tests.test_executable_release import _boolean_answers
from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_boolean_course


def _profile():
    return CurriculumProfile(
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


class ExecutableConsumerTests(unittest.TestCase):
    def setUp(self):
        self.course, self.registry = _synthetic_boolean_course()
        self.curriculum, self.bindings = from_legacy_course(self.course)
        self.answers = _boolean_answers()
        self.graph = {
            "tokens": [
                "fixture.padding",
                "cogal.value.false",
                "cogal.value.true",
                *(f"cogal.operator.{value}" for value in BOOLEAN_OPERATORS),
            ],
        }
        self.full = compile_executable_factory_release(
            self.curriculum, self.bindings, CurriculumProfile.full(),
            self.registry, self.answers, source_root=None, graph=self.graph,
            verification_seed=31)
        self.reduced = compile_executable_factory_release(
            self.curriculum, self.bindings, _profile(),
            self.registry, self.answers, source_root=None, graph=self.graph,
            verification_seed=31,
            predecessor=self.full)

    def test_same_generation_consumer_obeys_release_profile(self):
        full = draw_executable_release_rows(
            None, self.graph, self.full, self.registry,
            seed=37,
            capability="B.IDBOOLOPS")
        reduced = draw_executable_release_rows(
            None, self.graph, self.reduced, self.registry,
            seed=37,
            capability="B.IDBOOLOPS")

        self.assertEqual(
            {row["gold"] for row in full},
            set(BOOLEAN_OPERATORS))
        self.assertEqual(
            {row["gold"] for row in reduced},
            {"AND", "IFF"})

    def test_same_answer_consumer_obeys_release_profile(self):
        full = answer_heads_from_executable_release(
            self.full, self.graph)
        reduced = answer_heads_from_executable_release(
            self.reduced, self.graph)

        self.assertEqual(
            full["boolean_operator"]["values"],
            list(BOOLEAN_OPERATORS))
        self.assertEqual(
            reduced["boolean_operator"]["values"],
            ["AND", "IFF"])
        self.assertEqual(
            reduced["semantic_token"]["values"],
            self.graph["tokens"])

    def _registry_with_reimplemented_provider(self, draw=None):
        registered = self.registry.require(
            self.bindings.by_capability["B.IDBOOLOPS"].generator_id,
            self.bindings.by_capability["B.IDBOOLOPS"].oracle_id)
        changed = replace(
            registered.descriptor,
            implementation_sha256="f" * 64)
        return SourceAdapterRegistry((
            *(item for item in self.registry._by_generator.values()
              if item.descriptor.adapter_id != changed.adapter_id),
            RegisteredSourceAdapter(
                changed, draw or registered.draw, registered.check),
        ))

    def test_matching_specimens_do_not_substitute_an_unadmitted_provider(self):
        expected = draw_executable_release_rows(
            None, self.graph, self.reduced, self.registry,
            seed=41, capability="B.IDBOOLOPS")
        self.assertTrue(expected)
        registry = self._registry_with_reimplemented_provider()
        with self.assertRaisesRegex(
                ValueError, "FACTORY_EXECUTABLE_GENERATION_ADAPTER_DRIFT"):
            draw_executable_release_rows(
                None, self.graph, self.reduced, registry,
                seed=41, capability="B.IDBOOLOPS")

    def test_generation_refuses_provider_behavior_drift(self):
        registered = self.registry.require(
            self.bindings.by_capability["B.IDBOOLOPS"].generator_id,
            self.bindings.by_capability["B.IDBOOLOPS"].oracle_id)

        def drifted_draw(**kwargs):
            rows = list(registered.draw(**kwargs))
            rows[0] = {**rows[0], "id": "drifted-" + rows[0]["id"]}
            return tuple(rows)

        registry = self._registry_with_reimplemented_provider(drifted_draw)
        with self.assertRaisesRegex(
                ValueError, "FACTORY_EXECUTABLE_GENERATION_ADAPTER_DRIFT"):
            draw_executable_release_rows(
                None, self.graph, self.reduced, registry,
                seed=41,
                capability="B.IDBOOLOPS")

    def test_known_1324082_grade_a_provider_pair_is_resume_compatible(self):
        current = SourceAdapter(
            adapter_id="source.micro.predicates/v1",
            generator_id="bilqis_mlx.grade_a_probe.make_record",
            accepted_oracle_ids=("bilqis.mlx.grade-a-record-oracle/v2",),
            implementation_sha256=(
                "c451c3e6bf5ab538450c691d504230036b9a729ddfc67b53163c6a1f106d62a9"),
            cohort_generator_id="bilqis.mlx.grade-a-live-constructor/v1",
            cohort_releases=((
                "bilqis.mlx.grade-a-live/20261015",
                "c451c3e6bf5ab538450c691d504230036b9a729ddfc67b53163c6a1f106d62a9",
            ),),
            variation_axes=(
                "source-valid", "balanced-gold", "fresh-seed",
                "member-decoy-set-context-v1", "irrelevant-source-context-v2",
            ),
        )
        admitted = SourceAdapter(
            adapter_id="source.micro.predicates/v1",
            generator_id="bilqis_mlx.grade_a_probe.make_record",
            accepted_oracle_ids=("bilqis.mlx.grade-a-record-oracle/v2",),
            implementation_sha256=(
                "f8e5aec9398538adc633deabe9c41c485e69a96044b9b86a5f1075ce6e201778"),
            cohort_generator_id="bilqis.mlx.grade-a-live-constructor/v1",
            cohort_releases=((
                "bilqis.mlx.grade-a-live/20261015",
                "f8e5aec9398538adc633deabe9c41c485e69a96044b9b86a5f1075ce6e201778",
            ),),
            variation_axes=(
                "source-valid", "balanced-gold", "fresh-seed",
                "member-decoy-set-context-v1", "irrelevant-source-context-v2",
                "generalization-only-source-context-v3",
            ),
        )

        self.assertTrue(_is_1324082_rollback_adapter_pair(admitted, current))
        self.assertFalse(_is_1324082_rollback_adapter_pair(current, admitted))
        self.assertFalse(_is_1324082_rollback_adapter_pair(
            replace(admitted, implementation_sha256="f" * 64), current))

    def test_historical_provider_chains_reach_current_runtime_adapters(self):
        from bilqis_mlx.source_adapters.school import C_ORACLE, live_source_registry

        registry = live_source_registry()
        grade_a = registry.resolve_owner("bilqis_mlx.grade_a_probe.make_record")
        numeric = registry.require(
            "bilqis_mlx.numeric_curriculum.draw_numeric", C_ORACLE)
        cases = (
            (
                grade_a,
                replace(
                    grade_a.descriptor,
                    implementation_sha256=(
                        "f8e5aec9398538adc633deabe9c41c485e69a96044b9b86a5f1075ce6e201778"),
                    cohort_releases=((
                        grade_a.descriptor.cohort_releases[0][0],
                        "f8e5aec9398538adc633deabe9c41c485e69a96044b9b86a5f1075ce6e201778",
                    ),),
                    variation_axes=(
                        *grade_a.descriptor.variation_axes,
                        "generalization-only-source-context-v3",
                    ),
                ),
            ),
            (
                numeric,
                replace(
                    numeric.descriptor,
                    implementation_sha256=(
                        "a52f346478852775053f07a79342e5a9e9266bc64a2df6fe953d6a64881c8b7d"),
                ),
            ),
        )
        for registered, admitted in cases:
            with self.subTest(adapter=admitted.adapter_id):
                capability_id = "fixture." + admitted.adapter_id
                release = SimpleNamespace(
                    source_bindings=SimpleNamespace(by_capability={
                        capability_id: SimpleNamespace(
                            generator_id=admitted.generator_id,
                            oracle_id=admitted.accepted_oracle_ids[0],
                        ),
                    }),
                    source_adapters=(admitted,),
                )
                execution = SimpleNamespace(
                    capability_id=capability_id,
                    provider_id=admitted.adapter_id,
                )
                self.assertIs(
                    runtime_adapter_for_release(
                        None, {}, release, registry, execution),
                    registered,
                )


if __name__ == "__main__":
    unittest.main()
