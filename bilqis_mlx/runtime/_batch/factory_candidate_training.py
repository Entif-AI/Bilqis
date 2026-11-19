"""Production C02 composition for one source-qualified BAMF candidate step."""
from __future__ import annotations

import time

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.atlas_resources import MemoryBudget
from bilqis_mlx.runtime.bamf_bundle import (
    AuthenticatedGenerationFeatureContext, CompleteStudent,
)

from .atlas_visit_provenance import BamfVisitProvenance
from .candidate.step import (
    _candidate_cache_and_generation, _execute_prepared_candidate,
    _realized_candidate_cost,
)
from .factory_candidate_components import (
    FactoryCandidateDiagnostics, FactoryCandidateStep, FactoryDeliveryObservation,
    _frame_stats, _invalid, _reporting_diagnostics, _resource_plan,
)
from .factory_training_bridge import prepare_factory_training_batch


def _prepare_candidate_step_inputs(
        run_dir, source_context, parent, atlas_artifact_path, feature_artifact_path,
        delivered_rows, capability, delivery, requested_count, source_seed,
        source_each, optimizer_step_seed, visit_provenance, teacher_strategy,
        rehearsal_by_id, rehearsal_bindings, rehearsal_authorities,
        salience_provider, candidate, currentness_transaction,
        candidate_step_started_at, currentness_binding_wall_seconds,
        upstream_pre_neural_source_compile_wall_seconds, semantic_context,
        prepared_source):
    start = time.perf_counter()
    if candidate_step_started_at is None:
        candidate_step_started_at = start
    binding_started = time.perf_counter()
    cache, generation = _candidate_cache_and_generation(
        run_dir, source_context, parent, candidate, currentness_transaction)
    stage_metrics = {
        "candidate_step_started_at": candidate_step_started_at,
        "currentness_binding_wall_seconds": (
            float(currentness_binding_wall_seconds)
            + time.perf_counter() - binding_started),
    }
    semantic_context_materialized_in_step = semantic_context is None
    pre_neural_started = time.perf_counter()
    prepared = prepare_factory_training_batch(
        source_context, parent, atlas_artifact_path, feature_artifact_path,
        delivered_rows, generation, capability=capability, delivery=delivery,
        requested_count=requested_count, source_seed=source_seed,
        source_each=source_each, optimizer_step_seed=optimizer_step_seed,
        visit_provenance=visit_provenance, teacher_strategy=teacher_strategy,
        rehearsal_by_id=rehearsal_by_id,
        rehearsal_bindings=rehearsal_bindings,
        rehearsal_authorities=rehearsal_authorities,
        semantic_context=semantic_context,
        prepared_source=prepared_source)
    supervision = None
    if salience_provider is not None:
        from bilqis_mlx.runtime.salience_training import prepare_salience_training
        if not callable(salience_provider):
            _invalid("BAMF_SALIENCE_PROVIDER_REQUIRED")
        prepared, supervision = prepare_salience_training(
            prepared, source_context, salience_provider(prepared))
    stage_metrics["pre_neural_source_compile_wall_seconds"] = (
        float(upstream_pre_neural_source_compile_wall_seconds)
        + time.perf_counter() - pre_neural_started)
    return (
        start, cache, generation, stage_metrics, prepared, supervision,
        semantic_context_materialized_in_step,
    )


def _require_mentor_supervision_current(
        mentor_supervision, observation, parent, cache, teacher_strategy,
        source_seed):
    if mentor_supervision is None:
        if (observation.mentors is not None
                or (isinstance(observation.guidance, dict)
                    and observation.guidance.get("schema")
                    == "bilqis.mlx.championship-guidance/v1")):
            _invalid("FACTORY_MENTOR_EVIDENCE_WITHOUT_SUPERVISION")
        return
    from bilqis_mlx.learning._championship.adviser_supervision import (
        MentorSupervision, mentor_policy_binding,
    )
    from bilqis_mlx.learning._championship.cohort_soup import POLICY_ID
    from bilqis_mlx.semantics.domains import contract_digest
    if type(mentor_supervision) is not MentorSupervision:
        _invalid("FACTORY_MENTOR_SUPERVISION_INVALID")
    championship_state = getattr(parent, "championship_state", None)
    if not isinstance(championship_state, dict):
        _invalid("FACTORY_MENTOR_CHAMPIONSHIP_STATE_REQUIRED")
    try:
        mentor_supervision.require_current(
            cache.accepted_manifest_sha256,
            contract_digest(championship_state["identity"]),
            POLICY_ID,
            mentor_policy_binding(POLICY_ID, teacher_strategy),
            source_seed,
        )
        mentor_supervision.require_evidence(
            observation.mentors, observation.guidance)
    except BilqisError:
        _invalid("FACTORY_MENTOR_SUPERVISION_CURRENTNESS_DRIFT")


