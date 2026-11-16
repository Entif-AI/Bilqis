"""Epoch championship settled ledger behavior."""
from bilqis_mlx.learning.tests.test_epoch_championships import (
    EpochChampionshipTests, GRADES, _battery_answers, _epoch,
    _match, _panel, advance_epoch, build_school_identity,
    deepcopy, enforce_school_identity, needed_incumbents,
)


class EpochSettledLedgerTests(EpochChampionshipTests):
    def test_settled_pair_never_rematches_or_mutates_role_again(self):
        first = _panel("a", 11, "B.XOR", 12)
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        role = epoch["active_roles"]["B.XOR"]
        challenger = _panel("c", 12, "B.XOR", 12, cohort="6")
        incumbent = _panel("a", 11, "B.XOR", 12, cohort="6")
        incumbent_battery = _battery_answers(role, drop=0)
        challenger_battery = _battery_answers(role, drop=1)
        defended, _, _ = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams={"a" * 64: incumbent},
            title_matches={"B.XOR": _match(
                role, _panel("a", 11, "B.XOR", 11, cohort="6"),
                _panel("c", 12, "B.XOR", 11, cohort="6"),
                incumbent_battery=incumbent_battery,
                challenger_battery=challenger_battery)})
        frozen_role = deepcopy(defended["active_roles"]["B.XOR"])
        self.assertEqual(len(defended["settled_matchups"]), 1)

        rematch = _panel("c", 12, "B.XOR", 12, cohort="7")
        rematch_incumbent = _panel("a", 11, "B.XOR", 8, cohort="7")
        result, changes, decisions = advance_epoch(
            defended, grades=GRADES, challenger_exam=rematch,
            incumbent_exams={"a" * 64: rematch_incumbent})
        self.assertEqual(changes, ())
        self.assertEqual(
            needed_incumbents(defended, grades=GRADES, challenger_exam=rematch), {})
        self.assertTrue(any(d.get("decision") == "TITLE_MATCH_ALREADY_SETTLED"
                            for d in decisions))
        self.assertFalse(any(d.get("decision") in (
            "TITLE_MATCH_REQUIRED", "TITLE_WON", "TITLE_DEFENDED")
                             for d in decisions))
        self.assertEqual(result["active_roles"]["B.XOR"], frozen_role)

    def test_settled_pair_remains_permanent_after_holistic_identity_reset(self):
        first = _panel("a", 11, "B.XOR", 12)
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        role = epoch["active_roles"]["B.XOR"]
        challenger = _panel("c", 12, "B.XOR", 12, cohort="6")
        defended, _, _ = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams={
                "a" * 64: _panel("a", 11, "B.XOR", 12, cohort="6")},
            title_matches={"B.XOR": _match(
                role, _panel("a", 11, "B.XOR", 11, cohort="6"),
                _panel("c", 12, "B.XOR", 11, cohort="6"),
                incumbent_battery=_battery_answers(role, drop=0),
                challenger_battery=_battery_answers(role, drop=1))})
        old_identity = build_school_identity(
            course_sha256="1" * 64, semantic_graph_sha256="2" * 64,
            parameter_shapes={"embedding.weight": [1, 1]},
            factory_release_sha256="3" * 64)
        new_identity = build_school_identity(
            course_sha256="4" * 64, semantic_graph_sha256="2" * 64,
            parameter_shapes={"embedding.weight": [1, 1]},
            factory_release_sha256="3" * 64)
        defended["championship_school_identity"] = old_identity
        settled = deepcopy(defended["settled_matchups"])
        reset, changed = enforce_school_identity(
            defended, new_identity, generation=20,
            student=_panel("d", 12, "B.XOR", 12)["checkpoint"])
        self.assertTrue(changed)
        self.assertEqual(reset["active_roles"], {})
        self.assertEqual(reset["settled_matchups"], settled)

        reearned, changes, _ = advance_epoch(
            reset, grades=GRADES,
            challenger_exam=_panel("a", 13, "B.XOR", 12, cohort="7"),
            incumbent_exams={})
        self.assertEqual(changes, ("B.XOR",))
        rematch = _panel("c", 14, "B.XOR", 12, cohort="8")
        result, changes, decisions = advance_epoch(
            reearned, grades=GRADES, challenger_exam=rematch,
            incumbent_exams={})
        self.assertEqual(changes, ())
        self.assertEqual(needed_incumbents(
            reearned, grades=GRADES, challenger_exam=rematch), {})
        self.assertTrue(any(
            decision.get("decision") == "TITLE_MATCH_ALREADY_SETTLED"
            for decision in decisions))
        self.assertEqual(
            result["active_roles"]["B.XOR"]["checkpoint"]["sha256"],
            "a" * 64)

    def test_settled_pair_key_is_direction_independent_after_title_transfer(self):
        first = _panel("a", 11, "B.XOR", 12)
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        role = epoch["active_roles"]["B.XOR"]
        challenger = _panel("c", 12, "B.XOR", 12, cohort="6")
        won, _, _ = advance_epoch(
            epoch, grades=GRADES, challenger_exam=challenger,
            incumbent_exams={"a" * 64: _panel("a", 11, "B.XOR", 12, cohort="6")},
            title_matches={"B.XOR": _match(
                role, _panel("a", 11, "B.XOR", 10, cohort="6"),
                _panel("c", 12, "B.XOR", 11, cohort="6"),
                incumbent_battery=_battery_answers(role, drop=2),
                challenger_battery=_battery_answers(role, drop=0))})
        reverse = _panel("a", 14, "B.XOR", 12, cohort="7")
        result, changes, decisions = advance_epoch(
            won, grades=GRADES, challenger_exam=reverse, incumbent_exams={})
        self.assertEqual(changes, ())
        self.assertEqual(result["active_roles"]["B.XOR"]["checkpoint"]["sha256"],
                         "c" * 64)
        self.assertTrue(any(d.get("decision") == "TITLE_MATCH_ALREADY_SETTLED"
                            for d in decisions))
