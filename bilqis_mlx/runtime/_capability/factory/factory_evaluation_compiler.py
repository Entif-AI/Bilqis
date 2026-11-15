"""Compile one Factory-owned evaluation row through the accepted A01/A05 path."""
from __future__ import annotations

from dataclasses import dataclass, field
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
from bilqis_mlx.semantics.context_eligibility import (
    PUBLIC_FORMAL, ContextPolicy, SourceFrontier, TaskScope,
)
from bilqis_mlx.semantics.frame_compiler import (
    compile_prefix_rows, validate_partial_visible_forest,
)
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.source_adapters.atoms.admission import (
    authorize_public_formal_prefix, public_formal_atom_context,
)
from bilqis_mlx.source_adapters.atoms.authority import canonical_graph_for

from .capability_evaluation import _invalid
from .factory_compiled_cohort import (
    compiled_case_identity_digest, compiled_case_identity_record,
    compiled_frame_identity_digest,
)
from .factory_task_authority import (
    FactoryTaskAuthority, rebind_factory_task_authority,
)
from .factory_task_template import (
    FactoryTaskTemplate, factory_task_template, factory_task_template_matches,
)


_PRINCIPAL = "bamf-c05-evaluator"
_TENANT = "bamf-c05"
_PURPOSE = "C05_EVALUATION"
_JURISDICTION = "LOCAL"

@dataclass(frozen=True)
class CompiledFactoryEvaluationCase:
    """Gold-blind immutable source compilation reused across C05 generations."""

    compiled_rows: object = field(repr=False, compare=False)
    compiler_configs: tuple = field(repr=False, compare=False)
    source_asts: tuple = field(repr=False, compare=False)
    partial_forest_receipts: tuple = field(repr=False, compare=False)
    task_template: FactoryTaskTemplate
    identity_items: tuple[tuple[str, str], ...]
    identity_sha256: str

    @property
    def identity_record(self) -> dict:
        return compiled_case_identity_record(**dict(self.identity_items))

    def __post_init__(self) -> None:
        if (not isinstance(self.compiler_configs, tuple)
                or len(self.compiler_configs) != 1
                or not isinstance(self.source_asts, tuple)
                or len(self.source_asts) != 1
                or not isinstance(self.partial_forest_receipts, tuple)
                or len(self.partial_forest_receipts) != 1
                or type(self.task_template) is not FactoryTaskTemplate
                or type(self.identity_items) is not tuple
                or compiled_case_identity_digest(self.identity_record)
                != self.identity_sha256):
            _invalid("BAMF_C05_COMPILED_CASE_INVALID")
        self.compiled_rows.__post_init__()
        self.task_template.__post_init__()
        identity = self.identity_record
        config = self.compiler_configs[0]
        template = self.task_template
        if (identity["factory_release_sha256"] != template.release_sha256
                or identity["semantic_release_sha256"] != template.goal.semantic_release
                or identity["source_row_id"] != template.source_row_id
                or identity["source_row_sha256"] != template.source_row_sha256
                or identity["source_binding_sha256"] != template.source_binding_sha256
                or identity["lowerer_sha256"] != template.lowerer_sha256
                or identity["evaluator_policy_sha256"] != contract_digest((
                    config.task, config.frontier, config.policy))
                or identity["compiled_frame_sha256"]
                != compiled_frame_identity_digest(self.compiled_rows)
                or identity["goal_sha256"] != contract_digest(template.goal)
                or identity["source_family_id"] != template.source_family_id
                or identity["episode_id"] != template.episode_id):
            _invalid("BAMF_C05_COMPILED_CASE_IDENTITY_DRIFT")
def _evaluation_context(release: str, capability: str, prefix_end: int):
    task = TaskScope(
        _PRINCIPAL, _TENANT, _PURPOSE, release, _JURISDICTION,
        capability, 0, 0, prefix_end,
    )
    frontier = SourceFrontier(1, 1, ())
    policy = ContextPolicy(
        "bamf-c05-public-formal/v1", 1, 1,
        (_PURPOSE,), (PUBLIC_FORMAL,), (_JURISDICTION,), (capability,),
        (PUBLIC_FORMAL,), (), (),
    )
    return task, frontier, policy


