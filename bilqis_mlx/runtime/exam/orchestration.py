"""Routine and promotion exam orchestration."""
from __future__ import annotations

from .finalize import ExamFinalization, finalize_exam
from .orchestration_phases import (
    prepare_exam,
    run_championship,
    run_promotion,
    run_routine,
)


def _take_exam(
        mx, run_dir, receipt, manifest, course, source_root, source_checkpoint,
        parameters, optimizer, graph, *, reserve_gib,
        scheduler_only: bool = False, session_elapsed_seconds=None):
    setup = prepare_exam(
        mx, run_dir, receipt, manifest, course, source_root, parameters,
        optimizer, graph, reserve_gib=reserve_gib,
        scheduler_only=scheduler_only)
    routine = run_routine(
        mx, run_dir, setup, graph, parameters,
        scheduler_only=scheduler_only,
        session_elapsed_seconds=session_elapsed_seconds)
    selected = run_promotion(
        mx, run_dir, setup, routine, manifest, source_root, graph, parameters,
        scheduler_only=scheduler_only)
    championship = run_championship(
        mx, run_dir, setup, selected, course, graph, parameters,
        reserve_gib=reserve_gib, scheduler_only=scheduler_only)
    final_receipt = {
        **setup.receipt,
        "_routine_learning_diagnostics": routine.warnings,
        "_candidate_cohort_sha256": (
            setup.candidate_cohort.digest
            if setup.candidate_cohort is not None else None),
    }
    return finalize_exam(ExamFinalization(
        mx=mx,
        run_dir=run_dir,
        receipt=final_receipt,
        graph=graph,
        school=setup.school,
        full_scope=setup.full_scope,
        blocked_before=setup.blocked_before,
        blocked_after=routine.blocked_after,
        routine_cohort=setup.routine_cohort,
        routine_file=setup.routine_file,
        routine_measured=routine.measured,
        routine_guesses=routine.guesses,
        parent_checkpoint=setup.parent_checkpoint,
        parent_routine_scores=routine.parent_scores,
        parent_routine_issue=routine.parent_issue,
        cohort=selected.cohort,
        cohort_pointer=selected.pointer,
        cohort_file=selected.cohort_file,
        rows=selected.rows,
        guesses=selected.guesses,
        measured=selected.measured,
        assessment=selected.assessment,
        advanced=selected.advanced,
        qualification=selected.qualification,
        promotion_passed=selected.promotion_passed,
        frontier=setup.frontier,
        roles=setup.roles,
        compared=setup.compared,
        stagnation=routine.stagnation,
        stagnation_events=routine.stagnation_events,
        epoch=championship.epoch,
        perfect=championship.perfect,
        frozen_soups=championship.frozen_soups,
        soup_changes=championship.soup_changes,
        championship_roles=championship.roles,
        championship_decisions=championship.decisions,
        generator=setup.generator,
        scheduler_only=scheduler_only,
    ))
