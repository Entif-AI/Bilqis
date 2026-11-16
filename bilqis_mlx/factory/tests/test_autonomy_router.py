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

from bilqis_mlx.factory.tests.autonomy_support import AutonomyFixture, _sha

class AutonomyRouterTests(AutonomyFixture, unittest.TestCase):
    def test_router_prioritizes_source_debt_before_learner_work(self):
        from bilqis_mlx.factory.autonomy import (
            AutonomyActionKind, compile_autonomy_plan, next_action,
        )
        plan = compile_autonomy_plan(
            self.release,
            self.coverage_report(status="AWAITING_SOURCE_WITNESS", debt=True),
        )
        ledger = initial_evidence_ledger(self.release, plan=plan)
        action = next_action(self.release, ledger, plan=plan)
        self.assertEqual(action.kind, AutonomyActionKind.SOURCE_COVERAGE)
        self.assertEqual(action.source_coverage_debt,
                         "A.F3:A.BASE:0:AWAITING_SOURCE_WITNESS")
        self.assertIsNone(action.evidence_work)

    def test_router_selects_learner_evidence_when_source_is_clean(self):
        from bilqis_mlx.factory.autonomy import AutonomyActionKind, next_action
        ledger = initial_evidence_ledger(self.release)
        action = next_action(self.release, ledger)
        self.assertEqual(action.kind, AutonomyActionKind.LEARNING_EVIDENCE)
        self.assertEqual(action.evidence_work.capability_id, "A.BASE")
        self.assertIsNone(action.source_coverage_debt)

    def test_router_hands_off_to_qualification_after_evidence_closure(self):
        from bilqis_mlx.factory.autonomy import AutonomyActionKind, next_action
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
