"""Epoch championship reset behavior."""
from bilqis_mlx.learning.tests.championship.epoch_fixtures import (
    EARNED_ONLY_POLICY, EpochChampionshipTests, GRADES, _epoch,
    _exam, _panel, active_frontier, advance_epoch,
    deepcopy, grade_soup_recipe, rebase_active_championships, reset_active_championships,
)


class EpochResetTests(EpochChampionshipTests):
    def test_experiment_rebase_clears_titles_without_making_baseline_a_champ(self):
        first = _panel("c", 11, "C.0", 9, grade="C")
        earned, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        earned["active_grade_soups"] = {
            "C": grade_soup_recipe(active_frontier(earned), "C", GRADES["C"])}
        old_student = _exam("d", 210)["checkpoint"]
        old_student["optimizer_step"] = 12
        baseline = _exam("e", 208)["checkpoint"]
        baseline["optimizer_step"] = 11
        rebased = rebase_active_championships(
            earned, prior_student=old_student, baseline=baseline, generation=500)
        self.assertEqual(rebased["active_roles"], {})
        self.assertEqual(rebased["active_grade_soups"], {})
        self.assertEqual(rebased["baseline"], baseline)
        self.assertFalse(rebased["baseline_challenge_required"])

    def test_reset_archives_earned_roles_and_soups_without_new_teacher(self):
        first = _panel("c", 11, "C.0", 9, grade="C")
        original, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        original["active_grade_soups"] = {
            "C": grade_soup_recipe(active_frontier(original), "C", GRADES["C"])}
        original["baseline_roles"] = {"A.0": "b" * 64}
        before = deepcopy(original)
        student = _exam("d", 210)["checkpoint"]
        result, changed = reset_active_championships(
            original, student=student, generation=400)
        self.assertTrue(changed)
        self.assertEqual(original, before)
        self.assertEqual(result["active_roles"], {})
        self.assertEqual(result["active_grade_soups"], {})
        self.assertEqual(result["guidance_policy"], EARNED_ONLY_POLICY)
        historic = result["superseded_active_championships"][-1]
        self.assertEqual(historic["active_roles"], original["active_roles"])

    def test_reset_and_rebase_preserve_permanent_settled_match_ledger(self):
        original = _epoch()
        original["settled_matchups"] = {
            "A.0|" + "a" * 64 + "|" + "c" * 64: {"winner_sha256": "a" * 64}}
        student = _exam("d", 210)["checkpoint"]
        reset, _ = reset_active_championships(
            original, student=student, generation=400)
        self.assertEqual(reset["settled_matchups"], original["settled_matchups"])
        baseline = _exam("e", 208)["checkpoint"]
        rebased = rebase_active_championships(
            reset, prior_student=student, baseline=baseline, generation=401)
        self.assertEqual(rebased["settled_matchups"], original["settled_matchups"])

    def test_reset_baseline_cannot_immediately_reclaim_title(self):
        current = _exam("c", 209)["checkpoint"]
        cleared, _ = reset_active_championships(
            _epoch(), student=current, generation=400)
        same_step = _panel("c", 10, "C.0", 12, grade="C")
        result, changes, _ = advance_epoch(
            cleared, grades=GRADES, challenger_exam=same_step, incumbent_exams={})
        self.assertEqual(changes, ())
        self.assertEqual(result["active_roles"], {})
        later = _panel("d", 11, "C.0", 12, grade="C")
        result, changes, _ = advance_epoch(
            cleared, grades=GRADES, challenger_exam=later, incumbent_exams={})
        self.assertEqual(changes, ("C.0",))
        self.assertEqual(result["active_roles"]["C.0"]["checkpoint"]["sha256"],
                         "d" * 64)
