"""Multi-grade championship adjudication orchestration."""
from __future__ import annotations

import bilqis_mlx.learning.epoch_championships as _learning_epoch_championships
import bilqis_mlx.runtime.release_adoption as _runtime_release_adoption

from .exams import _epoch_paired_examinations
from .matches import _fresh_fanout_screen, _fresh_title_match


def _advance_exam_championship_grade(mx, run_dir, receipt, epoch, course, school,
                                     cohort, measured, predictions, parameters, graph,
                                     *, challenge_grade):
    current = {**receipt, "mentor_epoch": epoch}
    grades, challenger, incumbents = _epoch_paired_examinations(
        mx, run_dir, current, course, school, cohort, measured["scores"], predictions,
        graph, challenge_grade=challenge_grade)
    title_matches = {}
    fanout_screen = None
    proposed = epoch
    changes = decisions = ()
    for round_index in range(5):
        proposed, changes, decisions = _learning_epoch_championships.advance_epoch(
            epoch, grades=grades, challenger_exam=challenger,
            incumbent_exams=incumbents, title_matches=title_matches,
            fanout_screen=fanout_screen)
        screen_requests = [decision for decision in decisions
                           if decision["decision"] == "FANOUT_SCREEN_REQUIRED"]
        if screen_requests:
            if fanout_screen is not None or len(screen_requests) != 1:
                raise ValueError("CHAMPIONSHIP_FANOUT_SCREEN_RECURSION")
            request = screen_requests[0]
            fanout_screen = _fresh_fanout_screen(
                mx, run_dir, receipt, epoch, cohort, challenger,
                parameters, graph, request["capabilities"])
            continue
        pending = {
            decision["capability"] for decision in decisions
            if decision["decision"] in (
                "TITLE_MATCH_REQUIRED", "FANOUT_TITLE_MATCH_REQUIRED") and
            decision["capability"] not in title_matches}
        if not pending:
            return proposed, changes, decisions
        if round_index == 4:
            raise ValueError("CHAMPIONSHIP_TITLE_MATCH_RECURSION")
        for cap in sorted(pending):
            role = epoch["active_roles"][cap]
            title_matches[cap] = _fresh_title_match(
                mx, run_dir, receipt, epoch, cohort, challenger,
                parameters, graph, cap)
    raise AssertionError("unreachable")


def _advance_exam_championships(mx, run_dir, receipt, epoch, course, school,
                                cohort, measured, predictions, parameters, graph):
    """Adjudicate every measured capability grade for the intact checkpoint."""
    scores = measured["scores"]
    represented = [
        grade.id for grade in _runtime_release_adoption._schedule_for_receipt(run_dir, receipt, course).grades
        if any(cap.id in scores for cap in grade.capabilities)
    ]
    if not represented:
        raise ValueError("CHAMPIONSHIP_EPOCH_NO_MEASURED_TITLE_GRADE")
    updated = epoch
    changed_roles, decisions = set(), []
    for grade in represented:
        updated, changed, verdicts = _advance_exam_championship_grade(
            mx, run_dir, receipt, updated, course, school, cohort, measured,
            predictions, parameters, graph, challenge_grade=grade)
        changed_roles.update(changed)
        decisions.extend(verdicts)
    return updated, tuple(sorted(changed_roles)), tuple(decisions)
