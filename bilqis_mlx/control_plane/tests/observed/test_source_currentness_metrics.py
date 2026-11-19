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

    def test_v6_currentness_subspans_remain_raw_diagnostics_not_cp02_authority(self):
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
            "bilqis.bamf.mission-control.trainer-observation/v5",
        )
        self.assertEqual(len(observed.candidate_steps), 1)
        self.assertEqual(observed.candidate_steps[0].candidate_step, 1)
        self.assertFalse(hasattr(
            observed.candidate_steps[0],
            "lawful_frontier_currentness_wall_seconds",
        ))
