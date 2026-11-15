"""Source/context preparation owned by the Factory training bridge."""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from bilqis_mlx.factory.generation import runtime_adapter_for_release
from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.learning.source_atoms import SourceAtomRow
from bilqis_mlx.runtime.atlas_model_contracts import bind_candidate_active_semantic_rows
from bilqis_mlx.runtime.atlas_training_authority import bind_compiled_training_batch
from bilqis_mlx.runtime._model.backbone.source_execution_authority import (
    bind_b11_source_execution_authority,
)
from bilqis_mlx.semantics.atlas_features.formal import source_family_for_adapter
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, ContextPolicy, SourceFrontier, TaskScope,
    project_context,
)
from bilqis_mlx.semantics.frame_adapters import public_formal_context
from bilqis_mlx.semantics.frame_compiler import (
    CompiledFrameRows, FrameCompilerConfig, validate_partial_visible_forest,
)
from bilqis_mlx.semantics.released_frame_schemas import (
    _load_pinned_released_frame_schemas_from_snapshot,
)
from bilqis_mlx.source_adapters.atoms.admission import (
    _public_formal_atom_context_from_snapshot, authorize_public_formal_prefix,
)
from bilqis_mlx.source_adapters.atoms.authority import canonical_graph_for

from .atlas_training_contracts import _invalid
from .factory_training_context import public_training_context


@dataclass(frozen=True)
class _FactoryMotifPlanningInput:
    """Exact source-owner inputs B07 must replay against retained custody."""

    source_adapter: object
    row: dict
    atlas_selection: object
    source_root: Path
    source_graph: dict
    task: TaskScope
    frontier: SourceFrontier
    policy: ContextPolicy
    source_seed: int
    source_each: int
    source_profile_parameters: dict | None
    course: object

    def __post_init__(self) -> None:
        if (not isinstance(self.row, dict)
                or not isinstance(self.source_root, Path)
                or not isinstance(self.source_graph, dict)
                or type(self.task) is not TaskScope
                or type(self.frontier) is not SourceFrontier
                or type(self.policy) is not ContextPolicy
                or type(self.source_seed) is not int or self.source_seed < 0
                or type(self.source_each) is not int or self.source_each < 1
                or (self.source_profile_parameters is not None
                    and not isinstance(self.source_profile_parameters, dict))):
            _invalid("FACTORY_MOTIF_PLANNING_INPUT_INVALID")


@dataclass(frozen=True)
class _FactorySourceRow:
    row: dict
    source_id: str
    frames: tuple
    ast: object
    projection: object
    source_graph: object
    config: FrameCompilerConfig
    task: TaskScope
    frontier: SourceFrontier
    policy: ContextPolicy


def _prepare_source_row(source_context, authenticated, adapter, manifest,
                        profile, row, *, capability, source_seed, source_each):
    if row.get("capability") != capability:
        _invalid("FACTORY_TRAINING_CAPABILITY_MISMATCH")
    source_graph = canonical_graph_for(row.get("generator"), source_context.source_root)
    task, frontier, policy = public_training_context(
        authenticated.features.semantic_release, capability, len(row.get("tokens", ())))
    projection, frame_frontier = public_formal_context(
        adapter, row, authenticated.snapshot,
        source_root=source_context.source_root, graph=source_graph,
        task_scope=task, source_frontier=frontier, policy=policy,
        source_seed=source_seed, source_each=source_each,
        source_profile_parameters=profile, course=source_context.release.curriculum)
    if type(projection) is not ApprovedContextProjection:
        _invalid("FACTORY_TRAINING_CONTEXT_HELD")
    from bilqis_mlx.runtime.factory_training_context import (
        _source_frame_inventory_from_context,
    )
    source_id, frames = _source_frame_inventory_from_context(
        source_context, row, authenticated, manifest)
    if frames:
        atom_ast, atom_config = _public_formal_atom_context_from_snapshot(
            authenticated.selection, authenticated.snapshot, row, source_graph,
            source_root=source_context.source_root, source_seed=source_seed,
            source_each=source_each, task=task, frontier=frame_frontier,
            policy=policy, course=source_context.release.curriculum,
            source_profile_parameters=profile)
        ast = replace(atom_ast, frames=frames)
        current = atom_config.frontier
        config = FrameCompilerConfig(
            tuple(body.parse() for body in manifest.bodies), manifest.schema_map,
            None, task, current, policy)
        approved = project_context(projection.envelopes, task, current, policy)
    else:
        atom_ast, atom_config = _public_formal_atom_context_from_snapshot(
            authenticated.selection, authenticated.snapshot, row, source_graph,
            source_root=source_context.source_root, source_seed=source_seed,
            source_each=source_each, task=task, frontier=frontier,
            policy=policy, course=source_context.release.curriculum,
            source_profile_parameters=profile)
        ast, approved, config, current = atom_ast, None, atom_config, atom_config.frontier
    return _FactorySourceRow(
        row, source_id, frames, ast, approved, source_graph, config, task, current, policy)


