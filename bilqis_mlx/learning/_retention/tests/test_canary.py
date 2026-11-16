"""Reject-only retention-canary policy and calibration tests."""
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning._retention import canary


def _review(*, false_kill=False, would_stop=True):
    return {
        "schema": canary.SCHEMA,
        "channel": "RETENTION_TARGET_CANARY",
        "mode": "SHADOW",
        "policy_version": canary.DEFAULT_POLICY.version,
        "first_would_stop_step": 8 if would_stop else None,
        "final_retained": false_kill,
        "false_kill": false_kill,
        "false_continue": False,
        "actual_steps_spent": 16,
        "shadow_steps_if_active": 8 if would_stop else 16,
        "shadow_steps_saved": 8 if would_stop else 0,
    }


class RetentionCanaryTests(unittest.TestCase):
    rows = ({"id": "q1", "gold": "TRUE"}, {"id": "q2", "gold": "FALSE"})
    parent = {"q1": "TRUE", "q2": "FALSE"}

    def test_shadow_probe_cannot_stop_before_activation(self):
        state = canary.activation({})
        receipt = canary.probe(
            canary.DEFAULT_POLICY, rung=8, full_budget_steps=16,
            rows=self.rows, parent_predictions=self.parent,
            candidate_predictions=self.parent, activation_state=state)
        self.assertEqual(state["status"], "NOT_QUALIFIED")
        self.assertTrue(receipt["would_stop"])
        self.assertFalse(receipt["stop"])
        self.assertEqual(receipt["authority"], "REJECT_ONLY")

    def test_qualified_history_activates_rung_eight_stop(self):
        teacher = {
            "retention_canary_projection": {
                "schema": canary.HISTORY_SCHEMA,
                "reviews": [_review() for _ in range(64)],
            },
        }
        state = canary.activation(teacher)
        receipt = canary.probe(
            canary.DEFAULT_POLICY, rung=8, full_budget_steps=16,
            rows=self.rows, parent_predictions=self.parent,
            candidate_predictions=self.parent, activation_state=state)
        self.assertEqual(state["status"], "QUALIFIED")
        self.assertTrue(receipt["stop"])

    def test_positive_target_gain_never_stops_even_when_qualified(self):
        teacher = {
            "retention_canary_projection": {
                "schema": canary.HISTORY_SCHEMA,
                "reviews": [_review() for _ in range(64)],
            },
        }
        rows = ({"id": "q1", "gold": "TRUE"}, {"id": "q3", "gold": "TRUE"})
        parent = {"q1": "TRUE", "q3": "FALSE"}
        candidate = {"q1": "TRUE", "q3": "TRUE"}
        receipt = canary.probe(
            canary.DEFAULT_POLICY, rung=8, full_budget_steps=16,
            rows=rows, parent_predictions=parent,
            candidate_predictions=candidate, activation_state=canary.activation(teacher))
        self.assertEqual(receipt["target_correct_delta"], 1)
        self.assertFalse(receipt["would_stop"])
        self.assertFalse(receipt["stop"])

    def test_shadow_completion_promotes_calibration_only_after_enough_reviews(self):
        teacher = {
            "retention_canary_projection": {
                "schema": canary.HISTORY_SCHEMA,
                "reviews": [_review() for _ in range(63)],
            },
        }
        receipt = canary.probe(
            canary.DEFAULT_POLICY, rung=8, full_budget_steps=16,
            rows=self.rows, parent_predictions=self.parent,
            candidate_predictions=self.parent, activation_state=canary.activation(teacher))
        completed = canary.complete(
            teacher, receipt, final_retained=False, spent_steps=16,
            full_budget_steps=16)
        self.assertEqual(completed["post_visit_activation"]["status"], "QUALIFIED")
        self.assertEqual(len(teacher["retention_canary_projection"]["reviews"]), 64)

    def test_active_stop_must_be_confirmed_by_authoritative_target_rejection(self):
        teacher = {
            "retention_canary_projection": {
                "schema": canary.HISTORY_SCHEMA,
                "reviews": [_review() for _ in range(64)],
            },
        }
        receipt = canary.probe(
            canary.DEFAULT_POLICY, rung=8, full_budget_steps=16,
            rows=self.rows, parent_predictions=self.parent,
            candidate_predictions=self.parent, activation_state=canary.activation(teacher))
        canary.require_confirmed_reject(
            receipt, stage="TARGET_ONLY_REJECTED",
            outcome={"decision": "REJECT", "reason": "NO_MEASURABLE_TARGET_GAIN"})
        with self.assertRaises(BilqisError):
            canary.require_confirmed_reject(
                receipt, stage="COMPLETE_SAME_GRADE",
                outcome={"decision": "PROVISIONAL", "reason": "PAIRED_SCREEN_WITHIN_BUDGET"})


if __name__ == "__main__":
    unittest.main()
