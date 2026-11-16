"""Epoch championship competition behavior."""
from bilqis_mlx.learning.tests.test_epoch_championships import (
    EpochChampionshipTests, GRADES, _battery_answers, _epoch,
    _match, _panel, advance_epoch,
)


class EpochCompetitionTests(EpochChampionshipTests):
    def test_single_capability_max_opens_title_fight_even_when_incumbent_also_maxed(self):
        first = _panel("a", 11, "B.XOR", 12, cohort="1")
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        challenger = _panel("c", 12, "B.XOR", 12, cohort="6")
        incumbent = _panel("a", 11, "B.XOR", 12, cohort="6")
        _, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams={"a" * 64: incumbent})
        self.assertEqual(changes, ())
        self.assertTrue(any(d["decision"] == "TITLE_MATCH_REQUIRED" and
                            d["qualification"] == "CAPABILITY_MAX"
                            for d in decisions))

    def test_strict_gain_below_max_opens_title_fight_but_below_max_tie_does_not(self):
        first = _panel("a", 11, "B.XOR", 8)
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        challenger = _panel("c", 12, "B.XOR", 9, cohort="6")
        incumbent = _panel("a", 11, "B.XOR", 8, cohort="6")
        _, _, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams={"a" * 64: incumbent})
        self.assertTrue(any(d["qualification"] == "STRICT_GAIN" for d in decisions))

        tied = _panel("d", 13, "B.XOR", 8, cohort="7")
        incumbent_tie = _panel("a", 11, "B.XOR", 8, cohort="7")
        _, _, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=tied,
            incumbent_exams={"a" * 64: incumbent_tie})
        self.assertFalse(any(d.get("decision") == "TITLE_MATCH_REQUIRED"
                             for d in decisions))

    def test_battery_can_crown_contender_even_after_fresh_current_score_drops(self):
        first = _panel("a", 11, "B.XOR", 12)
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        role = epoch["active_roles"]["B.XOR"]
        challenger = _panel("c", 12, "B.XOR", 11, cohort="6")
        incumbent = _panel("a", 11, "B.XOR", 8, cohort="6")
        incumbent_fresh = _panel("a", 11, "B.XOR", 7, cohort="6")
        challenger_fresh = _panel("c", 12, "B.XOR", 6, cohort="6")
        match = _match(
            role, incumbent_fresh, challenger_fresh,
            incumbent_battery=_battery_answers(role, drop=2),
            challenger_battery=_battery_answers(role, drop=0))
        result, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams={"a" * 64: incumbent},
            title_matches={"B.XOR": match})
        self.assertIn("B.XOR", changes)
        champion = result["active_roles"]["B.XOR"]
        self.assertEqual(champion["checkpoint"]["sha256"], "c" * 64)
        self.assertEqual(champion["correct"], 6)
        self.assertFalse(champion["maxed"])
        self.assertTrue(any(d["decision"] == "TITLE_WON" for d in decisions))

    def test_battery_tie_transfers_title_to_challenger(self):
        first = _panel("a", 11, "B.XOR", 12)
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        role = epoch["active_roles"]["B.XOR"]
        challenger = _panel("c", 12, "B.XOR", 11, cohort="6")
        incumbent = _panel("a", 11, "B.XOR", 8, cohort="6")
        incumbent_fresh = _panel("a", 11, "B.XOR", 7, cohort="6")
        challenger_fresh = _panel("c", 12, "B.XOR", 6, cohort="6")
        tied = _battery_answers(role, drop=2)
        result, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams={"a" * 64: incumbent},
            title_matches={"B.XOR": _match(
                role, incumbent_fresh, challenger_fresh,
                incumbent_battery=tied, challenger_battery=tied)})
        self.assertIn("B.XOR", changes)
        champion = result["active_roles"]["B.XOR"]
        self.assertEqual(champion["checkpoint"]["sha256"], "c" * 64)
        self.assertEqual(champion["correct"], 6)
        self.assertTrue(any(d["decision"] == "TITLE_WON" for d in decisions))

    def test_defended_battery_drops_questions_the_winner_now_misses(self):
        first = _panel("a", 11, "B.XOR", 12)
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        role = epoch["active_roles"]["B.XOR"]
        challenger = _panel("c", 12, "B.XOR", 11, cohort="6")
        incumbent = _panel("a", 11, "B.XOR", 8, cohort="6")
        incumbent_fresh = _panel("a", 11, "B.XOR", 7, cohort="6")
        challenger_fresh = _panel("c", 12, "B.XOR", 6, cohort="6")
        result, _, _ = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams={"a" * 64: incumbent},
            title_matches={"B.XOR": _match(
                role, incumbent_fresh, challenger_fresh,
                incumbent_battery=_battery_answers(role, drop=4),
                challenger_battery=_battery_answers(role, drop=5))})
        refreshed = result["active_roles"]["B.XOR"]["surviving_battery"]
        active_ids = {q["id"] for segment in refreshed for q in segment["questions"]}
        old_ids = {q["id"] for segment in role["surviving_battery"]
                   for q in segment["questions"]}
        self.assertTrue(active_ids < old_ids | {
            q["id"] for q in incumbent["correct_questions"]["B.XOR"]})
        self.assertLess(len(active_ids & old_ids), len(old_ids))
