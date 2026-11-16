"""Create collision-checked grants for already verified source frame trees."""
from dataclasses import replace

from ...generated_assessment import digest
from ..atlas.snapshot import AtlasArtifactSelection
from ..context_eligibility import (
    PUBLIC_FORMAL, ApprovedContextProjection, ContextEligibility, ContextHold,
    ContextMember, ContextPolicy, SourceFrontier, SourceGrant, TaskScope,
    frame_evidence_digest, member_evidence_digest, project_context,
)
from ..frame_schema import FrameInstance, SourceSpan
from .common import PUBLIC_FORMAL_TIMELESS_EPOCH, _adapter_fail
from .public_formal_schema_rights import (
    _current_source_schema_grant_from_snapshot,
    current_source_schema_grant, issue_source_schema_rights_authority,
    schema_evidence_digest, schema_source_handle, source_schema_rights_frontier,
)


def _walk(node):
    yield node.root
    for child in node.children:
        yield from _walk(child)


def _envelope(frame, prefix, task, frontier, policy):
    members = (
        tuple(ContextMember(
            binding.role_id, binding.occurrence_index,
            prefix + ":member:" + binding.role_id + ":" + str(binding.occurrence_index),
            frame.causal_prefix_end) for binding in frame.bindings)
        if isinstance(frame, FrameInstance)
        else (ContextMember("<atomic>", 0, prefix + ":member:<atomic>:0", frame.causal_prefix_end),))
    return ContextEligibility(
        frame_handle=prefix + ":frame", frame=frame,
        source_handle=prefix + ":source", members=members,
        principal_id=task.principal_id, tenant_id=task.tenant_id,
        purpose=task.purpose, source_regime=PUBLIC_FORMAL,
        semantic_release=task.semantic_release,
        jurisdiction=task.jurisdiction, scope=task.scope,
        join_class=PUBLIC_FORMAL, policy_epoch=policy.policy_epoch,
        rights_epoch=frontier.rights_epoch, correction_generation=frontier.correction_generation,
        observed_at=PUBLIC_FORMAL_TIMELESS_EPOCH,
        effective_from=PUBLIC_FORMAL_TIMELESS_EPOCH, effective_until=None,
        causal_prefix_end=frame.causal_prefix_end)


def _issue_source_schema_grants(
    projection: ApprovedContextProjection,
    *,
    source_adapter_id: str,
    atlas_selection: AtlasArtifactSelection,
    task_scope: TaskScope,
    source_frontier: SourceFrontier,
    policy: ContextPolicy,
    snapshot=None,
) -> SourceFrontier:
    """Issue motif-schema rights only from the source-owned A01/A03 boundary."""
    span = SourceSpan(0, 0)
    if (type(projection) is not ApprovedContextProjection
            or not isinstance(source_adapter_id, str) or not source_adapter_id
            or type(atlas_selection) is not AtlasArtifactSelection
            or type(task_scope) is not TaskScope
            or type(source_frontier) is not SourceFrontier
            or type(policy) is not ContextPolicy
            or task_scope.purpose is None
            or atlas_selection.release_sha256 != task_scope.semantic_release):
        _adapter_fail(
            "BAMF_CONTEXT_PUBLIC_FORMAL_SCHEMA_AUTHORITY_INVALID",
            source_adapter_id if isinstance(source_adapter_id, str) else "<unknown>",
            span, "<schema>")
    atlas_selection.__post_init__()
    authority = issue_source_schema_rights_authority(atlas_selection)
    owner_frontier = source_schema_rights_frontier(authority)
    if (source_frontier.rights_epoch != owner_frontier.rights_epoch
            or source_frontier.correction_generation
            != owner_frontier.correction_generation
            or policy.rights_epoch != owner_frontier.rights_epoch):
        _adapter_fail(
            "BAMF_CONTEXT_PUBLIC_FORMAL_SCHEMA_OWNER_VERSION_DRIFT",
            source_adapter_id, span, "<schema>")
    current = project_context(
        projection.envelopes, task_scope, source_frontier, policy)
    if type(current) is not ApprovedContextProjection or current != projection:
        _adapter_fail(
            "BAMF_CONTEXT_PUBLIC_FORMAL_SCHEMA_CONTEXT_DRIFT",
            source_adapter_id, span, "<schema>")

    grants = {item.source_handle: item for item in source_frontier.grants}
    for envelope in projection.envelopes:
        frame = envelope.frame
        if type(frame) is not FrameInstance:
            continue
        span = frame.source_span
        grant = (
            current_source_schema_grant(
                authority, source_adapter_id, projection, frame)
            if snapshot is None else
            _current_source_schema_grant_from_snapshot(
                authority, source_adapter_id, projection, frame, snapshot))
        prior = grants.get(grant.source_handle)
        if prior is not None and prior != grant:
            _adapter_fail(
                "BAMF_CONTEXT_PUBLIC_FORMAL_SCHEMA_GRANT_COLLISION",
                source_adapter_id, span, "<schema>")
        grants[grant.source_handle] = grant
    return replace(
        source_frontier,
        grants=tuple(sorted(
            grants.values(), key=lambda item: item.source_handle)))


