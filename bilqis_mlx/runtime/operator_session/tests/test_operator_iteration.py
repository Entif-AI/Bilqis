"""Session budget stops dispatch before any assessment or visit."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError, SCHOOL
from bilqis_mlx.runtime.atlas_admission_policy import AdmissionResult, AdmissionStatus
from bilqis_mlx.runtime.operator_session import operator_iteration as subject
from bilqis_mlx.runtime.operator_session.operator_autonomy import DispatchControl


class IterationTest(TestCase):
    def test_atlas_dispatch_rejects_non_admission_result_with_typed_error(self):
        with patch(
            "bilqis_mlx.runtime.atlas_admission.dispatch_atlas_frontier_proposal",
            return_value=object(),
        ), self.assertRaises(BilqisError) as caught:
            subject._dispatch_atlas_frontier_attempt(
                "run",
                {"generation": 7},
                object(),
                "autonomy/proposals/fixture.json",
            )
        self.assertIs(caught.exception.spec, SCHOOL.BAMF_ATLAS_ADMISSION.INVALID)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_ATLAS_ADMISSION_RESULT_REQUIRED",
        )

    def test_adopted_atlas_result_requires_cold_resume(self):
        adopted = AdmissionResult(
            AdmissionStatus.ADOPTED,
            "1" * 64,
            "2" * 64,
            "3" * 64,
            "4" * 64,
            "ADOPTED",
            "Cold-resume from accepted B13 custody before further neural work.",
            state_adopted=True,
            requires_cold_resume=True,
            accepted_generation=8,
            accepted_manifest_sha256="5" * 64,
        )
        records = []
        with patch(
            "bilqis_mlx.runtime.atlas_admission.dispatch_atlas_frontier_proposal",
            return_value=adopted,
        ):
            control, reason = subject._dispatch_atlas_frontier_attempt(
                "run",
                {"generation": 7},
                object(),
                "autonomy/proposals/fixture.json",
                record=lambda _path, event: records.append(event),
            )
        self.assertIs(control, DispatchControl.COLD_RESUME)
        self.assertEqual(reason, "ATLAS_ADMISSION_ADOPTED_COLD_RESUME")
        self.assertEqual(records, [])

    def test_out_of_scope_atlas_stage_allows_existing_learning_to_continue(self):
        staged = AdmissionResult(
            AdmissionStatus.STAGED,
            "1" * 64,
            "2" * 64,
            "3" * 64,
            "4" * 64,
            "OUT_OF_LEASE_SCOPE",
            "Renew the lease for the new release; keep current learning active.",
        )
        records = []
        with patch(
            "bilqis_mlx.runtime.atlas_admission.dispatch_atlas_frontier_proposal",
            return_value=staged,
        ):
            control, reason = subject._dispatch_atlas_frontier_attempt(
                "run", {"generation": 7}, object(),
                "autonomy/proposals/fixture.json",
                record=lambda _path, event: records.append(event),
            )
        self.assertIs(control, DispatchControl.PROCEED)
        self.assertEqual(reason, "ATLAS_ADMISSION_STAGED")
        self.assertEqual(records[0]["reason"], "OUT_OF_LEASE_SCOPE")
        self.assertEqual(records[0]["actual_neural_updates"], 0)

    def test_time_limit_stops_before_assessment(self):
        receipt = {"school": {}}
        school = SimpleNamespace(stage="MAIN", grade="A")
        calls = []
        adoption = SimpleNamespace(
            _advance_provider_dimensions=lambda *a, **k: (receipt, "course", "release", "schedule"),
            _auto_adopt_known_grade_boundary=lambda *a, **k: ("params", "optimizer", "graph", receipt, "course", False),
            _schedule_for_receipt=lambda *a: "schedule")
        session = SimpleNamespace(session_stop_reason=lambda **kw: calls.append(kw) or (None if len(calls) == 1 else "TIME_LIMIT"))
        replacements = dict(_runtime_release_adoption=adoption, _runtime_state=SimpleNamespace(_state_from_json=lambda *a: school),
            _runtime_reconciliation=SimpleNamespace(_reconcile_stagnation_scope=lambda *a: receipt),
            _runtime_session=session, _time=SimpleNamespace(monotonic=lambda: 5))
        with patch.multiple(subject, **replacements):
            result = subject.prepare_operator_iteration(experiment_budget=None, run_dir="run", receipt=receipt,
                course_a="a", source_root="source", graph="graph", course="course",
                executable_release="release", schedule_program="schedule", numeric_staircase=False,
                mx=None, manifest=None, params="params", optimizer="optimizer", reserve_gib=1,
                full_grade_b=True, autonomy_session=None, start=0, minutes=1, visits=0,
                max_visits=0, flash_mode=False, source_checkpoint="checkpoint")
        self.assertEqual(result[:2], (DispatchControl.STOP, "TIME_LIMIT"))
        self.assertEqual([call["stage"] for call in calls], ["MAIN", "MAIN"])
