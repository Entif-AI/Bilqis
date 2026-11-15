"""Source-owned B11 forward execution and typed readout composition."""
from __future__ import annotations

from dataclasses import replace

import mlx.core as mx

from bilqis_mlx.learning.atlas_engram_reads.source_owner import _B13_EXECUTION_SEAL
from bilqis_mlx.learning.atlas_readout import (
    AnswerPlan, DecoderMemory, ExecutionMode, ModelOutput,
    ReadoutSemantics, predict_typed,
)
from bilqis_mlx.learning.frame_embeddings import semantic_bank_views
from bilqis_mlx.learning.source_atoms.backbone import (
    finalize_source_backbone_hidden,
    start_retained_source_backbone_producer,
    start_source_backbone_producer,
)
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    CandidateExecutionCache, bind_motif_artifact_owner,
    require_accepted_execution_cache, require_candidate_execution_cache,
)
from bilqis_mlx.runtime.model_topology_v2 import (
    ModelTopologySpecV2, validate_bamf_parameters,
)
from bilqis_mlx.semantics.context_eligibility import ApprovedContextProjection

from .atlas_model_backend import Backend, model_backend
from .atlas_model_contracts import (
    BamfCompiledBatch, _FORWARD_ISSUANCE, _invalid,
)
from .atlas_model_participation import _active_banks, _forward_participation
from .atlas_model_refinement import _prediction_local_refinement


def _source_producer(params, compiled_batch, generation, cache):
    speculative = type(cache) is CandidateExecutionCache
    execution_cache = (
        require_candidate_execution_cache(cache) if speculative
        else (None if cache is None else require_accepted_execution_cache(cache)))
    accepted_cache = (
        execution_cache._accepted_cache if speculative else execution_cache)
    banks = semantic_bank_views(
        params, compiled_batch.compiled.extents,
        compiled_batch.compiled.features.semantic_release,
        compiled_batch.active_semantic_rows.active_indices)
    if accepted_cache is None:
        return start_source_backbone_producer(
            compiled_batch.compiled,
            params,
            compiled_batch.sources,
            compiled_batch.feature_schema,
            banks,
            compiled_batch.atlas_feature_artifact_owner,
        ), None, True
    if (
        accepted_cache.run_id != compiled_batch.active_semantic_rows.run_id
        or accepted_cache.generation != compiled_batch.active_semantic_rows.generation
        or execution_cache.generation_binding != generation
        or accepted_cache.motif_manifest.digest
        != compiled_batch.compiled.extents.motif_key_map_digest
    ):
        _invalid("B11_ACCEPTED_CACHE_GENERATION_MISMATCH")
    bind_motif_artifact_owner(accepted_cache, compiled_batch.compiled)
    producer = start_retained_source_backbone_producer(
        compiled_batch.compiled,
        params,
        compiled_batch.sources,
        compiled_batch.feature_schema,
        banks,
        accepted_cache.motif_manifest,
        compiled_batch.atlas_feature_artifact_owner,
        seal=_B13_EXECUTION_SEAL,
    )
    # Speculative execution still carries accepted-generation provenance for
    # motif dependency accounting, but it must never write derived attention
    # caches into accepted-generation custody.
    return producer, accepted_cache, not speculative


def _finalize_source_hidden(
    producer, accepted_cache, compiled_batch, *, capture_derived_cache: bool,
):
    hidden = finalize_source_backbone_hidden(producer)
    if (capture_derived_cache and accepted_cache is not None
            and accepted_cache._run_dir is not None):
        from bilqis_mlx.runtime.atlas_cache_runtime import (
            _capture_forward_attention_caches,
        )
        _capture_forward_attention_caches(
            accepted_cache, compiled_batch, producer)
    return hidden


