"""Verified, database-free readback for immutable semantic Atlas artifacts."""
from __future__ import annotations

from ..atlas_projection import FrozenAtlasSnapshot
from bilqis_mlx.b11_observation import note_atlas_reload
from .snapshot_contracts import (
    AtlasArtifactIdentity, AtlasArtifactSelection, _require_registered_source_pin,
    resolve_atlas_artifact_selection,
)
from .snapshot_materialize import load_atlas_snapshot


def load_pinned_atlas_snapshot(selection: AtlasArtifactSelection) -> FrozenAtlasSnapshot:
    """Reload a source artifact only under an independently governed A01 pin."""
    note_atlas_reload()
    _require_registered_source_pin(selection)
    return load_atlas_snapshot(
        selection.path,
        expected_bundle_id=selection.bundle_id,
        expected_release_sha256=selection.release_sha256,
        expected_source_bundle_id=selection.source_bundle_id,
    )


__all__ = (
    "AtlasArtifactIdentity",
    "AtlasArtifactSelection",
    "load_atlas_snapshot",
    "load_pinned_atlas_snapshot",
    "resolve_atlas_artifact_selection",
)
