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

class TypedCompositionAutonomyTests(AutonomyFixture, unittest.TestCase):
    def coverage_report(self, *, status="SOURCE_CONTRAST_COVERED", debt=False):
        from bilqis_mlx.curriculum_compiler import compile_ast
        return {
            "schema": "bilqis.mlx.semantic-composition-coverage/v1",
            "ast_sha256": compile_ast(self.release.course).digest(),
            "registry_sha256": "9" * 64,
            "capabilities": tuple(item.capability_id for item in self.release.capabilities),
            "obligations": ({
                "consumer": "A.F3",
                "producer": "A.BASE",
                "operand_slot": 0,
                "operand_type": "Boolean",
                "declared_prerequisite": True,
                "status": status,
                "coverage_debt": debt,
                "witness_ids": ("witness-1",) if not debt else (),
            },),
            "unresolved": (),
            "source_witness_cohort_sha256": "8" * 64,
            "training_authorized": False,
        }

    def test_source_covered_discovered_edge_becomes_composition_obligation(self):
        from bilqis_mlx.factory.autonomy import compile_autonomy_plan
        plan = compile_autonomy_plan(self.release, self.coverage_report())
        obligations = obligations_for_capability(self.release, "A.F3", plan=plan)
        typed = [item for item in obligations if item.kind is EvidenceKind.COMPOSITION]
        self.assertEqual(len(typed), 1)
        self.assertEqual(typed[0].requires_capabilities, ("A.BASE",))
        self.assertIn("typed-composition/A.BASE/slot/0", typed[0].obligation_id)
        self.assertEqual(plan.coverage_debt, ())

    def test_unverified_discovered_edge_stays_source_coverage_debt(self):
        from bilqis_mlx.factory.autonomy import compile_autonomy_plan, next_source_coverage_debt
        report = self.coverage_report(status="AWAITING_SOURCE_WITNESS", debt=True)
        plan = compile_autonomy_plan(self.release, report)
        obligations = obligations_for_capability(self.release, "A.F3", plan=plan)
        self.assertFalse(any(item.kind is EvidenceKind.COMPOSITION for item in obligations))
        self.assertIn("A.F3:A.BASE:0:AWAITING_SOURCE_WITNESS",
                      next_source_coverage_debt(plan))

    def test_undeclared_unverified_candidate_is_deferred_not_blocking(self):
        from bilqis_mlx.factory.autonomy import compile_autonomy_plan, next_source_coverage_debt
        report = self.coverage_report(
            status="CROSS_SOURCE_AST_BRIDGE_UNVERIFIED", debt=True)
        report["obligations"][0]["declared_prerequisite"] = False
        plan = compile_autonomy_plan(self.release, report)
        self.assertEqual(plan.coverage_debt, ())
        self.assertEqual(plan.blocked_capabilities, ())
        self.assertEqual(
            plan.deferred_composition_candidates,
            ("A.F3:A.BASE:0:CROSS_SOURCE_AST_BRIDGE_UNVERIFIED",),
        )
        self.assertIsNone(next_source_coverage_debt(plan))

    def test_evidence_ledger_is_bound_to_exact_autonomy_plan(self):
        from bilqis_mlx.factory.autonomy import compile_autonomy_plan
        plan = compile_autonomy_plan(self.release, self.coverage_report())
        ledger = initial_evidence_ledger(self.release, plan=plan)
        changed = compile_autonomy_plan(
            self.release,
            self.coverage_report(status="SOURCE_CONTRAST_PARTIAL", debt=True),
        )
        with self.assertRaisesRegex(ValueError, "AUTONOMY_PLAN_MISMATCH"):
            next_work(self.release, ledger, plan=changed)
