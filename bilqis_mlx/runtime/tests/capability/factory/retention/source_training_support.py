"""Current source-owned training-batch setup for Factory retention witnesses."""
from __future__ import annotations

from dataclasses import replace
from tempfile import TemporaryDirectory

from bilqis_mlx.factory.generation import runtime_adapter_for_release
from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.runtime.atlas_training_adapter import compile_training_batch
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.runtime.bamf_bundle import authenticate_bamf_execution_feature_context
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import visit_provenance
from bilqis_mlx.semantics.context_eligibility import (
    PUBLIC_FORMAL, ContextPolicy, SourceFrontier, TaskScope,
)
from bilqis_mlx.semantics.atlas.feature_io import persist_feature_manifest
from bilqis_mlx.semantics.frame_adapters import public_formal_context
from bilqis_mlx.semantics.frame_compiler import FrameCompilerConfig
from bilqis_mlx.semantics.released_frame_schemas import (
    _load_pinned_released_frame_schemas,
)
from bilqis_mlx.source_adapters.atoms.admission import public_formal_atom_context
from bilqis_mlx.source_adapters.atoms.authority import canonical_graph_for
from bilqis_mlx.runtime.factory_training_context import source_frame_inventory


def _answer_plan(prefix, release, _capability, kind, generation_binding):
    head = next(item for item in release.answer_heads if item.kind == kind)
    return {
        "modalityID": head.modality_id,
        "input_prefix_end": prefix.visible_end,
        "decisions": [
            {"id": "value", "roleID": "answer", "occurrence": 0,
             "kind": "VALUE", "legalValues": list(head.values), "depends_on": []},
            {"id": "end", "roleID": "end", "occurrence": 0,
             "kind": "CONTROL", "legalValues": ["END_FRAME"],
             "depends_on": ["value"]},
        ],
        "allowedOutputSchema": "factory-retention-live",
        "maximum_decisions": 2,
        "generation_binding": generation_binding,
    }


def _training_context(source_context, candidate, artifact_path, row, capability,
                      source_seed, source_each):
    authenticated = authenticate_bamf_execution_feature_context(
        candidate, str(artifact_path), source_context.run_dir)
    execution = source_context.release.execution_plan.capability_map[capability]
    adapter = runtime_adapter_for_release(
        source_context.source_root, source_context.graph, source_context.release,
        source_context.source_registry, execution)
    source_graph = canonical_graph_for(
        row.get("generator"), source_context.source_root, row=row)
    prefix_end = len(row["tokens"])
    task = TaskScope(
        "bamf-retention-trainer", "bamf-retention", "TRAINING",
        authenticated.features.semantic_release, "LOCAL", capability,
        0, 0, prefix_end)
    policy = ContextPolicy(
        "bamf-retention-public-formal/v1", 1, 1,
        ("TRAINING",), (PUBLIC_FORMAL,), ("LOCAL",), (capability,),
        (PUBLIC_FORMAL,), ((PUBLIC_FORMAL, PUBLIC_FORMAL),),
        tuple((PUBLIC_FORMAL,) * count for count in range(3, 25)))
    _source_id, frames = source_frame_inventory(
        source_context, row, authenticated.selection)
    frame_frontier = SourceFrontier(1, 1, ())
    projection = None
    if frames:
        projection, frame_frontier = public_formal_context(
            adapter, row, authenticated.snapshot,
            source_root=source_context.source_root, graph=source_graph,
            task_scope=task, source_frontier=frame_frontier, policy=policy,
            source_seed=source_seed, source_each=source_each,
            source_profile_parameters=(dict(execution.provider_parameters)
                                       if execution.provider_parameters else None),
            course=source_context.release.curriculum)
    atom_ast, atom_config = public_formal_atom_context(
        authenticated.selection, row, source_graph,
        source_root=source_context.source_root, source_seed=source_seed,
        source_each=source_each, task=task, frontier=frame_frontier,
        policy=policy, course=source_context.release.curriculum,
        source_profile_parameters=(dict(execution.provider_parameters)
                                   if execution.provider_parameters else None))
    ast = replace(atom_ast, frames=frames)
    manifest = _load_pinned_released_frame_schemas(
        "boolean", authenticated.selection).manifest
    compiler_config = FrameCompilerConfig(
        tuple(body.parse() for body in manifest.bodies), manifest.schema_map,
        None, task, atom_config.frontier, policy)
    return authenticated, ast, projection, compiler_config, task, policy


def source_training_batch(source_context, candidate, artifact_path, row, generation,
                          *, capability, source_seed, source_each=1,
                          optimizer_step_seed=0, teacher_strategy=None,
                          teacher_visit_provenance=None):
    """Compile one real source row through current A05/A06 training authority."""
    authenticated, ast, projection, config, task, policy = _training_context(
        source_context, candidate, artifact_path, row, capability,
        source_seed, source_each)
    execution = source_context.release.execution_plan.capability_map[capability]
    delivery = describe_delivered_teaching(
        source_context.release, capability, execution.teaching_option_ids[0], (row,))
    with TemporaryDirectory() as feature_root:
        receipt = persist_feature_manifest(authenticated.features, feature_root)
        return compile_training_batch(
            (row,), source_context, ModelTopologySpecV2(),
            delivery=delivery, delivery_capability=capability,
            delivery_release_sha256=source_context.release.release_sha256,
            teacher_strategy=(teacher_strategy or {"policy": "factory-c05-live"}),
            requested_count=1, optimizer_step_seed=optimizer_step_seed,
            visit_provenance=(teacher_visit_provenance
                              or visit_provenance(capability)),
            source_authority=source_context.bind_rows(
                (row,), seed=source_seed, capability=capability, each=source_each),
            rehearsal_by_id={}, visible_ends={row["id"]: len(row["tokens"])},
            source_ast_for=lambda _tokens: ast,
            compiler_config=config, feature_artifact_path=receipt.path,
            answer_plan_for=lambda prefix, release, cap, kind: _answer_plan(
                prefix, release, cap, kind, generation),
            frames_for_ast=lambda _ast: (
                () if projection is None else projection.envelopes),
            task_scope=task, source_frontier=config.frontier,
            eligibility_policy=policy, generation_binding=generation,
            atlas_selection=authenticated.selection)


__all__ = ("source_training_batch",)
