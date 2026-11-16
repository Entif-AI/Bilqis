"""Source/context preparation owned by the Factory training bridge."""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from bilqis_mlx.factory.generation import runtime_adapter_for_release
from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.learning.source_atoms import SourceAtomRow
from bilqis_mlx.runtime.atlas_model_contracts import bind_candidate_active_semantic_rows
from bilqis_mlx.runtime.atlas_training_authority import bind_compiled_training_batch
from bilqis_mlx.runtime.b11_source_execution_authority import (
    B11SourceExecutionAuthority, _bind_prepared_b11_source_execution_authority,
    _issue_prepared_b11_source_proof,
    require_b11_source_execution_authority_current,
)
from bilqis_mlx.semantics.atlas_features.formal import source_family_for_adapter
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, ContextPolicy, SourceFrontier, TaskScope,
    project_context,
)
from bilqis_mlx.semantics.frame_adapters import public_formal_context
from bilqis_mlx.semantics.frame_adapters.public_formal import (
    _public_formal_context_from_verified_row,
)
from bilqis_mlx.semantics.frame_compiler import (
    CompiledFrameBatch, CompiledFrameRows, FrameCompilerConfig,
    validate_partial_visible_forest,
)
from bilqis_mlx.semantics.released_frame_schemas import (
    _load_pinned_released_frame_schemas_from_snapshot,
)
from bilqis_mlx.source_adapters.atoms.admission import (
    _public_formal_atom_context_from_witness,
    authorize_public_formal_prefix,
)
from bilqis_mlx.source_adapters.atoms.authority import canonical_graph_for
from bilqis_mlx.source_adapters.atom_binding import (
    _verified_source_row_witness, verify_source_row,
)
from bilqis_mlx.runtime.source_execution import SourceBatchAuthority
from bilqis_mlx.semantics.source_atom_binding import SourceRowWitness

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
    source_adapter: object
    source_id: str
    frames: tuple
    ast: object
    projection: object
    source_graph: object
    config: FrameCompilerConfig
    task: TaskScope
    frontier: SourceFrontier
    policy: ContextPolicy
    source_inventory: tuple
    formal_projection: ApprovedContextProjection
    formal_frontier: SourceFrontier
    source_witness: SourceRowWitness
    b11_proof: object | None = None


@dataclass(frozen=True)
class _PreparedB11SourceBinding:
    """Visit-scoped B11 proof bound to exact prefix/config/source identities."""

    prefix: CompiledFrameBatch
    config: FrameCompilerConfig
    source: SourceAtomRow
    authority: B11SourceExecutionAuthority

    def require_current(self):
        return require_b11_source_execution_authority_current(
            self.authority, self.prefix, self.config, self.source)


def _prepare_source_row(source_context, authenticated, manifest,
                        profile, row, *, capability, source_seed, source_each,
                        prequalified=False):
    if row.get("capability") != capability:
        _invalid("FACTORY_TRAINING_CAPABILITY_MISMATCH")
    source_adapter = source_context.source_registry.resolve_owner(
        row.get("generator"))
    source_graph = canonical_graph_for(row.get("generator"), source_context.source_root)
    task, frontier, policy = public_training_context(
        authenticated.features.semantic_release, capability, len(row.get("tokens", ())))
    if prequalified:
        projection, frame_frontier = _public_formal_context_from_verified_row(
            source_adapter, row, authenticated.snapshot,
            source_root=source_context.source_root, graph=source_graph,
            task_scope=task, source_frontier=frontier, policy=policy)
        source_witness, reason = _verified_source_row_witness(
            row, expected_adapter_id=source_adapter.descriptor.adapter_id)
    else:
        projection, frame_frontier = public_formal_context(
            source_adapter, row, authenticated.snapshot,
            source_root=source_context.source_root, graph=source_graph,
            task_scope=task, source_frontier=frontier, policy=policy,
            source_seed=source_seed, source_each=source_each,
            source_profile_parameters=profile,
            course=source_context.release.curriculum)
        source_witness, reason = verify_source_row(
            row, source_graph, source_root=source_context.source_root,
            source_seed=source_seed, source_each=source_each,
            course=source_context.release.curriculum,
            source_profile_parameters=profile)
    if type(projection) is not ApprovedContextProjection:
        _invalid("FACTORY_TRAINING_CONTEXT_HELD")
    if source_witness is None:
        _invalid("FACTORY_TRAINING_SOURCE_ROW_HELD:" + str(reason))
    from bilqis_mlx.runtime.factory_training_context import (
        _source_frame_inventory_from_context,
        _source_frame_inventory_from_verified_context,
    )
    source_inventory = (
        _source_frame_inventory_from_verified_context(
            source_context, row, authenticated, manifest)
        if prequalified else
        _source_frame_inventory_from_context(
            source_context, row, authenticated, manifest))
    source_id, frames = source_inventory
    if frames:
        atom_ast, atom_config = _public_formal_atom_context_from_witness(
            authenticated.selection, authenticated.snapshot, row, source_graph,
            source_witness, source_root=source_context.source_root, task=task,
            frontier=frame_frontier, policy=policy)
        ast = replace(atom_ast, frames=frames)
        current = atom_config.frontier
        config = FrameCompilerConfig(
            tuple(body.parse() for body in manifest.bodies), manifest.schema_map,
            None, task, current, policy)
        approved = project_context(projection.envelopes, task, current, policy)
    else:
        atom_ast, atom_config = _public_formal_atom_context_from_witness(
            authenticated.selection, authenticated.snapshot, row, source_graph,
            source_witness, source_root=source_context.source_root, task=task,
            frontier=frontier, policy=policy)
        ast, approved, config, current = atom_ast, None, atom_config, atom_config.frontier
    return _FactorySourceRow(
        row, source_adapter, source_id, frames, ast, approved, source_graph,
        config, task, current, policy, source_inventory, projection,
        frame_frontier, source_witness)


