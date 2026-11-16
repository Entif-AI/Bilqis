"""Visit preparation through candidate-fork creation."""
from __future__ import annotations

import json
import random


def _prepare_authority(d, s):
    s.capture = d.ObservationCapture(s.run_dir, s.receipt, enabled=s.capture_teacher_observations)
    s.school = d._runtime_state._state_from_json(
        s.receipt["school"],
        d._runtime_release_adoption._schedule_for_receipt(s.run_dir, s.receipt, s.course))
    if (s.receipt.get("mentor_epoch") is not None and
            s.receipt.get("championship_school_identity") !=
            d._learning_championship_runtime._live_championship_identity(
                s.receipt, s.course, s.graph, s.params)):
        raise ValueError("CHAMPIONSHIP_SCHOOL_IDENTITY_RESET_REQUIRED")
    s.cap = d._curriculum_scheduler.next_capability(s.school)
    if s.cap is None:
        raise ValueError("HUMAN_TRAINER_NO_SCHEDULED_CAPABILITY")
    s.stage_before = s.school.stage
    d._runtime_timing_trace.trace_mark(
        "VISIT_START", generation=s.receipt["generation"], capability=s.cap,
        phase=s.stage_before, optimizer_step=int(s.optimizer.state["step"].item()))
    if s.cap in set(d._learning_stagnation_control.quarantined_capabilities(
            s.receipt.get("stagnation_session"))):
        return d._skip_stagnant_target_visit(
            s.run_dir, s.receipt, s.school, s.course, s.cap,
            int(s.optimizer.state["step"].item()))
    s.introduction_pass = s.school.stage == "MAIN"
    s.lesson_grade = s.cap.split(".", 1)[0]
    s.executable_release = d._runtime_admission._read_executable_factory_release_artifact(
        s.run_dir, s.receipt)
    s.program = d._factory_schedule.schedule_program_from_executable_release(s.executable_release)
    if s.lesson_grade not in {grade.id for grade in s.program.grades}:
        raise ValueError("HUMAN_TRAINER_UNKNOWN_LESSON_GRADE")
    s.teacher = json.loads(d._runtime_state._canonical(s.receipt["teacher"]))
    s.rng = random.Random(d._runtime_state._seed(s.receipt, capability=s.cap))
    s.teacher_curriculum_scope = (
        str(s.receipt.get("curriculum_mode", "")) + "/" +
        str(s.receipt.get("numeric_maximum", "")))
    s.plasticity_escape = d._learning_plasticity_escape.activation(
        s.teacher, s.cap, s.teacher_curriculum_scope, s.school, s.program,
        receipt=s.receipt)
    s.candidate_steps = d._learning_learning_experiment.candidate_step_budget(
        s.steps_per_visit, s.teacher, s.cap, curriculum_scope=s.teacher_curriculum_scope)
    if s.source_root is None:
        raise ValueError("HUMAN_TRAINER_LIVE_SOURCE_REQUIRED")
    return None


def _prepare_policy_and_trial(d, s):
    with d._runtime_timing_trace.trace_span("VISIT_SOURCE_DRAW", capability=s.cap):
        s.rows = d._runtime_assessment._draw_live_rows(
            s.source_root, s.graph,
            seed=d._runtime_state._seed(s.receipt, capability=s.cap), capability=s.cap,
            each=max(32, s.batch_size), course=s.course,
            executable_release=s.executable_release)
    s.confidence_champions, s.frozen_soups, s.soup_vote_receipts = d._load_visit_mentors(
        s.run_dir, s.receipt, s.lesson_grade, s.graph, s.program, s.cap)
    s.confidence_examples = 0
    s.confidence_total_weight = 0.0
    s.confidence_applied_steps = 0
    s.direct_capability_votes, s.direct_capabilities = d._direct_mentor_votes(
        s.confidence_champions)
    s.champion_candidates, s.champion_candidate_ids = d._discover_champion_weakness(
        s.mx, s.confidence_champions, s.params, s.rows, s.receipt, s.cap)
    (s.priority, s.deferred_misses, s.miss_exposures, s.warnings,
     s.previsit_diagnostics) = d._prepare_visit_feedback(
        s.receipt, s.cap, s.champion_candidates, s.champion_candidate_ids)
    s.policy_key, s.policy, s.policy_selection = d._select_visit_policy(
        s.engine, s.teacher, s.cap, s.school, s.rng, s.learning_settings,
        s.teacher_curriculum_scope, s.previsit_diagnostics, s.lesson_grade,
        len(d._curriculum_scheduler.assessment_capabilities(s.program, s.school)),
        s.plasticity_escape)
    s.capture.select_option(s.cap, s.autonomy_teaching_option)
    s.capture.propose(
        s.executable_release, s.school, s.cap, s.policy_key, s.policy, s.policy_selection,
        configured_steps=s.steps_per_visit, effective_steps=s.candidate_steps,
        batch_size=s.batch_size, settings=s.learning_settings,
        enrichment=s.boolean_association_bridge, source_rows=s.rows, teacher=s.teacher,
        parent_optimizer_step=int(s.optimizer.state["step"].item()))
    s.original_learning_rate = s.optimizer.learning_rate
    s.optimizer.learning_rate = float(s.policy["lr"])
    with d._runtime_timing_trace.trace_span(
            "TRAIN_SCORE_BEFORE", capability=s.cap, row_count=len(s.rows)):
        s.before = d._learning_student_ops._train_score(
            s.mx, s.params, s.rows, s.receipt["config"], s.receipt["answer_ids"])
    s.shadow_rungs = (
        d._learning_teacher_multifidelity.active_rungs(
            d._learning_teacher_multifidelity.DEFAULT_SHADOW_POLICY, s.candidate_steps)
        if s.learning_settings is not None else ())
    s.shadow_probes = []
    s.retention_canary_activation = (
        d._learning_retention_canary.activation(s.teacher)
        if s.learning_settings is not None else {"status": "NOT_QUALIFIED"})
    s.retention_canary_probe = None
    s.retention_canary_stop = False
    s.attempted_candidate_steps = 0
    s.parent_parameters, s.parent_optimizer = s.params, s.optimizer
    (s.probe_rows, s.protected_caps, s.parent_predictions, s.params, s.optimizer,
     skipped) = d._prepare_retention_trial(
        s.mx, s.run_dir, s.receipt, s.course, s.school, s.cap, s.learning_settings,
        s.source_root, s.graph, s.executable_release, s.params, s.optimizer,
        s.original_learning_rate, s.teacher)
    if skipped is not None:
        s.capture.finish(
            skipped["_pending_visit_events"][-1], decision=None, paired=None,
            protected=None, stage="PERFECT_TARGET_SKIP", attempted=0, retained=0)
        return skipped
    return None


def prepare(d, s):
    early = _prepare_authority(d, s)
    if early is not None:
        return early
    return _prepare_policy_and_trial(d, s)
