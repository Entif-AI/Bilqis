"""Currentness subspans stay diagnostic and outside CP02 authority."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.control_plane.observed import observed_records
from bilqis_mlx.control_plane.tests.observed import test_source as support


class ObservedCurrentnessMetricTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_v6_currentness_subspans_are_preserved_as_measured_partial_diagnostics(self):
        step = {
            key: value for key, value in support.performance().items()
            if key not in {
                "retention_wall_seconds",
                "evidence_finalization_wall_seconds",
                "publishing_wall_seconds",
            }
        }
        step.update(
            candidate_step=1,
            candidate_optimizer_step=8,
            accepted_currentness_refresh_wall_seconds=0.001,
            accepted_currentness_live_fence_wall_seconds=0.001,
            accepted_parent_currentness_wall_seconds=0.001,
            lawful_frontier_currentness_wall_seconds=0.08,
            teacher_visit_currentness_wall_seconds=0.04,
            source_currentness_wall_seconds=0.02,
            candidate_binding_wall_seconds=0.05,
        )
        row = support.visit(
            **support.performance(),
            candidate_steps=[step],
            planning_wall_seconds=None,
            source_materialization_wall_seconds=None,
            target_evaluation_wall_seconds=None,
            protected_retention_wall_seconds=None,
            broad_certification_wall_seconds=None,
            visit_evidence=None,
            generated_grade_evidence=None,
            retention_stage_timings=[],
            learning_health=None,
            accepted_currentness_refresh_wall_seconds=0.001,
            accepted_currentness_live_fence_wall_seconds=0.001,
            accepted_parent_currentness_wall_seconds=0.001,
            lawful_frontier_currentness_wall_seconds=0.08,
            teacher_visit_currentness_wall_seconds=0.04,
            source_currentness_wall_seconds=0.02,
            candidate_binding_wall_seconds=0.05,
        )
        (self.root / "trainer-observed.json").write_text(json.dumps({
            "schema": "bilqis.bamf.trainer-observed/v6",
            "visits": [row],
        }))
        with patch(
                "bilqis_mlx.control_plane.observed.source.process_exists",
                return_value=True):
            observed = observed_records(
                self.root, (support.RUN,), now_ms=101000)[0]
        self.assertEqual(
            observed.schema_version,
            "bilqis.bamf.mission-control.trainer-observation/v6",
        )
        self.assertEqual(len(observed.candidate_steps), 1)
        self.assertEqual(observed.candidate_steps[0].candidate_step, 1)
        self.assertEqual(
            observed.candidate_steps[0].lawful_frontier_currentness_wall_seconds,
            0.08,
        )
        self.assertEqual(observed.lawful_frontier_currentness_wall_seconds, 0.08)
        self.assertEqual(observed.meta.authority.value, "MEASURED")
        self.assertEqual(observed.meta.coverage.value, "PARTIAL")


def test_v7_activity_is_projected_as_measured_partial_operator_state(tmp_path):
    from unittest.mock import patch
    from bilqis_mlx.control_plane.observed import observed_records
    from bilqis_mlx.control_plane.tests.observed import test_source as support

    step = {
        key: value for key, value in support.performance().items()
        if key not in {"retention_wall_seconds", "evidence_finalization_wall_seconds",
                       "publishing_wall_seconds"}
    }
    step.update(candidate_step=1, candidate_optimizer_step=8)
    row = support.visit(
        **support.performance(), candidate_steps=[step],
        planning_wall_seconds=None, source_materialization_wall_seconds=None,
        target_evaluation_wall_seconds=None, protected_retention_wall_seconds=None,
        broad_certification_wall_seconds=None, visit_evidence=None,
        generated_grade_evidence=None, retention_stage_timings=[], learning_health=None,
        activity="planner: compiling semantic curriculum", activity_elapsed_ms=4200)
    (tmp_path / "trainer-observed.json").write_text(json.dumps({
        "schema": "bilqis.bamf.trainer-observed/v7", "visits": [row],
    }))
    with patch("bilqis_mlx.control_plane.observed.source.process_exists", return_value=True):
        observed = observed_records(tmp_path, (support.RUN,), now_ms=101000)[0]
    assert observed.schema_version == "bilqis.bamf.mission-control.trainer-observation/v7"
    assert observed.activity == "planner: compiling semantic curriculum"
    assert observed.activity_elapsed_ms == 4200
    assert observed.meta.authority.value == "MEASURED"
    assert observed.meta.coverage.value == "PARTIAL"
