from bilqis_mlx.factory.autonomy import (
    AutonomyActionKind,
    EvidenceReceipt,
    RejectedTeachingAttemptReceipt,
    TeachingReceipt,
    initial_evidence_ledger,
    next_action,
    next_work,
    record_evidence,
    record_rejected_teaching_attempt,
    record_teaching_intervention,
)

from .support import AutonomyFixture, sha


class TeachingInterventionTests(AutonomyFixture):
    def test_repeated_rejected_challengers_consume_remediation_budget(self):
        ledger = initial_evidence_ledger(self.release)
        work = next_work(self.release, ledger)
        failed = EvidenceReceipt(
            obligation_id=work.obligation.obligation_id,
            evidence_id="rejected-campaign-parent",
            checkpoint_sha256="1" * 64,
            optimizer_step=10,
            cohort_sha256=sha("rejected-campaign-cohort"),
            specimen_count=work.obligation.minimum_specimens,
            passed=False)
        ledger = record_evidence(self.release, ledger, failed)
        provider = self.release.source_adapters[0]
        for index in range(3):
            ledger = record_rejected_teaching_attempt(
                self.release, ledger,
                RejectedTeachingAttemptReceipt(
                    obligation_id=failed.obligation_id,
                    parent_evidence_id=failed.evidence_id,
                    attempt_id=f"rejected-campaign-{index}",
                    teaching_option_id=work.teaching_option_ids[0],
                    retained_checkpoint_sha256=failed.checkpoint_sha256,
                    retained_optimizer_step=failed.optimizer_step,
                    candidate_optimizer_step=failed.optimizer_step + 4,
                    retention_reason="NO_MEASURABLE_TARGET_GAIN",
                    selected_provider_id=provider.adapter_id,
                    provider_implementation_sha256=provider.implementation_sha256,
                    specimen_content_sha256=f"{index + 3:064x}"))
        action = next_action(self.release, ledger)
        self.assertEqual(action.kind, AutonomyActionKind.LEARNING_EVIDENCE)
        self.assertEqual(action.evidence_work.capability_id, "A.OTHER")
        self.assertEqual(
            action.deferred_obligation_ids, (work.obligation.obligation_id,))

    def test_repeated_failed_remediation_yields_to_legal_breadth(self):
        ledger = initial_evidence_ledger(self.release)
        work = next_work(self.release, ledger)
        parent_step = 10
        parent_sha = "1" * 64
        for cycle in range(3):
            failed = EvidenceReceipt(
                obligation_id=work.obligation.obligation_id,
                evidence_id=f"stagnation-fail-{cycle}",
                checkpoint_sha256=parent_sha,
                optimizer_step=parent_step,
                cohort_sha256=sha(f"stagnation-cohort-{cycle}"),
                specimen_count=work.obligation.minimum_specimens,
                passed=False)
            ledger = record_evidence(self.release, ledger, failed)
            intervention = self.teaching_receipt(
                failed, intervention_id=f"stagnation-teach-{cycle}",
                checkpoint_sha256=f"{cycle + 10:064x}",
                optimizer_step=parent_step + 1)
            ledger = record_teaching_intervention(
                self.release, ledger, intervention)
            parent_step = intervention.optimizer_step
            parent_sha = intervention.checkpoint_sha256
        final_failure = EvidenceReceipt(
            obligation_id=work.obligation.obligation_id,
            evidence_id="stagnation-fail-final",
            checkpoint_sha256=parent_sha,
            optimizer_step=parent_step,
            cohort_sha256=sha("stagnation-cohort-final"),
            specimen_count=work.obligation.minimum_specimens,
            passed=False)
        ledger = record_evidence(self.release, ledger, final_failure)
        action = next_action(self.release, ledger)
        self.assertEqual(action.kind, AutonomyActionKind.LEARNING_EVIDENCE)
        self.assertEqual(action.evidence_work.capability_id, "A.OTHER")
        self.assertEqual(
            action.deferred_obligation_ids, (work.obligation.obligation_id,))

    def test_failed_evidence_requires_teaching_before_remeasurement(self):
        ledger = initial_evidence_ledger(self.release)
        work = next_work(self.release, ledger)
        failed = self.receipt(work.obligation, passed=False)
        ledger = record_evidence(self.release, ledger, failed)
        action = next_action(self.release, ledger)
        self.assertEqual(action.kind, AutonomyActionKind.TEACHING)
        self.assertEqual(action.teaching_work.failed_evidence, failed)
        intervention = self.teaching_receipt(
            failed, teaching_option_id=action.teaching_work.teaching_option_ids[0])
        ledger = record_teaching_intervention(
            self.release, ledger, intervention)
        action = next_action(self.release, ledger)
        self.assertEqual(action.kind, AutonomyActionKind.LEARNING_EVIDENCE)
        self.assertEqual(action.evidence_work.obligation, work.obligation)
        passed = EvidenceReceipt(
            obligation_id=work.obligation.obligation_id,
            evidence_id="evidence-after-teaching",
            checkpoint_sha256="f" * 64,
            optimizer_step=failed.optimizer_step + 1,
            cohort_sha256="7" * 64,
            specimen_count=work.obligation.minimum_specimens,
            passed=True)
        ledger = record_evidence(self.release, ledger, passed)
        self.assertNotEqual(
            next_action(self.release, ledger).kind, AutonomyActionKind.TEACHING)

    def test_teaching_receipt_must_prove_checkpoint_progress(self):
        with self.assertRaisesRegex(ValueError, "NO_CHECKPOINT_PROGRESS"):
            TeachingReceipt(
                obligation_id="A.BASE/direct",
                intervention_id="teach-stale",
                teaching_option_id="source.direct/A.BASE",
                parent_checkpoint_sha256="e" * 64,
                parent_optimizer_step=9,
                checkpoint_sha256="e" * 64,
                optimizer_step=9)

    def test_unreleased_teaching_option_is_rejected(self):
        ledger = initial_evidence_ledger(self.release)
        work = next_work(self.release, ledger)
        failed = self.receipt(work.obligation, passed=False)
        ledger = record_evidence(self.release, ledger, failed)
        receipt = self.teaching_receipt(
            failed, intervention_id="teach-unreleased",
            teaching_option_id="fixture.not-released")
        with self.assertRaisesRegex(ValueError, "TEACHING_OPTION_NOT_RELEASED"):
            record_teaching_intervention(self.release, ledger, receipt)

    def test_new_teaching_receipt_requires_delivered_provenance(self):
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
        failed = self.receipt(
            next_work(
                self.release,
                initial_evidence_ledger(self.release)).obligation,
            passed=False)
        with self.assertRaisesRegex(ValueError, "STEP_DELTA_INVALID"):
            self.teaching_receipt(failed, optimizer_step_delta=2)
