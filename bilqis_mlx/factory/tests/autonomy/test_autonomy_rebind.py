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

class AutonomyPlanRebindTests(AutonomyFixture, unittest.TestCase):
    def test_source_debt_resolution_can_preserve_unaffected_evidence(self):
        from bilqis_mlx.factory.autonomy import (
            compile_autonomy_plan, rebind_evidence_ledger,
        )
        blocked = compile_autonomy_plan(
            self.release,
            self.coverage_report(status="AWAITING_SOURCE_WITNESS", debt=True),
        )
        ledger = initial_evidence_ledger(self.release, plan=blocked)
        work = next_work(self.release, ledger, plan=blocked)
        self.assertEqual(work.capability_id, "A.BASE")
        ledger = record_evidence(
            self.release, ledger, self.receipt(work.obligation), plan=blocked)

        covered = compile_autonomy_plan(self.release, self.coverage_report())
        rebound = rebind_evidence_ledger(
            self.release, ledger, old_plan=blocked, new_plan=covered)
        self.assertEqual(rebound.receipts, ledger.receipts)
        self.assertEqual(rebound.autonomy_plan_sha256, covered.digest())
        self.assertEqual(
            next_work(self.release, rebound, plan=covered).capability_id,
            "A.OTHER",
        )

    def test_plan_rebind_rejects_receipts_for_changed_obligation_contract(self):
        from bilqis_mlx.factory.autonomy import (
            AutonomyPlan, compile_autonomy_plan, rebind_evidence_ledger,
        )
        old = compile_autonomy_plan(self.release)
        ledger = initial_evidence_ledger(self.release, plan=old)
        ledger = self.close_current_capability(ledger)
        # Auditing composition changes A.COMPOSITE's composition obligation IDs.
        new = compile_autonomy_plan(self.release, self.coverage_report())
        # Evidence only exists for A.BASE here and remains compatible.
        compatible = rebind_evidence_ledger(
            self.release, ledger, old_plan=old, new_plan=new)
        self.assertEqual(compatible.receipts, ledger.receipts)

        # Now close through the old-plan composite. Explicit composition evidence
        # remains valid; the audited plan may add extra typed-slot obligations
        # without relabeling or discarding the original receipts.
        ledger = self.close_current_capability(ledger)
        ledger = self.close_current_capability(ledger)
        rebound = rebind_evidence_ledger(
            self.release, ledger, old_plan=old, new_plan=new)
        self.assertEqual(rebound.receipts, ledger.receipts)
        typed = tuple(
            obligation for obligation in obligations_for_capability(
                self.release, "A.F3", plan=new)
            if "typed-composition" in obligation.obligation_id)
        self.assertEqual(len(typed), 1)
        self.assertNotIn(
            typed[0].obligation_id,
            {receipt.obligation_id for receipt in rebound.receipts},
        )
