"""Source-owned B11 forward execution and typed readout composition."""
from __future__ import annotations

from dataclasses import replace

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
    row = compiled_batch.compiled.compiled.rows[0]
    projection = compiled_batch.compiled._projections[0]
    if (
        projection is not None
        and type(projection) is not ApprovedContextProjection
    ):
        _invalid("B11_APPROVED_CONTEXT_REQUIRED")
    row_hidden = hidden[0]
    salience_hidden = row_hidden[-1]
    if row_hidden.shape[0] != len(row.positions):
        _invalid("B11_HIDDEN_POSITION_MISMATCH")
    semantics = ReadoutSemantics(
        compiled_batch.compiled.features,
        _active_banks(params, compiled_batch, answer_plan),
        extents,
    )
    row_hidden, refinement_roles, refinement_executed = _prediction_local_refinement(
        params, compiled_batch, answer_plan, generation, producer, row_hidden, semantics,
        training=refinement_training)
    memory = DecoderMemory(
        row_hidden,
        tuple(item.cache_identity for item in row.positions),
        row,
        generation,
    )
    output = predict_typed(
        memory, projection, answer_plan, semantics, params)
    if type(output) is not ModelOutput or output.execution_mode is not mode:
        _invalid("B11_TYPED_OUTPUT_INVALID")
    return _FORWARD_ISSUANCE.issue(
        output, replace(_forward_participation(
            params, compiled_batch, answer_plan, output, producer, accepted_cache,
            refinement_roles, refinement_executed),
            salience_hidden=salience_hidden, salience_parameters=params, compiled_batch=compiled_batch))


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
