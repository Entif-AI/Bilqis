from bilqis_mlx.factory.autonomy import (
    AutonomyActionKind,
    compile_autonomy_plan,
    initial_evidence_ledger,
    next_action,
    next_work,
    obligations_for_capability,
    rebind_evidence_ledger,
    record_evidence,
)

from .support import AutonomyFixture


class AutonomyRouterTests(AutonomyFixture):
    def test_router_prioritizes_source_debt_before_learner_work(self):
        plan = compile_autonomy_plan(
            self.release,
            self.coverage_report(status="AWAITING_SOURCE_WITNESS", debt=True))
        ledger = initial_evidence_ledger(self.release, plan=plan)
        action = next_action(self.release, ledger, plan=plan)
        self.assertEqual(action.kind, AutonomyActionKind.SOURCE_COVERAGE)
        self.assertEqual(
            action.source_coverage_debt,
            "A.F3:A.BASE:0:AWAITING_SOURCE_WITNESS")
        self.assertIsNone(action.evidence_work)

    def test_router_selects_learner_evidence_when_source_is_clean(self):
        ledger = initial_evidence_ledger(self.release)
        action = next_action(self.release, ledger)
        self.assertEqual(action.kind, AutonomyActionKind.LEARNING_EVIDENCE)
        self.assertEqual(action.evidence_work.capability_id, "A.BASE")
        self.assertIsNone(action.source_coverage_debt)

    def test_router_hands_off_to_qualification_after_evidence_closure(self):
        ledger = initial_evidence_ledger(self.release)
        for _ in range(40):
            action = next_action(self.release, ledger)
            if action.kind is AutonomyActionKind.QUALIFICATION:
                break
            self.assertEqual(action.kind, AutonomyActionKind.LEARNING_EVIDENCE)
            ledger = record_evidence(
                self.release, ledger, self.receipt(action.evidence_work.obligation))
        else:
            self.fail("router never reached qualification")
        self.assertEqual(action.kind, AutonomyActionKind.QUALIFICATION)
        self.assertIsNone(action.evidence_work)
        self.assertIsNone(action.source_coverage_debt)


class AutonomyPlanRebindTests(AutonomyFixture):
    def test_source_debt_resolution_can_preserve_unaffected_evidence(self):
        blocked = compile_autonomy_plan(
            self.release,
            self.coverage_report(status="AWAITING_SOURCE_WITNESS", debt=True))
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
            "A.OTHER")

    def test_plan_rebind_rejects_receipts_for_changed_obligation_contract(self):
        old = compile_autonomy_plan(self.release)
        ledger = initial_evidence_ledger(self.release, plan=old)
        ledger = self.close_current_capability(ledger)
        new = compile_autonomy_plan(self.release, self.coverage_report())
        compatible = rebind_evidence_ledger(
            self.release, ledger, old_plan=old, new_plan=new)
        self.assertEqual(compatible.receipts, ledger.receipts)
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
            {receipt.obligation_id for receipt in rebound.receipts})
