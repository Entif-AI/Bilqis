"""Provider-declared dimension progression stays Factory-owned and grade-neutral."""
from dataclasses import replace
import json
import unittest

from bilqis_mlx.factory.adapters import SourceAdapterRegistry
from bilqis_mlx.factory.executable_release import (
    ExecutableFactoryRelease, compile_executable_factory_release)
from bilqis_mlx.factory.execution import (
    CapabilityProfile, CurriculumProfile, GradeProfile)
from bilqis_mlx.factory.model import ProviderDimensionPolicy
from bilqis_mlx.factory.provider_dimensions import (
    compile_provider_dimension_successor, provider_dimension_state)
from bilqis_mlx.factory.tests.executable_release.support import ReleaseTestSupport


class ProviderDimensionProgressionTests(ReleaseTestSupport):
    def setUp(self):
        super().setUp()
        registered = self.registry.require(
            "fixture.z-generator/v1", "fixture.z-oracle/v1")
        descriptor = replace(
            registered.descriptor,
            profile_dimensions=(("intensity", ("low", "mid", "high")),))
        policy = ProviderDimensionPolicy(
            provider_id=descriptor.adapter_id,
            dimension_id="lesson-intensity",
            parameter_name="intensity",
            progression_values=("low", "mid", "high"),
            selection_mode="CANONICAL_PREFIX",
            step_mode="ADJACENT",
            advance_trigger="DEVELOPMENTAL_BOUNDARY",
            terminal_value="high",
            source_constraint="SAME_PROVIDER_BINDING",
            admission_constraint="EXISTING_CAPABILITY_PROFILE",
            telemetry_projection="INTENSITY",
            changes_source_projection=True,
        )
        self.registry = SourceAdapterRegistry((replace(
            registered, descriptor=descriptor, dimension_policies=(policy,)),))
        capabilities = tuple(
            capability.capability_id for capability in self.curriculum.grades[0].capabilities)
        self.profile = CurriculumProfile(
            "fixture/intensity/low",
            grades=(GradeProfile("Z", capabilities=tuple(
                CapabilityProfile(
                    capability,
                    provider_parameters=(("intensity", ("low",)),))
                for capability in capabilities)),))

    def compile_profile(self):
        return compile_executable_factory_release(
            self.curriculum, self.bindings, self.profile,
            self.registry, self.answers, source_root=None, graph=self.graph,
            verification_seed=41)

    def test_future_provider_advances_one_declared_step_to_terminal(self):
        release = self.compile_profile()
        first = provider_dimension_state(release, "lesson-intensity")
        self.assertEqual((first.value, first.terminal), ("low", False))
        policy = release.provider_dimension_policies[0]
        self.assertEqual((
            policy.step_mode, policy.terminal_value, policy.source_constraint,
            policy.admission_constraint,
        ), (
            "ADJACENT", "high", "SAME_PROVIDER_BINDING",
            "EXISTING_CAPABILITY_PROFILE",
        ))

        middle = compile_provider_dimension_successor(
            release, "lesson-intensity", self.registry, self.answers,
            source_root=None, graph=self.graph, verification_seed=42)
        self.assertEqual((middle.previous.value, middle.current.value), ("low", "mid"))
        self.assertFalse(middle.current.terminal)
        self.assertEqual(middle.release.transition.projection_changes, ("source",))
        self.assertEqual(middle.release.transition.added_capabilities, ())

        terminal = compile_provider_dimension_successor(
            middle.release, "lesson-intensity", self.registry, self.answers,
            source_root=None, graph=self.graph, verification_seed=43)
        self.assertEqual((terminal.current.value, terminal.current.terminal), ("high", True))
        self.assertIsNone(compile_provider_dimension_successor(
            terminal.release, "lesson-intensity", self.registry, self.answers,
            source_root=None, graph=self.graph, verification_seed=44))

    def test_policy_and_exact_scope_roundtrip_in_immutable_release(self):
        transition = compile_provider_dimension_successor(
            self.compile_profile(), "lesson-intensity", self.registry, self.answers,
            source_root=None, graph=self.graph, verification_seed=42)
        payload = json.loads(json.dumps(transition.release.manifest()))
        restored = ExecutableFactoryRelease.from_manifest(
            payload, transition.release.release_sha256)

        state = provider_dimension_state(restored, "lesson-intensity")
        self.assertEqual((state.value, state.telemetry_projection), ("mid", "INTENSITY"))
        self.assertEqual(restored.provider_dimension_policies,
                         transition.release.provider_dimension_policies)


if __name__ == "__main__":
    unittest.main()
