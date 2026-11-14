"""Exact provider compatibility across admitted school-owner migrations."""
from dataclasses import replace
from types import SimpleNamespace
import unittest

from bilqis_mlx.compatibility.source_adapter_resume import (
    SUPPORTED_SOURCE_PROVIDER_RESUME_EDGES,
    predecessor_compatible_source_registry,
    resume_adapter_compatible,
)
from bilqis_mlx.source_adapters.school import C_ORACLE, live_source_registry


class ProviderCompatibilityTests(unittest.TestCase):
    def test_supported_resume_matrix_is_explicit_one_way_and_targets_live_code(self):
        registry = live_source_registry()
        current_by_adapter = {
            item.descriptor.adapter_id: item.descriptor
            for item in registry._by_generator.values()
        }
        self.assertEqual(
            tuple(edge.edge_id for edge in SUPPORTED_SOURCE_PROVIDER_RESUME_EDGES),
            (
                "grade-a-1324082-to-current",
                "grade-a-accepted-to-current",
                "boolean-identification-accepted-to-current",
                "numeric-accepted-to-current",
                "numeric-modular-to-current",
                "numeric-current-adr106-cohort-repair",
            ),
        )
        self.assertEqual(
            len({(edge.adapter_id, edge.admitted_implementation_sha256,
                 edge.current_implementation_sha256, edge.rule)
                 for edge in SUPPORTED_SOURCE_PROVIDER_RESUME_EDGES}),
            len(SUPPORTED_SOURCE_PROVIDER_RESUME_EDGES),
        )
        for edge in SUPPORTED_SOURCE_PROVIDER_RESUME_EDGES:
            with self.subTest(edge=edge.edge_id):
                current = current_by_adapter[edge.adapter_id]
                self.assertEqual(
                    edge.current_implementation_sha256,
                    current.implementation_sha256,
                )

    def test_exact_accepted_provider_lineage_resumes_on_current_implementations(self):
        registry = live_source_registry()
        cases = (
            (
                "bilqis_mlx.grade_a_probe.make_record",
                "c451c3e6bf5ab538450c691d504230036b9a729ddfc67b53163c6a1f106d62a9",
                True,
            ),
            (
                "bilqis.mlx.grade-b-idboolops-constructor/v1",
                "6399dae052a289d46063df0e897e14f1392e2f1b99e90c2ae791fda9a8246743",
                True,
            ),
            (
                "bilqis_mlx.numeric_curriculum.draw_numeric",
                "2758cf678e9d2a45f3f5a1b5edd85d5ae513e54506c0d98853b9402b91572754",
                False,
            ),
        )
        for generator, admitted_sha256, bind_cohort in cases:
            with self.subTest(generator=generator):
                current = registry.resolve_owner(generator).descriptor
                cohort_releases = current.cohort_releases
                if bind_cohort:
                    self.assertEqual(len(cohort_releases), 1)
                    cohort_releases = ((cohort_releases[0][0], admitted_sha256),)
                admitted = replace(
                    current,
                    implementation_sha256=admitted_sha256,
                    cohort_releases=cohort_releases,
                )
                self.assertTrue(resume_adapter_compatible(admitted, current))
                self.assertFalse(resume_adapter_compatible(current, admitted))
                self.assertFalse(resume_adapter_compatible(
                    replace(admitted, generator_id=admitted.generator_id + ".drift"),
                    current,
                ))

    def test_successor_staging_preserves_compatible_predecessor_descriptor(self):
        current_registry = live_source_registry()
        registered = current_registry.resolve_owner(
            "bilqis_mlx.grade_a_probe.make_record")
        admitted_sha256 = (
            "c451c3e6bf5ab538450c691d504230036b9a729ddfc67b53163c6a1f106d62a9")
        admitted = replace(
            registered.descriptor,
            implementation_sha256=admitted_sha256,
            cohort_releases=((
                registered.descriptor.cohort_releases[0][0], admitted_sha256),),
        )
        staging_registry = predecessor_compatible_source_registry(
            SimpleNamespace(source_adapters=(admitted,)), current_registry)

        rebound = staging_registry.resolve_owner(admitted.generator_id)
        self.assertEqual(rebound.descriptor, admitted)
        self.assertIs(rebound.draw, registered.draw)
        self.assertIs(rebound.check, registered.check)

    def test_exact_prior_provider_can_resume_without_weakening_descriptor_checks(self):
        current = live_source_registry().require(
            "bilqis_mlx.numeric_curriculum.draw_numeric", C_ORACLE).descriptor
        prior = replace(current, implementation_sha256=
            "2758cf678e9d2a45f3f5a1b5edd85d5ae513e54506c0d98853b9402b91572754")
        self.assertTrue(resume_adapter_compatible(prior, current))
        self.assertFalse(resume_adapter_compatible(current, prior))
        for changed in (
                replace(current, implementation_sha256="f" * 64),
                replace(current, profile_dimensions=(("numbers", ("0",)),)),
                replace(current, accepted_oracle_ids=("foreign-oracle",)),
                replace(current, cohort_releases=((
                    current.cohort_releases[-1][0], "f" * 64),))):
            with self.subTest(changed=changed):
                self.assertFalse(resume_adapter_compatible(prior, changed))

    def test_intermediate_numeric_provider_resumes_on_current_implementation(self):
        registry = live_source_registry()
        registered = registry.require(
            "bilqis_mlx.numeric_curriculum.draw_numeric", C_ORACLE)
        current = registered.descriptor
        modular_sha256 = (
            "a52f346478852775053f07a79342e5a9e9266bc64a2df6fe953d6a64881c8b7d")
        prior_staircase_sha256 = (
            "ec3b5338fc1604a6250a847ee99eae09956b5a5bb269a63f3ac8372205133e74")
        for cohort_releases in (
            current.cohort_releases,
            tuple(
                (release, prior_staircase_sha256 if
                 release == "bilqis.mlx.numeric-staircase/20261017-v1" else digest)
                for release, digest in current.cohort_releases
            ),
        ):
            with self.subTest(cohort_releases=cohort_releases):
                admitted = replace(
                    current,
                    implementation_sha256=modular_sha256,
                    cohort_releases=cohort_releases,
                )
                self.assertTrue(resume_adapter_compatible(admitted, current))
                self.assertFalse(resume_adapter_compatible(current, admitted))
                staging = predecessor_compatible_source_registry(
                    SimpleNamespace(source_adapters=(admitted,)), registry)
                rebound = staging.require(
                    "bilqis_mlx.numeric_curriculum.draw_numeric", C_ORACLE)
                self.assertEqual(rebound.descriptor, admitted)
                self.assertIs(rebound.draw, registered.draw)

    def test_grade_a_1324082_provider_resumes_through_current_implementation(self):
        registry = live_source_registry()
        registered = registry.resolve_owner(
            "bilqis_mlx.grade_a_probe.make_record")
        current = registered.descriptor
        removed_sha256 = (
            "f8e5aec9398538adc633deabe9c41c485e69a96044b9b86a5f1075ce6e201778")
        admitted = replace(
            current,
            implementation_sha256=removed_sha256,
            cohort_releases=((current.cohort_releases[0][0], removed_sha256),),
            variation_axes=(
                *current.variation_axes, "generalization-only-source-context-v3"),
        )
        self.assertTrue(resume_adapter_compatible(admitted, current))
        self.assertFalse(resume_adapter_compatible(current, admitted))
        staging = predecessor_compatible_source_registry(
            SimpleNamespace(source_adapters=(admitted,)), registry)
        rebound = staging.resolve_owner(admitted.generator_id)
        self.assertEqual(rebound.descriptor, admitted)
        self.assertIs(rebound.draw, registered.draw)
