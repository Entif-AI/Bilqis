"""Source-qualified public boundary preserving the no-hit quarantine."""
from __future__ import annotations

from dataclasses import asdict

import mlx.core as mx

from bilqis_mlx.semantics.context_eligibility import ApprovedContextProjection, ContextHold, ContextPolicy, SourceFrontier, TaskScope, project_context
from bilqis_mlx.semantics.frame_schema import AtomicFrame
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.released_frame_schemas import (
    lookup_source_pinned_frame_schema,
)
from ..atlas_engram import MotifManifest


from .records import _invalid, _SHA, WIDTH, READ_TENSOR_RANK, FEATURE_AXIS, MotifReadPosition, MotifReadResult

def _source_witnesses(row, projection, atlas_selection):
    source_witnesses = []
    row_status = []
    for item in row:
        if item is None or type(item.envelope.frame) is AtomicFrame:
            row_status.append("MISS")
            continue
        if item.schema is None or item.source_family is None:
            _invalid()
        canonical, witness = lookup_source_pinned_frame_schema(
            item.schema.schema_id, item.schema.revision,
            source_family=item.source_family,
            atlas_selection=atlas_selection,
        )
        if item.schema.canonical_bytes() != canonical.canonical_bytes():
            _invalid()
        if (projection.frame(item.envelope.frame_handle)
                != item.envelope.frame):
            _invalid()
        source_witnesses.append((item.source_family, asdict(witness)))
        row_status.append("QUARANTINED_NO_HIT")

    return source_witnesses, row_status


def _validate_guarded_inputs(
    site_index, hidden, positions, tasks, frontiers, policies, manifest,
    atlas_selection, retained_generation_digest, parameter_tree_digest,
    expected_cache_digests,
):
    if (site_index != 1
            or not isinstance(hidden, mx.array)
            or hidden.ndim != READ_TENSOR_RANK
            or hidden.shape[FEATURE_AXIS] != WIDTH
            or hidden.dtype != mx.float32
            or type(manifest) is not MotifManifest
            or type(atlas_selection) is not AtlasArtifactSelection
            or not isinstance(positions, tuple)
            or not isinstance(tasks, tuple)
            or not isinstance(frontiers, tuple)
            or not isinstance(policies, tuple)
            or not (len(positions) == len(tasks) == len(frontiers)
                    == len(policies) == hidden.shape[0])
            or any(not isinstance(value, str) or not _SHA.fullmatch(value)
                   for value in (retained_generation_digest,
                                 parameter_tree_digest))
            or (expected_cache_digests is not None
                and (not isinstance(expected_cache_digests, tuple)
                     or len(expected_cache_digests) != hidden.shape[0]
                     or any(value is not None
                            and (not isinstance(value, str)
                                 or not _SHA.fullmatch(value))
                            for value in expected_cache_digests)))):
        _invalid()


def read_motif(
    *,
    site_index: int,
    hidden: mx.array,
    positions: tuple[tuple[MotifReadPosition | None, ...], ...],
    tasks: tuple[TaskScope, ...],
    frontiers: tuple[SourceFrontier, ...],
    policies: tuple[ContextPolicy, ...],
    manifest: MotifManifest,
    atlas_selection: AtlasArtifactSelection,
    retained_generation_digest: str,
    parameter_tree_digest: str,
    expected_cache_digests: tuple[str | None, ...] | None = None,
) -> MotifReadResult:
    """Source-qualified group-1 second motif boundary, quarantined to no-hit.

    A03.4 is now present in reviewed unified. The public boundary remains
    quarantined pending source/feature/retained-parameter qualification.
    Every non-atomic frame re-enters the repository-owned A03.4 source pins and
    current A13 eligibility.  The returned cache identity binds those source
    witnesses, live rights state, manifest, retained generation and parameter
    tree.  None of those caller-visible digests can authorize a motif hit here:
    while that qualification remains open, the public path returns the exact
    input tensor with an explicit QUARANTINED_NO_HIT disposition.
    """
    _validate_guarded_inputs(
        site_index, hidden, positions, tasks, frontiers, policies, manifest,
        atlas_selection, retained_generation_digest, parameter_tree_digest,
        expected_cache_digests)

    dispositions = []
    cache_digests = []
    for row_index, row in enumerate(positions):
        if (not isinstance(row, tuple) or len(row) != hidden.shape[1]
                or any(item is not None and type(item) is not MotifReadPosition
                       for item in row)):
            _invalid()
        envelopes = tuple(item.envelope for item in row if item is not None)
        if not envelopes:
            dispositions.append(("MISS",) * hidden.shape[1])
            cache_digests.append(None)
            continue
        task, frontier, policy = (
            tasks[row_index], frontiers[row_index], policies[row_index])
        projection = project_context(envelopes, task, frontier, policy)
        if isinstance(projection, ContextHold):
            dispositions.append(tuple(
                "HELD" if item is not None else "MISS" for item in row))
            cache_digests.append(None)
            continue
        if type(projection) is not ApprovedContextProjection:
            _invalid()

        source_witnesses, row_status = _source_witnesses(
            row, projection, atlas_selection)

        cache_digests.append(projection.cache_key(
            "B08.1_GROUP1_SECOND_MOTIF_NO_HIT",
            site_index,
            tuple(source_witnesses),
            manifest.digest,
            retained_generation_digest,
            parameter_tree_digest,
            atlas_selection.bundle_id,
            atlas_selection.source_bundle_id,
        ))
        dispositions.append(tuple(row_status))

    cache_digests = tuple(cache_digests)
    if (expected_cache_digests is not None
            and expected_cache_digests != cache_digests):
        _invalid()
    return MotifReadResult(
        hidden, tuple(dispositions), (), cache_digests,
        tuple(() for _ in dispositions))
