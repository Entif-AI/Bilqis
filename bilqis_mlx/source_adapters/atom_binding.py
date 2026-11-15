"""Source-owned verification boundary for A05 raw-atom semantic candidates."""
from __future__ import annotations

from pathlib import Path

from ..errors import BilqisError, ErrorBus, SEMANTIC_FRAME
from ..semantics.atlas.snapshot import AtlasArtifactSelection, load_pinned_atlas_snapshot
from ..semantics.frame_compiler import CompiledFrameBatch, FrameCompilerConfig
from ..semantics.source_atom_binding import (
    SourceAtomHandoff, SourceRowWitness, _resolve_visible_atoms,
)
from .school import live_source_registry
from .atoms.authority import project_verified_row, require_canonical_graph


def _invalid(reason: str) -> None:
    ErrorBus.raise_(
        SEMANTIC_FRAME.BINDING.INVALID,
        reason=reason, role_id="<source-atom-binding>",
        span_start=0, span_end=0,
    )


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def verify_source_row(
    row: object,
    graph: object,
    *,
    source_root: str | Path,
    source_seed: int,
    source_each: int,
    course,
    source_profile_parameters,
) -> tuple[SourceRowWitness | None, str | None]:
    """Reproduce one row with the canonical live source adapter."""
    if (not isinstance(row, dict) or not isinstance(graph, dict)
            or not isinstance(row.get("tokens"), list)
            or not row["tokens"]
            or any(type(item) is not int or item < 0 for item in row["tokens"])
            or not all(_text(row.get(name)) for name in (
                "generator", "oracle", "capability"))
            or type(source_seed) is not int or type(source_each) is not int
            or not 1 <= source_each <= 128):
        return None, "SOURCE_ATOM_SOURCE_ROW_INVALID"
    try:
        canonical = live_source_registry().resolve_owner(row["generator"])
    except (KeyError, TypeError, ValueError, BilqisError):
        return None, "SOURCE_ATOM_SOURCE_ADAPTER_UNSUPPORTED"
    try:
        graph = require_canonical_graph(row, graph, source_root)
    except (KeyError, OSError, TypeError, ValueError, BilqisError):
        return None, "SOURCE_ATOM_CANONICAL_GRAPH_OR_ROOT_UNVERIFIED"
    draw_args = {
        "source_root": Path(source_root),
        "graph": graph,
        "course": course,
        "capability": row["capability"],
        "seed": source_seed,
        "each": source_each,
    }
    if source_profile_parameters is not None:
        draw_args["profile_parameters"] = source_profile_parameters
    try:
        rows = canonical.draw(**draw_args)
        checked = canonical.check(
            row, source_root=Path(source_root), graph=graph, course=course)
    except (KeyError, OSError, TypeError, ValueError, BilqisError):
        return None, "SOURCE_ATOM_SOURCE_ROW_UNVERIFIED"
    if (not isinstance(rows, (tuple, list))
            or not any(candidate == row for candidate in rows)
            or checked is not True):
        return None, "SOURCE_ATOM_SOURCE_ROW_UNVERIFIED"
    sense = row.get("source_sense_id")
    if not _text(sense):
        sense = "UNDECLARED_SOURCE_SENSE"
    accepted_oracles = canonical.descriptor.accepted_oracle_ids
    if row["oracle"] in accepted_oracles:
        oracle_id = row["oracle"]
    elif len(accepted_oracles) == 1:
        oracle_id = accepted_oracles[0]
    else:
        return None, "SOURCE_ATOM_SOURCE_ROW_UNVERIFIED"
    return SourceRowWitness(
        canonical.descriptor.adapter_id,
        canonical.descriptor.generator_id,
        oracle_id,
        row["capability"],
        sense,
        tuple(row["tokens"]),
    ), None


def _build_source_atom_handoff_from_snapshot(
    compiled: CompiledFrameBatch,
    config: FrameCompilerConfig,
    selection: AtlasArtifactSelection,
    snapshot,
    source_row: dict,
    graph: dict,
    *,
    source_root: str | Path,
    source_seed: int,
    source_each: int,
    course=None,
    source_profile_parameters=None,
) -> SourceAtomHandoff:
    if ((snapshot.release_sha256, snapshot.bundle_id, snapshot.source_bundle_id)
          != (selection.release_sha256, selection.bundle_id,
              selection.source_bundle_id)):
        _invalid("BAMF_SOURCE_ATOM_SOURCE_DRIFT")
    witness, reason = verify_source_row(
        source_row, graph,
        source_root=source_root,
        source_seed=source_seed,
        source_each=source_each,
        course=course,
        source_profile_parameters=source_profile_parameters,
    )
    if witness is None:
        _invalid("BAMF_SOURCE_ATOM_SOURCE_ROW_HELD:" + str(reason))
    source_projection = project_verified_row(source_row, graph, snapshot, witness)
    return _resolve_visible_atoms(
        compiled, config, snapshot, witness, graph, source_projection=source_projection)


