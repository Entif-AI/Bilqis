"""Regression coverage for persistent operation across ordinary rejections."""
from contextlib import nullcontext
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
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

    def test_admission_hold_stops_before_another_neural_visit(self):
        current = self._current()
        parent_graph = {"tokens": ["fixture"]}
        with TemporaryDirectory() as temporary, patch(
                "bilqis_mlx.runtime.bamf_operator.session._visit",
                return_value="ACCEPTED") as visit, patch(
                "bilqis_mlx.runtime.bamf_operator.session._accepted_admission_reentry",
                return_value=("HELD", 0, "ADMISSION_HOLD")), patch(
                "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                return_value=current):
            result = operate_bamf(
                temporary, minutes=1, max_visits=0, reserve_gib=0.0,
                source_prefetch_workers=0, parent_graph=parent_graph)

        self.assertEqual(result.status, "ADMISSION_HOLD")
        self.assertEqual((result.visits, result.accepted, result.rejected), (1, 1, 0))
        self.assertEqual(result.admission_status, "HELD")
        visit.assert_called_once()

    def test_missing_accepted_lease_returns_typed_admission_stop(self):
        before = SimpleNamespace(release_sha256="a" * 64)
        missing = BilqisError(
            SCHOOL.BAMF_ATLAS_ADMISSION.ACCEPTED_LEASE_REQUIRED, {})
        with patch(
                "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_factory_release",
                return_value=before), patch(
                "bilqis_mlx.runtime.atlas_flywheel_runtime.run_accepted_atlas_flywheel",
                side_effect=missing), patch(
                "bilqis_mlx.runtime.bamf_operator.session._execution_context",
                side_effect=AssertionError("missing lease must not refresh custody")):
            actual = _accepted_admission_reentry(
                Path("/run"), {"tokens": []}, 100.0)

        self.assertEqual(actual, ("LEASE_REQUIRED", 0, "ADMISSION_LEASE_REQUIRED"))

    def test_invalid_accepted_lease_returns_typed_admission_stop(self):
        before = SimpleNamespace(release_sha256="a" * 64)
        invalid_lease = BilqisError(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            {"reason": "BAMF_ATLAS_LEASE_V2_REFERENCE_DRIFT"})
        with patch(
                "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_factory_release",
                return_value=before), patch(
                "bilqis_mlx.runtime.atlas_flywheel_runtime.run_accepted_atlas_flywheel",
                side_effect=invalid_lease):
            actual = _accepted_admission_reentry(
                Path("/run"), {"tokens": []}, 100.0)

        self.assertEqual(actual, ("LEASE_REQUIRED", 0, "ADMISSION_LEASE_REQUIRED"))

    def test_source_rights_error_is_not_reclassified_as_lease_hold(self):
        before = SimpleNamespace(release_sha256="a" * 64)
        source_hold = BilqisError(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            {"reason": "BAMF_ATLAS_SOURCE_OR_RIGHTS_HELD"})
        with patch(
                "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_factory_release",
                return_value=before), patch(
                "bilqis_mlx.runtime.atlas_flywheel_runtime.run_accepted_atlas_flywheel",
                side_effect=source_hold):
            with self.assertRaises(BilqisError) as raised:
                _accepted_admission_reentry(
                    Path("/run"), {"tokens": []}, 100.0)

        self.assertIs(raised.exception, source_hold)

    def test_fixed_point_does_not_fake_adoption_or_cold_refresh(self):
        from bilqis_mlx.runtime.atlas_flywheel import AdmissionFlywheelStatus

        current = SimpleNamespace(release_sha256="b" * 64)
        result = SimpleNamespace(
            status=AdmissionFlywheelStatus.FIXED_POINT,
            advances=0,
            final_state=SimpleNamespace(
                epoch=SimpleNamespace(current_release=current)))
        with patch(
                "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_factory_release",
                side_effect=(current, current)), patch(
                "bilqis_mlx.runtime.atlas_flywheel_runtime.run_accepted_atlas_flywheel",
                return_value=result), patch(
                "bilqis_mlx.runtime.bamf_operator.session._execution_context",
                side_effect=AssertionError("fixed point must not fake a refresh")):
            actual = _accepted_admission_reentry(
                Path("/run"), {"tokens": []}, 100.0)

        self.assertEqual(actual, ("FIXED_POINT", 0, None))


def _rejected_resource_fixture():
    return {
        "schema": "bilqis.bamf.c16.3-resource-observation/v2",
        "memory_budget_bytes": 1, "disk_used_bytes": 1,
        "optimizer_steps": 1, "wall_seconds": 1.0,
    }


class BamfOperatorRejectionReplayIntegrationTests(NativeSourceFixture, unittest.TestCase):
    def test_real_rejections_replay_and_accumulate_without_parent_drift(self):
        parent = self.parent()
        pointer_before = (self.run / "bamf-state.json").read_bytes()
        parent_identity = candidate_identity_digest(parent.retained_state)
        teacher_before = dict(parent.teacher_state)
        visit = self.bound_native_visit(parent, capability="A.REJECT")
        decision = retention_decision(
            accepted=False, parent=parent.retained_state,
            retained=parent.retained_state)
        selection = SimpleNamespace(option_id="A.REJECT", visit=visit)
        step = SimpleNamespace(
            transaction=SimpleNamespace(parent=parent.retained_state, update_steps=1),
            realized_cost={
                "wall_seconds": 1.0,
                "optimizer_steps": 1,
                "candidate_optimizer_steps": 1,
                "c08_memory_budget_bytes": 1,
            })
        rejected = BamfPreparedVisit(
            "REJECTED", parent, selection=selection, step=step,
            decision=decision, retained=parent.retained_state,
            capability="A.REJECT", resource=_rejected_resource_fixture())
        held = BamfPreparedVisit("HELD", parent)
        pointer = json.loads(pointer_before)
        cache = SimpleNamespace(
            run_id=parent.run_id,
            generation=parent.generation,
            accepted_manifest_sha256=pointer["manifest_sha256"])
        prepared_calls = 0

        def prepare(run_dir, **_kwargs):
            nonlocal prepared_calls
            prepared_calls += 1
            replayed = current_rejections(run_dir, parent, cache)
            if prepared_calls == 1:
                self.assertEqual(replayed, ())
                return replace(
                    rejected, rejection_journal_ordinal=1,
                    rejection_attempt_ordinal=1)
            if prepared_calls == 2:
                self.assertEqual(len(replayed), 1)
                self.assertEqual(replayed[0][:3], (
                    "A.REJECT", visit.identity.visit_id, decision.reason))
                return replace(
                    rejected, rejection_journal_ordinal=2,
                    rejection_attempt_ordinal=2)
            self.assertEqual(len(replayed), 2)
            return held

        with patch(
                "bilqis_mlx.runtime.bamf_operator.session.prepare_bamf_visit",
                side_effect=prepare), patch(
                "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                return_value=parent), patch(
                "bilqis_mlx.runtime.bamf_operator.session.bind_accepted_execution_cache",
                return_value=cache):
            result = operate_bamf(
                self.run, minutes=1, max_visits=0, reserve_gib=0.0,
                source_prefetch_workers=0)

        self.assertEqual(result.status, "PRIORITY_HOLD")
        self.assertEqual((result.visits, result.accepted, result.rejected), (2, 0, 2))
        self.assertEqual(prepared_calls, 3)
        events = [
            json.loads(line)
            for line in (self.run / "events.jsonl").read_text().splitlines()
            if '"event":"BAMF_CANDIDATE_REJECTED"' in line
        ]
        self.assertEqual(
            [event["evidence"]["rejection_attempt_ordinal"] for event in events],
            [1, 2])
        self.assertEqual(
            [event["evidence"]["rejection_journal_ordinal"] for event in events],
            [1, 2])
        self.assertEqual((self.run / "bamf-state.json").read_bytes(), pointer_before)
        with shape_patch():
            after = load_bamf_generation(self.run / "bamf-state.json")
        self.assertEqual(candidate_identity_digest(after.retained_state), parent_identity)
        self.assertEqual(after.teacher_state, teacher_before)
        self.assertEqual(after.retained_state.optimizer_step, parent.retained_state.optimizer_step)
        self.assertEqual(
            candidate_step_horizon(self.run, parent, cache, "A.REJECT", 16), 8)
        native_query_catalog(self.run)


if __name__ == "__main__":
    unittest.main()
