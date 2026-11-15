"""C13.1 candidate-accounting and cold-restart unit contracts."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from scripts.bamf.c13 import delivery_runtime
from scripts.bamf.c13.contracts import CandidateAttemptReceipt
from scripts.bamf.c13.contracts import NextUpdateReceipt, RollbackResumeReceipt


class BamfLearningPathCandidateAccountingTests(unittest.TestCase):
    @staticmethod
    def student(generation, step):
        return SimpleNamespace(
            generation=generation,
            retained_state=SimpleNamespace(optimizer_step=step),
        )

    def test_owner_candidate_acceptance_must_advance_generation_and_optimizer(self):
        parent, current = self.student(0, 0), self.student(1, 1)
        result = SimpleNamespace(status="VISIT_LIMIT", visits=1, accepted=1, rejected=0)
        with patch.object(
                delivery_runtime, "load_accepted_generation",
                side_effect=(parent, current)), patch.object(
                delivery_runtime, "operate_bamf", return_value=result) as operate, patch.object(
                delivery_runtime, "_identity", side_effect=("1" * 64, "2" * 64)), patch.object(
                delivery_runtime, "event_offset", return_value=10), patch.object(
                delivery_runtime, "owner_event_after",
                return_value=("BAMF_C16_3_ACCEPTED", "a" * 64)):
            receipt = delivery_runtime.attempt_owner_candidate(Path("/tmp/disposable"))
        self.assertEqual(receipt.outcome, "ACCEPTED")
        self.assertEqual(receipt.attempted_steps, 1)
        self.assertEqual((receipt.current_generation, receipt.current_optimizer_step), (1, 1))
        self.assertEqual(receipt.owner_event, "BAMF_C16_3_ACCEPTED")
        self.assertEqual(receipt.owner_evidence_sha256, "a" * 64)
        self.assertEqual(operate.call_args.kwargs["reserve_gib"], 100.0)

    def test_owner_candidate_rejection_and_hold_preserve_accepted_parent(self):
        cases = (
            (SimpleNamespace(status="VISIT_LIMIT", visits=1, accepted=0, rejected=1),
             "REJECTED", 1),
            (SimpleNamespace(status="PRIORITY_HOLD", visits=0, accepted=0, rejected=0),
             "HELD", 0),
        )
        for result, expected, attempted in cases:
            with self.subTest(outcome=expected):
                parent, current = self.student(3, 7), self.student(3, 7)
                with patch.object(
                        delivery_runtime, "load_accepted_generation",
                        side_effect=(parent, current)), patch.object(
                        delivery_runtime, "operate_bamf", return_value=result), patch.object(
                        delivery_runtime, "_identity", side_effect=("3" * 64, "3" * 64)), patch.object(
                        delivery_runtime, "event_offset", return_value=10), patch.object(
                        delivery_runtime, "owner_event_after", return_value=(
                            ("BAMF_CANDIDATE_REJECTED", "b" * 64)
                            if expected == "REJECTED" else (None, None))):
                    receipt = delivery_runtime.attempt_owner_candidate(Path("/tmp/disposable"))
                self.assertEqual(receipt.outcome, expected)
                self.assertEqual(receipt.attempted_steps, attempted)

    def test_candidate_loop_stops_at_first_rejection_after_acceptance(self):
        accepted = CandidateAttemptReceipt(
            "ACCEPTED", 0, 1, 0, 1, "1" * 64, "2" * 64, 1)
        rejected = CandidateAttemptReceipt(
            "REJECTED", 1, 1, 1, 1, "2" * 64, "2" * 64, 1)
        with patch.object(
                delivery_runtime, "attempt_owner_candidate",
                side_effect=(accepted, rejected, AssertionError("must stop"))):
            attempts = delivery_runtime.run_candidate_attempts(Path("/tmp/disposable"), 64)
        self.assertEqual(attempts, (accepted, rejected))

    def test_cold_restart_identity_uses_fresh_process_and_preserves_full_candidate_digest(self):
        parent = self.student(4, 9)
        with patch.object(
                delivery_runtime, "load_accepted_generation", return_value=parent), patch.object(
                delivery_runtime, "_identity", return_value="7" * 64), patch.object(
                delivery_runtime.subprocess, "run") as run:
            run.return_value = SimpleNamespace(
                returncode=0, stderr="",
                stdout=json.dumps({
                    "generation": 4,
                    "optimizer_step": 9,
                    "candidate_identity_sha256": "7" * 64,
                    "generation_identity_sha256": "8" * 64,
                }) + "\n")
            with patch.object(
                    delivery_runtime, "successor_candidate_identity_digest",
                    return_value="8" * 64):
                receipt = delivery_runtime.cold_restart_identity(Path("/tmp/disposable"))
        self.assertEqual(receipt["candidate_identity_sha256"], "7" * 64)
        self.assertEqual(receipt["generation_identity_sha256"], "8" * 64)
        self.assertIn("-c", run.call_args.args[0])

    def test_rollback_resume_receipt_requires_exact_parent_and_next_update_identity(self):
        update = NextUpdateReceipt(
            "1" * 64, "2" * 64, "visit", "Z.C13_EPISODE", "3" * 64,
            "4" * 64, "5" * 64, "6" * 64, ("7" * 64,), ("8" * 64,))
        receipt = RollbackResumeReceipt(
            "1" * 64, "2" * 64, "2" * 64, "4" * 64, "5" * 64,
            "4" * 64, update, update)
        self.assertEqual(receipt.warm_next_update, receipt.cold_next_update)

    def test_rollback_resume_receipt_rejects_drift(self):
        update = NextUpdateReceipt(
            "1" * 64, "2" * 64, "visit", "Z.C13_EPISODE", "3" * 64,
            "4" * 64, "5" * 64, "6" * 64, ("7" * 64,), ("8" * 64,))
        with self.assertRaises(BilqisError):
            RollbackResumeReceipt(
                "1" * 64, "2" * 64, "9" * 64, "4" * 64, "5" * 64,
                "4" * 64, update, update)

    def test_next_update_identity_binds_real_owner_coordinates_without_publication(self):
        parent = SimpleNamespace(retained_state=object())
        transaction = SimpleNamespace(
            parent=object(),
            training_authorities=(SimpleNamespace(digest="7" * 64),),
            step_proofs=(SimpleNamespace(digest="8" * 64),),
        )
        prepared = SimpleNamespace(
            status="ACCEPTED", parent=parent,
            selection=SimpleNamespace(visit=SimpleNamespace(
                identity=SimpleNamespace(visit_id="visit-1"))),
            step=SimpleNamespace(transaction=transaction),
            decision=SimpleNamespace(accepted=True, digest="3" * 64),
            capability="Z.C13_EPISODE",
        )
        with patch.object(
                delivery_runtime, "bind_accepted_execution_cache",
                return_value=SimpleNamespace(accepted_manifest_sha256="1" * 64)), patch.object(
                delivery_runtime, "prepare_bamf_visit", return_value=prepared), patch.object(
                delivery_runtime, "resolve_candidate",
                side_effect=(SimpleNamespace(), SimpleNamespace())), patch.object(
                delivery_runtime, "successor_candidate_identity_digest",
                return_value="2" * 64), patch.object(
                delivery_runtime, "candidate_identity_digest",
                side_effect=("4" * 64, "5" * 64, "6" * 64)):
            receipt = delivery_runtime.next_update_identity(Path("/tmp/disposable"))
        self.assertEqual(receipt.decision_sha256, "3" * 64)
        self.assertEqual(receipt.speculative_candidate_sha256, "5" * 64)
        self.assertEqual(receipt.retained_candidate_sha256, "6" * 64)
        self.assertEqual(receipt.parent_candidate_sha256, "4" * 64)
        self.assertEqual(receipt.training_authority_sha256s, ("7" * 64,))
        self.assertEqual(receipt.step_proof_sha256s, ("8" * 64,))


__all__ = ("BamfLearningPathCandidateAccountingTests",)
