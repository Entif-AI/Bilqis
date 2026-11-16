"""CP03 current query parity with the existing C11 read-only status surface."""
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bilqis_mlx.control_plane import ControlPlaneClient, ControlPlaneService
from bilqis_mlx.mission_control.model import (
    AuthorityClass, CoverageState, RecordMeta, RunRef,
)
from bilqis_mlx.mission_control.query_catalog import MissionControlQueryCatalog
from bilqis_mlx.mission_control.query_contracts import QueryFamily, QueryRequest, QueryState
from bilqis_mlx.mission_control.snapshots import OperatorView, RunContext
from bilqis_mlx.presentation.operator_cli.inspection import _inspect

from .support import start_service


class ControlPlaneC11QueryTests(unittest.TestCase):
    def test_current_query_matches_c11_disposable_run_truth_without_mutation(self):
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
            (run_dir / "state.json").write_text(
                json.dumps(saved, sort_keys=True), encoding="utf-8")
            before = (run_dir / "state.json").read_bytes()
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
            service = ControlPlaneService(
                run_dir, root / "cp.sock",
                query_source=lambda: MissionControlQueryCatalog(records),
            )
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
                operator_view = next(
                    item for item in page["records"]
                    if item["schema_version"].endswith("operator-view/v1"))
                self.assertEqual(run_context["run_state"], status["status"])
                self.assertEqual(run_context["optimizer_step"], status["optimizer_step"])
                self.assertEqual(run_context["stage"], status["phase"])
                self.assertEqual(operator_view["learner_state"], status["status"])
                self.assertEqual(operator_view["stage"], status["phase"])
            finally:
                service.shutdown()
                thread.join(2)
            self.assertEqual((run_dir / "state.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
