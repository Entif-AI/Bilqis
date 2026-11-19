"""Trainer-observation literal samples for CP02 compatibility tests."""
from dataclasses import fields

from bilqis_mlx.mission_control.model import AuthorityClass, CoverageState, RecordMeta
from bilqis_mlx.mission_control.contracts.trainer import (
    CandidateStepPerformance, TrainerObservation, TrainerObservationV2,
    TrainerObservationV3, TrainerObservationV4, TrainerObservationV5,
    TrainerObservationV6, TrainerObservationV7,
)
from bilqis_mlx.mission_control.contracts.trainer_evidence import (
    LearningHealthCheckpoint, LearningHealthEvidence, LearningHealthScore,
    LearningHealthWarning,
)
from .base import D1, D2, RUN


TRAINER_SAMPLES = (
    TrainerObservation(
        meta=RecordMeta('observed:sample', RUN, 120, 118, None,
                        CoverageState.PARTIAL, AuthorityClass.MEASURED),
        observation_id='sample', revision=1, process_id=1, visit_index=1,
        posture='OBSERVED', phase='PREPARING', outcome='RUNNING', connection_state='LIVE',
        capability_id=None, elapsed_ms=0, candidate_optimizer_step=None,
        candidate_step=None, candidate_horizon=None, retention_completed=None,
        retention_total=None, retention_subject=None, retention_role=None,
        cpu_seconds=None, peak_rss_bytes=None, disk_free_bytes=None,
        error_code=None, error_detail=None,
    ),
    TrainerObservationV2(
        meta=RecordMeta('observed:sample-v2', RUN, 120, 118, None,
                        CoverageState.PARTIAL, AuthorityClass.MEASURED),
        observation_id='sample-v2', revision=1, process_id=1, visit_index=1,
        posture='OBSERVED', phase='TRAINING', outcome='RUNNING',
        connection_state='LIVE', capability_id='A.IDENTITY', elapsed_ms=100,
        candidate_optimizer_step=8, candidate_step=1, candidate_horizon=2,
        retention_completed=None, retention_total=None,
        retention_subject=None, retention_role=None,
        cpu_seconds=0.1, peak_rss_bytes=4096, disk_free_bytes=100000,
        error_code=None, error_detail=None,
        candidate_step_wall_seconds=0.9,
        pre_neural_source_compile_wall_seconds=0.1,
        currentness_binding_wall_seconds=0.01,
        b11_preflight_wall_seconds=0.2,
        b11_autodiff_wall_seconds=0.4,
        optimizer_admission_wall_seconds=0.1,
        motif_staging_wall_seconds=0.0,
        evidence_capture_wall_seconds=0.01,
        candidate_terminal_step=False,
        c08_gradient_launches=1,
        c08_vectorized_microbatches=1,
        c08_materialization_barriers=1,
        c08_scalar_fallback_rows=0,
        c08_logical_batch_wall_seconds=0.6,
        c08_rows_per_gradient_launch=4.0,
        b11_provider_draw_count=16,
        b11_atlas_reload_count=0,
        logical_rows=4,
        compiled_positions=32,
        retention_wall_seconds=None,
        evidence_finalization_wall_seconds=None,
        publishing_wall_seconds=None,
    ),
    TrainerObservationV3(
        meta=RecordMeta('observed:sample-v3', RUN, 120, 118, None,
                        CoverageState.PARTIAL, AuthorityClass.MEASURED),
        observation_id='sample-v3', revision=1, process_id=1, visit_index=1,
        posture='OBSERVED', phase='TRAINING', outcome='RUNNING',
        connection_state='LIVE', capability_id='A.IDENTITY', elapsed_ms=100,
        candidate_optimizer_step=9, candidate_step=2, candidate_horizon=2,
        retention_completed=None, retention_total=None, retention_subject=None,
        retention_role=None, cpu_seconds=0.1, peak_rss_bytes=4096,
        disk_free_bytes=100000, error_code=None, error_detail=None,
        candidate_step_wall_seconds=0.5,
        pre_neural_source_compile_wall_seconds=None,
        currentness_binding_wall_seconds=None, b11_preflight_wall_seconds=None,
        b11_autodiff_wall_seconds=None, optimizer_admission_wall_seconds=None,
        motif_staging_wall_seconds=None, evidence_capture_wall_seconds=None,
        candidate_terminal_step=None, c08_gradient_launches=None,
        c08_vectorized_microbatches=None, c08_materialization_barriers=None,
        c08_scalar_fallback_rows=None, c08_logical_batch_wall_seconds=None,
        c08_rows_per_gradient_launch=None, b11_provider_draw_count=None,
        b11_atlas_reload_count=None, logical_rows=None, compiled_positions=None,
        retention_wall_seconds=None, evidence_finalization_wall_seconds=None,
        publishing_wall_seconds=None,
        candidate_steps=(CandidateStepPerformance(
            candidate_step=1, candidate_optimizer_step=8,
            candidate_step_wall_seconds=0.9,
            pre_neural_source_compile_wall_seconds=0.1,
            currentness_binding_wall_seconds=0.01, b11_preflight_wall_seconds=0.2,
            b11_autodiff_wall_seconds=0.4, optimizer_admission_wall_seconds=0.1,
            motif_staging_wall_seconds=0.0, evidence_capture_wall_seconds=0.01,
            candidate_terminal_step=False, c08_gradient_launches=1,
            c08_vectorized_microbatches=1, c08_materialization_barriers=1,
            c08_scalar_fallback_rows=0, c08_logical_batch_wall_seconds=0.6,
            c08_rows_per_gradient_launch=4.0, b11_provider_draw_count=16,
            b11_atlas_reload_count=0, logical_rows=4, compiled_positions=32),),
    ),

)