def execute_factory_candidate_step(
    run_dir: Path,
    source_context,
    parent: CompleteStudent,
    atlas_artifact_path: str,
    feature_artifact_path: str,
    delivered_rows,
    *,
    capability: str,
    delivery,
    requested_count: int,
    source_seed: int,
    source_each: int,
    optimizer_step_seed: int,
    visit_provenance: BamfVisitProvenance,
    teacher_strategy: dict,
    teacher_hparams,
    max_norm: float,
    observation: FactoryDeliveryObservation,
    rehearsal_by_id: dict | None = None,
    rehearsal_bindings: dict | None = None,
    rehearsal_authorities: dict | None = None,
    memory_budget: MemoryBudget | None = None,
    capture_diagnostics: bool = False,
    salience_provider=None,
    mentor_supervision=None,
    candidate=None,
    finalize_candidate: bool = True,
    currentness_transaction=None,
    candidate_step_started_at: float | None = None,
    currentness_binding_wall_seconds: float = 0.0,
    upstream_pre_neural_source_compile_wall_seconds: float = 0.0,
    semantic_context=None,
    prepared_source=None,
    distributed_profile=None,
    distributed_executor=None,
) -> FactoryCandidateStep:
    """Compose C02→C08→B10/B11→candidate custody without publishing state.

    C08 plans the complete delivered batch, vectorizes compatible planned groups,
    preserves row-scoped B11 loss/authority evidence, accumulates group gradients
    with plan weights, and enters B12 exactly once per logical teacher step.
    """
    if (not isinstance(parent, CompleteStudent)
            or not isinstance(observation, FactoryDeliveryObservation)
            or type(capture_diagnostics) is not bool
            or type(finalize_candidate) is not bool):
        _invalid("FACTORY_CANDIDATE_STEP_INPUT_INVALID")
    observed_mentor_supervision = observation._mentor_supervision
    if mentor_supervision is None:
        mentor_supervision = observed_mentor_supervision
    elif (observed_mentor_supervision is not None
          and mentor_supervision is not observed_mentor_supervision):
        _invalid("FACTORY_MENTOR_SUPERVISION_BINDING_DRIFT")
    (
        start, cache, generation, stage_metrics, prepared, supervision,
        semantic_context_materialized_in_step,
    ) = _prepare_candidate_step_inputs(
        run_dir, source_context, parent, atlas_artifact_path, feature_artifact_path,
        delivered_rows, capability, delivery, requested_count, source_seed,
        source_each, optimizer_step_seed, visit_provenance, teacher_strategy,
        rehearsal_by_id, rehearsal_bindings, rehearsal_authorities,
        salience_provider, candidate, currentness_transaction,
        candidate_step_started_at, currentness_binding_wall_seconds,
        upstream_pre_neural_source_compile_wall_seconds, semantic_context,
        prepared_source)
    _require_mentor_supervision_current(
        mentor_supervision, observation, parent, cache, teacher_strategy,
        source_seed)
    return _execute_prepared_candidate(
        run_dir, source_context, parent, atlas_artifact_path, delivered_rows,
        capability=capability, teacher_hparams=teacher_hparams,
        max_norm=max_norm, observation=observation, memory_budget=memory_budget,
        cache=cache, generation=generation, prepared=prepared, start=start,
        capture_diagnostics=capture_diagnostics,
        salience_supervision=supervision, mentor_supervision=mentor_supervision,
        candidate=candidate,
        currentness_transaction=currentness_transaction,
        finalize_candidate=finalize_candidate, semantic_context=semantic_context,
        semantic_context_materialized_in_step=semantic_context_materialized_in_step,
        stage_metrics=stage_metrics, distributed_profile=distributed_profile,
        distributed_executor=distributed_executor)


__all__ = (
    "FactoryCandidateDiagnostics", "FactoryCandidateStep",
    "FactoryDeliveryObservation",
    "execute_factory_candidate_step",
)
