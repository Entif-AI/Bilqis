"""Operator-facing authority and partial-measurement projections."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from bilqis_mlx.presentation.school50.exams import ExamsProjection
from bilqis_mlx.presentation.school50.labels import _candidate_admission_text, _candidate_result_reason


class AuthorityConsumerTests(unittest.TestCase):
    def test_candidate_retention_projects_evidence_without_inventing_regression(self):
        event = {"candidate_retention": {"decision": "REJECT", "reason": "BASELINE_ABSENT"},
                 "retained_optimizer_updates": 0}
        self.assertIn("Baseline absent or unmeasured", _candidate_result_reason(event)[1])
        self.assertIn("Baseline absent or unmeasured", _candidate_admission_text(event))
        event["candidate_retention"].update(reason="PROTECTED_CAPABILITY_REGRESSION",
                                            blocking_capability="A.LINK")
        self.assertIn("blocking capability A.LINK", _candidate_result_reason(event)[1])
        self.assertIn("blocking capability A.LINK", _candidate_admission_text(event))
        event["candidate_retention"]["reason"] = "FUTURE_REASON"
        self.assertIn("FUTURE_REASON", _candidate_result_reason(event)[1])

    def test_withheld_exam_is_partial_even_with_a_champion(self):
        projection = ExamsProjection()
        projection.champions = {"A": object()}
        outcome, _ = projection._exam_outcome(
            "A", "A", {}, {"withheld_capabilities": ["A.Z", "A.B"]},
            True, 5, 12, 1)
        self.assertEqual(outcome, "PARTIAL EXAM | SAMPLE 5/12 | NOT_MEASURED: A.B, A.Z")
        complete, _ = projection._exam_outcome("A", "A", {}, {}, True, 5, 12, 1)
        self.assertEqual(complete, "CURRENT REGRESSION | SAMPLE 5/12")

    def test_withheld_is_visible_on_flash_title_and_live_decisions(self):
        projection = ExamsProjection()
        projection.champions = {"A": object()}
        projection.board = SimpleNamespace(push=Mock())
        base = {"withheld_capabilities": ["A.Z", "A.B"]}
        cases = (
            ({**base, "flash_scheduler_only": True}, "FLASH SAMPLE 5/12 | NO TITLES"),
            ({**base, "championship_epoch": {"earned_roles": ["A.B"]}}, "TITLE MOVED 1 | SAMPLE 5/12"),
            ({**base, "championship_epoch": {}}, "NO TITLE CHANGE | SAMPLE 5/12"),
        )
        for event, prefix in cases:
            with self.subTest(event=event):
                outcome, _ = projection._exam_outcome(
                    "A", "A", {"A.B": (5, 12)}, event, True, 5, 12, 1)
                self.assertEqual(outcome, prefix + " | PARTIAL EXAM | NOT_MEASURED: A.B, A.Z")