def _motif_planning_input(source_context, authenticated, adapter, profile, item, *,
                          source_seed, source_each):
    result = _FactoryMotifPlanningInput(
        adapter, item.row, authenticated.selection,
        Path(source_context.source_root), item.source_graph,
        item.task, item.frontier, item.policy,
        source_seed, source_each, profile, source_context.release.curriculum)
    result.__post_init__()
    return result


def _prepare_b11_source_binding(
        source_context, authenticated, profile, item, prefix, config, *,
        source_seed, source_each):
    if item.b11_proof is None:
        _invalid("FACTORY_TRAINING_PREPARED_B11_PROOF_REQUIRED")
    source = SourceAtomRow(
        authenticated.selection, item.row, item.source_graph,
        Path(source_context.source_root), source_seed, source_each,
        source_context.release.curriculum, profile)
    authority = _bind_prepared_b11_source_execution_authority(
        prefix, config, source, item.source_adapter, authenticated.snapshot,
        authenticated.features, item.b11_proof)
    prepared = _PreparedB11SourceBinding(prefix, config, source, authority)
    prepared.require_current()
    return prepared


def _bind_b11_rows(source_context, candidate, authenticated, training, source_rows,
                   profile, *, source_seed, source_each, prepared_b11=None):
    compiled_rows = []
    if prepared_b11 is not None and (
            type(prepared_b11) is not tuple
            or len(prepared_b11) != len(source_rows)
            or any(type(item) is not _PreparedB11SourceBinding
                   for item in prepared_b11)):
        _invalid("FACTORY_TRAINING_PREPARED_B11_INVALID")
    active_semantic_rows = bind_candidate_active_semantic_rows(candidate, authenticated)
    for index, item in enumerate(source_rows):
        prefix = training.rows[index].model_input.prefix
        if prepared_b11 is None:
            approved_config = (item.config if item.projection is None
                               else replace(item.config, approved=item.projection))
            approved_config = authorize_public_formal_prefix(
                item.ast, prefix, approved_config)
            prepared = _prepare_b11_source_binding(
                source_context, authenticated, profile, item, prefix,
                approved_config, source_seed=source_seed, source_each=source_each)
        else:
            prepared = prepared_b11[index]
            if prepared.prefix is not prefix:
                _invalid("FACTORY_TRAINING_PREPARED_B11_PREFIX_DRIFT")
            prepared.require_current()
            approved_config = prepared.config
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
        if (compiled.compiled.rows[0] is not prepared.prefix
                or compiled.compiler_configs[0] is not prepared.config):
            _invalid("FACTORY_TRAINING_PREPARED_B11_COMPILED_DRIFT")
        source = prepared.source
        source_execution_authority = prepared.authority
        batch = bind_compiled_training_batch(
            training, compiled, (source,), authenticated.schema,
            active_semantic_rows=active_semantic_rows, row_index=index,
            source_execution_authority=source_execution_authority)
        source_context.register_compiled_batch(batch)
        compiled_rows.append(batch)
    return tuple(compiled_rows)


def _prepare_factory_source_rows(source_context, authenticated, rows, *, capability,
                                 source_seed, source_each, source_authority=None):
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
    prequalified = source_authority is not None
    if prequalified:
        if (type(source_authority) is not SourceBatchAuthority
                or source_authority.capability_id != capability
                or source_authority.seed != source_seed
                or source_authority.each != source_each
                or source_authority.provider_id != adapter.descriptor.adapter_id):
            _invalid("FACTORY_TRAINING_SOURCE_AUTHORITY_INVALID")
        source_context.require_bound_rows(rows, source_authority)
    source_rows = tuple(_prepare_source_row(
        source_context, authenticated, manifest, profile, row,
        capability=capability, source_seed=source_seed, source_each=source_each,
        prequalified=prequalified)
        for row in rows)
    if prequalified:
        source_rows = tuple(replace(
            item,
            b11_proof=_issue_prepared_b11_source_proof(
                source_context, rows, source_authority, item.row,
                item.source_witness, item.formal_projection,
                item.formal_frontier)) for item in source_rows)
    return adapter, manifest, profile, source_rows
