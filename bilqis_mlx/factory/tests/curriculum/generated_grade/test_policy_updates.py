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
from bilqis_mlx.factory.generated_grade.inputs import (
    _measured_acquisition_cost,
    _measured_cost_profile,
)
from bilqis_mlx.factory.autonomy import (
    EvidenceLedger, EvidenceReceipt, compile_autonomy_plan, evidence_complete_capabilities,
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
    def test_developmental_dimensions_change_pareto_membership(self):
        snapshot, closure, release, evidence, _, learner = _fixture()
        policy = GeneratedGradePolicy("learner-relative-grade/v1", 1, 0, 17)
        changed = tuple(
            replace(
                item,
                grounding_quality=99,
                reusable_constituent_value=99,
                downstream_unlocks=99,
                minimal_contrast_value=99,
                transfer_breadth=99,
                learning_progress=99,
            ) if item.semantic_id == "skos:cluster-b" else item
            for item in evidence
        )

        result = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, changed, policy))

        self.assertEqual(result.member_semantic_ids, ("skos:cluster-b",))

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
                grounding_quality=99,
                answer_modality_burden=0,
                ast_burden=0,
                entanglement=0,
                reusable_constituent_value=99,
                downstream_unlocks=99,
                minimal_contrast_value=99,
                transfer_breadth=99,
                learning_progress=99,
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

    def test_accepted_teaching_history_produces_signed_transfer_evidence(self):
        plan = compile_autonomy_plan(self.release)
        ledger = initial_evidence_ledger(self.release, plan=plan)
        work = next_work(self.release, ledger, plan=plan)
        failed = self.receipt(work.obligation, passed=False)
        control = replace(
            self.teaching_receipt(
                failed, checkpoint_sha256="f" * 64,
                optimizer_step=failed.optimizer_step + 7,
                optimizer_step_delta=7),
            obligation_id="control-obligation",
            intervention_id="accepted-transfer-control",
        )
        treatment = replace(
            self.teaching_receipt(
                failed, checkpoint_sha256="c" * 64,
                optimizer_step=failed.optimizer_step + 3,
                optimizer_step_delta=3),
            obligation_id="treatment-obligation",
            intervention_id="accepted-transfer-treatment",
            parent_checkpoint_sha256="d" * 64,
            parent_optimizer_step=failed.optimizer_step + 10,
            checkpoint_sha256="e" * 64,
            optimizer_step=failed.optimizer_step + 13,
        )
        ledger = EvidenceLedger(
            ledger.factory_release_sha256, ledger.autonomy_plan_sha256,
            ledger.receipts, (control, treatment), ledger.rejected_attempts)
        foot = AcceptedLearnerFoot(
            "e" * 64, failed.optimizer_step + 13,
            self.release.release_sha256, 0, 0, (),
            ("A.BASE", "A.OTHER"), _sha("accepted-transfer-foot"))
        epoch = SimpleNamespace(current_release=self.release)
        learner = SimpleNamespace(ledger=ledger)
        module = __import__(
            _measured_acquisition_cost.__module__,
            fromlist=[
                "_mastery_before_intervention",
                "obligations_for_capability",
                "release_capabilities",
            ])

        def obligations(_release, capability, *, plan):
            return (SimpleNamespace(
                obligation_id=(
                    "control-obligation"
                    if capability == "A.BASE"
                    else "treatment-obligation")),)

        with patch.object(
                module, "obligations_for_capability",
                side_effect=obligations), patch.object(
                    module, "_mastery_before_intervention",
                    side_effect=lambda _epoch, _learner, _plan, receipt: (
                        {"PREREQ.CAPABILITY"}
                        if receipt.obligation_id == "treatment-obligation"
                        else set())):
            measured, progress = _measured_cost_profile(
                epoch, learner, plan, foot, ("A.BASE", "A.OTHER"),
                ("positive_identity",),
                (("skos:bridge", ("PREREQ.CAPABILITY",)),))

        self.assertIs(measured.status, CostEvidenceKind.MEASURED)
        self.assertEqual(measured.units, 5)
        self.assertEqual(measured.transfer_savings, (("skos:bridge", 4),))
        self.assertEqual(progress, 4)

    def test_multi_intervention_episode_uses_total_cost_for_transfer(self):
        plan = compile_autonomy_plan(self.release)
        ledger = initial_evidence_ledger(self.release, plan=plan)
        work = next_work(self.release, ledger, plan=plan)
        failed = self.receipt(work.obligation, passed=False)
        first = self.teaching_receipt(
            failed, checkpoint_sha256="f" * 64,
            optimizer_step=failed.optimizer_step + 2,
            optimizer_step_delta=2)
        second = replace(
            first,
            intervention_id="accepted-transfer-second-fragment",
            obligation_id=first.obligation_id,
            parent_checkpoint_sha256="d" * 64,
            parent_optimizer_step=first.optimizer_step,
            checkpoint_sha256="e" * 64,
            optimizer_step=first.optimizer_step + 5,
            optimizer_step_delta=5,
        )
        ledger = EvidenceLedger(
            ledger.factory_release_sha256, ledger.autonomy_plan_sha256,
            ledger.receipts, (first, second), ledger.rejected_attempts)
        foot = AcceptedLearnerFoot(
            "e" * 64, second.optimizer_step, self.release.release_sha256, 0, 0, (),
            ("A.BASE",), _sha("accepted-transfer-foot"))
        epoch = SimpleNamespace(current_release=self.release)
        learner = SimpleNamespace(ledger=ledger)
        module = __import__(
            _measured_acquisition_cost.__module__,
            fromlist=["_mastery_before_intervention"])
        with patch.object(
                module, "_mastery_before_intervention",
                return_value=set()):
            measured = _measured_acquisition_cost(
                epoch, learner, plan, foot, ("A.BASE",),
                ("positive_identity",),
                (("skos:bridge", ("PREREQ.CAPABILITY",)),))

        self.assertIs(measured.status, CostEvidenceKind.MEASURED)
        self.assertEqual(measured.units, 7)
        self.assertIsNone(measured.transfer_savings)
