"""C16.2b C05-owned BAMF fixed-school materialization and public-route contract."""
from __future__ import annotations

import mlx.core as mx
import numpy as np
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

    def test_c05_reuses_founding_school_after_profile_successor(self):
        from dataclasses import replace
        from bilqis_mlx.errors.model import BilqisError
        from bilqis_mlx.factory.executable_release import compile_successor_profile_release
        from bilqis_mlx.factory.execution import CurriculumProfile, GradeProfile
        from bilqis_mlx.factory.tests.test_executable_release import _answers
        from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_registry
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        from bilqis_mlx.runtime.admission import _persist_executable_factory_release
        from bilqis_mlx.runtime.bamf_bundle.admission import bind_accepted_execution_cache
        import bilqis_mlx.runtime.factory_fixed_school as owner

        target = self.root / "c05-profile-successor"
        self.preflight(target)
        registry, answers = _synthetic_registry(), _answers()
        with patch("bilqis_mlx.source_adapters.school.live_source_registry", return_value=registry), \
                patch("bilqis_mlx.factory.live_answers.live_answer_registry", return_value=answers), \
                shape_patch():
            context = AcceptedRuntimeHost(target).source_context(graph=self.graph, source_root=None)
            cache = bind_accepted_execution_cache(target)
            first = owner._bamf_fixed_school_cohort(
                context, target, expected_parent_manifest_sha256=cache.accepted_manifest_sha256)
            parent, cache = owner._accepted_parent(context, target, cache.accepted_manifest_sha256)
            successor = compile_successor_profile_release(
                self.release, CurriculumProfile.full(), registry, answers,
                source_root=None, graph=self.graph, verification_seed=17)
            middle_path = target / _persist_executable_factory_release(target, successor)
            latest = compile_successor_profile_release(
                successor, CurriculumProfile.full(), registry, answers,
                source_root=None, graph=self.graph, verification_seed=17)
            current = replace(context, release=latest)
            receipt_path = target / "c05-fixed-school" / f"{parent.run_identity.digest}.json"
            receipt_before = receipt_path.read_bytes()
            with patch.object(owner, "_accepted_parent", return_value=(parent, cache)), \
                    patch.object(owner, "_draw_executable_scope_cohort", side_effect=AssertionError("redraw")):
                second = owner._bamf_fixed_school_cohort(
                    current, target, expected_parent_manifest_sha256=cache.accepted_manifest_sha256)
            self.assertEqual(first, second)
            self.assertEqual(receipt_path.read_bytes(), receipt_before)
            narrowed = compile_successor_profile_release(
                self.release, CurriculumProfile(
                    "narrow", (GradeProfile("Z", ("Z.C0",)),)), registry, answers,
                source_root=None, graph=self.graph, verification_seed=17)
            with patch.object(owner, "_accepted_parent", return_value=(parent, cache)):
                with self.assertRaises(BilqisError) as incompatible:
                    owner._bamf_fixed_school_cohort(
                        replace(context, release=narrowed), target,
                        expected_parent_manifest_sha256=cache.accepted_manifest_sha256)
            self.assertEqual(incompatible.exception.context["reason"],
                             "BAMF_C05_FIXED_SCHOOL_FOUNDING_RELEASE_INVALID")
            middle_path.unlink()
            with patch.object(owner, "_accepted_parent", return_value=(parent, cache)):
                with self.assertRaises(BilqisError) as failure:
                    owner._bamf_fixed_school_cohort(
                        current, target, expected_parent_manifest_sha256=cache.accepted_manifest_sha256)
            self.assertEqual(failure.exception.context["reason"],
                             "BAMF_C05_FIXED_SCHOOL_FOUNDING_RELEASE_INVALID")
            self.assertEqual(receipt_path.read_bytes(), receipt_before)

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

    def test_public_c05_candidate_route_does_not_materialize_broad_fixed_school(self):
        target = self.root / "c05-native-public-candidate"
        self.preflight(target)
        from bilqis_mlx.factory.tests.test_executable_release import _answers
        from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_registry
        from bilqis_mlx.learning.atlas_candidate import begin_candidate
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
            retention_owner.bind_current_retention_protection_plan(
                context, parent, cache)
            retention_owner.bind_current_retention_source_rows(
                context, cache, self.release.execution_plan.capabilities[0].capability_id)
        transaction = begin_candidate(parent.retained_state)
        target_capability = self.release.execution_plan.capabilities[0].capability_id
        sentinel = object()

        with patch.object(
                retention_owner, "_training_exclusions",
                return_value=((), ())), patch.object(
                retention_owner, "_candidate_from_live_parent",
                return_value=(parent, parent, parent.retained_state, cache)), patch.object(
                retention_owner, "_fixed_school_instruments",
                side_effect=AssertionError("ordinary candidate entered broad fixed school")), patch.object(
                retention_owner, "_local_retention_instruments",
                return_value=(object(),)), patch.object(
                retention_owner, "_foundation_retention_evaluation",
                return_value=sentinel), shape_patch():
            result = retention_owner.evaluate_factory_retention_candidate(
                context, transaction, "artifact", target_capability,
                run_dir=target)

        self.assertIs(result, sentinel)
        self.assertFalse((target / "state.json").exists())
        self.assertFalse((
            target / "c05-fixed-school" / f"{parent.run_identity.digest}.json"
        ).is_file())

    def test_public_c05_package_import_route_shares_native_school_without_training_state(self):
        target = self.root / "c05-native-public-package"
        self.preflight(target)
        from bilqis_mlx.factory.tests.test_executable_release import _answers
        from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_registry
        from bilqis_mlx.learning.atlas_package_import import (
            ImportSlice, prepare_package_import,
        )
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
        parameters = dict(parent.retained_state.optimizer.parameters)
        name = next(iter(parameters))
        before = parameters[name]
        changed = np.asarray(before).copy().reshape(-1)
        changed[0] = changed[0] + 1e-6
        parameters[name] = mx.array(changed.reshape(before.shape), dtype=mx.float32)
        transaction = prepare_package_import(
            parent.retained_state, parameters, (ImportSlice(name, 0, 1),))
        target_capability = self.release.execution_plan.capabilities[0].capability_id
        sentinel = object()
        captured = {}
        def foundation(*args, **_kwargs):
            captured["training"] = args[7]
            return sentinel

        with patch.object(
                retention_owner, "_instruments",
                return_value=(object(),)), patch.object(
                retention_owner, "_broad_foundation_retention_evaluation",
                side_effect=foundation), shape_patch():
            result = retention_owner.evaluate_factory_package_import(
                context, transaction, "artifact", target_capability,
                run_dir=target)

        self.assertIs(result, sentinel)
        self.assertEqual(captured["training"], ((), ()))
        self.assertFalse((target / "state.json").exists())
        self.assertTrue((
            target / "c05-fixed-school" / f"{parent.run_identity.digest}.json"
        ).is_file())



if __name__ == "__main__":
    import unittest
    unittest.main()
