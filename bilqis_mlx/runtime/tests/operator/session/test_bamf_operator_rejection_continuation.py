"""Regression coverage for persistent operation across ordinary rejections."""
from contextlib import nullcontext
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError, SCHOOL
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation
from bilqis_mlx.runtime.bamf_operator.session import (
    BamfPreparedVisit, _accepted_admission_reentry, operate_bamf,
)
from bilqis_mlx.runtime.priority_rejection_replay import (
    candidate_step_horizon, current_rejections,
)
from bilqis_mlx.control_plane.native_source import native_query_catalog
from bilqis_mlx.control_plane.tests.cp07.native_source_support import NativeSourceFixture
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    retention_decision, shape_patch,
)


class BamfOperatorRejectionContinuationTests(unittest.TestCase):
    def setUp(self):
        self.run_storage = patch("bilqis_mlx.runtime.run_authority.binding.storage_root", return_value=Path(gettempdir()))
        self.run_storage.start()
        self.addCleanup(self.run_storage.stop)
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
        observer = SimpleNamespace(finish=lambda _outcome: None)
        with TemporaryDirectory() as temporary, patch(
                "bilqis_mlx.runtime.bamf_operator.session.time.monotonic",
                side_effect=(0.0, 0.0, 61.0)), patch(
                "bilqis_mlx.runtime.bamf_operator.session.TrainerObservation",
                return_value=nullcontext(observer)), patch(
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

    def test_action_required_remains_terminal_without_counting_a_neural_visit(self):
        current = self._current()
        with TemporaryDirectory() as temporary, patch(
                "bilqis_mlx.runtime.bamf_operator.session._visit",
                return_value="ACTION_REQUIRED") as visit, patch(
                "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                return_value=current):
            result = operate_bamf(
                temporary, minutes=1, max_visits=0, reserve_gib=0.0,
                source_prefetch_workers=0)

        self.assertEqual(result.status, "ACTION_REQUIRED")
        self.assertEqual((result.visits, result.accepted, result.rejected), (0, 0, 0))
        visit.assert_called_once()

    def test_grade_transition_counts_operation_without_counting_neural_acceptance(self):
        current = self._current()
        with TemporaryDirectory() as temporary, patch(
                "bilqis_mlx.runtime.bamf_operator.session._visit",
                side_effect=("GRADE_TRANSITIONED", "HELD")) as visit, patch(
                "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                return_value=current):
            result = operate_bamf(
                temporary, minutes=1, max_visits=0, reserve_gib=0.0,
                source_prefetch_workers=0)

        self.assertEqual(result.status, "PRIORITY_HOLD")
        self.assertEqual((result.visits, result.accepted, result.rejected), (1, 0, 0))
        self.assertEqual(visit.call_count, 2)

    def test_certification_failure_is_terminal_without_counting_neural_visit(self):
        current = self._current()
        with TemporaryDirectory() as temporary, patch(
                "bilqis_mlx.runtime.bamf_operator.session._visit",
                return_value="CERTIFICATION_FAILED"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                return_value=current):
            result = operate_bamf(
                temporary, minutes=1, max_visits=0, reserve_gib=0.0,
                source_prefetch_workers=0)

        self.assertEqual(result.status, "CERTIFICATION_FAILED")
        self.assertEqual((result.visits, result.accepted, result.rejected), (0, 0, 0))

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

    def test_accepted_visit_reenters_admission_before_next_neural_visit(self):
        current = SimpleNamespace(
            generation=2,
            retained_state=SimpleNamespace(optimizer_step=8),
        )
        parent_graph = {"tokens": ["fixture"]}
        progress = []
        with TemporaryDirectory() as temporary, patch(
                "bilqis_mlx.runtime.bamf_operator.session._visit",
                side_effect=("ACCEPTED", "HELD")) as visit, patch(
                "bilqis_mlx.runtime.bamf_operator.accepted_learning_evidence."
                "refresh_accepted_learning_evidence",
                return_value=SimpleNamespace(
                    measured=0, passed=0, final_action="QUALIFICATION")), patch(
                "bilqis_mlx.runtime.bamf_operator.session._accepted_admission_reentry",
                return_value=("WAITING_FOR_EVIDENCE", 1, None)) as reentry, patch(
                "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                return_value=current):
            result = operate_bamf(
                temporary, minutes=1, max_visits=0, reserve_gib=0.0,
                source_prefetch_workers=0, parent_graph=parent_graph,
                progress=progress.append)

        self.assertEqual(result.status, "PRIORITY_HOLD")
        self.assertEqual((result.visits, result.accepted, result.rejected), (1, 1, 0))
        self.assertEqual(result.admission_status, "WAITING_FOR_EVIDENCE")
        self.assertEqual(result.admission_advances, 1)
        reentry.assert_called_once_with(
            Path(temporary).resolve(), parent_graph, 0.0, progress.append)
        self.assertEqual(visit.call_count, 2)
