"""Fixed-school profile expansion and founding-census regressions."""
from unittest.mock import patch

from bilqis_mlx.runtime.tests.bamf_first_student._bamf_first_student_support import BamfFirstStudentCase
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch


class BamfFixedSchoolProfileExpansionTests(BamfFirstStudentCase):
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

    def test_foundation_progress_reports_only_founding_capabilities_after_expansion(self):
        from dataclasses import replace
        from types import SimpleNamespace
        from bilqis_mlx.errors import BilqisError
        from bilqis_mlx.factory.executable_release import (
            compile_executable_factory_release, compile_successor_profile_release,
        )
        from bilqis_mlx.factory.execution import CurriculumProfile, GradeProfile
        from bilqis_mlx.factory.tests.test_executable_release import _answers
        from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_registry
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        from bilqis_mlx.runtime.source_execution import SourceExecutionContext
        from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
            PARENT, _cases, _solver,
        )
        import bilqis_mlx.runtime.factory_retention_owner as owner

        target = self.root / "c05-progress-expanded"
        self.preflight(target)
        registry, answers = _synthetic_registry(), _answers()
        founding = compile_executable_factory_release(
            self.release.curriculum, self.release.source_bindings,
            CurriculumProfile("founding", (GradeProfile("Z", ("Z.C0", "Z.C1")),)),
            registry, answers, source_root=None, graph=self.graph, verification_seed=17)
        current = compile_successor_profile_release(
            founding, CurriculumProfile.full(), registry, answers,
            source_root=None, graph=self.graph, verification_seed=17)
        cases, contexts = [], {}
        for capability in ("Z.C0", "Z.C1"):
            part, bindings = _cases(capability, "Z", 1, capability)
            cases.extend(part)
            contexts.update(bindings)
        instruments = tuple(SimpleNamespace(case=case) for case in cases)
        with patch("bilqis_mlx.source_adapters.school.live_source_registry", return_value=registry), \
                patch("bilqis_mlx.factory.live_answers.live_answer_registry", return_value=answers), \
                shape_patch():
            context = AcceptedRuntimeHost(target).source_context(graph=self.graph, source_root=None)
        context = replace(context, release=current)
        solver = _solver(contexts, {case.case_id for case in cases})
        with patch.object(SourceExecutionContext, "require_accepted_runtime"), \
                patch.object(owner, "load_accepted_generation", return_value=object()), \
                patch.object(owner, "bind_accepted_execution_cache", return_value=object()), \
                patch.object(owner, "_fixed_school_instruments", return_value=instruments), \
                patch.object(owner, "factory_complete_solver", return_value=(solver, PARENT)):
            assessment = owner.measure_factory_foundation_progress(context, "artifact", run_dir=target)
        self.assertEqual(assessment.cohort.capability_groups, (("Z.C0", "Z"), ("Z.C1", "Z")))
        self.assertEqual(assessment.score("Z.C0"), (1, 1))
        with self.assertRaises(BilqisError):
            assessment.score("Z.C2")

    def test_package_import_rejects_incomplete_fixed_school_before_retention(self):
        from types import SimpleNamespace
        from bilqis_mlx.errors import BilqisError
        from bilqis_mlx.factory.tests.test_executable_release import _answers
        from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_registry
        from bilqis_mlx.learning.atlas_package_import import PackageImportTransaction
        from bilqis_mlx.runtime.source_execution import SourceExecutionContext
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        import bilqis_mlx.runtime.factory_retention_owner as owner

        target = self.root / "c05-incomplete-package-school"
        self.preflight(target)
        with patch("bilqis_mlx.source_adapters.school.live_source_registry", return_value=_synthetic_registry()), \
                patch("bilqis_mlx.factory.live_answers.live_answer_registry", return_value=_answers()), shape_patch():
            context = AcceptedRuntimeHost(target).source_context(graph=self.graph, source_root=None)
        transaction = object.__new__(PackageImportTransaction)
        partial = (SimpleNamespace(case=SimpleNamespace(capability_id="Z.C0", group_id="Z")),)
        with patch.object(SourceExecutionContext, "require_accepted_runtime"), \
                patch.object(owner, "_package_import_from_live_parent", return_value=(object(), object(), object(), object())), \
                patch.object(owner, "_fixed_school_instruments", return_value=partial), \
                patch.object(owner, "_broad_foundation_retention_evaluation", side_effect=AssertionError("incomplete school entered retention")):
            with self.assertRaises(BilqisError) as failure:
                owner.evaluate_factory_package_import(context, transaction, "artifact", "Z.C0", run_dir=target)
        self.assertEqual(failure.exception.context["reason"], "BAMF_C05_FIXED_SCHOOL_COVERAGE_INCOMPLETE")
