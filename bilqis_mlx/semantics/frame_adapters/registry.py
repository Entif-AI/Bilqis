"""Source-owned frame registry behavior."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping
from types import MappingProxyType
from bilqis_mlx.b11_observation import note_provider_check
from ...factory.adapters import RegisteredSourceAdapter
from ..atlas_projection import FrozenAtlasSnapshot
from ..frame_schema import FrameTree, SourceSpan, atomic_fallback, validate_frame_tree
from .common import BOOLEAN_COMPOSITE_ADAPTER, BOOLEAN_CONNECTIVE_ADAPTER, BOOLEAN_IDENTIFICATION_ADAPTER, C13_EPISODE_ADAPTER, FINITE_NUMERIC_ADAPTER, MICRO_PREDICATE_ADAPTER, _adapter_fail, _source_id
from .micro import _bind_source_row
from .numeric import _bind_numeric_row


def _bind_identification_row(
    row: dict,
    snapshot: FrozenAtlasSnapshot,
    graph: dict,
    *,
    adapter_id: str,
    span: SourceSpan,
    causal_prefix_end: int,
) -> FrameTree:
    del snapshot, graph
    record = row.get("record")
    if not isinstance(record, dict) or record.get("task") != "identify_boolean_operator":
        _adapter_fail("FRAME_BOOLEAN_IDENTIFICATION_RECORD_INVALID",
                      adapter_id, span, "<source-row>")
    atomic = atomic_fallback(
        record,
        source_instance_id=_source_id(row, adapter_id, span),
        structural_path=(),
        source_span=span,
        parent_occurrence_id=None,
        causal_prefix_end=causal_prefix_end,
    )
    return validate_frame_tree(FrameTree(atomic))


def _bind_identification_release_row(
    row: dict,
    snapshot: FrozenAtlasSnapshot,
    graph: dict,
    *,
    adapter_id: str,
    span: SourceSpan,
    causal_prefix_end: int,
) -> FrameTree:
    record = row.get("record")
    if (isinstance(record, dict)
            and record.get("task") == "identify_boolean_operator"):
        return _bind_identification_row(
            row, snapshot, graph, adapter_id=adapter_id, span=span,
            causal_prefix_end=causal_prefix_end)
    return _bind_source_row(
        row, snapshot, graph, adapter_id=adapter_id, span=span,
        causal_prefix_end=causal_prefix_end)


def _bind_c13_episode_row(
    row: dict,
    snapshot: FrozenAtlasSnapshot,
    graph: dict,
    *,
    adapter_id: str,
    span: SourceSpan,
    causal_prefix_end: int,
) -> FrameTree:
    del snapshot, graph
    record = row.get("record")
    if (not isinstance(record, dict)
            or record.get("source_family_id") != "bamf.c13.episode-binding/v1"):
        _adapter_fail("FRAME_C13_EPISODE_RECORD_INVALID",
                      adapter_id, span, "<source-row>")
    atomic = atomic_fallback(
        {"task": "bamf.c13.episode-binding/v1", "record": record},
        source_instance_id=_source_id(row, adapter_id, span),
        structural_path=(),
        source_span=span,
        parent_occurrence_id=None,
        causal_prefix_end=causal_prefix_end,
    )
    return validate_frame_tree(FrameTree(atomic))

RowBinder = Callable[..., FrameTree]

_ROW_BINDERS: Mapping[str, RowBinder] = MappingProxyType({
    MICRO_PREDICATE_ADAPTER: _bind_source_row,
    BOOLEAN_CONNECTIVE_ADAPTER: _bind_source_row,
    BOOLEAN_COMPOSITE_ADAPTER: _bind_source_row,
    BOOLEAN_IDENTIFICATION_ADAPTER: _bind_identification_release_row,
    FINITE_NUMERIC_ADAPTER: _bind_numeric_row,
    C13_EPISODE_ADAPTER: _bind_c13_episode_row,
})

@dataclass(frozen=True)
class ReleasedFrameAdapter:
    source_adapter_id: str
    binder: RowBinder

def released_frame_adapter_ids() -> tuple[str, ...]:
    return tuple(sorted(_ROW_BINDERS))

def released_frame_adapter(
    source_adapter: RegisteredSourceAdapter,
    *,
    span: SourceSpan,
) -> ReleasedFrameAdapter:
    if not isinstance(source_adapter, RegisteredSourceAdapter):
        _adapter_fail("FRAME_REGISTERED_SOURCE_ADAPTER_REQUIRED",
                      "<unknown>", span, "<adapter>")
    adapter_id = source_adapter.descriptor.adapter_id
    binder = _ROW_BINDERS.get(adapter_id)
    if binder is None:
        _adapter_fail("FRAME_SOURCE_ADAPTER_UNRELEASED",
                      adapter_id, span, "<adapter>")
    return ReleasedFrameAdapter(adapter_id, binder)


def _bind_verified_source_row(
    source_adapter: RegisteredSourceAdapter,
    row: dict,
    snapshot: FrozenAtlasSnapshot,
    *,
    graph: dict,
    source_span: SourceSpan,
    causal_prefix_end: int,
) -> FrameTree:
    """Bind a row whose provider draw/check has already been proven upstream."""
    released = released_frame_adapter(source_adapter, span=source_span)
    if causal_prefix_end < source_span.end:
        _adapter_fail("FRAME_CAUSAL_PREFIX_INVALID",
                      released.source_adapter_id, source_span, "<frame>")
    return released.binder(
        row,
        snapshot,
        graph,
        adapter_id=released.source_adapter_id,
        span=source_span,
        causal_prefix_end=causal_prefix_end,
    )

def bind_registered_source_row(
    source_adapter: RegisteredSourceAdapter,
    row: dict,
    snapshot: FrozenAtlasSnapshot,
    *,
    source_root: str | Path,
    graph: dict,
    source_span: SourceSpan,
    causal_prefix_end: int,
    course=None,
) -> FrameTree:
    """Recheck and frame one row through its existing registered source owner."""
    released = released_frame_adapter(source_adapter, span=source_span)
    try:
        note_provider_check()
        valid = source_adapter.check(
            row,
            source_root=source_root,
            graph=graph,
            course=course,
        )
    except (KeyError, TypeError, ValueError, IndexError):
        _adapter_fail("FRAME_SOURCE_ADAPTER_CHECK_ERROR",
                      released.source_adapter_id, source_span, "<source-row>")
    if valid is not True:
        _adapter_fail("FRAME_SOURCE_ADAPTER_CHECK_FAILED",
                      released.source_adapter_id, source_span, "<source-row>")
    return _bind_verified_source_row(
        source_adapter, row, snapshot, graph=graph, source_span=source_span,
        causal_prefix_end=causal_prefix_end)
