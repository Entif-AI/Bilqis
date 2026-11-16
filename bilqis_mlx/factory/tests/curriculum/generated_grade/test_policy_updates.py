"""Learner-relative evidence updates change policy output without semantic mutation."""
from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.factory.generated_grade import (
    AcceptedLearnerFoot,
    AcquisitionCostEvidence,
    CostEvidenceKind,
    GeneratedGradePolicy,
    synthesize_generated_grade,
)
from bilqis_mlx.factory.generated_grade.inputs import _measured_acquisition_cost
from bilqis_mlx.factory.autonomy import (
    EvidenceReceipt, compile_autonomy_plan, evidence_complete_capabilities,
    initial_evidence_ledger, next_work, record_evidence,
    record_teaching_intervention,
)
from bilqis_mlx.factory.tests.autonomy_support import AutonomyFixture, _sha
from bilqis_mlx.factory.tests.curriculum.generated_grade.test_synthesis import (
    _closure_with_bridge_mastered,
    _fixture,
    _inputs,
)


class GeneratedGradePolicyUpdateTests(unittest.TestCase):
    def test_cost_evidence_can_change_membership_with_same_canonical_snapshot(self):
        snapshot, closure, release, evidence, _, learner = _fixture()
        policy = GeneratedGradePolicy("learner-relative-grade/v1", 1, 0, 17)
        before = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, evidence, policy))
        changed = tuple(
            replace(
                item,
                acquisition_cost=AcquisitionCostEvidence(
                    CostEvidenceKind.MEASURED,
                    "optimizer-steps-to-criterion",
                    0,
                ),
            ) if item.semantic_id == "skos:distinct" else item
            for item in evidence
        )
        after = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, changed, policy))

        self.assertEqual(before.snapshot_sha256, after.snapshot_sha256)
        self.assertEqual(before.learner_foot_sha256, after.learner_foot_sha256)
        self.assertNotEqual(before.member_semantic_ids, after.member_semantic_ids)
        self.assertEqual(after.member_semantic_ids, ("skos:distinct",))

    def test_negative_transfer_is_explicit_interference_and_raises_cost(self):
        snapshot, closure, release, evidence, policy, learner = _fixture()
        closure = _closure_with_bridge_mastered(closure)
        changed = tuple(
            replace(
                item,
                acquisition_cost=AcquisitionCostEvidence(
                    CostEvidenceKind.MEASURED,
                    "optimizer-steps-to-criterion",
                    9,
                    (("skos:bridge", -3),),
                ),
            ) if item.semantic_id == "skos:descendant" else item
            for item in evidence
        )
        result = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, changed, policy))
        descendant = next(
            item for item in result.decisions if item.semantic_id == "skos:descendant")

        self.assertEqual(descendant.applied_transfer_savings, -3)
        self.assertEqual(descendant.effective_acquisition_units, 12)
        self.assertEqual(descendant.closure_acquisition_units, 12)


class GeneratedGradeAcceptedCostEvidenceTests(AutonomyFixture, unittest.TestCase):
    def test_completed_accepted_teaching_receipt_becomes_measured_cost(self):
        plan = compile_autonomy_plan(self.release)
        ledger = initial_evidence_ledger(self.release, plan=plan)
        work = next_work(self.release, ledger, plan=plan)
        failed = self.receipt(work.obligation, passed=False)
        ledger = record_evidence(self.release, ledger, failed, plan=plan)
        intervention = self.teaching_receipt(
            failed, checkpoint_sha256="f" * 64, optimizer_step=failed.optimizer_step + 3,
            optimizer_step_delta=3)
        ledger = record_teaching_intervention(
            self.release, ledger, intervention, plan=plan)
        passed = EvidenceReceipt(
            obligation_id=work.obligation.obligation_id,
            evidence_id="accepted-cost-pass",
            checkpoint_sha256=intervention.checkpoint_sha256,
            optimizer_step=intervention.optimizer_step,
            cohort_sha256=_sha("accepted-cost-pass"),
            specimen_count=work.obligation.minimum_specimens,
            passed=True,
        )
        ledger = record_evidence(self.release, ledger, passed, plan=plan)
        mastered = evidence_complete_capabilities(
            self.release, ledger, plan=plan,
            current_checkpoint_sha256=intervention.checkpoint_sha256,
            current_optimizer_step=intervention.optimizer_step)
        foot = AcceptedLearnerFoot(
            intervention.checkpoint_sha256, intervention.optimizer_step,
            self.release.release_sha256, 0, 0, (), tuple(sorted(mastered)),
            _sha("accepted-cost-foot"))
        measured = _measured_acquisition_cost(
            SimpleNamespace(current_release=self.release),
            SimpleNamespace(ledger=ledger), plan, foot, ("A.BASE",), ("positive_identity",))

        self.assertIs(measured.status, CostEvidenceKind.MEASURED)
        self.assertEqual(measured.units, 3)
        self.assertIsNone(measured.transfer_savings)

        historical = SimpleNamespace(
            semantic_id="historical.same-family",
            family_id="positive_identity",
        )
        epoch = SimpleNamespace(
            current_release=self.release,
            closure=SimpleNamespace(
                constituent_order=(historical.semantic_id,),
                candidates=(historical,),
            ),
        )
        module = __import__(
            _measured_acquisition_cost.__module__, fromlist=["_realization"])
        with patch.object(module, "_realization", return_value=(("A.BASE",), ())):
            comparable = _measured_acquisition_cost(
                epoch, SimpleNamespace(ledger=ledger), plan, foot,
                ("UNMASTERED.CANDIDATE",), ("positive_identity",))
        self.assertIs(comparable.status, CostEvidenceKind.MEASURED)
        self.assertEqual(comparable.units, 3)
