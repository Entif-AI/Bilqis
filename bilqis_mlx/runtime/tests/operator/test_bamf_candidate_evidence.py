"""C16.3 candidate evidence is batched once without weakening replay custody."""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.factory.teaching import content_digest
from bilqis_mlx.runtime.bamf_operator.evidence import (
    CandidateEvidenceCapture, prepare_candidate_evidence_root,
)
from bilqis_mlx.runtime.bamf_operator.evidence_validation import (
    read_candidate_horizon_evidence, validate_candidate_horizon_event,
)
from bilqis_mlx.runtime.teacher_observation_capture import store_sidecar


class CandidateEvidenceCaptureTests(unittest.TestCase):
    @staticmethod
    def _selection():
        identity = SimpleNamespace(
            visit_id="visit:evidence", policy_key="policy:evidence",
            to_record=lambda: {
                "visit_id": "visit:evidence", "policy_key": "policy:evidence"})
        return SimpleNamespace(
            option_id="option:evidence",
            visit=SimpleNamespace(identity=identity),
            offer=SimpleNamespace(
                capability_id="capability:evidence", source_seed=17),
            policy={"lr": 0.001},
        )

    @staticmethod
    def _release():
        execution = SimpleNamespace(
            provider_id="provider:evidence",
            provider_implementation_sha256="f" * 64,
            variation_axes=("seed",),
            teaching_option_ids=("option:evidence",),
        )
        return SimpleNamespace(execution_plan=SimpleNamespace(
            capability_map={"capability:evidence": execution}))

    @classmethod
    def _capture(cls, root, *, candidate_attempt_ordinal=1):
        return CandidateEvidenceCapture(
            root, cls._selection(), generation=3,
            accepted_manifest_sha256="a" * 64,
            candidate_attempt_ordinal=candidate_attempt_ordinal,
            parent_optimizer_step=10,
        )

    @classmethod
    def _deliver(cls, capture, count=16):
        row = {
            "id": "row:one", "capability": "capability:evidence",
            "tokens": [1, 2, 3],
        }
        rows = (row, row)
        for ordinal in range(1, count + 1):
            capture.delivery(
                cls._release(), "capability:evidence", 10 + ordinal, rows,
                option_rows=(row,), priority=(row,), seed=ordinal,
                controls={
                    "realized_cost": {
                        "wall_seconds": 0.01,
                        "optimizer_steps": 1,
                        "candidate_optimizer_steps": ordinal,
                    },
                    "delivered_content_sha256": content_digest(rows),
                },
            )

    def test_evidence_root_is_durably_installed_once_before_hot_execution(self):
        with TemporaryDirectory() as temporary, patch(
                "bilqis_mlx.runtime.bamf_operator.evidence.os.fsync",
                wraps=os.fsync) as fsync:
            root = Path(temporary)
            objects = prepare_candidate_evidence_root(root)
            self.assertTrue(objects.is_dir())
            self.assertEqual(fsync.call_count, 4)
            prepare_candidate_evidence_root(root)
            self.assertEqual(fsync.call_count, 4)

    def test_preexisting_hierarchy_is_refsynced_once_after_process_restart(self):
        from bilqis_mlx.runtime.bamf_operator import evidence as evidence_module

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "teacher-observations" / "objects").mkdir(parents=True)
            evidence_module._PREPARED_ROOTS.discard(root)
            with patch(
                    "bilqis_mlx.runtime.bamf_operator.evidence.os.fsync",
                    wraps=os.fsync) as fsync:
                prepare_candidate_evidence_root(root)
                self.assertEqual(fsync.call_count, 4)
                prepare_candidate_evidence_root(root)
                self.assertEqual(fsync.call_count, 4)

    def test_one_horizon_write_preserves_all_steps_and_deduplicates_rows(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepare_candidate_evidence_root(root)
            capture = self._capture(root)
            with patch(
                    "bilqis_mlx.runtime.state.os.fsync",
                    wraps=os.fsync) as fsync:
                self._deliver(capture)
                self.assertEqual(fsync.call_count, 0)
                receipt = capture.finalize(
                    accepted=False,
                    decision={"decision": "REJECTED", "reason": "fixture"},
                )
                self.assertEqual(fsync.call_count, 2)
            self.assertEqual(receipt["persistence"]["file_fsyncs"], 1)
            self.assertEqual(receipt["persistence"]["directory_fsyncs"], 1)
            self.assertGreater(receipt["persistence"]["bytes_written"], 0)
            self.assertEqual(receipt["persistence"]["delivery_records"], 16)

            payload = read_candidate_horizon_evidence(root, receipt)
            self.assertEqual(len(payload["steps"]), 16)
            self.assertEqual(len(payload["source_objects"]), 1)
            row_digest = next(iter(payload["source_objects"]))
            self.assertTrue(all(
                [position["row"] for position in step["positions"]]
                == [row_digest, row_digest]
                for step in payload["steps"]))
            self.assertTrue(all(
                step["delivered_teaching"]["provider_id"] == "provider:evidence"
                for step in payload["steps"]))
            self.assertFalse(payload["outcome"]["accepted"])
            self.assertEqual(payload["outcome"]["decision"]["reason"], "fixture")

    def test_mid_install_failure_leaves_no_declared_horizon_object(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepare_candidate_evidence_root(root)
            capture = self._capture(root)
            self._deliver(capture, count=2)
            with patch(
                    "bilqis_mlx.runtime.state.os.link",
                    side_effect=OSError("simulated crash after file fsync")):
                with self.assertRaises(OSError):
                    capture.finalize(
                        accepted=False, decision={"decision": "REJECTED"})
            self.assertEqual(list(root.glob("teacher-observations/objects/*.json")), [])
            self.assertEqual(list(root.glob("teacher-observations/objects/*.tmp")), [])

    def test_replay_of_already_durable_horizon_is_idempotent_and_cold_readable(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepare_candidate_evidence_root(root)
            first = self._capture(root)
            self._deliver(first, count=4)
            first_receipt = first.finalize(
                accepted=True, decision={"decision": "ACCEPTED"})

            replay = self._capture(root)
            self._deliver(replay, count=4)
            with patch(
                    "bilqis_mlx.runtime.state.os.fsync",
                    wraps=os.fsync) as fsync:
                replay_receipt = replay.finalize(
                    accepted=True, decision={"decision": "ACCEPTED"})
            self.assertEqual(fsync.call_count, 0)
            self.assertEqual(replay_receipt["object"], first_receipt["object"])
            self.assertEqual(replay_receipt["persistence"]["bytes_written"], 0)
            self.assertEqual(replay_receipt["persistence"]["file_fsyncs"], 0)
            self.assertEqual(replay_receipt["persistence"]["directory_fsyncs"], 0)
            self.assertEqual(
                read_candidate_horizon_evidence(root, replay_receipt)["steps"],
                read_candidate_horizon_evidence(root, first_receipt)["steps"],
            )

    def test_cold_read_rejects_tampered_horizon_bytes(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepare_candidate_evidence_root(root)
            capture = self._capture(root)
            self._deliver(capture, count=1)
            receipt = capture.finalize(
                accepted=False, decision={"decision": "REJECTED"})
            path = root / receipt["object"]["file"]
            path.write_text("{}\n")
            with self.assertRaises(ValueError):
                read_candidate_horizon_evidence(root, receipt)

    def test_same_parent_retry_keeps_attempt_identity_until_rejection_is_durable(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepare_candidate_evidence_root(root)
            first = self._capture(root, candidate_attempt_ordinal=1)
            crash_retry = self._capture(root, candidate_attempt_ordinal=1)
            next_rejection = self._capture(root, candidate_attempt_ordinal=2)
        self.assertEqual(first.attempt_id, crash_retry.attempt_id)
        self.assertNotEqual(first.attempt_id, next_rejection.attempt_id)

    def test_cold_validator_binds_rejection_event_to_exact_horizon(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepare_candidate_evidence_root(root)
            capture = self._capture(root)
            self._deliver(capture, count=2)
            decision = {"decision": "REJECTED", "reason": "fixture"}
            receipt = capture.finalize(accepted=False, decision=decision)
            event = {
                "event": "BAMF_CANDIDATE_REJECTED",
                "generation": 3,
                "student_manifest_sha256": "a" * 64,
                "evidence": {
                    "schema": "bilqis.bamf.c16.3-rejection/v2",
                    "rejection_journal_ordinal": 1,
                    "rejection_attempt_ordinal": 1,
                    "visit_id": "visit:evidence",
                    "selected_policy_key": "policy:evidence",
                    "selected_option_id": "option:evidence",
                    "capability": "capability:evidence",
                    "candidate_optimizer_step": 12,
                    "retained_optimizer_step": 10,
                    "decision": decision,
                    "candidate_evidence": receipt,
                },
            }
            payload = validate_candidate_horizon_event(root, event, self._release())
            self.assertEqual(payload["steps"][-1]["step"], 12)
            event["evidence"]["rejection_journal_ordinal"] = 2
            with self.assertRaises(ValueError):
                validate_candidate_horizon_event(root, event, self._release())

    def test_cold_validator_binds_accepted_event_to_exact_horizon(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepare_candidate_evidence_root(root)
            capture = self._capture(root)
            self._deliver(capture, count=2)
            receipt = capture.finalize(
                accepted=True, decision={"decision": "ACCEPTED"})
            persistence = receipt["persistence"]
            event = {
                "event": "BAMF_C16_3_ACCEPTED",
                "optimizer_step": 12,
                "parent_generation": 3,
                "accepted_manifest_sha256": "a" * 64,
                "candidate_attempt_ordinal": 1,
                "capability": "capability:evidence",
                "visit_id": "visit:evidence",
                "selected_policy_key": "policy:evidence",
                "selected_option_id": "option:evidence",
                "resource": {
                    "optimizer_steps": 2,
                    "evidence_bytes_written": persistence["bytes_written"],
                    "evidence_file_fsyncs": persistence["file_fsyncs"],
                    "evidence_directory_fsyncs": persistence["directory_fsyncs"],
                    "evidence_objects": persistence["evidence_objects"],
                },
                "candidate_evidence": receipt,
            }
            payload = validate_candidate_horizon_event(root, event, self._release())
            self.assertTrue(payload["outcome"]["accepted"])
            event["optimizer_step"] = 13
            with self.assertRaises(ValueError):
                validate_candidate_horizon_event(root, event, self._release())

    def test_disposable_fsync_latency_fixture_favors_one_horizon_write(self):
        real_fsync = os.fsync

        def delayed_fsync(fd):
            time.sleep(0.002)
            return real_fsync(fd)

        with TemporaryDirectory() as legacy_tmp, TemporaryDirectory() as batch_tmp:
            legacy_root = Path(legacy_tmp)
            batch_root = Path(batch_tmp)
            prepare_candidate_evidence_root(legacy_root)
            prepare_candidate_evidence_root(batch_root)
            with patch(
                    "bilqis_mlx.runtime.state.os.fsync",
                    side_effect=delayed_fsync):
                started = time.perf_counter()
                for ordinal in range(1, 17):
                    store_sidecar(legacy_root, {
                        "schema": "legacy-per-step-fixture",
                        "step": ordinal,
                        "row": {"id": "row:one", "tokens": [1, 2, 3]},
                    })
                legacy_seconds = time.perf_counter() - started

                capture = self._capture(batch_root)
                self._deliver(capture)
                started = time.perf_counter()
                receipt = capture.finalize(
                    accepted=False, decision={"decision": "REJECTED"})
                batch_seconds = time.perf_counter() - started

        self.assertEqual(receipt["persistence"]["file_fsyncs"], 1)
        self.assertEqual(receipt["persistence"]["directory_fsyncs"], 1)
        self.assertLess(batch_seconds, legacy_seconds / 2)


if __name__ == "__main__":
    unittest.main()
