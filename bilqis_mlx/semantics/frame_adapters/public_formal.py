"""Source-owned A/B/C admission before solver-visible context exists."""
from pathlib import Path

from ...factory.adapters import RegisteredSourceAdapter
from ..atlas_projection import FrozenAtlasSnapshot
from ..context_eligibility import ApprovedContextProjection, ContextHold, ContextPolicy, SourceFrontier, TaskScope
from ..frame_schema import SourceSpan
from .common import _adapter_fail
from .public_formal_sources import (
    _issue_public_formal_projection_authority, canonical_adapter, canonical_graph,
    validate_policy, verify_draw,
)
from .public_formal_grants import admit_tree
from .registry import (
    _bind_verified_source_row, bind_registered_source_row, released_frame_adapter,
)


def _admit_public_formal_tree(source_adapter, row, snapshot, tree, *,
                              task_scope, source_frontier, policy, span):
    adapter_id = source_adapter.descriptor.adapter_id
    validate_policy(snapshot, task_scope, source_frontier, policy, adapter_id, span)
    if span.end > task_scope.causal_prefix_end:
        return ContextHold(("BAMF_CONTEXT_INVISIBLE_PREFIX",), (), ())
    released = released_frame_adapter(source_adapter, span=span)
    admitted = admit_tree(tree, row, released.source_adapter_id,
                          task_scope, source_frontier, policy, span)
    if isinstance(admitted, ContextHold):
        return admitted
    projection, frontier = admitted
    _issue_public_formal_projection_authority(projection, released.source_adapter_id)
    return projection, frontier


def _public_formal_context_from_verified_row(
    source_adapter: RegisteredSourceAdapter,
    row: dict,
    snapshot: FrozenAtlasSnapshot,
    *,
    source_root: str | Path,
    graph: dict,
    task_scope: TaskScope,
    source_frontier: SourceFrontier,
    policy: ContextPolicy,
) -> tuple[ApprovedContextProjection, SourceFrontier] | ContextHold:
    """Project an exact row whose provider proof is already owned upstream."""
    tokens = row.get("tokens") if type(row) is dict else None
    if not isinstance(tokens, list) or not tokens:
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_TOKENS_MISSING",
                      "<unknown>", SourceSpan(0, 0), "<public-formal>")
    span = SourceSpan(0, len(tokens))
    source_adapter = canonical_adapter(source_adapter, span)
    adapter_id = source_adapter.descriptor.adapter_id
    _, graph = canonical_graph(source_root, graph, adapter_id, span)
    tree = _bind_verified_source_row(
        source_adapter, row, snapshot, graph=graph, source_span=span,
        causal_prefix_end=span.end)
    return _admit_public_formal_tree(
        source_adapter, row, snapshot, tree, task_scope=task_scope,
        source_frontier=source_frontier, policy=policy, span=span)


def public_formal_context(
    source_adapter: RegisteredSourceAdapter,
    row: dict,
    snapshot: FrozenAtlasSnapshot,
    *,
    source_root: str | Path,
    graph: dict,
    task_scope: TaskScope,
    source_frontier: SourceFrontier,
    policy: ContextPolicy,
    source_seed: int,
    source_each: int,
    source_profile_parameters: dict | None = None,
    course=None,
) -> tuple[ApprovedContextProjection, SourceFrontier] | ContextHold:
    """Reproduce a complete source row before creating any PUBLIC_FORMAL grants."""
    tokens = row.get("tokens") if type(row) is dict else None
    if not isinstance(tokens, list) or not tokens:
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_TOKENS_MISSING",
                      "<unknown>", SourceSpan(0, 0), "<public-formal>")
    # A/B/C records own their complete span. Callers cannot backdate it.
    span = SourceSpan(0, len(tokens))
    source_adapter = canonical_adapter(source_adapter, span)
    adapter_id = source_adapter.descriptor.adapter_id
    root, graph = canonical_graph(source_root, graph, adapter_id, span)
    row = verify_draw(source_adapter, row, root, graph, span, source_seed,
                      source_each, source_profile_parameters, course)
    tree = bind_registered_source_row(
        source_adapter, row, snapshot, source_root=source_root, graph=graph,
        source_span=span, causal_prefix_end=span.end, course=course)
    return _admit_public_formal_tree(
        source_adapter, row, snapshot, tree, task_scope=task_scope,
        source_frontier=source_frontier, policy=policy, span=span)
