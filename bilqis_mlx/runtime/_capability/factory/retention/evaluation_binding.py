"""Reuse and generation binding for compiled Factory evaluation cases."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.learning.source_atoms import SourceAtomRow
from bilqis_mlx.runtime.atlas_model_contracts import (
    BamfCompiledBatch, bind_candidate_active_semantic_rows,
)
from bilqis_mlx.runtime.bamf_bundle import (
    BamfBundleCandidate, authenticate_bamf_execution_feature_context,
)
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.source_adapters.atoms.authority import canonical_graph_for

from ..capability_evaluation import _invalid
from ..factory_compiled_cohort import compiled_frame_identity_digest
from ..factory_evaluation_compiler import (
    CompiledFactoryEvaluationCase, _evaluation_context,
)
from ..factory_task_authority import (
    FactoryTaskAuthority, rebind_factory_task_authority,
)
from ..factory_task_template import factory_task_template_matches


def _source_atom_row(
    source_context: SourceExecutionContext,
    authenticated,
    row: dict,
    *,
    source_seed: int,
    source_each: int,
) -> SourceAtomRow:
    try:
        execution = source_context.execution_for(row.get("capability"))
    except Exception:
        _invalid("BAMF_C05_COMPILED_CASE_SOURCE_CAPABILITY_MISSING")
        raise AssertionError
    profile_parameters = (dict(execution.provider_parameters)
                          if execution.provider_parameters else None)
    source_graph = canonical_graph_for(
        row.get("generator"), source_context.source_root, row=row)
    return SourceAtomRow(
        authenticated.selection, row, source_graph,
        Path(source_context.source_root), source_seed, source_each,
        source_context.release.curriculum, profile_parameters)


def compiled_case_matches_contract(
    source_context: SourceExecutionContext,
    candidate: BamfBundleCandidate,
    artifact_path: str,
    compiled_case: CompiledFactoryEvaluationCase,
    row: dict,
    *,
    source_seed: int,
    source_each: int,
    authenticated=None,
    release_prevalidated: bool = False,
) -> bool:
    """Check cold-cache reuse without recompiling or invoking the C04 lowerer."""
    if type(compiled_case) is not CompiledFactoryEvaluationCase:
        _invalid("BAMF_C05_COMPILED_CASE_REQUIRED")
    compiled_case.__post_init__()
    if type(release_prevalidated) is not bool:
        _invalid("BAMF_C05_EVALUATION_PREVALIDATION_INVALID")
    if not release_prevalidated:
        source_context.release.verify()
        source_context.release.verify_semantic_catalog(source_context.graph)
    else:
        source_context.require_accepted_runtime(source_context.run_dir)
    authenticated = (authenticated if authenticated is not None else
                     authenticate_bamf_execution_feature_context(
                         candidate, artifact_path, source_context.run_dir))
    authenticated.__post_init__()
    identity = compiled_case.identity_record
    compiler_sha256 = candidate.compiler_features.get("compiler_sha256")
    expected_task, expected_frontier, expected_policy = _evaluation_context(
        authenticated.features.semantic_release,
        row.get("capability"), len(row.get("tokens", ())))
    if (identity["factory_release_sha256"] != source_context.release.release_sha256
            or identity["semantic_catalog_sha256"]
            != source_context.release.semantic_catalog_sha256
            or identity["semantic_release_sha256"]
            != authenticated.features.semantic_release
            or identity["source_artifact_sha256"]
            != contract_digest(authenticated.selection.identity)
            or identity["compiler_sha256"] != compiler_sha256
            or identity["feature_schema_sha256"]
            != contract_digest(authenticated.schema)
            or identity["evaluator_policy_sha256"] != contract_digest((
                expected_task, expected_frontier, expected_policy))):
        return False
    compiled = CompiledEncoderInput(
        compiled_case.compiled_rows, compiled_case.compiler_configs,
        authenticated.features, candidate.extents,
        source_asts=compiled_case.source_asts,
        partial_forest_receipts=compiled_case.partial_forest_receipts)
    source = _source_atom_row(
        source_context, authenticated, row,
        source_seed=source_seed, source_each=source_each)
    batch = BamfCompiledBatch(
        compiled, (source,), authenticated.schema,
        bind_candidate_active_semantic_rows(candidate, authenticated))
    batch.__post_init__()
    return factory_task_template_matches(
        source_context, batch, compiled_case.task_template)


def bind_factory_evaluation_case(
    source_context: SourceExecutionContext,
    candidate: BamfBundleCandidate,
    artifact_path: str,
    compiled_case: CompiledFactoryEvaluationCase,
    row: dict,
    *,
    generation: str,
    source_seed: int,
    source_each: int,
    authenticated=None,
    release_prevalidated: bool = False,
) -> tuple[BamfCompiledBatch, FactoryTaskAuthority]:
    """Attach one immutable compilation to exact generation execution state."""
    if type(compiled_case) is not CompiledFactoryEvaluationCase:
        _invalid("BAMF_C05_COMPILED_CASE_REQUIRED")
    compiled_case.__post_init__()
    if type(release_prevalidated) is not bool:
        _invalid("BAMF_C05_EVALUATION_PREVALIDATION_INVALID")
    if not release_prevalidated:
        source_context.release.verify()
        source_context.release.verify_semantic_catalog(source_context.graph)
    else:
        source_context.require_accepted_runtime(source_context.run_dir)
    authenticated = (authenticated if authenticated is not None else
                     authenticate_bamf_execution_feature_context(
                         candidate, artifact_path, source_context.run_dir))
    authenticated.__post_init__()
    identity = compiled_case.identity_record
    compiler_sha256 = candidate.compiler_features.get("compiler_sha256")
    if (identity["factory_release_sha256"] != source_context.release.release_sha256
            or identity["semantic_catalog_sha256"]
            != source_context.release.semantic_catalog_sha256
            or identity["semantic_release_sha256"]
            != authenticated.features.semantic_release
            or identity["source_artifact_sha256"]
            != contract_digest(authenticated.selection.identity)
            or identity["compiler_sha256"] != compiler_sha256
            or identity["feature_schema_sha256"]
            != contract_digest(authenticated.schema)):
        _invalid("BAMF_C05_COMPILED_CASE_CONTRACT_DRIFT")
    config = compiled_case.compiler_configs[0]
    if (identity["evaluator_policy_sha256"] != contract_digest((
            config.task, config.frontier, config.policy))
            or identity["compiled_frame_sha256"]
            != compiled_frame_identity_digest(compiled_case.compiled_rows)):
        _invalid("BAMF_C05_COMPILED_CASE_CONTRACT_DRIFT")
    compiled = CompiledEncoderInput(
        compiled_case.compiled_rows, compiled_case.compiler_configs,
        authenticated.features, candidate.extents,
        source_asts=compiled_case.source_asts,
        partial_forest_receipts=compiled_case.partial_forest_receipts)
    source = _source_atom_row(
        source_context, authenticated, row,
        source_seed=source_seed, source_each=source_each)
    batch = BamfCompiledBatch(
        compiled, (source,), authenticated.schema,
        bind_candidate_active_semantic_rows(candidate, authenticated))
    authority = rebind_factory_task_authority(
        source_context, batch, compiled_case.task_template,
        generation_binding=generation)
    batch = BamfCompiledBatch(
        batch.compiled, batch.sources, batch.feature_schema,
        batch.active_semantic_rows, task_authority=authority)
    source_context.register_compiled_batch(batch)
    return batch, authority


__all__ = ("bind_factory_evaluation_case", "compiled_case_matches_contract")
