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
        "protected_scope_state": "MEASURED",
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
        self.assertEqual(second["distance_to_mastery_state"], "MEASURED")
        self.assertEqual(second["distance_to_mastery"], 2)
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
        self.assertEqual(
            health["protected_regression_state"], "OBSERVED_REGRESSION")

        unknown = visit(10)
        unknown["protected_scope_state"] = "UNKNOWN"
        unknown["protected"] = []
        unknown_health = project_learning_health(unknown, accepted=True)
        self.assertEqual(
            unknown_health["protected_regression_state"], "NOT_MEASURED")

    def test_certified_surface_regression_is_grade_neutral_when_producer_supplies_evidence(self):
        current = visit(7, grade="grade:disposable-z")
        health = project_learning_health(
            current, accepted=True, certified_surfaces=({
                "surface_id": "certification:prior-surface",
                "capability_id": "arith.successor",
                "rubric_sha256": "c" * 64, "source_sha256": "d" * 64,
                "fixed_cohort_sha256": "b" * 64,
                "retention_policy_sha256": "a" * 64,
                "certified_checkpoint_sha256": "f" * 64,
                "state": "MEASURED", "after": 9, "total": 10,
            },))
        self.assertEqual(health["distance_to_mastery"], 3)
        self.assertEqual(health["qualification_state"], "NOT_MEASURED")
        self.assertEqual(
            health["prior_certified_surface_ids"], ("certification:prior-surface",))
        self.assertEqual(
            health["certified_surface_regression_state"], "OBSERVED_REGRESSION")

        equal = project_learning_health(
            visit(9, grade="grade:another-future"), accepted=True,
            certified_surfaces=({
                "surface_id": "certification:prior-surface",
                "capability_id": "arith.successor",
                "rubric_sha256": "c" * 64, "source_sha256": "d" * 64,
                "fixed_cohort_sha256": "b" * 64,
                "retention_policy_sha256": "a" * 64,
                "certified_checkpoint_sha256": "f" * 64,
                "state": "MEASURED", "after": 9, "total": 10,
            },))
        self.assertEqual(equal["certified_surface_regression_state"], "NOT_OBSERVED")

        incomparable = project_learning_health(
            visit(7), accepted=True, certified_surfaces=({
                "surface_id": "certification:other-rubric",
                "capability_id": "arith.successor",
                "rubric_sha256": "9" * 64, "source_sha256": "d" * 64,
                "fixed_cohort_sha256": "b" * 64,
                "retention_policy_sha256": "e" * 64,
                "certified_checkpoint_sha256": "f" * 64,
                "state": "MEASURED", "after": 10, "total": 10,
            },))
        self.assertEqual(
            incomparable["certified_surface_regression_state"], "NOT_MEASURED")

        other_policy = project_learning_health(
            visit(7), accepted=True, certified_surfaces=({
                "surface_id": "certification:other-policy",
                "capability_id": "arith.successor",
                "rubric_sha256": "c" * 64, "source_sha256": "d" * 64,
                "fixed_cohort_sha256": "b" * 64,
                "retention_policy_sha256": "e" * 64,
                "certified_checkpoint_sha256": "f" * 64,
                "state": "MEASURED", "after": 10, "total": 10,
            },))
        self.assertEqual(
            other_policy["certified_surface_regression_state"], "NOT_MEASURED")

    def test_s3_requires_three_distinct_accepted_checkpoints_on_fixed_school(self):
        previous = None
        for index, score in enumerate((4, 8, 5)):
            current = visit(score)
            current["accepted_checkpoint_sha256"] = str(index + 1) * 64
            current["accepted_optimizer_step"] = index + 1
            previous = project_learning_health(
                current, accepted=True, previous=previous)
            if index < 2:
                self.assertEqual(previous["warnings"][2]["status"], "NOT_MEASURED")
        self.assertEqual(previous["warnings"][2]["status"],
                         "OBSERVED_LONGITUDINALLY")
        self.assertEqual(previous["warnings"][2]["evidence_count"], 3)
        self.assertEqual(previous["best"]["correct"], 8)
        self.assertEqual(previous["latest"]["correct"], 5)
        self.assertEqual(len(previous["recent_checkpoints"]), 3)

    def test_s3_ignores_replay_and_changed_fixed_cohort(self):
        first = visit(4)
        first["accepted_checkpoint_sha256"] = "a" * 64
        first["accepted_optimizer_step"] = 1
        saved = project_learning_health(first, accepted=True)
        replay = project_learning_health(first, accepted=True, previous=saved)
        self.assertEqual(replay["warnings"][2]["status"], "NOT_MEASURED")
        self.assertEqual(len(replay["recent_checkpoints"]), 1)
        changed = visit(7, cohort="e")
        changed["accepted_checkpoint_sha256"] = "b" * 64
        changed["accepted_optimizer_step"] = 2
        different = project_learning_health(changed, accepted=True, previous=replay)
        self.assertEqual(len(different["recent_checkpoints"]), 1)

    def test_s3_fails_closed_on_backward_step_and_same_checkpoint_drift(self):
        first = visit(4)
        first.update(accepted_checkpoint_sha256="a" * 64, accepted_optimizer_step=10)
        saved = project_learning_health(first, accepted=True)
        backward = visit(6)
        backward.update(accepted_checkpoint_sha256="b" * 64, accepted_optimizer_step=9)
        reset = project_learning_health(backward, accepted=True, previous=saved)
        self.assertEqual(reset["history_state"], "INVALID")
        self.assertEqual(
            reset["history_error"], "NON_MONOTONIC_OPTIMIZER_STEP")
        self.assertEqual(reset["warnings"][2]["status"], "NOT_MEASURED")
        drift = visit(7)
        drift.update(accepted_checkpoint_sha256="a" * 64, accepted_optimizer_step=10)
        reset_again = project_learning_health(drift, accepted=True, previous=saved)
        self.assertEqual(reset_again["history_state"], "INVALID")
        self.assertEqual(
            reset_again["history_error"], "CHECKPOINT_EVIDENCE_DIVERGENCE")


if __name__ == "__main__":
    unittest.main()
