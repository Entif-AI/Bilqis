"""Cold restart keeps only bounded, accepted learning-health observations."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bilqis_mlx.diagnostics.learning_health import project_learning_health
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
    def test_restart_preserves_first_latest_best_without_claiming_qualification(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bamf-state.json").write_text(json.dumps({
                "run_id": "run", "manifest_sha256": "a" * 64,
            }))
            first = project_learning_health(_visit(4), accepted=True)
            with TrainerObservation(root, 1, heartbeat_seconds=60) as observation:
                observation.update(learning_health=first)
                observation.finish("ACCEPTED")
            with TrainerObservation(root, 2, heartbeat_seconds=60) as observation:
                previous = observation.learning_health_by_capability["novel:successor"]
                next_health = project_learning_health(
                    _visit(8), accepted=True, previous=previous)
                observation.update(learning_health=next_health)
                observation.finish("ACCEPTED")
            payload = json.loads((root / "trainer-observed.json").read_text())
            health = payload["learning_health_by_capability"]["novel:successor"]
            self.assertEqual(health["first"]["correct"], 4)
            self.assertEqual(health["best"]["correct"], 8)
            self.assertEqual(health["gain_from_first"], 4)
            self.assertEqual(health["qualification_state"], "NOT_MEASURED")
            self.assertEqual(payload["schema"], "bilqis.bamf.trainer-observed/v5")

    def test_nonaccepted_visit_cannot_change_accepted_summary(self):
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
                observation.update(phase="RETENTION")
                observation.finish("REJECTED")
            with TrainerObservation(root, 3) as observation:
                self.assertEqual(
                    observation.learning_health_by_capability[
                        "novel:successor"]["latest"]["correct"], 4)
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
