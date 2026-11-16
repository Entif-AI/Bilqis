"""Epoch championship fanout behavior."""
from bilqis_mlx.learning.tests.test_epoch_championships import (
    EpochChampionshipTests, GRADES, _battery_answers, _match,
    _panel, advance_epoch,
)


class EpochFanoutTests(EpochChampionshipTests):
    def test_primary_takeover_queues_one_same_grade_fanout_for_match_or_beat(self):
        epoch, challenger, incumbents = self._fanout_fixture()
        and_role = epoch["active_roles"]["B.AND"]
        primary = _match(
            and_role,
            _panel("a", 11, "B.AND", 7, cohort="6"),
            _panel("c", 13, "B.AND", 9, cohort="6"),
            incumbent_battery=_battery_answers(and_role, drop=2),
            challenger_battery=_battery_answers(and_role, drop=0))
        _, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams=incumbents, title_matches={"B.AND": primary})
        self.assertIn("B.AND", changes)
        self.assertTrue(any(d["decision"] == "FANOUT_SCREEN_REQUIRED"
                            for d in decisions))
        screen = {"B.XOR": {
            "incumbent_checkpoint_sha256": "b" * 64,
            "challenger_checkpoint_sha256": "c" * 64,
            "incumbent_exam": _panel("b", 12, "B.XOR", 8, cohort="6"),
            "challenger_exam": _panel("c", 13, "B.XOR", 8, cohort="6"),
        }}
        _, _, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams=incumbents, title_matches={"B.AND": primary},
            fanout_screen=screen)
        self.assertTrue(any(d["decision"] == "FANOUT_TITLE_MATCH_REQUIRED" and
                            d["capability"] == "B.XOR" for d in decisions))

    def test_primary_takeover_defers_unmeasured_sibling_fanout(self):
        epoch, _, _ = self._fanout_fixture()
        and_role = epoch["active_roles"]["B.AND"]
        challenger = _panel("c", 13, "B.AND", 10, cohort="6", grade="B")
        incumbent = _panel("a", 11, "B.AND", 8, cohort="6", grade="B")
        primary = _match(
            and_role,
            _panel("a", 11, "B.AND", 7, cohort="6", grade="B"),
            _panel("c", 13, "B.AND", 9, cohort="6", grade="B"),
            incumbent_battery=_battery_answers(and_role, drop=2),
            challenger_battery=_battery_answers(and_role, drop=0))
        result, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams={"a" * 64: incumbent},
            title_matches={"B.AND": primary})
        self.assertIn("B.AND", changes)
        self.assertTrue(any(d["decision"] == "FANOUT_DEFERRED_UNMEASURED" and
                            d["capability"] == "B.XOR" for d in decisions))
        self.assertFalse(any(d["decision"] in (
            "FANOUT_SCREEN_REQUIRED", "FANOUT_TITLE_MATCH_REQUIRED")
            for d in decisions))
        self.assertNotIn(
            "B.XOR|" + "b" * 64 + "|" + "c" * 64,
            result["settled_matchups"])

    def test_defended_primary_title_does_not_open_fanout(self):
        epoch, challenger, incumbents = self._fanout_fixture()
        and_role = epoch["active_roles"]["B.AND"]
        incumbent_battery = _battery_answers(and_role, drop=0)
        challenger_battery = _battery_answers(and_role, drop=1)
        primary = _match(
            and_role,
            _panel("a", 11, "B.AND", 7, cohort="6"),
            _panel("c", 13, "B.AND", 9, cohort="6"),
            incumbent_battery=incumbent_battery,
            challenger_battery=challenger_battery)
        _, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams=incumbents, title_matches={"B.AND": primary})
        self.assertNotIn("B.AND", changes)
        self.assertFalse(any(d["decision"] in (
            "FANOUT_SCREEN_REQUIRED", "FANOUT_TITLE_MATCH_REQUIRED")
                             for d in decisions))

    def test_primary_win_does_not_fanout_into_already_settled_sibling_pair(self):
        epoch, challenger, incumbents = self._fanout_fixture()
        xor_role = epoch["active_roles"]["B.XOR"]
        epoch["settled_matchups"] = {
            "B.XOR|" + "b" * 64 + "|" + "c" * 64: {
                "decision": "TITLE_DEFENDED", "winner_sha256": "b" * 64}}
        and_role = epoch["active_roles"]["B.AND"]
        primary = _match(
            and_role,
            _panel("a", 11, "B.AND", 7, cohort="6"),
            _panel("c", 13, "B.AND", 9, cohort="6"),
            incumbent_battery=_battery_answers(and_role, drop=2),
            challenger_battery=_battery_answers(and_role, drop=0))
        _, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams=incumbents, title_matches={"B.AND": primary})
        self.assertIn("B.AND", changes)
        self.assertFalse(any(d["decision"] in (
            "FANOUT_SCREEN_REQUIRED", "FANOUT_TITLE_MATCH_REQUIRED")
                             for d in decisions))

    def test_secondary_fanout_win_does_not_recurse(self):
        epoch, challenger, incumbents = self._fanout_fixture()
        and_role = epoch["active_roles"]["B.AND"]
        xor_role = epoch["active_roles"]["B.XOR"]
        matches = {
            "B.AND": _match(
                and_role,
                _panel("a", 11, "B.AND", 7, cohort="6"),
                _panel("c", 13, "B.AND", 9, cohort="6"),
                incumbent_battery=_battery_answers(and_role, drop=2),
                challenger_battery=_battery_answers(and_role, drop=0)),
            "B.XOR": _match(
                xor_role,
                _panel("b", 12, "B.XOR", 7, cohort="6"),
                _panel("c", 13, "B.XOR", 7, cohort="6"),
                incumbent_battery=_battery_answers(xor_role, drop=2),
                challenger_battery=_battery_answers(xor_role, drop=0)),
        }
        result, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams=incumbents, title_matches=matches,
            fanout_screen={"B.XOR": {
                "incumbent_checkpoint_sha256": "b" * 64,
                "challenger_checkpoint_sha256": "c" * 64,
                "incumbent_exam": _panel("b", 12, "B.XOR", 8, cohort="6"),
                "challenger_exam": _panel("c", 13, "B.XOR", 8, cohort="6"),
            }})
        self.assertTrue({"B.AND", "B.XOR"} <= set(changes))
        self.assertFalse(any(d["decision"] in (
            "TITLE_MATCH_REQUIRED", "FANOUT_SCREEN_REQUIRED",
            "FANOUT_TITLE_MATCH_REQUIRED") for d in decisions))
        xor_battery = result["active_roles"]["B.XOR"]["surviving_battery"]
        current_ids = {q["id"] for segment in xor_battery
                       for q in segment["questions"]
                       if q["id"].startswith("6" * 64 + "B.XOR")}
        self.assertEqual(len(current_ids), 8,
                         "the fresh fan-out gate's eighth correct answer must survive")
