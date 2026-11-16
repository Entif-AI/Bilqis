"""Capability-local defended championships and one-hop same-grade fan-out."""
from copy import deepcopy
from types import MappingProxyType
from unittest import TestCase

from bilqis_mlx.learning.championship_identity import (
    build_school_identity, enforce_school_identity)
from bilqis_mlx.learning.epoch_championships import (
    active_frontier, advance_epoch, needed_incumbents,
    rebase_active_championships, reset_active_championships,
)
from bilqis_mlx.learning.grade_soup import grade_soup_recipe
from bilqis_mlx.learning.mentor_epoch import EARNED_ONLY_POLICY
from bilqis_mlx.learning.tests.test_championship_policy import GRADE_B, SCHOOL, _exam


GRADES = MappingProxyType({
    "A": tuple(cap for cap in SCHOOL if cap.startswith("A.")),
    "B": GRADE_B,
    "C": tuple(cap for cap in SCHOOL if cap.startswith("C.")),
})


def _epoch():
    return {
        "introduced_grade": "C",
        "baseline": _exam("b", 208)["checkpoint"],
        "previous_capabilities": list(GRADES["A"] + GRADES["B"]),
        "qualified": [],
        "historical_advisers_remain_archived": True,
    }


def _with_question_evidence(exam):
    result = deepcopy(exam)
    result["correct_questions"] = {
        cap: [{"id": result["cohort_sha256"] + cap + str(i), "gold": "TRUE"}
              for i in range(score["correct"])]
        for cap, score in result["scores"].items()}
    result["questions"] = {
        cap: [{"id": result["cohort_sha256"] + cap + str(i), "gold": "TRUE"}
              for i in range(score["total"])]
        for cap, score in result["scores"].items()}
    return result


def _panel(seed, step, capability, correct, *, cohort="1", grade=None):
    exam = _exam(seed, 208)
    exam["checkpoint"]["optimizer_step"] = step
    exam["cohort_sha256"] = cohort * 64
    exam["scores"] = {capability: {"correct": correct, "total": 12}}
    exam["challenge_grade"] = grade or capability.split(".", 1)[0]
    exam["checkpoint_origin_grade"] = exam["challenge_grade"]
    return _with_question_evidence(exam)


def _multi_panel(seed, step, scores, *, cohort="1", grade="B"):
    exam = _exam(seed, 208)
    exam["checkpoint"]["optimizer_step"] = step
    exam["cohort_sha256"] = cohort * 64
    exam["scores"] = {cap: {"correct": correct, "total": 12}
                      for cap, correct in scores.items()}
    exam["challenge_grade"] = grade
    exam["checkpoint_origin_grade"] = grade
    return _with_question_evidence(exam)


def _battery_answers(role, *, drop=0):
    result = {}
    for segment in role["surviving_battery"]:
        ids = [q["id"] for q in segment["questions"]]
        result[segment["sha256"]] = ids[:max(0, len(ids) - drop)]
    return result


def _match(role, incumbent_current, challenger_current, *,
           incumbent_battery, challenger_battery):
    return {
        "incumbent_checkpoint_sha256": role["checkpoint"]["sha256"],
        "challenger_checkpoint_sha256": challenger_current["checkpoint"]["sha256"],
        "incumbent_current_exam": incumbent_current,
        "challenger_current_exam": challenger_current,
        "battery_results": {
            role["checkpoint"]["sha256"]: incumbent_battery,
            challenger_current["checkpoint"]["sha256"]: challenger_battery,
        },
    }


class EpochChampionshipTests(TestCase):
    def _fanout_fixture(self):
        first = _panel("a", 11, "B.AND", 8)
        epoch, _, _ = advance_epoch(
            _epoch(), grades=GRADES, challenger_exam=first, incumbent_exams={})
        second = _panel("b", 12, "B.XOR", 8, cohort="2")
        epoch, _, _ = advance_epoch(
            epoch, grades=GRADES, challenger_exam=second, incumbent_exams={})
        challenger = _multi_panel(
            "c", 13, {"B.AND": 10, "B.XOR": 8}, cohort="6", grade="B")
        incumbents = {
            "a" * 64: _panel("a", 11, "B.AND", 8, cohort="6"),
            "b" * 64: _panel("b", 12, "B.XOR", 8, cohort="6"),
        }
        return epoch, challenger, incumbents
