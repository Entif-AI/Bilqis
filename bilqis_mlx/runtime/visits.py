"""Compatibility facade for source-grounded teaching visits.

The visit lifecycle is split into cohesive internal phase owners.  This module
keeps the historical patch/import surface stable for trainer code and tests.
"""
from __future__ import annotations

import dataclasses as _dataclasses
from types import SimpleNamespace as _SimpleNamespace

import bilqis_mlx.curriculum.scheduler as _curriculum_scheduler
import bilqis_mlx.diagnostics.teaching as _diagnostics_teaching
import bilqis_mlx.factory.schedule as _factory_schedule
import bilqis_mlx.learning.champion_confidence as _learning_champion_confidence
import bilqis_mlx.learning.championship_runtime as _learning_championship_runtime
import bilqis_mlx.learning.learning_experiment as _learning_learning_experiment
import bilqis_mlx.learning.lesson_guidance as _learning_lesson_guidance
import bilqis_mlx.learning.plasticity_escape as _learning_plasticity_escape
import bilqis_mlx.learning.stagnation_control as _learning_stagnation_control
import bilqis_mlx.learning.student_ops as _learning_student_ops
import bilqis_mlx.learning.teacher_feedback as _learning_teacher_feedback
import bilqis_mlx.learning.teacher_multifidelity as _learning_teacher_multifidelity
import bilqis_mlx.learning.teacher_strategy_population as _learning_teacher_strategy_population
import bilqis_mlx.mature_debt as _mature_debt
import bilqis_mlx.profiles.catalog as _profiles_catalog
import bilqis_mlx.profiles.retention as _profiles_retention
import bilqis_mlx.runtime.admission as _runtime_admission
import bilqis_mlx.runtime.assessment as _runtime_assessment
import bilqis_mlx.runtime.candidate_evidence as _runtime_candidate_evidence
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints
import bilqis_mlx.runtime.release_adoption as _runtime_release_adoption
import bilqis_mlx.runtime.state as _runtime_state
import bilqis_mlx.runtime.timing_trace as _runtime_timing_trace
import bilqis_mlx.source_adapters.school as _source_adapters_school

from ._visits import common as _common
from ._visits.orchestration import take_visit as _orchestrate_visit
from .teacher_observation_capture import ObservationCapture
from .teacher_policy_selection import select_visit_policy as _select_visit_policy


RETENTION_REQUIRES_ACTIVE_GRADE_ERROR = _common.RETENTION_REQUIRES_ACTIVE_GRADE_ERROR
TEACHER_EXPOSURE_HISTORY_INVALID = _common.TEACHER_EXPOSURE_HISTORY_INVALID


def _deps():
    return _SimpleNamespace(**globals())


def _retention_frontier_grade(school) -> str:
    return _common.retention_frontier_grade(school)


def _teacher_exposures_after_candidate(receipt: dict, attempted: dict, *, decision: str) -> dict:
    return _common.teacher_exposures_after_candidate(receipt, attempted, decision=decision)


def _teaching_enrichment_rows(source_root, graph, course, capability, *, seed: int,
                              enabled: bool, release=None):
    return _common.teaching_enrichment_rows(
        _deps(), source_root, graph, course, capability, seed=seed,
        enabled=enabled, release=release)


def _extend_binary_guidance(guidance, rows):
    return _common.extend_binary_guidance(guidance, rows)


def _skip_perfect_target_visit(run_dir, receipt, school, course, capability,
                               probe_total, optimizer_step, *, teacher=None):
    return _common.skip_perfect_target_visit(
        _deps(), run_dir, receipt, school, course, capability, probe_total,
        optimizer_step, teacher=teacher)


def _skip_stagnant_target_visit(run_dir, receipt, school, course, capability, optimizer_step):
    return _common.skip_stagnant_target_visit(
        _deps(), run_dir, receipt, school, course, capability, optimizer_step)


def _selection_feedback(teacher, capability, curriculum_scope, policy,
                        outcome, before, after, context_credit):
    return _common.selection_feedback(
        _deps(), teacher, capability, curriculum_scope, policy,
        outcome, before, after, context_credit)


def _teacher_event_fields(policy_selection, policy_health):
    return _common.teacher_event_fields(_deps(), policy_selection, policy_health)


def _prepare_visit_feedback(receipt, cap, champion_candidates, champion_candidate_ids):
    return _common.prepare_visit_feedback(
        _deps(), receipt, cap, champion_candidates, champion_candidate_ids)


def _direct_mentor_votes(confidence_champions):
    return _common.direct_mentor_votes(confidence_champions)


def _methodology_lesson_rows(capability: str, fresh, priority, picked):
    return _common.methodology_lesson_rows(capability, fresh, priority, picked)


def _visit_retention_scope(run_dir, receipt, course, school, cap, learning_settings,
                           *, candidate_steps=1, fragile_fixed_rows=()):
    return _common.visit_retention_scope(
        _deps(), run_dir, receipt, course, school, cap, learning_settings,
        candidate_steps=candidate_steps, fragile_fixed_rows=fragile_fixed_rows)


def _prepare_retention_trial(mx, run_dir, receipt, course, school, cap, learning_settings,
                             source_root, graph, executable_release, params, optimizer,
                             original_learning_rate, teacher):
    return _common.prepare_retention_trial(
        _deps(), mx, run_dir, receipt, course, school, cap, learning_settings,
        source_root, graph, executable_release, params, optimizer,
        original_learning_rate, teacher)


def _discover_champion_weakness(mx, confidence_champions, params, rows, receipt, cap):
    return _common.discover_champion_weakness(
        _deps(), mx, confidence_champions, params, rows, receipt, cap)


def _load_visit_mentors(run_dir, receipt, lesson_grade, graph, program, cap):
    return _common.load_visit_mentors(
        _deps(), run_dir, receipt, lesson_grade, graph, program, cap)


def _take_visit(mx, run_dir, receipt, manifest, course, engine,
                params, optimizer, graph, *, steps_per_visit, batch_size, reserve_gib,
                source_root=None,
                learning_settings: _learning_learning_experiment.Settings | None = None,
                boolean_association_bridge: bool = False,
                source_prefetch_executor=None, source_prefetch_workers: int = 0,
                autonomy_teaching_option: str | None = None,
                capture_teacher_observations: bool = True):
    return _orchestrate_visit(
        _deps(), mx, run_dir, receipt, manifest, course, engine, params, optimizer, graph,
        steps_per_visit=steps_per_visit, batch_size=batch_size, reserve_gib=reserve_gib,
        source_root=source_root, learning_settings=learning_settings,
        boolean_association_bridge=boolean_association_bridge,
        source_prefetch_executor=source_prefetch_executor,
        source_prefetch_workers=source_prefetch_workers,
        autonomy_teaching_option=autonomy_teaching_option,
        capture_teacher_observations=capture_teacher_observations)
