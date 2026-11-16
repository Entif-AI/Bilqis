"""Exact earning questions protect titles without freezing historical scores."""
from copy import deepcopy
from unittest import TestCase

from bilqis_mlx.learning.championship_witnesses import (
    battery_from_exam, earning_witness, maxed_role, refresh_battery,
    verified_battery, verified_witnesses,
)


def exam():
    return {
        "cohort_sha256": "a" * 64, "rubric_sha256": "b" * 64,
        "source_graph_sha256": "c" * 64, "source_oracle_sha256": "d" * 64,
        "assessment_scope_sha256": "e" * 64,
        "scores": {"A.X": {"correct": 2, "total": 2},
                   "B.Y": {"correct": 1, "total": 2}},
        "correct_questions": {
            "A.X": [{"id": "a0", "gold": "TRUE"}, {"id": "a1", "gold": "FALSE"}],
            "B.Y": [{"id": "b0", "gold": "TRUE"}],
        },
        "questions": {
            "A.X": [{"id": "a0", "gold": "TRUE"}, {"id": "a1", "gold": "FALSE"}],
            "B.Y": [{"id": "b0", "gold": "TRUE"}, {"id": "b1", "gold": "FALSE"}],
        },
    }


class ChampionshipWitnessTests(TestCase):
    def test_initial_epoch_is_empty_eligible_and_does_not_fabricate_a_graduate(self):
        from bilqis_mlx.learning.mentor_epoch import begin_initial_epoch, reference_checkpoints
        student = {"filename": "bundles/inert", "sha256": "a" * 64,
                   "optimizer_step": 10, "model_and_native_adamw": True}
        epoch = begin_initial_epoch(student=student, introduced_grade="A",
                                    source_graph_sha256="b" * 64, frontier={}, soups={})
        self.assertEqual(epoch["active_roles"], {})
        self.assertIsNone(epoch["previous_graduate"])
        self.assertLess(epoch["championship_eligibility_after_step"], 10)
        self.assertEqual(reference_checkpoints(epoch), (student,))

    def test_archived_same_sha_bundle_aliases_are_all_pinned(self):
        from bilqis_mlx.learning.mentor_epoch import begin_initial_epoch, reference_checkpoints
        student = {"filename": "bundles/inert", "sha256": "a" * 64,
                   "optimizer_step": 10, "model_and_native_adamw": True}
        epoch = begin_initial_epoch(student=student, introduced_grade="A",
                                    source_graph_sha256="b" * 64, frontier={}, soups={})
        first = {**student, "filename": "bundles/first"}
        second = {**student, "filename": "bundles/second"}
        epoch["superseded_active_championships"] = [{
            "starting_student": student,
            "active_roles": {
                "A.X": {"checkpoint": first},
                "A.Y": {"checkpoint": second},
            },
            "active_grade_soups": {},
        }]
        pointers = reference_checkpoints(epoch)
        self.assertIn(first, pointers)
        self.assertIn(second, pointers)

    def test_archived_same_sha_with_conflicting_optimizer_step_fails_closed(self):
        from bilqis_mlx.learning.mentor_epoch import begin_initial_epoch, reference_checkpoints
        student = {"filename": "bundles/inert", "sha256": "a" * 64,
                   "optimizer_step": 10, "model_and_native_adamw": True}
        epoch = begin_initial_epoch(student=student, introduced_grade="A",
                                    source_graph_sha256="b" * 64, frontier={}, soups={})
        first = {**student, "filename": "bundles/first"}
        conflicting = {**student, "filename": "bundles/second", "optimizer_step": 11}
        epoch["superseded_active_championships"] = [{
            "starting_student": student,
            "active_roles": {
                "A.X": {"checkpoint": first},
                "A.Y": {"checkpoint": conflicting},
            },
            "active_grade_soups": {},
        }]
        with self.assertRaisesRegex(ValueError, "MENTOR_EPOCH_CHECKPOINT_POINTER_CONFLICT"):
            reference_checkpoints(epoch)

    def test_all_influencing_questions_become_obligations_including_misses(self):
        measured = exam()
        proof = earning_witness(measured, ("A.X", "B.Y"))
        self.assertEqual({q["id"] for q in proof["questions"]}, {"a0", "a1", "b0", "b1"})
        self.assertEqual(proof["perfect_capabilities"], ["A.X"])
        self.assertEqual(measured, exam())

    def test_witness_and_battery_preserve_distinct_cohort_source_rubric(self):
        measured = exam()
        measured["cohort_rubric_sha256"] = "f" * 64
        witness = earning_witness(measured, ("A.X",))
        battery = battery_from_exam(measured, ("A.X",))
        self.assertEqual(witness["rubric_sha256"], "b" * 64)
        self.assertEqual(witness["cohort_rubric_sha256"], "f" * 64)
        self.assertEqual(battery[0]["rubric_sha256"], "b" * 64)
        self.assertEqual(battery[0]["cohort_rubric_sha256"], "f" * 64)

    def test_surviving_battery_can_shrink_to_latest_winning_answers(self):
        original = exam()
        role = {"capability": "A.X",
                "surviving_battery": list(battery_from_exam(original, ("A.X",)))}
        segment = verified_battery(role)[0]
        gate = deepcopy(original)
        fresh = deepcopy(original)
        gate["correct_questions"]["A.X"] = [gate["correct_questions"]["A.X"][0]]
        fresh["correct_questions"]["A.X"] = [fresh["correct_questions"]["A.X"][0]]
        refreshed = refresh_battery(
            role, gate_exam=gate, fresh_exam=fresh,
            qualification_scope=("A.X",),
            battery_correct={segment["sha256"]: ["a0"]})
        self.assertEqual({q["id"] for s in refreshed for q in s["questions"]}, {"a0"})

    def test_initial_and_fresh_current_wins_are_both_carried_forward(self):
        original = exam()
        role = {"capability": "A.X",
                "surviving_battery": list(battery_from_exam(original, ("A.X",)))}
        segment = verified_battery(role)[0]
        gate = deepcopy(original)
        fresh = deepcopy(original)
        gate["correct_questions"]["A.X"] = [gate["correct_questions"]["A.X"][0]]
        fresh["correct_questions"]["A.X"] = [fresh["correct_questions"]["A.X"][1]]
        refreshed = refresh_battery(
            role, gate_exam=gate, fresh_exam=fresh,
            qualification_scope=("A.X",), battery_correct={segment["sha256"]: []})
        self.assertEqual({q["id"] for s in refreshed for q in s["questions"]}, {"a0", "a1"})

    def test_surviving_battery_deduplicates_question_identity_across_historic_segments(self):
        first = exam()
        second = deepcopy(first)
        second["cohort_sha256"] = "f" * 64
        role = {
            "capability": "A.X",
            "surviving_battery": [
                *battery_from_exam(first, ("A.X",)),
                *battery_from_exam(second, ("A.X",)),
            ],
        }
        battery = verified_battery(role)
        self.assertEqual(
            {q["id"] for segment in battery for q in segment["questions"]},
            {"a0", "a1"})
        self.assertEqual(sum(len(segment["questions"]) for segment in battery), 2)

    def test_latest_winning_occurrence_owns_duplicate_question_context(self):
        prior_exam = exam()
        current = deepcopy(prior_exam)
        current["cohort_sha256"] = "f" * 64
        role = {"capability": "A.X",
                "surviving_battery": list(battery_from_exam(prior_exam, ("A.X",)))}
        prior_segment = verified_battery(role)[0]
        refreshed = refresh_battery(
            role, gate_exam=current, fresh_exam=current,
            qualification_scope=("A.X",),
            battery_correct={prior_segment["sha256"]: ["a0", "a1"]})
        self.assertEqual(len(refreshed), 1)
        self.assertEqual(refreshed[0]["cohort_sha256"], "f" * 64)

    def test_max_vote_entitlement_uses_saved_proof_even_if_fresh_score_is_lower(self):
        proof = earning_witness(exam(), ("A.X",))
        role = {"capability": "A.X", "correct": 1, "total": 2,
                "qualification_witnesses": [proof]}
        self.assertTrue(maxed_role(role))

    def test_changed_or_missing_earning_evidence_fails_closed(self):
        measured = exam()
        measured["correct_questions"]["A.X"].pop()
        with self.assertRaises(ValueError):
            earning_witness(measured, ("A.X",))
        proof = earning_witness(exam(), ("A.X",))
        damaged = deepcopy(proof)
        damaged["questions"][0]["gold"] = "FALSE"
        with self.assertRaises(ValueError):
            verified_witnesses({"qualification_witnesses": [damaged]})
