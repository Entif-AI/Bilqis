"""Commit visit evidence and construct the next provisional runtime state."""
from __future__ import annotations


def _advance_school_and_describe(d, s):
    s.school = d._curriculum_scheduler.visit(
        d._runtime_release_adoption._schedule_for_receipt(s.run_dir, s.receipt, s.course),
        s.school, s.cap, s.school.current_student,
        retention_frontier=d._mature_debt.retained_frontier(s.outcome))
    methodology = d._diagnostics_teaching.summarize_teaching_visit(
        s.executable_release.curriculum, s.cap, tuple(s.methodology_steps),
        introductory=s.introduction_pass, unmeasured_reason=s.methodology_unavailable)
    teacher_decision = d._learning_teacher_feedback.summarize_teacher_decision(
        d._learning_teacher_feedback.TeacherDecisionInput(
            capability=s.cap, policy_key=s.policy_key, warnings=s.warnings,
            unresolved_miss_count=len(s.priority),
            champion_candidate_count=len(s.champion_candidate_ids),
            prerequisite_capabilities=(
                s.executable_release.execution_plan.capability_map[s.cap].prerequisites),
            methodology=methodology,
            delivered_examples=s.attempted_candidate_steps * s.batch_size,
            replayed_misses=s.replayed_misses,
            resolved_exam_misses=len(s.resolved_priority_ids),
            champion_prioritized=s.champion_prioritized,
            seed=d._runtime_state._seed(s.receipt, capability=s.cap),
            diagnostic_context_consumed=s.policy_selection["diagnostic_context_consumed"],
            diagnostic_context_key=s.policy_selection["diagnostic_context_key"]))
    lesson_generator, lesson_source_digest = d._runtime_assessment.released_lesson_source_identity(
        s.executable_release, s.cap)
    return methodology, teacher_decision, lesson_generator, lesson_source_digest


def _base_event(d, s, methodology, teacher_decision, lesson_generator, lesson_source_digest):
    event = {
        "event": "SCHOOL_TEACHER_VISIT_COMMITTED", "grade": s.lesson_grade,
        "active_grade": s.school.grade, "generation": s.receipt["generation"] + 1,
        "capability": s.cap, "teacher_policy": s.policy_key, "strategy": s.policy,
        "loss": s.last_loss, "gradient_norm": s.last_norm,
        "source_training_accuracy_before": s.before, "source_training_accuracy_after": s.after,
        "teacher_reward": s.reward, "teacher_selection_reward": s.bandit_credit,
        **d._teacher_event_fields(s.policy_selection, s.policy_health),
        "attempted_optimizer_updates": s.attempted_optimizer_updates,
        "candidate_step_control": {
            "configured_steps": s.steps_per_visit, "effective_steps": s.candidate_steps,
            "spent_steps": s.attempted_candidate_steps,
            "adaptive": s.candidate_steps != s.steps_per_visit,
            "retention_canary_stopped": s.retention_canary_stop},
        "source_prefetch": {
            "schema": "bilqis.mlx.source-prefetch/v1",
            "mode": "PROCESS_POOL" if s.prefetch_enabled else "SERIAL",
            "workers": s.source_prefetch_workers if s.prefetch_enabled else 0,
            "prepared_steps": s.candidate_steps if s.prefetch_enabled else 0,
            "serial_steps": 0 if s.prefetch_enabled else s.candidate_steps,
            "consumed_steps": s.attempted_candidate_steps,
            "packet_identity_verified": s.prefetch_enabled, "neural_owner": "MAIN_LANE_ONLY"},
        "generator_version": lesson_generator, "generator_code_sha256": lesson_source_digest,
        "lesson_source_sha256": s.manifest["manifest_sha256"],
        "lesson_seed": d._runtime_state._seed(s.receipt, capability=s.cap),
        "prior_exam_misses_available": len(s.priority),
        "prior_exam_misses_deferred_by_scope": len(s.deferred_misses),
        "prior_exam_misses_remaining": len(s.remaining_priority),
        "prior_grade_champion_votes": {
            grade: votes for grade, votes in s.direct_capability_votes.items() if grade != s.lesson_grade},
        "champion_directed_examples_available": len(s.champion_candidate_ids),
        "champion_confidence": {
            "policy": d._learning_champion_confidence.POLICY,
            "frozen_unique_champions": len(s.confidence_champions),
            "direct_capability_votes": dict(sorted(s.direct_capability_votes.items())),
            "direct_capabilities": sorted(s.direct_capabilities),
            "frozen_grade_soups": list(s.soup_vote_receipts),
            "teacher_distill": float(s.policy.get("distill", 0.0)),
            "examples_with_gold_agreeing_advice": s.confidence_examples,
            "total_per_row_influence": round(s.confidence_total_weight, 8),
            "guided_optimizer_steps": s.confidence_applied_steps},
        "lesson_methodology": methodology, "teacher_decision": teacher_decision,
        "optimizer_step": int(s.optimizer.state["step"].item()), "next_phase": s.school.stage,
        "checkpoint_status": "PROVISIONAL_UNTIL_NEXT_RECOVERY_BOUNDARY",
        "unavailable_teacher_dimensions": (
            (["old"] if not any(r["eligible_prior_capabilities"] for r in s.policy_control_receipts) else []) +
            ["preview"] + ([] if s.confidence_applied_steps else ["distill"])),
    }
    return event


