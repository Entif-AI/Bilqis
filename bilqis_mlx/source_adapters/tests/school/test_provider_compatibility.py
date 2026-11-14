"""Exact provider compatibility across admitted school-owner migrations."""
from dataclasses import replace
from types import SimpleNamespace
import unittest

from bilqis_mlx.compatibility.source_adapter_resume import (
    predecessor_compatible_source_registry,
    resume_adapter_compatible,
)
from bilqis_mlx.source_adapters.school import C_ORACLE, live_source_registry


class ProviderCompatibilityTests(unittest.TestCase):
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
                replace(current, accepted_oracle_ids=("foreign-oracle",))):
            with self.subTest(changed=changed):
                self.assertFalse(resume_adapter_compatible(prior, changed))
