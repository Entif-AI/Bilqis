from dataclasses import replace
import hashlib
import unittest
from unittest.mock import patch

from bilqis_mlx.curriculum import AnswerFamily, BINARY, Capability, Course, Grade
from bilqis_mlx.factory.adapters import RegisteredSourceAdapter, SourceAdapterRegistry
from bilqis_mlx.factory.autonomy import (
    AutonomyActionKind,
    EvidenceKind,
    EvidenceReceipt,
    RejectedTeachingAttemptReceipt,
    ProjectionEvidenceSpec,
    compile_autonomy_plan,
    initial_evidence_ledger,
    evidence_complete_capabilities,
    next_action,
    next_work,
    obligations_for_capability,
    record_evidence,
    record_rejected_teaching_attempt,
)
from bilqis_mlx.factory.model import SourceAdapter
from bilqis_mlx.factory.release import compile_factory_release

from bilqis_mlx.factory.tests.autonomy_support import AutonomyFixture, _sha

class AutonomousCurriculumPlannerCoreTests(AutonomyFixture, unittest.TestCase):
    def test_public_contract_records_keep_historical_module_identity(self):
        from bilqis_mlx.factory import autonomy
        for name in (
            "AutonomyAction", "AutonomyPlan", "EvidenceLedger",
            "EvidenceObligation", "EvidenceReceipt", "TeachingReceipt",
        ):
            self.assertEqual(getattr(autonomy, name).__module__, autonomy.__name__)
        for name in (
            "compile_autonomy_plan", "initial_evidence_ledger",
            "evidence_complete_capabilities", "next_work",
        ):
            self.assertEqual(getattr(autonomy, name).__module__, autonomy.__name__)

    def test_implicit_plan_resolution_preserves_public_patch_seam(self):
        from bilqis_mlx.factory import autonomy
        with patch.object(
            autonomy, "compile_autonomy_plan",
            side_effect=RuntimeError("public-patch-seam"),
        ):
            with self.assertRaisesRegex(RuntimeError, "public-patch-seam"):
                autonomy.initial_evidence_ledger(self.release)

    def test_generation_axes_constrain_evidence_without_becoming_mastery_claims(self):
        obligations = obligations_for_capability(self.release, "A.BASE")
        self.assertEqual(len(obligations), 1)
        self.assertEqual(obligations[0].kind, EvidenceKind.DIRECT)
        self.assertEqual(obligations[0].generation_axes,
                         ("source-valid", "balanced-gold", "fresh-seed"))

    def test_planner_closes_roots_then_unlocks_composite(self):
        ledger = initial_evidence_ledger(self.release)
        first = next_work(self.release, ledger)
        self.assertEqual(first.capability_id, "A.BASE")
        self.assertEqual(first.obligation.kind, EvidenceKind.DIRECT)
        self.assertEqual(first.teaching_option_ids,
                         ("source.direct/A.BASE", "fixture.transfer"))

        ledger = self.close_current_capability(ledger)
        self.assertEqual(evidence_complete_capabilities(self.release, ledger), ("A.BASE",))
        self.assertEqual(next_work(self.release, ledger).capability_id, "A.OTHER")

        ledger = self.close_current_capability(ledger)
        self.assertEqual(evidence_complete_capabilities(self.release, ledger),
                         ("A.BASE", "A.OTHER"))
        work = next_work(self.release, ledger)
        self.assertEqual(work.capability_id, "A.COMPOSITE")
        kinds = {item.kind for item in obligations_for_capability(
            self.release, "A.COMPOSITE")}
        self.assertEqual(kinds, {EvidenceKind.DIRECT, EvidenceKind.PREREQUISITE,
                                 EvidenceKind.COMPOSITION})

    def test_next_work_is_deterministic_for_unchanged_ledger(self):
        ledger = initial_evidence_ledger(self.release)
        first = next_work(self.release, ledger)
        second = next_work(self.release, ledger)
        self.assertEqual(first, second)

    def test_explicit_current_context_excludes_stale_mastery(self):
        ledger = initial_evidence_ledger(self.release)
        first = next_work(self.release, ledger)
        ledger = record_evidence(self.release, ledger, self.receipt(first.obligation))
        self.assertEqual(
            evidence_complete_capabilities(self.release, ledger), ("A.BASE",))
        self.assertEqual(
            evidence_complete_capabilities(
                self.release, ledger,
                current_checkpoint_sha256="f" * 64,
                current_optimizer_step=999),
            (),
        )
        self.assertEqual(
            next_work(
                self.release, ledger, current_checkpoint_sha256="f" * 64,
                current_optimizer_step=999).capability_id,
            "A.BASE",
        )

    def test_recording_with_explicit_context_rejects_another_checkpoint(self):
        ledger = initial_evidence_ledger(self.release)
        work = next_work(self.release, ledger)
        with self.assertRaisesRegex(ValueError, "EVIDENCE_CURRENT_CHECKPOINT_MISMATCH"):
            record_evidence(
                self.release, ledger, self.receipt(work.obligation),
                current_checkpoint_sha256="f" * 64,
                current_optimizer_step=1)

    def test_explicit_current_context_does_not_reteach_a_stale_failure(self):
        ledger = initial_evidence_ledger(self.release)
        work = next_work(self.release, ledger)
        ledger = record_evidence(
            self.release, ledger, self.receipt(work.obligation, passed=False))
        action = next_action(
            self.release, ledger,
            current_checkpoint_sha256="f" * 64,
            current_optimizer_step=999)
        self.assertEqual(action.kind, AutonomyActionKind.LEARNING_EVIDENCE)
        self.assertEqual(action.evidence_work.obligation, work.obligation)

    def test_composition_evidence_is_required_for_evidence_complete_state(self):
        ledger = initial_evidence_ledger(self.release)
        ledger = self.close_current_capability(ledger)
        ledger = self.close_current_capability(ledger)
        composite = obligations_for_capability(self.release, "A.COMPOSITE")
        missing = next(item for item in composite if item.kind is EvidenceKind.COMPOSITION)
        for obligation in composite:
            if obligation != missing:
                ledger = record_evidence(self.release, ledger, self.receipt(obligation))
        self.assertNotIn("A.COMPOSITE", evidence_complete_capabilities(self.release, ledger))
        self.assertEqual(next_work(self.release, ledger).obligation, missing)
        ledger = record_evidence(self.release, ledger, self.receipt(missing))
        self.assertIn("A.COMPOSITE", evidence_complete_capabilities(self.release, ledger))

    def test_failed_receipt_reopens_before_new_work(self):
        ledger = initial_evidence_ledger(self.release)
        obligation = next_work(self.release, ledger).obligation
        ledger = record_evidence(self.release, ledger, self.receipt(obligation))
        self.assertNotEqual(next_work(self.release, ledger).obligation.obligation_id,
                            obligation.obligation_id)
        ledger = record_evidence(self.release, ledger, self.receipt(obligation, passed=False))
        self.assertEqual(next_work(self.release, ledger).obligation.obligation_id,
                         obligation.obligation_id)
        self.assertNotIn("A.BASE", evidence_complete_capabilities(self.release, ledger))
