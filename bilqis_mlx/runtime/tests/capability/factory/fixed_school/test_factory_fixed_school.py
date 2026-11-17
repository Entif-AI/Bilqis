"""C16.2b C05-owned BAMF fixed-school materialization and public-route contract."""
from __future__ import annotations

from unittest.mock import patch

from bilqis_mlx.runtime.tests.bamf_first_student._bamf_first_student_support import BamfFirstStudentCase
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch


class BamfFactoryFixedSchoolTests(BamfFirstStudentCase):
    def test_c05_materializes_bamf_fixed_school_without_legacy_state(self):
        target = self.root / "c05-native-fixed-school"
        self.preflight(target)
        from bilqis_mlx.factory.tests.test_executable_release import _answers
        from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_registry
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        from bilqis_mlx.runtime.bamf_bundle.admission import (
            bind_accepted_execution_cache,
            load_accepted_generation,
        )
        import bilqis_mlx.runtime.factory_retention_owner as retention_owner

        with patch(
                "bilqis_mlx.source_adapters.school.live_source_registry",
                return_value=_synthetic_registry()), patch(
                "bilqis_mlx.factory.live_answers.live_answer_registry",
                return_value=_answers()), shape_patch():
            context = AcceptedRuntimeHost(target).source_context(
                graph=self.graph, source_root=None)
            parent = load_accepted_generation(target)
            cache = bind_accepted_execution_cache(target)
        self.assertFalse((target / "state.json").exists())

        captured = {}
        def instruments(_context, _candidate, _artifact, rows, *, seed):
            captured["rows"] = tuple(rows)
            captured["seed"] = seed
            return ()

        with patch.object(retention_owner, "_instruments", side_effect=instruments), \
                shape_patch():
            retention_owner._fixed_school_instruments(
                context, parent, "artifact", target, self.release,
                parent=parent, cache=cache)

        receipt_path = (
            target / "c05-fixed-school" / f"{parent.run_identity.digest}.json")
        self.assertTrue(receipt_path.is_file())
        receipt = __import__("json").loads(receipt_path.read_text())
        self.assertEqual(receipt["run_id"], parent.run_id)
        self.assertEqual(
            receipt["source_identity_sha256"],
            parent.run_identity.initial_source_identity)
        self.assertEqual(
            receipt["foundation_parent_manifest_sha256"],
            cache.accepted_manifest_sha256)
        self.assertNotEqual(
            receipt["source_identity_sha256"],
            receipt["foundation_parent_manifest_sha256"])
        self.assertEqual(
            tuple(receipt["capabilities"]),
            tuple(item.capability_id
                  for item in self.release.execution_plan.capabilities))
        self.assertEqual(receipt["seed"], receipt["cohort_seed"])
        from bilqis_mlx.factory.assessment import assessment_scope_contract
        from bilqis_mlx.semantics.domains import contract_digest
        capabilities = tuple(receipt["capabilities"])
        contract = assessment_scope_contract(self.release, capabilities)
        expected_seed = int(contract_digest({
            "schema": "bilqis.mlx.c05-bamf-fixed-school-seed/v1",
            "run_identity": parent.run_identity.digest,
            "factory_release": self.release.release_sha256,
            "source_identity": parent.run_identity.initial_source_identity,
            "semantic_catalog": self.release.semantic_catalog_sha256,
            "capabilities": capabilities,
            "rubric": contract.rubric_sha256,
            "source": contract.source_sha256,
        })[:16], 16)
        self.assertEqual(receipt["seed"], expected_seed)
        cohort = __import__("json").loads(
            (target / receipt["cohort_file"]).read_text())
        self.assertEqual(
            cohort["source_manifest_sha256"],
            parent.run_identity.initial_source_identity)
        self.assertNotEqual(
            cohort["source_manifest_sha256"],
            cache.accepted_manifest_sha256)
        self.assertTrue(captured["rows"])
        self.assertEqual(captured["seed"], receipt["seed"])
        self.assertFalse((target / "state.json").exists())

    def test_c05_bamf_fixed_school_cold_reuses_without_source_redraw_or_state_fallback(self):
        target = self.root / "c05-native-fixed-school-cold"
        self.preflight(target)
        from bilqis_mlx.factory.tests.test_executable_release import _answers
        from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_registry
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        from bilqis_mlx.runtime.bamf_bundle.admission import (
            bind_accepted_execution_cache,
            load_accepted_generation,
        )
        import bilqis_mlx.runtime.factory_fixed_school as fixed_owner

        with patch(
                "bilqis_mlx.source_adapters.school.live_source_registry",
                return_value=_synthetic_registry()), patch(
                "bilqis_mlx.factory.live_answers.live_answer_registry",
                return_value=_answers()), shape_patch():
            context = AcceptedRuntimeHost(target).source_context(
                graph=self.graph, source_root=None)
            parent = load_accepted_generation(target)
            cache = bind_accepted_execution_cache(target)
            first = fixed_owner._bamf_fixed_school_cohort(
                context, target, expected_parent_manifest_sha256=cache.accepted_manifest_sha256)

        # A stray legacy receipt is never authority for a BAMF lineage.
        (target / "state.json").write_text('{"factory_release_sha256":"bad"}\n')
        with patch.object(
                fixed_owner,
                "_draw_executable_scope_cohort",
                side_effect=AssertionError("cold C05 redrew mutable source")), shape_patch():
            second = fixed_owner._bamf_fixed_school_cohort(
                context, target, expected_parent_manifest_sha256=cache.accepted_manifest_sha256)
        self.assertEqual(second, first)

    def test_c05_bamf_fixed_school_recovers_interrupted_projection_without_redraw(self):
        target = self.root / "c05-native-fixed-school-interrupted-projection"
        self.preflight(target)
        from bilqis_mlx.factory.tests.test_executable_release import _answers
        from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_registry
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        from bilqis_mlx.runtime.bamf_bundle.admission import bind_accepted_execution_cache
        import bilqis_mlx.runtime.factory_fixed_school as fixed_owner

        with patch(
                "bilqis_mlx.source_adapters.school.live_source_registry",
                return_value=_synthetic_registry()), patch(
                "bilqis_mlx.factory.live_answers.live_answer_registry",
                return_value=_answers()), shape_patch():
            context = AcceptedRuntimeHost(target).source_context(
                graph=self.graph, source_root=None)
            cache = bind_accepted_execution_cache(target)
            with patch.object(
                    fixed_owner, "require_projection_json",
                    side_effect=RuntimeError("simulated crash after immutable trust publish")):
                with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                    fixed_owner._bamf_fixed_school_cohort(
                        context, target,
                        expected_parent_manifest_sha256=cache.accepted_manifest_sha256)

        with patch.object(
                fixed_owner, "_draw_executable_scope_cohort",
                side_effect=AssertionError("retry redrew mutable source")), shape_patch():
            recovered = fixed_owner._bamf_fixed_school_cohort(
                context, target,
                expected_parent_manifest_sha256=cache.accepted_manifest_sha256)
        self.assertTrue(recovered.rows)



if __name__ == "__main__":
    import unittest
    unittest.main()
