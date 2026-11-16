import copy
import json
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.teacher_lineage import (
    HISTORICAL_REPLAY_HEAD, adaptation_authority_ref, advance_priority_rotation,
    advance_teacher_lineage, bind_next_teacher_epoch, initialize_teacher_lineage,
    priority_rotation_state, restore_teacher_lineage,
)
from bilqis_mlx.learning.teacher_visit_identity import (
    TeacherVisitIdentity, derive_teacher_visit_identity,
    record_teacher_visit_identity,
)
from bilqis_mlx.learning.tests.teacher_strategy_test_support import teacher_fixture


def _authority_record():
    return {
        "schema": "bilqis.bamf.legacy-trainer-authority/v1",
        "version": "1.0.0",
        "effective_date": "2026-11-07",
        "purpose": "latest legacy trainer adaptation and compatibility oracle",
        "source_branch": "codex/337-replay-349-20261026",
        "source_worktree": "/preserved/replay",
        "source_run": "/preserved/replay/run",
        "source_state": "/preserved/replay/run/state.json",
        "operator_preflight": "python3 -B scripts/check_legacy_trainer_authority.py --live",
        "historical_non_authoritative_runs": [],
    }


def _student(sha, region):
    return {"schema": "bilqis.bamf.student-reference/v1",
            "student_sha256": sha, "region": region}


