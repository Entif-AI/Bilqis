from dataclasses import replace
import hashlib
import unittest

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

from bilqis_mlx.factory.tests.autonomy.autonomy_support import AutonomyFixture, _sha

class TeachingValidationTests(AutonomyFixture, unittest.TestCase):
    def test_teaching_receipt_must_prove_checkpoint_progress(self):
        from bilqis_mlx.factory.autonomy import TeachingReceipt
        with self.assertRaisesRegex(ValueError, "NO_CHECKPOINT_PROGRESS"):
            TeachingReceipt(
                obligation_id="A.BASE/direct",
                intervention_id="teach-stale",
                teaching_option_id="source.direct/A.BASE",
                parent_checkpoint_sha256="e" * 64,
                parent_optimizer_step=9,
                checkpoint_sha256="e" * 64,
                optimizer_step=9,
            )

    def test_unreleased_teaching_option_is_rejected(self):
        from bilqis_mlx.factory.autonomy import (
            TeachingReceipt, next_action, record_teaching_intervention,
        )
        ledger = initial_evidence_ledger(self.release)
        work = next_work(self.release, ledger)
        failed = self.receipt(work.obligation, passed=False)
        ledger = record_evidence(self.release, ledger, failed)
        action = next_action(self.release, ledger)
        receipt = self.teaching_receipt(
            failed, intervention_id="teach-unreleased",
            teaching_option_id="fixture.not-released")
        with self.assertRaisesRegex(ValueError, "TEACHING_OPTION_NOT_RELEASED"):
            record_teaching_intervention(self.release, ledger, receipt)

    def test_new_teaching_receipt_requires_delivered_provenance(self):
        from bilqis_mlx.factory.autonomy import record_teaching_intervention
        ledger = initial_evidence_ledger(self.release)
        work = next_work(self.release, ledger)
        failed = self.receipt(work.obligation, passed=False)
        ledger = record_evidence(self.release, ledger, failed)
        receipt = self.teaching_receipt(
            failed, specimen_ids=(), specimen_content_sha256=None,
            variation_axes=(), optimizer_step_delta=None)
        with self.assertRaisesRegex(ValueError, "TEACHING_PROVENANCE_UNPROVEN"):
            record_teaching_intervention(self.release, ledger, receipt)

    def test_teaching_receipt_rejects_provider_or_axis_mutation(self):
        from bilqis_mlx.factory.autonomy import record_teaching_intervention
        ledger = initial_evidence_ledger(self.release)
        work = next_work(self.release, ledger)
        failed = self.receipt(work.obligation, passed=False)
        ledger = record_evidence(self.release, ledger, failed)
        with self.assertRaisesRegex(ValueError, "TEACHING_PROVIDER_MISMATCH"):
            record_teaching_intervention(
                self.release, ledger,
                self.teaching_receipt(failed, selected_provider_id="unbound"))
        with self.assertRaisesRegex(ValueError, "TEACHING_VARIATION_AXES_MISMATCH"):
            record_teaching_intervention(
                self.release, ledger,
                self.teaching_receipt(failed, variation_axes=("fresh-seed",)))

    def test_teaching_receipt_rejects_incorrect_step_delta(self):
        from bilqis_mlx.factory.autonomy import TeachingReceipt
        failed = self.receipt(next_work(self.release, initial_evidence_ledger(self.release)).obligation,
                              passed=False)
        with self.assertRaisesRegex(ValueError, "STEP_DELTA_INVALID"):
            self.teaching_receipt(failed, optimizer_step_delta=2)
