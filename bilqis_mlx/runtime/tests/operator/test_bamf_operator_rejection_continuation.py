"""Regression coverage for persistent operation across ordinary rejections."""
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.runtime.bamf_operator.session import operate_bamf


class BamfOperatorRejectionContinuationTests(unittest.TestCase):
    @staticmethod
    def _current():
        return SimpleNamespace(
            generation=0,
            retained_state=SimpleNamespace(optimizer_step=0),
        )

    def test_rejection_continues_to_next_visit_until_real_hold(self):
        progress = []
        current = self._current()
        with TemporaryDirectory() as temporary, patch(
                "bilqis_mlx.runtime.bamf_operator.session._visit",
                side_effect=("REJECTED", "HELD")) as visit, patch(
                "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                return_value=current):
            result = operate_bamf(
                temporary, minutes=1, max_visits=0, reserve_gib=0.0,
                source_prefetch_workers=0, progress=progress.append)

        self.assertEqual(result.status, "PRIORITY_HOLD")
        self.assertEqual(result.visits, 1)
        self.assertEqual(result.accepted, 0)
        self.assertEqual(result.rejected, 1)
        self.assertEqual(result.generation, 0)
        self.assertEqual(result.optimizer_step, 0)
        self.assertEqual(visit.call_count, 2)
        self.assertEqual(progress, [
            "starting visit 1",
            "visit 1 outcome: REJECTED",
            "starting visit 2",
            "visit 2 outcome: HELD",
        ])

    def test_rejected_visit_counts_toward_explicit_visit_limit(self):
        current = self._current()
        with TemporaryDirectory() as temporary, patch(
                "bilqis_mlx.runtime.bamf_operator.session._visit",
                return_value="REJECTED") as visit, patch(
                "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                return_value=current):
            result = operate_bamf(
                temporary, minutes=1, max_visits=1, reserve_gib=0.0,
                source_prefetch_workers=0)

        self.assertEqual(result.status, "VISIT_LIMIT")
        self.assertEqual(result.visits, 1)
        self.assertEqual(result.accepted, 0)
        self.assertEqual(result.rejected, 1)
        visit.assert_called_once()

    def test_rejection_still_yields_to_session_deadline_between_visits(self):
        current = self._current()
        with TemporaryDirectory() as temporary, patch(
                "bilqis_mlx.runtime.bamf_operator.session.time.monotonic",
                side_effect=(0.0, 0.0, 61.0)), patch(
                "bilqis_mlx.runtime.bamf_operator.session._visit",
                return_value="REJECTED") as visit, patch(
                "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                return_value=current):
            result = operate_bamf(
                temporary, minutes=1, max_visits=0, reserve_gib=0.0,
                source_prefetch_workers=0)

        self.assertEqual(result.status, "TIME_LIMIT")
        self.assertEqual(result.visits, 1)
        self.assertEqual(result.accepted, 0)
        self.assertEqual(result.rejected, 1)
        visit.assert_called_once()

    def test_uncapped_session_can_reject_then_accept_before_real_hold(self):
        current = SimpleNamespace(
            generation=1,
            retained_state=SimpleNamespace(optimizer_step=4),
        )
        with TemporaryDirectory() as temporary, patch(
                "bilqis_mlx.runtime.bamf_operator.session._visit",
                side_effect=("REJECTED", "ACCEPTED", "HELD")) as visit, patch(
                "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                return_value=current):
            result = operate_bamf(
                temporary, minutes=1, max_visits=0, reserve_gib=0.0,
                source_prefetch_workers=0)

        self.assertEqual(result.status, "PRIORITY_HOLD")
        self.assertEqual(result.visits, 2)
        self.assertEqual(result.accepted, 1)
        self.assertEqual(result.rejected, 1)
        self.assertEqual(result.generation, 1)
        self.assertEqual(result.optimizer_step, 4)
        self.assertEqual(visit.call_count, 3)


if __name__ == "__main__":
    unittest.main()