def build_source_atom_handoff(
    compiled: CompiledFrameBatch,
    config: FrameCompilerConfig,
    selection: AtlasArtifactSelection,
    source_row: dict,
    graph: dict,
    *,
    source_root: str | Path,
    source_seed: int,
    source_each: int,
    course=None,
    source_profile_parameters=None,
) -> SourceAtomHandoff:
    """Build the pinned A05-to-B02/B03 handoff without semantic invention."""
    snapshot = load_pinned_atlas_snapshot(selection)
    return _build_source_atom_handoff_from_snapshot(
        compiled, config, selection, snapshot, source_row, graph,
        source_root=source_root, source_seed=source_seed, source_each=source_each,
        course=course, source_profile_parameters=source_profile_parameters)


def _revalidate_source_atom_handoff_from_snapshot(
    handoff: SourceAtomHandoff,
    compiled: CompiledFrameBatch,
    config: FrameCompilerConfig,
    selection: AtlasArtifactSelection,
    snapshot,
    source_row: dict,
    graph: dict,
    **kwargs,
) -> SourceAtomHandoff:
    expected = _build_source_atom_handoff_from_snapshot(
        compiled, config, selection, snapshot, source_row, graph, **kwargs)
    if handoff != expected:
        _invalid("BAMF_SOURCE_ATOM_HANDOFF_AUTHORITY_DRIFT")
    return expected


def revalidate_source_atom_handoff(
    handoff: SourceAtomHandoff,
    compiled: CompiledFrameBatch,
    config: FrameCompilerConfig,
    selection: AtlasArtifactSelection,
    source_row: dict,
    graph: dict,
    *,
    source_root: str | Path,
    source_seed: int,
    source_each: int,
    course=None,
    source_profile_parameters=None,
) -> SourceAtomHandoff:
    """Rebuild from sources. A caller-supplied digest cannot authenticate itself."""
    snapshot = load_pinned_atlas_snapshot(selection)
    return _revalidate_source_atom_handoff_from_snapshot(
        handoff, compiled, config, selection, snapshot, source_row, graph,
        source_root=source_root, source_seed=source_seed, source_each=source_each,
        course=course, source_profile_parameters=source_profile_parameters)


def _require_embedding_ready_from_snapshot(
    handoff: SourceAtomHandoff,
    compiled: CompiledFrameBatch,
    config: FrameCompilerConfig,
    selection: AtlasArtifactSelection,
    snapshot,
    source_row: dict,
    graph: dict,
    **kwargs,
) -> tuple[tuple[int, tuple[str, ...]], ...]:
    expected = _revalidate_source_atom_handoff_from_snapshot(
        handoff, compiled, config, selection, snapshot, source_row, graph, **kwargs)
    if not expected.embedding_ready:
        _invalid("BAMF_SOURCE_ATOM_BINDING_HELD")
    return tuple(
        (item.candidate_abi_index, item.candidate_type_ids)
        for item in expected.bindings if item.candidate_abi_index is not None)


def require_pinned_embedding_ready(
    handoff: SourceAtomHandoff,
    compiled: CompiledFrameBatch,
    config: FrameCompilerConfig,
    selection: AtlasArtifactSelection,
    source_row: dict,
    graph: dict,
    *,
    source_root: str | Path,
    source_seed: int,
    source_each: int,
    course=None,
    source_profile_parameters=None,
) -> tuple[tuple[int, tuple[str, ...]], ...]:
    """B02/B03 guard. Rebuild from pins before exposing an ABI coordinate."""
    snapshot = load_pinned_atlas_snapshot(selection)
    return _require_embedding_ready_from_snapshot(
        handoff, compiled, config, selection, snapshot, source_row, graph,
        source_root=source_root, source_seed=source_seed, source_each=source_each,
        course=course, source_profile_parameters=source_profile_parameters)