def _add_optional_event_sections(s, event):
    if s.realized_action is not None:
        event["realized_teacher_action"] = s.realized_action
    if s.boolean_association_bridge:
        options = s.executable_release.execution_plan.capability_map[s.cap].teaching_option_ids
        event["teaching_enrichment"] = {
            "enabled": True, "active_for_visit": len(options) > 1,
            "option_ids": list(options[1:]), "delivered_examples": s.enrichment_examples,
            "exam_rubric_changed": False}
    if s.policy_control_receipts:
        controls = {
            "optimizer_batches_observed": len(s.policy_control_receipts),
            "old_grade_examples_delivered": sum(
                r["effective_old_grade_examples"] for r in s.policy_control_receipts),
            "last_batch_controls": s.policy_control_receipts[-1]}
        event["lesson_policy_controls"] = controls
        if any(kind != "binary" for r in s.policy_control_receipts
               for kind in r["selected_answer_kinds"]):
            event["typed_policy_controls"] = dict(controls)
    if s.outcome is not None:
        event.update({
            "candidate_retention": s.outcome, "context_teacher_credit": s.context_credit,
            "candidate_source_training_gain": s.candidate_gain,
            "candidate_attempt_optimizer_step": s.attempted_step,
            "retained_optimizer_updates": s.retained_optimizer_updates})


def _add_autonomy(d, s, event):
    if s.autonomy_teaching_option is not None and s.delivered_autonomy_rows:
        from bilqis_mlx.factory.teaching import describe_delivered_teaching
        delivery = describe_delivered_teaching(
            s.executable_release, s.cap, s.autonomy_teaching_option, s.delivered_autonomy_rows)
        teaching_file = "autonomy/teaching/" + delivery.specimen_content_sha256 + ".json"
        d._runtime_state._durable_json(s.run_dir / teaching_file, {"rows": s.delivered_autonomy_rows})
        event["autonomy_teaching"] = {**d._dataclasses.asdict(delivery), "specimen_file": teaching_file}


def _finish_capture(d, s, event):
    shadow_review = shadow_activation = None
    if (s.learning_settings is not None and s.outcome is not None
            and s.attempted_candidate_steps == s.candidate_steps):
        shadow_review = d._learning_teacher_multifidelity.evaluate_shadow(
            d._learning_teacher_multifidelity.DEFAULT_SHADOW_POLICY, probes=s.shadow_probes,
            final_retained=s.outcome["decision"] == "PROVISIONAL",
            full_budget_steps=s.candidate_steps)
        shadow_activation = d._learning_teacher_multifidelity.record_review(s.teacher, shadow_review)
        event["teacher_multifidelity_shadow"] = shadow_review
        event["teacher_multifidelity_activation"] = shadow_activation
    if s.learning_settings is not None and s.retention_canary_probe is not None:
        event["retention_canary"] = d._learning_retention_canary.complete(
            s.teacher, s.retention_canary_probe,
            final_retained=s.outcome["decision"] == "PROVISIONAL",
            spent_steps=s.attempted_candidate_steps,
            full_budget_steps=s.candidate_steps)
    s.capture.finish(
        event, decision=s.outcome, paired=s.pair if s.learning_settings is not None else None,
        protected=s.probed if s.learning_settings is not None else None,
        stage=s.stage if s.learning_settings is not None else "UNPROTECTED_VISIT",
        attempted=s.attempted_optimizer_updates, retained=s.retained_optimizer_updates,
        shadow_review=shadow_review, shadow_activation=shadow_activation)
    stagnation = s.receipt.get("stagnation_session")
    if stagnation is not None:
        stagnation = d._learning_stagnation_control.record_visit(
            stagnation, capability=s.cap, phase=s.stage_before,
            decision=s.outcome.get("decision") if isinstance(s.outcome, dict) else None,
            retained_optimizer_updates=s.retained_optimizer_updates, generation=event["generation"])
    return stagnation


def _advance_result(d, s, event, stagnation):
    pending = list(s.receipt.get("_pending_visit_events", ()))
    pending.append(event)
    with d._runtime_timing_trace.trace_span("VISIT_ADVANCE_STATE", capability=s.cap):
        result = d._runtime_checkpoints._advance(
            s.run_dir, s.receipt, s.school, teacher=s.teacher, persist=False)
    if s.retained_optimizer_updates > 0:
        result["last_retained_update_grade"] = s.lesson_grade
    if s.learning_settings is not None:
        result["learning_experiment"] = {
            "version": d._learning_learning_experiment.VERSION,
            "settings": d._dataclasses.asdict(s.learning_settings)}
    result["teacher_misses"] = s.all_teacher_misses
    result["teacher_miss_exposures"] = s.miss_exposures
    if stagnation is not None:
        result["stagnation_session"] = stagnation
    result.pop("teacher_miss_cursor", None)
    result["_pending_visit_events"] = pending
    d._runtime_timing_trace.trace_mark(
        "VISIT_END", generation=result["generation"], capability=s.cap,
        optimizer_step=int(s.optimizer.state["step"].item()),
        decision=s.outcome.get("decision") if isinstance(s.outcome, dict) else None)
    return result


def finalize(d, s):
    methodology, decision, generator, digest = _advance_school_and_describe(d, s)
    event = _base_event(d, s, methodology, decision, generator, digest)
    _add_optional_event_sections(s, event)
    _add_autonomy(d, s, event)
    stagnation = _finish_capture(d, s, event)
    return _advance_result(d, s, event, stagnation)
