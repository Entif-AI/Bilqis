"""Best-effort live performance projection for the BAMF operator."""
from __future__ import annotations

from contextlib import contextmanager
import time


STEP_COST_FIELDS = (
    "candidate_step_wall_seconds",
    "pre_neural_source_compile_wall_seconds",
    "currentness_binding_wall_seconds",
    "accepted_currentness_refresh_wall_seconds",
    "accepted_currentness_live_fence_wall_seconds",
    "accepted_parent_currentness_wall_seconds",
    "lawful_frontier_currentness_wall_seconds",
    "teacher_visit_currentness_wall_seconds",
    "source_currentness_wall_seconds",
    "candidate_binding_wall_seconds",
    "b11_preflight_wall_seconds",
    "b11_autodiff_wall_seconds",
    "optimizer_admission_wall_seconds",
    "motif_staging_wall_seconds",
    "evidence_capture_wall_seconds",
    "candidate_terminal_step",
    "c08_gradient_launches",
    "c08_vectorized_microbatches",
    "c08_materialization_barriers",
    "c08_scalar_fallback_rows",
    "c08_logical_batch_wall_seconds",
    "c08_rows_per_gradient_launch",
    "b11_provider_draw_count",
    "b11_atlas_reload_count",
    "logical_rows",
    "compiled_positions",
)

VISIT_PERFORMANCE_FIELDS = (
    "planning_wall_seconds",
    "source_materialization_wall_seconds",
    "target_evaluation_wall_seconds",
    "protected_retention_wall_seconds",
    "broad_certification_wall_seconds",
    "retention_wall_seconds",
    "retention_target_prepare_wall_seconds",
    "retention_target_solver_wall_seconds",
    "retention_target_parent_wall_seconds",
    "retention_target_candidate_wall_seconds",
    "retention_protected_prepare_wall_seconds",
    "retention_protected_parent_solver_wall_seconds",
    "retention_protected_parent_wall_seconds",
    "retention_protected_candidate_solver_wall_seconds",
    "retention_protected_candidate_wall_seconds",
    "retention_decision_finalize_wall_seconds",
    "championship_wall_seconds",
    "championship_prepare_wall_seconds",
    "championship_solver_wall_seconds",
    "championship_candidate_wall_seconds",
    "adviser_wall_seconds",
    "evidence_finalization_wall_seconds",
    "publishing_wall_seconds",
)

RETENTION_PROFILE_FIELDS = (
    "retention_target_case_count",
    "retention_protected_case_count",
    "retention_parent_cache_reused",
    "retention_target_shared_backbone_launches",
    "retention_target_scalar_neural_launches",
    "retention_protected_shared_backbone_launches",
    "retention_protected_scalar_neural_launches",
    "championship_case_count",
    "championship_shared_backbone_launches",
    "championship_scalar_neural_launches",
)

PERFORMANCE_FIELDS = STEP_COST_FIELDS + VISIT_PERFORMANCE_FIELDS


def observe_completed_step(observer, step, candidate) -> None:
    """Publish only already-realized host facts; never affect execution."""
    if observer is None:
        return
    try:
        cost = getattr(step, "realized_cost", {})
        fields = {
            name: cost[name] for name in STEP_COST_FIELDS
            if isinstance(cost, dict) and name in cost
        }
        payload = dict(
            candidate_step=candidate.update_steps,
            candidate_optimizer_step=candidate.parent.optimizer_step
            + candidate.update_steps,
            **fields)
        complete_step = getattr(observer, "complete_step", None)
        if callable(complete_step):
            complete_step(**payload)
        else:
            observer.update(**payload)
    except Exception:
        pass


@contextmanager
def measure_observed_phase(observer, field: str):
    """Time an existing host boundary without adding device synchronization."""
    started = time.perf_counter()
    try:
        yield
    finally:
        if observer is not None:
            try:
                stage = getattr(observer, "stage", None)
                if callable(stage):
                    stage(**{field: time.perf_counter() - started})
                else:
                    observer.update(**{field: time.perf_counter() - started})
            except Exception:
                pass


__all__ = (
    "PERFORMANCE_FIELDS", "RETENTION_PROFILE_FIELDS", "STEP_COST_FIELDS",
    "VISIT_PERFORMANCE_FIELDS",
    "measure_observed_phase", "observe_completed_step",
)
