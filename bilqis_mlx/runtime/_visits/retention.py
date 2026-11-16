"""Candidate evidence, retention decision, and teacher feedback."""
from __future__ import annotations


def _score_candidate(d, s):
    with d._runtime_timing_trace.trace_span(
            "TRAIN_SCORE_AFTER", capability=s.cap, row_count=len(s.rows)):
        s.after = d._learning_student_ops._train_score(
            s.mx, s.params, s.rows, s.receipt["config"], s.receipt["answer_ids"])
    s.attempted_step = int(s.optimizer.state["step"].item())
    if s.attempted_step != s.step_before + s.attempted_candidate_steps:
        raise ValueError("HUMAN_TRAINER_OPTIMIZER_STEP_DRIFT")
    s.candidate_gain = s.after - s.before
    if s.shadow_rungs and s.attempted_candidate_steps == s.candidate_steps:
        s.shadow_probes.append((
            s.candidate_steps, d._learning_teacher_multifidelity.target_correct_delta(
                s.before, s.after, len(s.rows))))
    s.realized_action = (
        d._learning_learning_experiment.realized_teacher_action(
            s.policy, candidate_steps=s.attempted_candidate_steps, batch_size=s.batch_size,
            policy_controls=s.policy_control_receipts,
            guidance_applied_steps=s.confidence_applied_steps,
            enrichment_examples=s.enrichment_examples)
        if s.learning_settings is not None else None)


def _decide_candidate(d, s):
    s.outcome = s.context_credit = None
    if s.learning_settings is not None:
        with d._runtime_timing_trace.trace_span("RETENTION_CANDIDATE_EVIDENCE", capability=s.cap):
            (s.pair, s.probed, current_grade, fixed_grade_evidence, replay, frontier,
             s.stage) = d._runtime_candidate_evidence._candidate_grade_evidence(
                s.mx, s.run_dir, s.receipt, s.course, s.school, s.cap,
                s.parent_parameters, s.params, s.probe_rows, s.parent_predictions,
                s.learning_settings, s.plasticity_escape)
        with d._runtime_timing_trace.trace_span("RETENTION_DECIDE", capability=s.cap):
            s.outcome = d._learning_learning_experiment.decide(
                s.pair, active_capability=s.cap, phase=s.school.stage,
                protected=s.probed, settings=s.learning_settings,
                same_grade_capabilities=current_grade, fixed_grade_replay=fixed_grade_evidence,
                fixed_frontier_replay=frontier,
                protected_frontier_grade=d._retention_frontier_grade(s.school),
                mature_grades=frozenset(s.school.champions),
                mature_grade_debt=d._mature_debt.as_mapping(s.school),
                negative_prototypes=s.teacher["causal_experiment"]["negative_archetypes"],
                source_cohort_sha256=d._runtime_state._fingerprint([
                    (r["id"], r["capability"], r["gold"], r["tokens"])
                    for r in s.probe_rows if r["capability"] in s.pair]),
                fragile_replay=replay, plasticity_escape=s.plasticity_escape)
        s.outcome["qualification_stage"] = s.stage
        d._learning_retention_canary.require_confirmed_reject(
            s.retention_canary_probe, stage=s.stage, outcome=s.outcome)
        from bilqis_mlx.learning.matrix_strain import observe as observe_matrix_strain
        with d._runtime_timing_trace.trace_span("MATRIX_STRAIN", capability=s.cap):
            s.outcome["matrix_strain"] = observe_matrix_strain(
                s.mx, s.run_dir, s.receipt, s.parent_parameters, s.params)
        s.outcome["unsampled_admitted_capabilities"] = (
            len(set(d._curriculum_scheduler.assessment_capabilities(
                d._runtime_release_adoption._schedule_for_receipt(
                    s.run_dir, s.receipt, s.course), s.school)) | {s.cap}) - len(s.pair))
        with d._runtime_timing_trace.trace_span(
                "RETENTION_APPLY_DECISION", capability=s.cap, decision=s.outcome["decision"]):
            s.context_credit = d._learning_learning_experiment.observe_context(
                s.teacher, capability=s.cap, phase=s.school.stage, policy_key=s.policy_key,
                decision=s.outcome, local_gain=s.candidate_gain,
                curriculum_scope=s.teacher_curriculum_scope,
                diagnostics=s.previsit_diagnostics, realized_action=s.realized_action,
                student_checkpoint_sha256=s.school.current_student.sha256)
            if s.outcome["decision"] == "PROVISIONAL":
                d._learning_learning_experiment.commit_trial(
                    s.parent_parameters, s.parent_optimizer, s.params, s.optimizer)
            else:
                s.parent_optimizer.learning_rate = s.original_learning_rate
                s.miss_exposures = d._teacher_exposures_after_candidate(
                    s.receipt, s.miss_exposures, decision=s.outcome["decision"])
                s.after = s.before
        s.params, s.optimizer = s.parent_parameters, s.parent_optimizer


def _reconcile_teacher(d, s):
    s.remaining_priority = s.priority
    if s.priority and (s.outcome is None or s.outcome["decision"] == "PROVISIONAL"):
        with d._runtime_timing_trace.trace_span(
                "MISS_RECONCILE", capability=s.cap, miss_count=len(s.priority)):
            guesses = d._learning_student_ops._predictions(
                s.mx, s.params, s.priority, s.receipt["config"], s.receipt["answer_ids"])
            s.remaining_priority = d._learning_teacher_feedback.reconcile_unresolved_misses(
                s.priority, s.priority, guesses)
    remaining_ids = {row["id"] for row in s.remaining_priority}
    s.resolved_priority_ids = {row["id"] for row in s.priority} - remaining_ids
    for identity in s.resolved_priority_ids:
        s.miss_exposures.pop(identity, None)
    s.all_teacher_misses = [
        row for row in s.receipt.get("teacher_misses", ()) if row["capability"] != s.cap
    ] + s.deferred_misses + s.remaining_priority
    s.all_teacher_misses.sort(key=lambda row: (row["capability"], row["id"]))
    s.reward, s.bandit_credit, s.policy_health = d._selection_feedback(
        s.teacher, s.cap, s.teacher_curriculum_scope, s.policy, s.outcome,
        s.before, s.after, s.context_credit)
    with d._runtime_timing_trace.trace_span("TEACHER_OBSERVE", capability=s.cap):
        s.engine.observe(s.teacher, s.lesson_grade, s.policy_key, s.bandit_credit)
    d._learning_plasticity_escape.record_school_visit(
        s.teacher, retained=bool(s.outcome and s.outcome["decision"] == "PROVISIONAL"))
    expected = (s.step_before if s.outcome is not None and s.outcome["decision"] == "REJECT"
                else s.attempted_step)
    s.attempted_optimizer_updates = s.attempted_step - s.step_before
    s.retained_optimizer_updates = expected - s.step_before
    if s.attempted_optimizer_updates < 0:
        raise ValueError("HUMAN_TRAINER_ATTEMPTED_OPTIMIZER_STEP_REGRESSION")
    if s.retained_optimizer_updates < 0:
        raise ValueError("HUMAN_TRAINER_RETAINED_OPTIMIZER_STEP_REGRESSION")
    if int(s.optimizer.state["step"].item()) != expected:
        raise ValueError("LEARNING_EXPERIMENT_RETAINED_ADAMW_STEP_DRIFT")


def evaluate(d, s):
    _score_candidate(d, s)
    _decide_candidate(d, s)
    _reconcile_teacher(d, s)
