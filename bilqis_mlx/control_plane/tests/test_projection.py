"""CP06 projection integration with CP03 queries and disposable C11 truth."""
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.control_plane import ControlPlaneClient, ControlPlaneService
from bilqis_mlx.control_plane.discovery import discover_learner
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.mission_control.model import (
    AuthorityClass, CoverageState, RecordMeta, RunRef,
)
from bilqis_mlx.mission_control.projection import MissionControlProjection
from bilqis_mlx.mission_control.query_contracts import (
    QueryFamily, QueryRequest, QueryState,
)
from bilqis_mlx.mission_control.snapshots import OperatorView, RunContext
from bilqis_mlx.presentation.operator_cli.inspection import _inspect
from bilqis_mlx.presentation.operator_cli.tests.bamf_lifecycle.create_resume_support import (
    BamfCreateResumeCase, TOPOLOGY,
)

from .support import start_service


class ControlPlaneProjectionTests(unittest.TestCase):
    def test_projection_queries_same_disposable_run_without_mutating_source(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "c11-run"
            run_dir.mkdir()
            saved = {
                "schema": "bilqis.mlx.letter-grade/v1",
                "active_grades": ["A"], "grade_index": 0,
                "stage": "ASSESS_MAIN", "visits": 3,
                "current_student": {
                    "optimizer_step": 42, "sha256": "a" * 64,
                },
                "champions": {},
            }
            state_path = run_dir / "state.json"
            state_path.write_text(json.dumps(saved, sort_keys=True), encoding="utf-8")
            before = state_path.read_bytes()
            status = _inspect(run_dir)
            run = RunRef(
                "c11-disposable", "1" * 64, 0, "2" * 64,
                "3" * 64, "4" * 64, "5" * 64, "6" * 64,
            )
            meta = RecordMeta(
                "operator-view:c11-disposable", run, 1, 1, 1,
                CoverageState.COMPLETE, AuthorityClass.DERIVED,
                evidence_refs=("evidence:c11-status",),
                receipt_refs=("receipt:c11-status",),
            )
            records = (
                RunContext(
                    replace(meta, record_id="run-context:c11-disposable"),
                    status["status"], status["optimizer_step"], status["phase"],
                ),
                OperatorView(meta, status["status"], status["phase"], None, ()),
            )
            projection_path = root / "mission-control.sqlite3"
            projection = MissionControlProjection.rebuild(projection_path, records)
            service = ControlPlaneService(
                run_dir, root / "cp.sock", query_source=projection.catalog)
            thread = start_service(service)
            try:
                with ControlPlaneClient(root / "cp.sock") as client:
                    page = client.query(QueryRequest(
                        QueryFamily.RUN, run_id="c11-disposable"))
                self.assertEqual(page["state"], QueryState.PRESENT.value)
                self.assertEqual(page["total_matches"], 2)
                run_context = next(
                    item for item in page["records"]
                    if item["schema_version"].endswith("run-context/v1"))
                self.assertEqual(run_context["run_state"], status["status"])
                self.assertEqual(run_context["optimizer_step"], status["optimizer_step"])
                self.assertEqual(run_context["stage"], status["phase"])
            finally:
                service.shutdown()
                thread.join(2)
            self.assertEqual(state_path.read_bytes(), before)

            projection_path.unlink()
            with self.assertRaises(BilqisError) as missing:
                projection.catalog()
            self.assertEqual(
                missing.exception.context["reason"],
                "PROJECTION_MISSING_REBUILD_REQUIRED",
            )
            self.assertEqual(_inspect(run_dir), status)
            self.assertEqual(state_path.read_bytes(), before)
            rebuilt = MissionControlProjection.rebuild(projection_path, records)
            self.assertEqual(rebuilt.stats().active_records, 2)
            projection_path.write_bytes(b"corrupt-projection")
            self.assertEqual(_inspect(run_dir), status)
            self.assertEqual(state_path.read_bytes(), before)
            recovered = MissionControlProjection.rebuild(projection_path, records)
            self.assertEqual(recovered.stats().active_records, 2)


class ControlPlaneProjectionBamfIntegrationTests(BamfCreateResumeCase):
    def _create_disposable_generation_zero(self) -> Path:
        target = self.root / "created-bamf"
        manifest = self.root / "manifest.json"
        manifest.write_text("{}", encoding="utf-8")
        with self.foundation_create_context():
            code, _output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--atlas-release-manifest", str(manifest),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])
        self.assertEqual((code, errors), (0, ""))
        return target

    def test_projection_corruption_and_deletion_never_block_real_bamf_learner(self):
        target = self._create_disposable_generation_zero()
        pointer = target / "bamf-state.json"
        before = pointer.read_bytes()
        projection_path = self.root / "mission-control.sqlite3"
        with patch(
                "bilqis_mlx.runtime.mlx_checkpoint.load_bamf_state_payload",
                side_effect=AssertionError("CP06 must not hydrate numerical state")):
            learner = discover_learner(target)
            self.assertEqual(learner.run_id, "operator-first-student")
            self.assertEqual(learner.generation, 0)

            projection = MissionControlProjection.rebuild(projection_path, ())
            self.assertEqual(projection.stats().active_records, 0)
            projection_path.unlink()
            self.assertEqual(discover_learner(target), learner)
            self.assertEqual(pointer.read_bytes(), before)

            projection_path.write_bytes(b"corrupt-projection")
            with self.assertRaises(BilqisError):
                MissionControlProjection(projection_path)
            self.assertEqual(discover_learner(target), learner)
            self.assertEqual(pointer.read_bytes(), before)

            rebuilt = MissionControlProjection.rebuild(projection_path, ())
            self.assertEqual(rebuilt.stats().active_records, 0)
            self.assertEqual(discover_learner(target), learner)
            self.assertEqual(pointer.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