TRAINER_SAMPLES += (
    TrainerObservationV4(
        meta=RecordMeta('observed:sample-v4', RUN, 120, 118, None,
                        CoverageState.PARTIAL, AuthorityClass.MEASURED),
        **{field.name: getattr(TRAINER_SAMPLES[-1], field.name)
           for field in fields(TrainerObservationV3)
           if field.name != 'meta'},
        planning_wall_seconds=0.12,
        source_materialization_wall_seconds=0.03,
        target_evaluation_wall_seconds=0.2,
        protected_retention_wall_seconds=0.4,
        broad_certification_wall_seconds=None,
        visit_evidence=None, generated_grade_evidence=None,
        retention_stage_timings=(),
    ),
)

TRAINER_SAMPLES += (
    TrainerObservationV5(
        meta=RecordMeta('observed:sample-v5', RUN, 120, 118, None,
                        CoverageState.PARTIAL, AuthorityClass.MEASURED),
        **{field.name: getattr(TRAINER_SAMPLES[-1], field.name)
           for field in fields(TrainerObservationV4)
           if field.name != 'meta'},
        learning_health=LearningHealthEvidence(
            capability_id='future:capability', grade_id='future:grade',
            grade_definition_id='future:definition',
            grade_definition_version='v1', epoch_sha256=D1,
            state='MEASURED', history_state='VALID', history_error=None,
            first=LearningHealthScore(3, 5),
            latest=LearningHealthScore(4, 5),
            best=LearningHealthScore(4, 5),
            comparable_points=2,
            recent_checkpoints=(LearningHealthCheckpoint(D2, 9, 4, 5),),
            gain_from_first=1, regressed_from_first=False,
            distance_to_mastery_state='NOT_MEASURED',
            distance_to_mastery=None, fixed_screen_errors=1,
            qualification_state='NOT_MEASURED',
            protected_regression_state='NOT_MEASURED',
            regressed_protected_capabilities=(),
            prior_certified_surface_ids=(),
            certified_surface_regression_state='NOT_MEASURED',
            warnings=tuple(LearningHealthWarning(
                signal, 'NOT_MEASURED', 'Fixture evidence unavailable', 0)
                for signal in (
                    'REPETITIVE_ANSWERS', 'CHANCE_LEVEL_OR_LAGGING',
                    'LACK_OF_DURABLE_GAIN', 'DISCONNECTED_PREREQUISITES',
                    'EXCESSIVE_INTRODUCTORY_COMPLEXITY')),
        ),
    ),
)


TRAINER_SAMPLES += (
    TrainerObservationV6(
        meta=RecordMeta('observed:sample-v6', RUN, 120, 118, None,
                        CoverageState.PARTIAL, AuthorityClass.MEASURED),
        **{field.name: getattr(TRAINER_SAMPLES[-1], field.name)
           for field in fields(TrainerObservationV5)
           if field.name not in {'meta', 'candidate_steps'}},
        accepted_currentness_refresh_wall_seconds=0.01,
        accepted_currentness_live_fence_wall_seconds=0.01,
        accepted_parent_currentness_wall_seconds=0.01,
        lawful_frontier_currentness_wall_seconds=0.02,
        teacher_visit_currentness_wall_seconds=0.01,
        source_currentness_wall_seconds=0.01,
        candidate_binding_wall_seconds=0.01,
        retention_target_prepare_wall_seconds=None,
        retention_target_solver_wall_seconds=None,
        retention_target_parent_wall_seconds=None,
        retention_target_candidate_wall_seconds=None,
        retention_protected_prepare_wall_seconds=None,
        retention_protected_parent_solver_wall_seconds=None,
        retention_protected_parent_wall_seconds=None,
        retention_protected_candidate_solver_wall_seconds=None,
        retention_protected_candidate_wall_seconds=None,
        retention_decision_finalize_wall_seconds=None,
        championship_wall_seconds=None,
        championship_prepare_wall_seconds=None,
        championship_solver_wall_seconds=None,
        championship_candidate_wall_seconds=None,
        adviser_wall_seconds=None,
        retention_target_case_count=None,
        retention_protected_case_count=None,
        retention_parent_cache_reused=None,
        retention_target_shared_backbone_launches=None,
        retention_target_scalar_neural_launches=None,
        retention_protected_shared_backbone_launches=None,
        retention_protected_scalar_neural_launches=None,
        championship_case_count=None,
        championship_shared_backbone_launches=None,
        championship_scalar_neural_launches=None,
        candidate_steps=(),
    ),
)


TRAINER_SAMPLES += (
    TrainerObservationV7(
        meta=RecordMeta('observed:sample-v7', RUN, 120, 118, None,
                        CoverageState.PARTIAL, AuthorityClass.MEASURED),
        **{field.name: getattr(TRAINER_SAMPLES[-1], field.name)
           for field in fields(TrainerObservationV6)
           if field.name != 'meta'},
        activity='planner: compiling semantic curriculum',
        activity_elapsed_ms=4200,
    ),
)