class TeacherLineageTests(unittest.TestCase):
    def initialize(self, *, observed="d" * 40):
        teacher, _strong, _weak = teacher_fixture()
        adaptation = adaptation_authority_ref(
            _authority_record(), observed_source_head=observed)
        projection = initialize_teacher_lineage(
            {"teacher": teacher}, _student("a" * 64, "student-a"), adaptation,
            prior_region="legacy-region", next_seed=42, cursor="lesson:7")
        return teacher, adaptation, projection

    def test_historical_replay_and_current_adaptation_are_distinct_attested_custody(self):
        teacher, adaptation, projection = self.initialize()
        epoch = restore_teacher_lineage(
            json.loads(json.dumps(projection.teacher_state)),
            expected_adaptation=adaptation)
        lineage = projection.teacher_state["c03_lineage"]
        self.assertEqual(epoch.replay_head, HISTORICAL_REPLAY_HEAD)
        self.assertEqual(lineage["adaptation_authority"]["observed_source_head"], "d" * 40)
        self.assertNotEqual(epoch.replay_head, "d" * 40)
        self.assertEqual(epoch.prior_teacher(), teacher)
        self.assertEqual(epoch.teacher()["grade_stats"], {})
        self.assertEqual(projection.teacher_epoch, 0)
        self.assertEqual(len(projection.teacher_identity), 64)

    def test_current_adaptation_head_changes_identity_without_rewriting_historical_replay(self):
        _, first, first_projection = self.initialize(observed="d" * 40)
        _, second, second_projection = self.initialize(observed="e" * 40)
        self.assertNotEqual(first, second)
        self.assertNotEqual(first_projection.teacher_identity, second_projection.teacher_identity)
        self.assertEqual(restore_teacher_lineage(first_projection.teacher_state).replay_head,
                         HISTORICAL_REPLAY_HEAD)
        self.assertEqual(restore_teacher_lineage(second_projection.teacher_state).replay_head,
                         HISTORICAL_REPLAY_HEAD)

    def test_changed_student_advances_epoch_and_resets_checkpoint_local_evidence(self):
        _teacher, adaptation, projection = self.initialize()
        current = restore_teacher_lineage(projection.teacher_state).teacher()
        current["causal_experiment"]["student_policy_epoch"]["contexts"]["dirty"] = {"x": 1}
        state = copy.deepcopy(projection.teacher_state)
        state["c03_lineage"]["current_teacher"] = current
        import hashlib
        raw = json.dumps(current, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        state["c03_lineage"]["current_teacher_sha256"] = hashlib.sha256(raw).hexdigest()
        next_epoch = bind_next_teacher_epoch(
            state, _student("b" * 64, "student-b"),
            bank_identity="bank:v2", plasticity_identity="plasticity:adaptive")
        advanced = advance_teacher_lineage(
            state, next_epoch, next_seed=43, cursor="lesson:8")
        restored = restore_teacher_lineage(
            json.loads(json.dumps(advanced.teacher_state)), expected_adaptation=adaptation)
        self.assertEqual(advanced.teacher_epoch, 1)
        self.assertEqual(restored.student_sha256, "b" * 64)
        self.assertEqual(restored.teacher()["grade_stats"], {})
        self.assertEqual(
            restored.teacher()["causal_experiment"]["student_policy_epoch"]["contexts"], {})
        self.assertEqual(advanced.teacher_state["next_seed"], 43)
        self.assertEqual(advanced.teacher_state["cursor"], "lesson:8")

    def test_tampered_lineage_and_adaptation_fail_closed(self):
        _teacher, adaptation, projection = self.initialize()
        for mutation in ("prior_teacher", "current_teacher", "student_sha256",
                         "historical_replay", "adaptation_authority"):
            with self.subTest(mutation=mutation):
                state = copy.deepcopy(projection.teacher_state)
                lineage = state["c03_lineage"]
                if mutation == "prior_teacher":
                    lineage[mutation]["tampered"] = True
                elif mutation == "current_teacher":
                    lineage[mutation]["tampered"] = True
                elif mutation == "student_sha256":
                    lineage[mutation] = "0" * 64
                elif mutation == "historical_replay":
                    lineage[mutation] = {"head": "0" * 40}
                else:
                    lineage[mutation]["observed_source_head"] = "0" * 40
                with self.assertRaises(BilqisError):
                    restore_teacher_lineage(state, expected_adaptation=adaptation)
        wrong = dict(adaptation)
        wrong["observed_source_head"] = "e" * 40
        with self.assertRaises(BilqisError):
            restore_teacher_lineage(projection.teacher_state, expected_adaptation=wrong)

    def test_malformed_legacy_receipt_seed_and_cursor_fail_closed(self):
        adaptation = adaptation_authority_ref(
            _authority_record(), observed_source_head="d" * 40)
        for receipt, seed, cursor in (({}, 1, "ok"), ({"teacher": {}}, -1, "ok"),
                                      ({"teacher": {}}, 1, "")):
            with self.subTest(receipt=receipt, seed=seed, cursor=cursor), self.assertRaises(BilqisError):
                initialize_teacher_lineage(
                    receipt, _student("a" * 64, "student-a"), adaptation,
                    prior_region="legacy-region", next_seed=seed, cursor=cursor)

    def test_true_visit_identity_uses_run_and_persisted_teacher_selection_state(self):
        _teacher, _adaptation, projection = self.initialize()
        visit = derive_teacher_visit_identity(
            projection.teacher_state,
            run_identity_sha256="1" * 64, run_seed=17, generation=0,
            accepted_manifest_sha256="2" * 64,
            capability_id="C.ADD", policy_key="p-strong")
        self.assertEqual(visit.run_seed, 17)
        self.assertEqual(visit.selection_seed, 42)
        self.assertEqual(visit.cursor, "lesson:7")
        self.assertEqual(visit.teacher_identity, projection.teacher_identity)
        self.assertEqual(visit.teacher_epoch, 0)
        self.assertEqual(visit.student_sha256, "a" * 64)
        self.assertEqual(len(visit.visit_id), 64)

        recorded = record_teacher_visit_identity(projection.teacher_state, visit)
        self.assertEqual(recorded.teacher_state["last_visit"], visit.to_record())
        restored = restore_teacher_lineage(recorded.teacher_state)
        self.assertEqual(restored.student_sha256, "a" * 64)

    def test_visit_identity_is_not_episode_or_optimizer_seed_alias(self):
        _teacher, _adaptation, projection = self.initialize()
        base = dict(
            teacher_state=projection.teacher_state,
            run_identity_sha256="1" * 64, run_seed=17, generation=4,
            accepted_manifest_sha256="2" * 64,
            capability_id="C.ADD", policy_key="p-strong")
        actual = derive_teacher_visit_identity(**base)
        for key, value in (
                ("run_seed", 18), ("generation", 5),
                ("run_identity_sha256", "3" * 64),
                ("accepted_manifest_sha256", "4" * 64),
                ("capability_id", "C.SUB"), ("policy_key", "p-weak")):
            with self.subTest(key=key):
                changed = dict(base)
                changed[key] = value
                self.assertNotEqual(
                    derive_teacher_visit_identity(**changed).visit_id,
                    actual.visit_id)

    def test_caller_cannot_record_a_rewritten_selection_seed(self):
        _teacher, _adaptation, projection = self.initialize()
        visit = derive_teacher_visit_identity(
            projection.teacher_state,
            run_identity_sha256="1" * 64, run_seed=17, generation=0,
            accepted_manifest_sha256="2" * 64,
            capability_id="C.ADD", policy_key="p-strong")
        forged = TeacherVisitIdentity(
            visit.run_identity_sha256, visit.run_seed, visit.generation,
            visit.accepted_manifest_sha256, visit.teacher_identity,
            visit.teacher_epoch, visit.student_sha256, visit.selection_seed + 1,
            visit.cursor, visit.capability_id, visit.policy_key)
        with self.assertRaises(BilqisError):
            record_teacher_visit_identity(projection.teacher_state, forged)

    def test_accepted_teacher_successor_preserves_prior_visit_evidence(self):
        _teacher, _adaptation, projection = self.initialize()
        visit = derive_teacher_visit_identity(
            projection.teacher_state,
            run_identity_sha256="1" * 64, run_seed=17, generation=0,
            accepted_manifest_sha256="2" * 64,
            capability_id="C.ADD", policy_key="p-strong")
        recorded = record_teacher_visit_identity(projection.teacher_state, visit)
        next_epoch = bind_next_teacher_epoch(
            recorded.teacher_state, _student("b" * 64, "student-b"),
            bank_identity="bank:v2", plasticity_identity="plasticity:adaptive")
        advanced = advance_teacher_lineage(
            recorded.teacher_state, next_epoch,
            next_seed=43, cursor="lesson:8")
        self.assertEqual(advanced.teacher_state["last_visit"], visit.to_record())
        self.assertEqual(advanced.teacher_state["next_seed"], 43)
        self.assertEqual(advanced.teacher_state["cursor"], "lesson:8")

    def test_priority_rotation_is_grade_neutral_backward_compatible_and_monotonic(self):
        _teacher, _adaptation, projection = self.initialize()
        self.assertEqual(priority_rotation_state(projection.teacher_state), (0, {}))
        first = advance_priority_rotation(projection.teacher_state, "capability:zeta")
        second = advance_priority_rotation(first, "capability:alpha")
        third = advance_priority_rotation(second, "capability:zeta")
        self.assertEqual(priority_rotation_state(third), (
            3, {"capability:alpha": 2, "capability:zeta": 3}))
        self.assertNotIn("grade", third)
        malformed = dict(third)
        malformed["priority_last_selected"] = {"capability:zeta": 4}
        with self.assertRaises(BilqisError):
            restore_teacher_lineage(malformed)


if __name__ == "__main__":
    unittest.main()
