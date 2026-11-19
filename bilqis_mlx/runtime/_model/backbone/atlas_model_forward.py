"""Source-owned B11 forward execution and typed readout composition."""
from __future__ import annotations
from dataclasses import replace

from bilqis_mlx.learning.atlas_engram_reads.source_owner import _B13_EXECUTION_SEAL
from bilqis_mlx.learning.atlas_readout import (
    AnswerPlan, DecoderMemory, ExecutionMode, ModelOutput,
    ReadoutSemantics, predict_typed,
)
from bilqis_mlx.learning.atlas_readout.decoder.replay import predict_typed_replay
from bilqis_mlx.learning.frame_embeddings import semantic_bank_views
from bilqis_mlx.learning.source_atoms.backbone import (
    finalize_source_backbone_hidden,
    start_retained_source_backbone_producer,
    start_source_backbone_producer,
)
from bilqis_mlx.runtime.backbone_identity import (
    issue_execution_generation_binding, require_execution_generation_binding,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    CandidateExecutionCache, DistributedExecutionCache,
    bind_execution_generation, bind_motif_artifact_owner,
    require_accepted_execution_cache, require_candidate_execution_cache,
    require_distributed_execution_cache,
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
from .atlas_model_forward_validation import (
    validate_decode_row_custody, validate_decode_row_input, validate_task_plan_custody,
)


def _source_execution_authorities(compiled_batch):
    row_batches = getattr(compiled_batch, "row_batches", None)
    if row_batches is not None:
        values = tuple(
            getattr(item, "source_execution_authority", None)
            for item in row_batches)
    else:
        values = (getattr(compiled_batch, "source_execution_authority", None),)
    bound = tuple(item is not None for item in values)
    if any(bound) and not all(bound):
        _invalid("B11_SOURCE_EXECUTION_AUTHORITY_PARTIAL")
    return None if not any(bound) else values


def _source_producer(
        params, compiled_batch, generation, cache, execution_binding=None, *,
        trace=False, snapshot=None):
    candidate = type(cache) is CandidateExecutionCache
    distributed = type(cache) is DistributedExecutionCache
    speculative = candidate or distributed
    execution_cache = (
        require_candidate_execution_cache(cache) if candidate
        else (require_distributed_execution_cache(cache) if distributed
              else (None if cache is None else require_accepted_execution_cache(cache))))
    accepted_cache = execution_cache._accepted_cache if candidate else execution_cache
    banks = semantic_bank_views(
        params, compiled_batch.compiled.extents,
        compiled_batch.compiled.features.semantic_release,
        compiled_batch.active_semantic_rows.active_indices)
    source_execution_authorities = _source_execution_authorities(compiled_batch)
    if accepted_cache is None:
        return start_source_backbone_producer(
            compiled_batch.compiled,
            params,
            compiled_batch.sources,
            compiled_batch.feature_schema,
            banks,
            compiled_batch.atlas_feature_artifact_owner,
            execution_binding=execution_binding,
            trace=trace,
            snapshot=snapshot,
            source_execution_authorities=source_execution_authorities,
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
        execution_binding=execution_binding,
        trace=trace,
        snapshot=snapshot,
        source_execution_authorities=source_execution_authorities,
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
    execution_binding=None,
    *,
    refinement_training: bool = False,
    teacher_targets=None,
    trace=False,
    replay_output=None,
) -> ModelOutput:
    """Decode one task-owned row from a B11 source producer and issue its provenance."""
    validate_decode_row_input(
        backend, compiled_batch, answer_plan, final_hidden, row_index)
    spec = backend.topology
    extents = compiled_batch.compiled.extents
    validate_bamf_parameters(spec, extents, params)
    generation = require_execution_generation_binding(
        execution_binding, params, spec=spec, extents=extents).generation_digest
    validate_decode_row_custody(
        compiled_batch, answer_plan, producer, row_index, generation)
    validate_task_plan_custody(compiled_batch, answer_plan)
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
        training=refinement_training, producer_row_index=row_index)
    memory = DecoderMemory(
        row_hidden,
        tuple(item.cache_identity for item in row.positions),
        row,
        generation,
    )
    if replay_output is not None:
        replay_record = _FORWARD_ISSUANCE.require(replay_output)
        if (replay_record.compiled_batch is not compiled_batch
                or replay_record.generation_binding != generation
                or replay_output.plan != answer_plan):
            _invalid("B11_REPLAY_OUTPUT_CUSTODY_MISMATCH")
    output = (
        predict_typed_replay(
            memory, projection, answer_plan, semantics, params, replay_output)
        if replay_output is not None else predict_typed(
            memory, projection, answer_plan, semantics, params,
            teacher_targets, trace=trace))
    expected_mode = (
        ExecutionMode.INFERENCE if replay_output is not None else
        ExecutionMode.TEACHER_FORCED
        if teacher_targets is not None else ExecutionMode.INFERENCE)
    if type(output) is not ModelOutput or output.execution_mode is not expected_mode:
        _invalid("B11_TYPED_OUTPUT_INVALID")
    return _FORWARD_ISSUANCE.issue(
        output, replace(_forward_participation(
            params, compiled_batch, answer_plan, output, producer, accepted_cache,
            refinement_roles, refinement_executed,
            producer_row_index=row_index),
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
    execution_binding=None,
    teacher_targets=None,
    decoder_trace=None,
    replay_output=None,
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
    if execution_binding is not None:
        execution_binding = require_execution_generation_binding(
            execution_binding, params, spec=spec, extents=extents)
        if (cache is not None
                and cache.generation_binding != execution_binding.generation_digest):
            _invalid("B11_EXECUTION_BINDING_MISMATCH")
    elif cache is None:
        execution_binding = issue_execution_generation_binding(
            params, spec=spec, extents=extents,
            expected_generation=answer_plan.generation_binding)
    else:
        owned_binding = bind_execution_generation(
            cache, params, spec=spec, extents=extents)
        execution_binding = owned_binding
    generation = execution_binding.generation_digest
    if answer_plan.generation_binding != generation:
        _invalid("B11_GENERATION_BINDING_MISMATCH")
    if (compiled_batch.training_authority is not None
            and compiled_batch.training_authority.generation_binding != generation):
        _invalid("B11_TRAINING_AUTHORITY_GENERATION_MISMATCH")

    producer, accepted_cache, capture_derived_cache = _source_producer(
        params, compiled_batch, generation, cache, execution_binding,
        trace=refinement_training, snapshot=answer_plan.snapshot)
    hidden = _finalize_source_hidden(
        producer, accepted_cache, compiled_batch,
        capture_derived_cache=capture_derived_cache and not refinement_training)
    if hidden.shape[0] != 1:
        _invalid("B11_SINGLE_ROW_FORWARD_REQUIRED")
    return _decode_bamf_producer_row(
        backend, params, compiled_batch, answer_plan, producer, hidden, 0,
        accepted_cache, execution_binding,
        refinement_training=refinement_training,
        teacher_targets=teacher_targets,
        trace=refinement_training if decoder_trace is None else decoder_trace,
        replay_output=replay_output)


def forward_bamf(
    params,
    compiled_batch: BamfCompiledBatch,
    answer_plan: AnswerPlan,
    mode: ExecutionMode,
    cache,
    *,
    execution_binding=None,
) -> ModelOutput:
    """Public inference entrypoint through the single BAMF backend selector."""
    return model_backend(ModelTopologySpecV2()).forward(
        params, compiled_batch, answer_plan, mode, cache,
        execution_binding=execution_binding)


__all__ = ("forward_bamf",)
