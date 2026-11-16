"""Epoch championship authority behavior."""
from bilqis_mlx.learning.tests.test_epoch_championships import (
    EpochChampionshipTests, GRADES, _battery_answers, _epoch,
    _match, _multi_panel, _panel, advance_epoch,
    needed_incumbents,
)


class EpochAuthorityTests(EpochChampionshipTests):
    def test_explicit_reset_floor_blocks_same_step_authority_but_allows_newer_checkpoint(self):
        epoch = _epoch()
        epoch["championship_eligibility_after_step"] = 12
        stale = _panel("a", 12, "A.0", 12, grade="A")
        unchanged, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=stale, incumbent_exams={})
        self.assertEqual(changes, ())
        self.assertEqual(decisions, ())
        self.assertEqual(unchanged.get("active_roles", {}), {})

        fresh = _panel("c", 13, "A.0", 12, grade="A")
        admitted, changes, decisions = advance_epoch(
            unchanged, grades=GRADES, challenger_exam=fresh, incumbent_exams={})
        self.assertEqual(changes, ("A.0",))
        self.assertEqual(decisions, ())
        self.assertEqual(admitted["active_roles"]["A.0"]["checkpoint"]["sha256"],
                         "c" * 64)

    def test_role_persists_same_grade_checkpoint_origin(self):
        result, _, _ = advance_epoch(
            _epoch(), grades=GRADES,
            challenger_exam=_panel("a", 11, "A.0", 10, grade="A"),
            incumbent_exams={})
        self.assertEqual(result["active_roles"]["A.0"]["origin_grade"], "A")

    def test_cross_grade_legacy_owner_is_archived_before_same_grade_mint(self):
        first = _panel("a", 11, "A.0", 10, grade="A")
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        epoch["active_roles"]["A.0"]["origin_grade"] = "B"
        challenger = _panel("c", 12, "A.0", 12, cohort="6", grade="A")
        result, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger, incumbent_exams={})
        self.assertEqual(changes, ("A.0",))
        self.assertEqual(decisions, ())
        self.assertEqual(result["active_roles"]["A.0"]["checkpoint"]["sha256"],
                         "c" * 64)
        self.assertEqual(result["active_roles"]["A.0"]["origin_grade"], "A")
        archived = result["invalidated_active_roles"][-1]
        self.assertEqual((archived["capability"], archived["origin_grade"],
                          archived["reason"]),
                         ("A.0", "B", "CROSS_GRADE_TITLE_OWNER"))

    def test_missing_legacy_origin_is_archived_fail_closed_before_same_grade_mint(self):
        first = _panel("a", 11, "A.0", 10, grade="A")
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        del epoch["active_roles"]["A.0"]["origin_grade"]
        challenger = _panel("c", 12, "A.0", 12, cohort="6", grade="A")
        result, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger, incumbent_exams={})
        self.assertEqual(changes, ("A.0",))
        self.assertEqual(decisions, ())
        self.assertEqual(result["invalidated_active_roles"][-1]["reason"],
                         "TITLE_ORIGIN_PROVENANCE_MISSING")

    def test_empty_role_requires_at_least_sixty_six_percent(self):
        below = _panel("a", 11, "B.XOR", 7, grade="B")
        result, changes, decisions = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=below, incumbent_exams={})
        self.assertEqual(changes, ())
        self.assertNotIn("B.XOR", result.get("active_roles", {}))
        self.assertEqual(decisions[0]["decision"], "INITIAL_TITLE_THRESHOLD_NOT_MET")

        candidate = _panel("c", 12, "B.XOR", 8, grade="B")
        result, changes, decisions = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=candidate, incumbent_exams={})
        self.assertEqual(changes, ("B.XOR",))
        self.assertEqual(decisions, ())
        self.assertEqual(set(result["active_roles"]), {"B.XOR"})
        self.assertEqual(result["active_roles"]["B.XOR"]["correct"], 8)

    def test_initial_title_battery_is_exactly_first_threshold_passes(self):
        candidate = _panel("a", 11, "B.XOR", 8, grade="B")
        result, changes, decisions = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=candidate, incumbent_exams={})
        self.assertEqual(changes, ("B.XOR",))
        self.assertEqual(decisions, ())
        role = result["active_roles"]["B.XOR"]
        battery = [question for segment in role["surviving_battery"]
                   for question in segment["questions"]]
        expected = [
            {**question, "capability": "B.XOR"}
            for question in candidate["correct_questions"]["B.XOR"]
        ]
        self.assertEqual(
            {question["id"] for question in battery},
            {question["id"] for question in expected})
        self.assertEqual(len(battery), 8)
        self.assertEqual({question["capability"] for question in battery}, {"B.XOR"})

    def test_empty_roles_get_per_capability_batteries(self):
        candidate = _multi_panel("a", 11, {"B.AND": 12, "B.XOR": 12})
        result, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=candidate, incumbent_exams={})
        for cap in ("B.AND", "B.XOR"):
            battery = result["active_roles"][cap]["surviving_battery"]
            self.assertEqual(
                {q["capability"] for segment in battery for q in segment["questions"]},
                {cap})

    def test_cross_grade_incumbents_are_not_requested_or_competed(self):
        a = _panel("a", 11, "A.0", 10, grade="A")
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=a, incumbent_exams={})
        b = _panel("b", 12, "B.XOR", 10, grade="B")
        epoch, _, _ = advance_epoch(
            epoch, grades=GRADES, challenger_exam=b, incumbent_exams={})
        challenger = _multi_panel("c", 13, {"A.0": 12, "B.XOR": 11},
                                  cohort="6", grade="B")
        needed = needed_incumbents(epoch, grades=GRADES, challenger_exam=challenger)
        self.assertEqual(set(needed), {"b" * 64})
        incumbent = _panel("b", 12, "B.XOR", 10, cohort="6", grade="B")
        result, _, _ = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams={"b" * 64: incumbent})
        self.assertEqual(result["active_roles"]["A.0"], epoch["active_roles"]["A.0"])

    def test_cross_grade_update_can_win_a_capability_local_title(self):
        incumbent = _panel("a", 11, "B.XOR", 8, grade="B")
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=incumbent,
            incumbent_exams={})
        role = epoch["active_roles"]["B.XOR"]

        challenger = _panel("c", 12, "B.XOR", 12, cohort="6", grade="B")
        challenger["checkpoint_origin_grade"] = "A"
        requested = needed_incumbents(
            epoch, grades=GRADES, challenger_exam=challenger)
        self.assertEqual(set(requested), {"a" * 64})

        incumbent_current = _panel("a", 11, "B.XOR", 8, cohort="6", grade="B")
        challenger_current = _panel("c", 12, "B.XOR", 12, cohort="6", grade="B")
        challenger_current["checkpoint_origin_grade"] = "A"
        result, changes, decisions = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams={"a" * 64: incumbent_current},
            title_matches={"B.XOR": _match(
                role, incumbent_current, challenger_current,
                incumbent_battery=_battery_answers(role, drop=2),
                challenger_battery=_battery_answers(role, drop=0))})
        self.assertIn("B.XOR", changes)
        winner = result["active_roles"]["B.XOR"]
        self.assertEqual(winner["checkpoint"]["sha256"], "c" * 64)
        self.assertEqual(winner["origin_grade"], "B")
        self.assertEqual(winner["checkpoint_origin_grade"], "A")
        self.assertTrue(any(d["decision"] == "TITLE_WON" for d in decisions))
