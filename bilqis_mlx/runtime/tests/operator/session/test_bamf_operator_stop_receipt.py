"""R01 proof for durable native BAMF normal-stop receipts."""
from contextlib import nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bilqis_mlx.runtime.bamf_operator._session_execution import operate
from bilqis_mlx.runtime.bamf_operator.session_parts.stop_receipt import (
    read_latest_run_stop_receipt, record_normal_stop_receipt,
)


class NativeRunStopReceiptTests(unittest.TestCase):
    def _record(self, run_dir, student, status, witness):
        with patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.stop_receipt."
                "_accepted_pointer", return_value={
                    "run_id": student.run_id, "generation": student.generation,
                    "manifest_sha256": "a" * 64}), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.stop_receipt."
                "_checkpoint_identity", return_value="b" * 64):
            return record_normal_stop_receipt(
                run_dir, student, status=status, minutes=9,
                max_visits=3, steps_per_visit=8, reserve_gib=7.5,
                source_prefetch_workers=2, visits=3, accepted=2, rejected=1,
                elapsed_seconds=12.25, admission_status=None,
                admission_advances=0, resource_witness=witness)

    def test_normal_stop_is_cold_readable_without_minting_generation(self):
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            pointer = run_dir / "bamf-state.json"
            pointer.write_text(
                '{"run_id":"run:r01","generation":4,'
                '"manifest_sha256":"' + "a" * 64 + '"}\n')
            before = pointer.read_bytes()
            student = SimpleNamespace(
                run_id="run:r01", generation=4,
                retained_state=SimpleNamespace(optimizer_step=11))
            witness = {
                "free_bytes": 900, "reserve_bytes": 700,
                "estimated_write_bytes": 0, "sufficient": True,
            }
            digest = self._record(run_dir, student, "VISIT_LIMIT", witness)

            self.assertEqual(pointer.read_bytes(), before)
            receipt = read_latest_run_stop_receipt(run_dir)
            self.assertEqual(receipt["schema"], "bilqis.bamf.run-stop/v1")
            self.assertEqual(receipt["receipt_sha256"], digest)
            self.assertEqual(receipt["run_id"], "run:r01")
            self.assertEqual(receipt["accepted_manifest_sha256"], "a" * 64)
            self.assertEqual(receipt["accepted_generation"], 4)
            self.assertEqual(receipt["checkpoint_identity_sha256"], "b" * 64)
            self.assertEqual(receipt["optimizer_step"], 11)
            self.assertEqual(receipt["stop_reason"], "VISIT_LIMIT")
            self.assertEqual(receipt["configured"]["reserve_gib"], 7.5)
            self.assertEqual(receipt["resource_witness"], witness)
            self.assertTrue(receipt["safe_resume_available"])
            self.assertEqual(receipt["resume_disposition"], "RESUME_ALLOWED")

    def test_cold_read_preserves_normal_stop_resume_disposition(self):
        cases = (
            ("TIME_LIMIT", True, "RESUME_ALLOWED", True),
            ("PRIORITY_HOLD", True, "RESUME_WHEN_WORK_AVAILABLE", True),
            ("FIXED_POINT", True, "RESUME_WHEN_WORK_AVAILABLE", True),
            ("DISK_RESERVE_REACHED", False, "RESUME_AFTER_RESOURCE_RECOVERY", False),
            ("ADMISSION_LEASE_REQUIRED", False, "ACTION_REQUIRED", True),
        )
        for status, safe, disposition, sufficient in cases:
            with self.subTest(status=status), TemporaryDirectory() as temporary:
                run_dir = Path(temporary)
                student = SimpleNamespace(
                    run_id="run:r01", generation=4,
                    retained_state=SimpleNamespace(optimizer_step=11))
                witness = {
                    "free_bytes": 900, "reserve_bytes": 700,
                    "estimated_write_bytes": 0, "sufficient": sufficient,
                }
                self._record(run_dir, student, status, witness)
                receipt = read_latest_run_stop_receipt(run_dir)
                self.assertEqual(receipt["stop_reason"], status)
                self.assertEqual(receipt["safe_resume_available"], safe)
                self.assertEqual(receipt["resume_disposition"], disposition)

    def test_configured_reserve_stop_happens_before_another_visit(self):
        current = SimpleNamespace(
            generation=2, retained_state=SimpleNamespace(optimizer_step=5))
        witness = {
            "free_bytes": 10, "reserve_bytes": 20,
            "estimated_write_bytes": 0, "sufficient": False,
        }
        recorded = Mock(return_value="c" * 64)
        with TemporaryDirectory() as temporary:
            result = operate(
                Path(temporary), minutes=1, max_visits=0, steps_per_visit=4,
                reserve_gib=0.25, source_prefetch_workers=0, progress=None,
                max_horizon=16, worker_counts=(0, 1, 2),
                invalid=lambda reason: (_ for _ in ()).throw(ValueError(reason)),
                metrics_type=lambda: SimpleNamespace(
                    wait_seconds=0.0, overlap_seconds=0.0,
                    prepared_steps=0, serial_steps=0),
                source_pool_factory=lambda _workers: nullcontext(None),
                null_context=nullcontext, operator_lock=lambda _run: nullcontext(),
                visit_fn=Mock(side_effect=AssertionError("visit must not start")),
                observer_type=Mock(), emit_progress=lambda *_args: None,
                monotonic=Mock(side_effect=(0.0, 0.0)),
                load_generation=Mock(return_value=current),
                result_type=__import__(
                    "bilqis_mlx.runtime.bamf_operator.session_support",
                    fromlist=["BamfOperatorResult"]).BamfOperatorResult,
                resource_snapshot=lambda _run, _reserve: witness,
                record_stop=recorded, elapsed_clock=Mock(side_effect=(5.0, 5.5)))

        self.assertEqual(result.status, "DISK_RESERVE_REACHED")
        self.assertEqual((result.visits, result.accepted, result.rejected), (0, 0, 0))
        self.assertEqual(result.elapsed_seconds, 0.5)
        self.assertEqual(result.stop_receipt_sha256, "c" * 64)
        self.assertEqual(recorded.call_args.kwargs["resource_witness"], witness)
        self.assertEqual(recorded.call_args.kwargs["status"], "DISK_RESERVE_REACHED")

    def test_accepted_visit_reaches_visit_limit_without_admission_reentry(self):
        current = SimpleNamespace(
            generation=2, retained_state=SimpleNamespace(optimizer_step=5))
        recorded = Mock(return_value="d" * 64)
        observer = lambda *_args: nullcontext(SimpleNamespace(
            finish=lambda _outcome: None))
        with TemporaryDirectory() as temporary:
            result = operate(
                Path(temporary), minutes=1, max_visits=1, steps_per_visit=4,
                reserve_gib=0.0, source_prefetch_workers=0, progress=None,
                max_horizon=16, worker_counts=(0, 1, 2),
                invalid=lambda reason: (_ for _ in ()).throw(ValueError(reason)),
                metrics_type=lambda: SimpleNamespace(
                    wait_seconds=0.0, overlap_seconds=0.0,
                    prepared_steps=0, serial_steps=0),
                source_pool_factory=lambda _workers: nullcontext(None),
                null_context=nullcontext, operator_lock=lambda _run: nullcontext(),
                visit_fn=Mock(return_value="ACCEPTED"), observer_type=observer,
                emit_progress=lambda *_args: None,
                monotonic=Mock(return_value=0.0),
                load_generation=Mock(return_value=current),
                result_type=__import__(
                    "bilqis_mlx.runtime.bamf_operator.session_support",
                    fromlist=["BamfOperatorResult"]).BamfOperatorResult,
                resource_snapshot=lambda _run, _reserve: {
                    "free_bytes": 10, "reserve_bytes": 0,
                    "estimated_write_bytes": 0, "sufficient": True,
                }, record_stop=recorded,
                elapsed_clock=Mock(side_effect=(5.0, 5.5)))

        self.assertEqual(result.status, "VISIT_LIMIT")
        self.assertEqual(result.visits, 1)
        self.assertEqual(result.accepted, 1)
        self.assertIsNone(result.admission_status)
        self.assertEqual(result.admission_advances, 0)
        self.assertEqual(recorded.call_args.kwargs["status"], "VISIT_LIMIT")

    def test_error_termination_does_not_emit_normal_stop_receipt(self):
        recorded = Mock()
        with TemporaryDirectory() as temporary, self.assertRaisesRegex(
                RuntimeError, "candidate exploded"):
            operate(
                Path(temporary), minutes=1, max_visits=1, steps_per_visit=4,
                reserve_gib=0.0, source_prefetch_workers=0, progress=None,
                max_horizon=16, worker_counts=(0, 1, 2),
                invalid=lambda reason: (_ for _ in ()).throw(ValueError(reason)),
                metrics_type=lambda: SimpleNamespace(
                    wait_seconds=0.0, overlap_seconds=0.0,
                    prepared_steps=0, serial_steps=0),
                source_pool_factory=lambda _workers: nullcontext(None),
                null_context=nullcontext, operator_lock=lambda _run: nullcontext(),
                visit_fn=Mock(side_effect=RuntimeError("candidate exploded")),
                observer_type=lambda *_args: nullcontext(SimpleNamespace(
                    finish=lambda _outcome: None)),
                emit_progress=lambda *_args: None, monotonic=Mock(return_value=0.0),
                load_generation=Mock(), result_type=object,
                resource_snapshot=lambda _run, _reserve: {
                    "free_bytes": 10, "reserve_bytes": 0,
                    "estimated_write_bytes": 0, "sufficient": True,
                }, record_stop=recorded,
                elapsed_clock=Mock(return_value=0.0))
        recorded.assert_not_called()

    def test_bamf_status_reports_prior_stop_disposition(self):
        from bilqis_mlx.presentation.operator_cli.inspection import _inspect
        student = SimpleNamespace(
            run_id="run:r01", generation=4,
            retained_state=SimpleNamespace(optimizer_step=11),
            run_identity=SimpleNamespace(factory_release_sha256="c" * 64),
            topology=SimpleNamespace(digest="d" * 64),
            teacher_state={"teacher_epoch": 2, "cursor": "cursor", "next_seed": 8},
        )
        stop = {
            "schema": "bilqis.bamf.run-stop/v1",
            "stop_reason": "TIME_LIMIT",
            "resume_disposition": "RESUME_ALLOWED",
            "safe_resume_available": True,
        }
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "bamf-state.json").write_text("{}")
            with patch(
                    "bilqis_mlx.runtime.bamf_bundle.load_bamf_generation_authority",
                    return_value=(student, "a" * 64)), patch(
                    "bilqis_mlx.runtime.bamf_operator.read_latest_run_stop_receipt",
                    return_value=stop):
                report = _inspect(run_dir)
        self.assertEqual(report["last_session_stop"], stop)


if __name__ == "__main__":
    unittest.main()