def compile_factory_evaluation_batch(
    source_context: SourceExecutionContext,
    candidate: BamfBundleCandidate,
    artifact_path: str,
    row: dict,
    *,
    source_seed: int,
    source_each: int,
    _authenticated=None,
) -> BamfCompiledBatch:
    """Produce B11 input without constructing or exposing evaluator gold."""
    if (type(source_context) is not SourceExecutionContext
            or not isinstance(candidate, BamfBundleCandidate)
            or not isinstance(row, dict)
            or not isinstance(row.get("tokens"), list) or not row["tokens"]
            or not isinstance(row.get("capability"), str) or not row["capability"]
            or type(source_seed) is not int or source_seed < 0
            or type(source_each) is not int or source_each < 1
            or source_context.source_root is None):
        _invalid("BAMF_C05_EVALUATION_COMPILE_INPUT_INVALID")
    source_context.release.verify()
    source_context.release.verify_semantic_catalog(source_context.graph)
    authenticated = (_authenticated if _authenticated is not None else
                     authenticate_bamf_execution_feature_context(
                         candidate, artifact_path, source_context.run_dir))
    authenticated.__post_init__()
    execution = source_context.release.execution_plan.capability_map[
        row["capability"]]
    profile_parameters = (dict(execution.provider_parameters)
                          if execution.provider_parameters else None)
    source_graph = canonical_graph_for(
        row.get("generator"), source_context.source_root)
    task, frontier, policy = _evaluation_context(
        authenticated.features.semantic_release,
        row["capability"], len(row["tokens"]),
    )
    ast, config = public_formal_atom_context(
        authenticated.selection, row, source_graph,
        source_root=source_context.source_root,
        source_seed=source_seed, source_each=source_each,
        course=source_context.release.curriculum,
        source_profile_parameters=profile_parameters,
        task=task, frontier=frontier, policy=policy,
    )
    rows = compile_prefix_rows(
        ((ast, len(ast.atoms), config),), authenticated.features.semantic_release)
    config = authorize_public_formal_prefix(ast, rows.rows[0], config)
    receipt = validate_partial_visible_forest(rows.rows[0], ast, config)
    compiled = CompiledEncoderInput(
        rows, (config,), authenticated.features, candidate.extents,
        source_asts=(ast,), partial_forest_receipts=(receipt,))
    source = SourceAtomRow(
        authenticated.selection, row, source_graph,
        Path(source_context.source_root), source_seed, source_each,
        source_context.release.curriculum, profile_parameters)
    batch = BamfCompiledBatch(
        compiled, (source,), authenticated.schema,
        bind_candidate_active_semantic_rows(candidate, authenticated))
    batch.__post_init__()
    source_context.register_compiled_batch(batch)
    return batch

def compile_factory_evaluation_case(
    source_context: SourceExecutionContext,
    candidate: BamfBundleCandidate,
    artifact_path: str,
    row: dict,
    *,
    source_seed: int,
    source_each: int,
    authenticated=None,
) -> CompiledFactoryEvaluationCase:
    """Compile and lower one immutable evaluation case exactly once."""
    authenticated = (authenticated if authenticated is not None else
                     authenticate_bamf_execution_feature_context(
                         candidate, artifact_path, source_context.run_dir))
    authenticated.__post_init__()
    batch = compile_factory_evaluation_batch(
        source_context, candidate, artifact_path, row,
        source_seed=source_seed, source_each=source_each,
        _authenticated=authenticated)
    task_template = factory_task_template(source_context, batch)
    config = batch.compiled.compiler_configs[0]
    compiler_sha256 = candidate.compiler_features.get("compiler_sha256")
    if not isinstance(compiler_sha256, str) or not compiler_sha256:
        _invalid("BAMF_C05_COMPILED_CASE_COMPILER_IDENTITY_REQUIRED")
    record = compiled_case_identity_record(
        factory_release_sha256=source_context.release.release_sha256,
        semantic_catalog_sha256=source_context.release.semantic_catalog_sha256,
        semantic_release_sha256=authenticated.features.semantic_release,
        source_artifact_sha256=contract_digest(authenticated.selection.identity),
        source_row_id=task_template.source_row_id,
        source_row_sha256=task_template.source_row_sha256,
        source_binding_sha256=task_template.source_binding_sha256,
        lowerer_sha256=task_template.lowerer_sha256,
        evaluator_policy_sha256=contract_digest((
            config.task, config.frontier, config.policy)),
        compiler_sha256=compiler_sha256,
        feature_schema_sha256=contract_digest(authenticated.schema),
        compiled_frame_sha256=compiled_frame_identity_digest(
            batch.compiled.compiled),
        goal_sha256=contract_digest(task_template.goal),
        source_family_id=task_template.source_family_id,
        episode_id=task_template.episode_id,
    )
    items = tuple((key, value) for key, value in record.items() if key != "schema")
    return CompiledFactoryEvaluationCase(
        batch.compiled.compiled, batch.compiled.compiler_configs,
        batch.compiled.source_asts, batch.compiled.partial_forest_receipts,
        task_template, items, compiled_case_identity_digest(record))

def _source_atom_row(
    source_context: SourceExecutionContext,
    authenticated,
    row: dict,
    *,
    source_seed: int,
    source_each: int,
) -> SourceAtomRow:
    execution = source_context.release.execution_plan.capability_map.get(
        row.get("capability"))
    if execution is None:
        _invalid("BAMF_C05_COMPILED_CASE_SOURCE_CAPABILITY_MISSING")
    profile_parameters = (dict(execution.provider_parameters)
                          if execution.provider_parameters else None)
    source_graph = canonical_graph_for(
        row.get("generator"), source_context.source_root)
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
) -> bool:
    """Check cold-cache reuse without recompiling or invoking the C04 lowerer."""
    if type(compiled_case) is not CompiledFactoryEvaluationCase:
        _invalid("BAMF_C05_COMPILED_CASE_REQUIRED")
    compiled_case.__post_init__()
    source_context.release.verify()
    source_context.release.verify_semantic_catalog(source_context.graph)
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
) -> tuple[BamfCompiledBatch, FactoryTaskAuthority]:
    """Attach one immutable compilation to exact generation execution state."""
    if type(compiled_case) is not CompiledFactoryEvaluationCase:
        _invalid("BAMF_C05_COMPILED_CASE_REQUIRED")
    compiled_case.__post_init__()
    source_context.release.verify()
    source_context.release.verify_semantic_catalog(source_context.graph)
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


__all__ = (
    "CompiledFactoryEvaluationCase", "bind_factory_evaluation_case",
    "compiled_case_matches_contract",
    "compile_factory_evaluation_batch", "compile_factory_evaluation_case",
)