def issue_source_schema_grants(
    projection: ApprovedContextProjection,
    *,
    source_adapter_id: str,
    atlas_selection: AtlasArtifactSelection,
    task_scope: TaskScope,
    source_frontier: SourceFrontier,
    policy: ContextPolicy,
) -> SourceFrontier:
    """Cold public path: re-enter A01/A03 while issuing schema grants."""
    return _issue_source_schema_grants(
        projection, source_adapter_id=source_adapter_id,
        atlas_selection=atlas_selection, task_scope=task_scope,
        source_frontier=source_frontier, policy=policy)


def _issue_source_schema_grants_from_snapshot(
    projection: ApprovedContextProjection,
    *,
    source_adapter_id: str,
    atlas_selection: AtlasArtifactSelection,
    task_scope: TaskScope,
    source_frontier: SourceFrontier,
    policy: ContextPolicy,
    snapshot,
) -> SourceFrontier:
    """Hot owner path from one already-authenticated immutable A01 snapshot."""
    return _issue_source_schema_grants(
        projection, source_adapter_id=source_adapter_id,
        atlas_selection=atlas_selection, task_scope=task_scope,
        source_frontier=source_frontier, policy=policy, snapshot=snapshot)


def admit_tree(tree, row, source_adapter_id, task, source_frontier, policy, source_span):
    envelopes = []
    grants = {item.source_handle: item for item in source_frontier.grants}
    visible_digest = digest({
        "source_id": row.get("source_id") or row.get("id"),
        "record": row.get("record"), "tokens": row.get("tokens")})
    for frame in _walk(tree):
        prefix = "public-formal:" + source_adapter_id + ":" + visible_digest + ":" + frame.occurrence_id
        envelope = _envelope(frame, prefix, task, source_frontier, policy)
        evidence = {envelope.source_handle: frame_evidence_digest(frame)}
        evidence.update({member.source_handle: member_evidence_digest(frame, member)
                         for member in envelope.members})
        for handle, evidence_sha in evidence.items():
            grant = SourceGrant(
                handle, task.principal_id, task.tenant_id, PUBLIC_FORMAL,
                task.semantic_release, evidence_sha,
                (task.purpose,), (task.jurisdiction,), (task.scope,),
                source_frontier.rights_epoch, source_frontier.correction_generation,
                PUBLIC_FORMAL_TIMELESS_EPOCH, PUBLIC_FORMAL_TIMELESS_EPOCH)
            prior = grants.get(handle)
            if prior is not None and prior != grant:
                _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_GRANT_COLLISION",
                              source_adapter_id, source_span, "<public-formal>")
            grants[handle] = grant
        envelopes.append(envelope)
    frontier = SourceFrontier(
        source_frontier.rights_epoch, source_frontier.correction_generation,
        tuple(sorted(grants.values(), key=lambda grant: grant.source_handle)))
    projected = project_context(tuple(envelopes), task, frontier, policy)
    return projected if isinstance(projected, ContextHold) else (projected, frontier)
