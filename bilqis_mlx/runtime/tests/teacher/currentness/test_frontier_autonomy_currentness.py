"""Lawful-frontier autonomy witnesses revoke on durable state movement."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bilqis_mlx.factory.autonomy import (
    EvidenceReceipt,
    initial_evidence_ledger,
    next_work,
    record_evidence,
)
from bilqis_mlx.factory.release import compile_factory_release
from bilqis_mlx.factory.tests.support import synthetic_release_inputs
from bilqis_mlx.runtime.autonomy_state import (
    persist_autonomy_state,
    read_autonomy_state,
)
from bilqis_mlx.runtime.frontier_autonomy_currentness import (
    _bind_autonomy_currentness,
    _require_autonomy_currentness,
)


class FrontierAutonomyCurrentnessTests(unittest.TestCase):
    def setUp(self):
        course, registry = synthetic_release_inputs()
        self.release = compile_factory_release(course, registry)

    @staticmethod
    def _receipt(obligation):
        return EvidenceReceipt(
            obligation_id=obligation.obligation_id,
            evidence_id="evidence-1",
            checkpoint_sha256="e" * 64,
            optimizer_step=1,
            cohort_sha256="1" * 64,
            specimen_count=obligation.minimum_specimens,
            passed=True,
        )

    def test_witness_rejects_pointer_advance(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = initial_evidence_ledger(self.release)
            persist_autonomy_state(root, self.release, ledger=ledger)
            plan, restored = read_autonomy_state(root, self.release)
            witness = _bind_autonomy_currentness(
                root, self.release, plan=plan, ledger=restored)
            self.assertIs(
                _require_autonomy_currentness(witness, self.release), witness)

            work = next_work(self.release, restored, plan=plan)
            updated = record_evidence(
                self.release, restored, self._receipt(work.obligation), plan=plan)
            persist_autonomy_state(
                root, self.release, plan=plan, ledger=updated)
            with self.assertRaises(ValueError) as raised:
                _require_autonomy_currentness(witness, self.release)
            self.assertEqual(
                raised.exception.context["reason"],
                "AUTONOMY_STATE_CURRENTNESS_DRIFT")

    def test_witness_rejects_bound_state_file_tamper(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = initial_evidence_ledger(self.release)
            pointer = persist_autonomy_state(root, self.release, ledger=ledger)
            plan, restored = read_autonomy_state(root, self.release)
            witness = _bind_autonomy_currentness(
                root, self.release, plan=plan, ledger=restored)

            state = root / pointer["state_file"]
            state.write_text(state.read_text(encoding="utf-8") + " ")
            with self.assertRaises(ValueError) as raised:
                _require_autonomy_currentness(witness, self.release)
            self.assertEqual(
                raised.exception.context["reason"],
                "AUTONOMY_STATE_CURRENTNESS_DRIFT")
