"""Target-specific transfer evidence must not be minted from family proxies."""
from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.factory.autonomy import (
    EvidenceLedger, compile_autonomy_plan, initial_evidence_ledger, next_work,
)
from bilqis_mlx.factory.generated_grade import AcceptedLearnerFoot, CostEvidenceKind
from bilqis_mlx.factory.generated_grade.inputs import _measured_acquisition_cost
from bilqis_mlx.factory.tests.autonomy.autonomy_support import AutonomyFixture, _sha


class GeneratedGradeTransferEvidenceTests(AutonomyFixture, unittest.TestCase):

    def test_same_family_proxy_cost_does_not_mint_candidate_transfer(self):
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
            intervention_id="family-proxy-control",
        )
        treatment = replace(
            control,
            obligation_id="treatment-obligation",
            intervention_id="family-proxy-treatment",
            parent_checkpoint_sha256="d" * 64,
            parent_optimizer_step=failed.optimizer_step + 10,
            checkpoint_sha256="e" * 64,
            optimizer_step=failed.optimizer_step + 13,
            optimizer_step_delta=3,
        )
        ledger = EvidenceLedger(
            ledger.factory_release_sha256, ledger.autonomy_plan_sha256,
            ledger.receipts, (control, treatment), ledger.rejected_attempts)
        foot = AcceptedLearnerFoot(
            "e" * 64, treatment.optimizer_step, self.release.release_sha256,
            0, 0, (), ("A.BASE", "A.OTHER"), _sha("family-proxy-foot"))
        historical = (
            SimpleNamespace(
                semantic_id="historical.base", family_id="positive_identity"),
            SimpleNamespace(
                semantic_id="historical.other", family_id="positive_identity"),
        )
        epoch = SimpleNamespace(
            current_release=self.release,
            closure=SimpleNamespace(
                constituent_order=tuple(item.semantic_id for item in historical),
                candidates=historical,
            ),
        )
        learner = SimpleNamespace(ledger=ledger)
        module = __import__(
            _measured_acquisition_cost.__module__,
            fromlist=["_realization", "obligations_for_capability"],
        )
        realized = {
            "historical.base": ("A.BASE",),
            "historical.other": ("A.OTHER",),
        }
        with patch.object(
                module, "_realization",
                side_effect=lambda _epoch, semantic_id, _rows: (
                    realized[semantic_id], ())), patch.object(
                    module, "obligations_for_capability",
                    side_effect=lambda _release, capability, *, plan: (
                        SimpleNamespace(obligation_id=(
                            "control-obligation"
                            if capability == "A.BASE"
                            else "treatment-obligation")),)), patch.object(
                    module, "_mastery_before_intervention",
                    side_effect=lambda _epoch, _learner, _plan, receipt: (
                        {"PREREQ.CAPABILITY"}
                        if receipt.obligation_id == "treatment-obligation"
                        else set())):
            measured = _measured_acquisition_cost(
                epoch, learner, plan, foot, ("UNMASTERED.CANDIDATE",),
                ("positive_identity",),
                (("skos:bridge", ("PREREQ.CAPABILITY",)),))

        self.assertIs(measured.status, CostEvidenceKind.MEASURED)
        self.assertEqual(measured.units, 5)
        self.assertIsNone(measured.transfer_savings)