def _decode_bamf_producer_row(
    backend: Backend,
    params,
    compiled_batch: BamfCompiledBatch,
    answer_plan: AnswerPlan,
    producer,
    final_hidden,
    row_index: int,
    accepted_cache=None,
) -> ModelOutput:
    """Decode one task-owned row from a B11 source producer and issue its provenance."""
    expected_hidden_rank = 3
    if (
        type(compiled_batch) is not BamfCompiledBatch
        or type(answer_plan) is not AnswerPlan
        or type(backend) is not Backend
        or type(row_index) is not int
        or row_index < 0
        or not isinstance(final_hidden, mx.array)
        or final_hidden.ndim != expected_hidden_rank
        or row_index >= final_hidden.shape[0]
    ):
        _invalid("B11_FORWARD_ROW_INPUT_INVALID")
    compiled_batch.__post_init__()
    answer_plan.__post_init__()
    backend.__post_init__()
    spec = backend.topology
    extents = compiled_batch.compiled.extents
    validate_bamf_parameters(spec, extents, params)
    generation = execution_generation_digest(params, spec=spec, extents=extents)
    if (
        answer_plan.generation_binding != generation
        or getattr(producer, "_generation", None) != generation
        or getattr(producer, "_compiled", None) is None
        or producer._compiled.features != compiled_batch.compiled.features
        or producer._compiled.extents != extents
        or row_index >= len(producer._compiled.compiled.rows)
        or producer._compiled.compiled.rows[row_index]
        != compiled_batch.compiled.compiled.rows[0]
        or getattr(producer, "_sources", None) is None
        or row_index >= len(producer._sources)
        or producer._sources[row_index] != compiled_batch.sources[0]
        or getattr(producer, "_feature_schema", None) != compiled_batch.feature_schema
        or producer._compiled.compiler_configs[row_index]
        != compiled_batch.compiled.compiler_configs[0]
        or producer._compiled._projections[row_index]
        != compiled_batch.compiled._projections[0]
    ):
        _invalid("B11_FORWARD_ROW_CUSTODY_MISMATCH")
    authority = compiled_batch.task_authority
    if authority is not None:
        from bilqis_mlx.runtime.refinement_request import refinement_request_disposition
        from bilqis_mlx.runtime.task_goal_readout import task_goal_route_decisions

        authority.__post_init__()
        route = task_goal_route_decisions(authority.goal)
        expected_refinement = refinement_request_disposition(authority.goal)
        if (answer_plan.refinement_request != expected_refinement
                or (answer_plan.route_only and answer_plan.decisions != route)
                or (not answer_plan.route_only
                    and answer_plan.decisions[:len(route)] != route)):
            _invalid("B11_FORWARD_TASK_PLAN_CUSTODY_MISMATCH")
    if (compiled_batch.training_authority is not None
            and compiled_batch.training_authority.generation_binding != generation):
        _invalid("B11_TRAINING_AUTHORITY_GENERATION_MISMATCH")

    row = compiled_batch.compiled.compiled.rows[0]
    row_hidden = final_hidden[row_index, :len(row.positions)]
    if row_hidden.shape != (len(row.positions), spec.width):
        _invalid("B11_HIDDEN_POSITION_MISMATCH")
    projection = compiled_batch.compiled._projections[0]
    if (
        projection is not None
        and type(projection) is not ApprovedContextProjection
    ):
        _invalid("B11_APPROVED_CONTEXT_REQUIRED")
    salience_hidden = row_hidden[-1]
    semantics = ReadoutSemantics(
        compiled_batch.compiled.features,
        _active_banks(params, compiled_batch, answer_plan),
        extents,
    )
    row_hidden, refinement_roles, refinement_executed = _prediction_local_refinement(
        params, compiled_batch, answer_plan, generation, producer, row_hidden, semantics,
        training=False, producer_row_index=row_index)
    memory = DecoderMemory(
        row_hidden,
        tuple(item.cache_identity for item in row.positions),
        row,
        generation,
    )
    output = predict_typed(
        memory, projection, answer_plan, semantics, params)
    if type(output) is not ModelOutput or output.execution_mode is not ExecutionMode.INFERENCE:
        _invalid("B11_TYPED_OUTPUT_INVALID")
    return _FORWARD_ISSUANCE.issue(
        output, replace(_forward_participation(
            params, compiled_batch, answer_plan, output, producer, accepted_cache,
            refinement_roles, refinement_executed),
            salience_hidden=salience_hidden, salience_parameters=params,
            compiled_batch=compiled_batch))


