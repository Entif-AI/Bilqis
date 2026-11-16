"""Cold restart keeps only bounded, accepted learning-health observations."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from bilqis_mlx.diagnostics.learning_health import STATE_SCHEMA, project_learning_health
from bilqis_mlx.runtime.bamf_operator.learning_health_runtime import (
    accepted_learning_health_from_parent, accepted_learning_health_state,
)
from bilqis_mlx.runtime.bamf_operator.telemetry import TrainerObservation


def _visit(score):
    return {
        "capability_id": "novel:successor", "grade_id": "grade:future",
        "grade_definition_id": None, "grade_definition_version": None,
        "retention_policy_sha256": "a" * 64,
        "fixed_cohort_sha256": "b" * 64,
        "rubric_sha256": "c" * 64, "source_sha256": "d" * 64,
        "target": {"state": "MEASURED", "before": score - 1,
                   "after": score, "total": 10},
        "protected": [],
    }


class AcceptedLearningObservationTests(unittest.TestCase):
    def test_authenticated_sidecar_state_preserves_bounded_health(self):
        health = project_learning_health(_visit(4), accepted=True)
        retained = SimpleNamespace(optimizer_step=4)
        parent = SimpleNamespace(
            run_id="run", generation=1, retained_state=retained,
            learning_health_state={
                "schema": STATE_SCHEMA,
                "coverage_state": "VALID",
                "by_capability": {"novel:successor": health},
                "certified_surfaces": [],
            })
        restored = accepted_learning_health_from_parent(parent)
        self.assertEqual(restored["novel:successor"]["latest"]["correct"], 4)
        self.assertEqual(restored["novel:successor"]["qualification_state"],
                         "NOT_MEASURED")

    def test_missing_history_on_active_run_bootstraps_partial_not_fabricated(self):
        retained = SimpleNamespace(optimizer_step=4)
        parent = SimpleNamespace(
            run_id="run", generation=3, retained_state=retained,
            learning_health_state=None)
        self.assertEqual(accepted_learning_health_from_parent(parent), {})

    def test_certified_surface_flows_through_live_accepted_state_projection(self):
        visit = _visit(7)
        visit.update({
            "accepted_checkpoint_sha256": "9" * 64,
            "accepted_optimizer_step": 5,
        })
        certified = {
            "surface_id": "certification:prior",
            "capability_id": "novel:successor",
            "rubric_sha256": "c" * 64, "source_sha256": "d" * 64,
            "fixed_cohort_sha256": "b" * 64,
            "retention_policy_sha256": "a" * 64,
            "certified_checkpoint_sha256": "f" * 64,
            "state": "MEASURED", "after": 9, "total": 10,
        }
        retained = SimpleNamespace(optimizer_step=5)
        parent = SimpleNamespace(
            run_id="run", generation=4,
            retained_state=SimpleNamespace(optimizer_step=4),
            learning_health_state={
                "schema": STATE_SCHEMA, "coverage_state": "VALID",
                "by_capability": {}, "certified_surfaces": [certified],
            })
        capture = SimpleNamespace(learning_methodology=lambda: ())
        with patch(
                "bilqis_mlx.runtime.bamf_operator.learning_health_runtime.selected_visit_evidence",
                return_value={}), patch(
                "bilqis_mlx.runtime.bamf_operator.learning_health_runtime.complete_visit_evidence",
                return_value=visit), patch(
                "bilqis_mlx.runtime.bamf_operator.learning_health_runtime.candidate_identity_digest",
                return_value="9" * 64):
            state, health = accepted_learning_health_state(
                Path("."), parent, object(), {}, object(), retained, capture)
        self.assertEqual(
            health["certified_surface_regression_state"], "OBSERVED_REGRESSION")
        self.assertEqual(
            state["certified_surfaces"][0]["surface_id"], "certification:prior")

    def test_telemetry_snapshot_is_not_reloaded_as_learning_authority(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bamf-state.json").write_text(json.dumps({
                "run_id": "run", "manifest_sha256": "a" * 64,
            }))
            first = project_learning_health(_visit(4), accepted=True)
            with TrainerObservation(root, 1) as observation:
                observation.update(learning_health=first)
                observation.finish("ACCEPTED")
            with TrainerObservation(root, 2) as observation:
                self.assertEqual(observation.learning_health_by_capability, {})
                observation.finish("HELD")

    def test_reusing_directory_with_different_run_discards_health(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            pointer = root / "bamf-state.json"
            pointer.write_text(json.dumps({
                "run_id": "first-run", "manifest_sha256": "a" * 64,
            }))
            with TrainerObservation(root, 1) as observation:
                observation.update(learning_health=project_learning_health(
                    _visit(4), accepted=True))
                observation.finish("ACCEPTED")
            pointer.write_text(json.dumps({
                "run_id": "second-run", "manifest_sha256": "b" * 64,
            }))
            with TrainerObservation(root, 1) as observation:
                self.assertEqual(observation.learning_health_by_capability, {})
                observation.finish("HELD")


if __name__ == "__main__":
    unittest.main()
