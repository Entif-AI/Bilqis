"""Accepted-only, grade-neutral learning health and epoch comparison."""
import unittest

from bilqis_mlx.diagnostics.learning_health import project_learning_health


def visit(correct, *, grade="Z.future", epoch="a", cohort="b"):
    return {
        "capability_id": "arith.successor", "grade_id": grade,
        "grade_definition_id": "definition.future", "grade_definition_version": "v9",
        "retention_policy_sha256": epoch * 64,
        "rubric_sha256": "c" * 64, "source_sha256": "d" * 64,
        "fixed_cohort_sha256": cohort * 64,
        "target": {"state": "MEASURED", "before": 3,
                   "after": correct, "total": 10},
        "protected": [{"capability_id": "predecessor.one",
                       "state": "MEASURED", "before": 8, "after": 7,
                       "total": 10}],
    }


class LearningHealthTests(unittest.TestCase):
    def test_only_accepted_checkpoint_advances_first_latest_best(self):
        first = project_learning_health(visit(4), accepted=True)
        second = project_learning_health(visit(8), accepted=True, previous=first)
        rejected = project_learning_health(visit(10), accepted=False, previous=second)
        self.assertEqual(second["first"], {"correct": 4, "total": 10})
        self.assertEqual(second["best"], {"correct": 8, "total": 10})
        self.assertEqual(second["gain_from_first"], 4)
        self.assertEqual(second["fixed_screen_errors"], 2)
        self.assertIsNone(second["distance_to_mastery"])
        self.assertEqual(rejected["state"], "NOT_MEASURED")
        self.assertIsNone(rejected["latest"])

    def test_changed_cohort_and_policy_do_not_combine_scores(self):
        first = project_learning_health(visit(6), accepted=True)
        for changed in (visit(8, cohort="e"), visit(8, epoch="f")):
            latest = project_learning_health(changed, accepted=True, previous=first)
            self.assertEqual(latest["first"]["correct"], 8)
            self.assertIsNone(latest["gain_from_first"])

    def test_future_grade_and_warning_evidence_are_non_authoritative(self):
        current = visit(10)
        current["learning_signals"] = (
            {"signal": "REPETITIVE_ANSWERS", "status": "OBSERVED_IN_COHORT",
             "note": "Constant answer", "evidence_count": 10},
        )
        health = project_learning_health(current, accepted=True)
        self.assertEqual(health["grade_id"], "Z.future")
        self.assertEqual(health["warnings"][0]["status"], "OBSERVED_IN_COHORT")
        self.assertEqual(health["warnings"][1]["status"], "NOT_MEASURED")
        self.assertEqual(health["warnings"][3]["status"], "NOT_MEASURED")
        self.assertEqual(health["warnings"][4]["status"], "NOT_MEASURED")
        self.assertEqual(health["qualification_state"], "NOT_MEASURED")
        self.assertEqual(health["certified_surface_regression_state"], "NOT_MEASURED")
        self.assertEqual(health["regressed_protected_capabilities"],
                         ("predecessor.one",))


if __name__ == "__main__":
    unittest.main()
