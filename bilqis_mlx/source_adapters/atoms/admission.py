"""Issue raw-atom grants through the existing public-formal source policy."""
from __future__ import annotations

from dataclasses import replace

from ...semantics.atlas.snapshot import load_pinned_atlas_snapshot
from ...semantics.context_eligibility import (
    PUBLIC_FORMAL, ContextPolicy, SourceFrontier, SourceGrant, TaskScope,
)
from ...semantics.frame_codec import SchemaTagMap
from ...semantics.frame_compiler import (
    CompiledFrameBatch, FrameCompilerConfig, StreamingAST, atom_evidence_digest,
    compile_prefix, prefix_inventory_evidence_digest, prefix_inventory_handle,
)
from ...semantics.source_atom_binding.common import invalid
from .authority import project_verified_row, require_canonical_graph


def _public_formal_atom_context_from_snapshot(
    selection, snapshot, source_row, graph, *, source_root, source_seed, source_each,
    task: TaskScope, frontier: SourceFrontier, policy: ContextPolicy,
    course=None, source_profile_parameters=None,
):
    """Return raw-atom authority from an already authenticated Atlas snapshot.

    Only atoms visible at the requested prefix receive grants. Existing
    conflicting or revoked grants are never replaced. This neither admits a
    lesson nor changes policy, model parameters or the source's ABI.
    """
    from ..atom_binding import verify_source_row

    if ((snapshot.release_sha256, snapshot.bundle_id, snapshot.source_bundle_id)
          != (selection.release_sha256, selection.bundle_id,
              selection.source_bundle_id)):
        invalid("SOURCE_ATOM_PUBLIC_FORMAL_SOURCE_DRIFT")
    canonical_graph = require_canonical_graph(source_row, graph, source_root)
    witness, reason = verify_source_row(
        source_row, canonical_graph, source_root=source_root,
        source_seed=source_seed, source_each=source_each, course=course,
        source_profile_parameters=source_profile_parameters)
    if witness is None:
        invalid("BAMF_SOURCE_ATOM_SOURCE_ROW_HELD:" + str(reason))
    if (type(task) is not TaskScope or type(frontier) is not SourceFrontier
            or type(policy) is not ContextPolicy
            or task.semantic_release != snapshot.release_sha256
            or task.purpose not in policy.allowed_purposes
            or PUBLIC_FORMAL not in policy.allowed_regimes
            or PUBLIC_FORMAL not in policy.allowed_join_classes
            or policy.rights_epoch != frontier.rights_epoch):
        invalid("SOURCE_ATOM_PUBLIC_FORMAL_POLICY_INVALID")
    source = project_verified_row(source_row, canonical_graph, snapshot, witness)
    if not 0 <= task.causal_prefix_end <= len(source.ast.atoms):
        invalid("SOURCE_ATOM_FUTURE_PREFIX")
    grants = {grant.source_handle: grant for grant in frontier.grants}
    if len(grants) != len(frontier.grants):
        invalid("SOURCE_ATOM_DUPLICATE_GRANT")
    for atom in source.ast.atoms[:task.causal_prefix_end]:
        grant = SourceGrant(
            atom.source_reference, task.principal_id, task.tenant_id,
            PUBLIC_FORMAL, task.semantic_release,
            atom_evidence_digest(source.ast.source_instance_id, atom, task.semantic_release),
            (task.purpose,), (task.jurisdiction,), (task.scope,),
            frontier.rights_epoch, frontier.correction_generation, 0, 0)
        prior = grants.get(atom.source_reference)
        if prior is not None and prior != grant:
            invalid("SOURCE_ATOM_PUBLIC_FORMAL_GRANT_COLLISION")
        grants[atom.source_reference] = grant
    current = replace(frontier, grants=tuple(sorted(
        grants.values(), key=lambda grant: grant.source_handle)))
    config = FrameCompilerConfig(
        (), SchemaTagMap.from_schemas(task.semantic_release, ()),
        None, task, current, policy)
    return source.ast, config


def public_formal_atom_context(
    selection, source_row, graph, *, source_root, source_seed, source_each,
    task: TaskScope, frontier: SourceFrontier, policy: ContextPolicy,
    course=None, source_profile_parameters=None,
):
    """Cold public source replay; hot owners use the private snapshot seam."""
    snapshot = load_pinned_atlas_snapshot(selection)
    return _public_formal_atom_context_from_snapshot(
        selection, snapshot, source_row, graph,
        source_root=source_root, source_seed=source_seed, source_each=source_each,
        task=task, frontier=frontier, policy=policy, course=course,
        source_profile_parameters=source_profile_parameters)


def authorize_public_formal_prefix(
    ast: StreamingAST, compiled: CompiledFrameBatch, config: FrameCompilerConfig,
) -> FrameCompilerConfig:
    """Issue A13 rights for the exact A05-compiled complete p-local inventory."""
    if (type(ast) is not StreamingAST or type(compiled) is not CompiledFrameBatch
            or type(config) is not FrameCompilerConfig
            or compiled.source_instance_id != ast.source_instance_id
            or compiled.semantic_release != config.task.semantic_release
            or compiled.visible_end != config.task.causal_prefix_end):
        invalid("SOURCE_ATOM_PREFIX_AUTHORITY_INVALID")
    replay = compile_prefix(
        ast, compiled.visible_end, compiled.semantic_release, config)
    if replay != compiled:
        invalid("SOURCE_ATOM_PREFIX_AUTHORITY_REPLAY_MISMATCH")
    task, frontier, policy = config.task, config.frontier, config.policy
    if (task.purpose not in policy.allowed_purposes
            or PUBLIC_FORMAL not in policy.allowed_regimes
            or PUBLIC_FORMAL not in policy.allowed_join_classes
            or task.jurisdiction not in policy.allowed_jurisdictions
            or task.scope not in policy.allowed_scopes
            or policy.rights_epoch != frontier.rights_epoch):
        invalid("SOURCE_ATOM_PREFIX_AUTHORITY_POLICY_INVALID")
    grant = SourceGrant(
        prefix_inventory_handle(ast.source_instance_id, compiled.visible_end),
        task.principal_id, task.tenant_id, PUBLIC_FORMAL, task.semantic_release,
        prefix_inventory_evidence_digest(compiled),
        (task.purpose,), (task.jurisdiction,), (task.scope,),
        frontier.rights_epoch, frontier.correction_generation, 0, 0)
    grants = {item.source_handle: item for item in frontier.grants}
    prior = grants.get(grant.source_handle)
    if prior is not None and prior != grant:
        invalid("SOURCE_ATOM_PREFIX_AUTHORITY_GRANT_COLLISION")
    grants[grant.source_handle] = grant
    current = replace(frontier, grants=tuple(sorted(
        grants.values(), key=lambda item: item.source_handle)))
    return replace(config, frontier=current)