def _forward_bamf_impl(
    backend: Backend,
    params,
    compiled_batch: BamfCompiledBatch,
    answer_plan: AnswerPlan,
    mode: ExecutionMode,
    cache,
    *,
    refinement_training: bool = False,
) -> ModelOutput:
    """Run the source-backed BAMF forward and typed decoder once."""
    if (
        type(compiled_batch) is not BamfCompiledBatch
        or type(answer_plan) is not AnswerPlan
        or mode is not ExecutionMode.INFERENCE
    ):
        _invalid("B11_FORWARD_INPUT_INVALID")
    compiled_batch.__post_init__()
    answer_plan.__post_init__()
    backend.__post_init__()
    spec = backend.topology
    extents = compiled_batch.compiled.extents
    validate_bamf_parameters(spec, extents, params)
    generation = execution_generation_digest(
        params, spec=spec, extents=extents)
    if answer_plan.generation_binding != generation:
        _invalid("B11_GENERATION_BINDING_MISMATCH")
    if (compiled_batch.training_authority is not None
            and compiled_batch.training_authority.generation_binding != generation):
        _invalid("B11_TRAINING_AUTHORITY_GENERATION_MISMATCH")

    producer, accepted_cache, capture_derived_cache = _source_producer(
        params, compiled_batch, generation, cache)
    hidden = _finalize_source_hidden(
        producer, accepted_cache, compiled_batch,
        capture_derived_cache=capture_derived_cache and not refinement_training)
    if hidden.shape[0] != 1:
        _invalid("B11_SINGLE_ROW_FORWARD_REQUIRED")
    if refinement_training:
        row = compiled_batch.compiled.compiled.rows[0]
        projection = compiled_batch.compiled._projections[0]
        if projection is not None and type(projection) is not ApprovedContextProjection:
            _invalid("B11_APPROVED_CONTEXT_REQUIRED")
        row_hidden = hidden[0]
        salience_hidden = row_hidden[-1]
        semantics = ReadoutSemantics(
            compiled_batch.compiled.features,
            _active_banks(params, compiled_batch, answer_plan),
            extents,
        )
        row_hidden, refinement_roles, refinement_executed = _prediction_local_refinement(
            params, compiled_batch, answer_plan, generation, producer, row_hidden, semantics,
            training=True)
        memory = DecoderMemory(
            row_hidden, tuple(item.cache_identity for item in row.positions), row, generation)
        output = predict_typed(memory, projection, answer_plan, semantics, params)
        if type(output) is not ModelOutput or output.execution_mode is not mode:
            _invalid("B11_TYPED_OUTPUT_INVALID")
        return _FORWARD_ISSUANCE.issue(
            output, replace(_forward_participation(
                params, compiled_batch, answer_plan, output, producer, accepted_cache,
                refinement_roles, refinement_executed),
                salience_hidden=salience_hidden, salience_parameters=params,
                compiled_batch=compiled_batch))
    return _decode_bamf_producer_row(
        backend, params, compiled_batch, answer_plan, producer, hidden, 0, accepted_cache)


def forward_bamf(
    params,
    compiled_batch: BamfCompiledBatch,
    answer_plan: AnswerPlan,
    mode: ExecutionMode,
    cache,
) -> ModelOutput:
    """Public inference entrypoint through the single BAMF backend selector."""
    return model_backend(ModelTopologySpecV2()).forward(
        params, compiled_batch, answer_plan, mode, cache)


__all__ = ("forward_bamf",)
