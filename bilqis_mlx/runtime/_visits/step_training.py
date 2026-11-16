"""Optimizer-step loop for one teaching visit."""
from __future__ import annotations

from . import selection, step_sources


def run(d, s):
    step_sources.initialize(d, s)
    for step in range(s.candidate_steps):
        d._runtime_timing_trace.trace_mark(
            "OPTIMIZER_STEP_START", capability=s.cap, visit_step=step + 1,
            optimizer_step=int(s.optimizer.state["step"].item()))
        prepared, fresh, option_rows, preservation, support = step_sources.for_step(d, s, step)
        training_rows, training_guidance = selection.select(
            d, s, step, prepared, fresh, option_rows, preservation, support)
        with d._runtime_timing_trace.trace_span(
                "STEP_TRAIN", capability=s.cap, visit_step=step + 1,
                batch_size=len(training_rows)):
            s.last_loss, s.last_norm = d._learning_student_ops._train_step(
                s.mx, s.params, s.optimizer, training_rows, s.receipt["config"],
                s.receipt["answer_ids"], champion_guidance=training_guidance)
        rung = step + 1
        s.attempted_candidate_steps = rung
        canary_rung = (
            d._learning_retention_canary.decision_rung(
                d._learning_retention_canary.DEFAULT_POLICY, s.candidate_steps)
            if s.learning_settings is not None else None)
        if canary_rung is not None and rung == canary_rung:
            target_rows = [
                row for row in s.probe_rows if row["capability"] == s.cap]
            with d._runtime_timing_trace.trace_span(
                    "RETENTION_CANARY_TARGET", capability=s.cap, visit_step=rung,
                    row_count=len(target_rows)):
                candidate_predictions = d._learning_student_ops._predictions(
                    s.mx, s.params, target_rows, s.receipt["config"],
                    s.receipt["answer_ids"])
            s.retention_canary_probe = d._learning_retention_canary.probe(
                d._learning_retention_canary.DEFAULT_POLICY,
                rung=rung, full_budget_steps=s.candidate_steps, rows=target_rows,
                parent_predictions=s.parent_predictions,
                candidate_predictions=candidate_predictions,
                activation_state=s.retention_canary_activation)
            if s.retention_canary_probe["stop"]:
                s.retention_canary_stop = True
                d._runtime_timing_trace.trace_mark(
                    "RETENTION_CANARY_STOP", capability=s.cap, visit_step=rung,
                    target_correct_delta=s.retention_canary_probe["target_correct_delta"])
                break
        if s.shadow_rungs and rung in s.shadow_rungs and rung < s.candidate_steps:
            with d._runtime_timing_trace.trace_span(
                    "TEACHER_SHADOW_RUNG", capability=s.cap, visit_step=rung):
                rung_score = d._learning_student_ops._train_score(
                    s.mx, s.params, s.rows, s.receipt["config"], s.receipt["answer_ids"])
            s.shadow_probes.append((
                rung, d._learning_teacher_multifidelity.target_correct_delta(
                    s.before, rung_score, len(s.rows))))
        d._runtime_timing_trace.trace_mark(
            "OPTIMIZER_STEP_END", capability=s.cap, visit_step=step + 1,
            optimizer_step=int(s.optimizer.state["step"].item()))