def _motif_planning_input(source_context, authenticated, adapter, profile, item, *,
                          source_seed, source_each):
    result = _FactoryMotifPlanningInput(
        adapter, item.row, authenticated.selection,
        Path(source_context.source_root), item.source_graph,
        item.task, item.frontier, item.policy,
        source_seed, source_each, profile, source_context.release.curriculum)
    result.__post_init__()
    return result


def _bind_b11_rows(source_context, candidate, authenticated, training, source_rows,
                   profile, *, source_seed, source_each):
    compiled_rows = []
    active_semantic_rows = bind_candidate_active_semantic_rows(candidate, authenticated)
    for index, item in enumerate(source_rows):
        approved_config = (item.config if item.projection is None
                           else replace(item.config, approved=item.projection))
        prefix = training.rows[index].model_input.prefix
        approved_config = authorize_public_formal_prefix(
            item.ast, prefix, approved_config)
        compiled_frame_rows = CompiledFrameRows(
            (prefix,), (prefix.positions,), ((True,) * len(prefix.positions),))
        if item.projection is None:
            compiled = CompiledEncoderInput(
                compiled_frame_rows, (approved_config,), authenticated.features,
                candidate.extents)
        else:
            receipt = validate_partial_visible_forest(prefix, item.ast, approved_config)
            compiled = CompiledEncoderInput(
                compiled_frame_rows, (approved_config,), authenticated.features,
                candidate.extents, source_asts=(item.ast,),
                partial_forest_receipts=(receipt,))
        source = SourceAtomRow(
            authenticated.selection, item.row, item.source_graph,
            Path(source_context.source_root), source_seed, source_each,
            source_context.release.curriculum, profile)
        source_execution_authority = bind_b11_source_execution_authority(
            compiled.compiled.rows[0], compiled.compiler_configs[0],
            source, adapter, authenticated.snapshot)
        batch = bind_compiled_training_batch(
            training, compiled, (source,), authenticated.schema,
            active_semantic_rows=active_semantic_rows, row_index=index,
            source_execution_authority=source_execution_authority)
        source_context.register_compiled_batch(batch)
        compiled_rows.append(batch)
    return tuple(compiled_rows)


def _prepare_factory_source_rows(source_context, authenticated, rows, *, capability,
                                 source_seed, source_each):
    """Prepare the same source-owned AST and eligibility inputs for C02 or an offer."""
    execution = source_context.release.execution_plan.capability_map[capability]
    adapter = runtime_adapter_for_release(
        source_context.source_root, source_context.graph, source_context.release,
        source_context.source_registry, execution)
    family = source_family_for_adapter(adapter.descriptor.adapter_id)
    manifest = _load_pinned_released_frame_schemas_from_snapshot(
        family, authenticated.selection, authenticated.snapshot).manifest
    profile = (dict(execution.provider_parameters)
               if execution.provider_parameters else None)
    source_rows = tuple(_prepare_source_row(
        source_context, authenticated, adapter, manifest, profile, row,
        capability=capability, source_seed=source_seed, source_each=source_each)
        for row in rows)
    return adapter, manifest, profile, source_rows
