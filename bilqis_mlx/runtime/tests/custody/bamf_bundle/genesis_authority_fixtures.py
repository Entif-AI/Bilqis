"""Owner-shaped Factory and Atlas authority fixtures for B13 genesis tests."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from tempfile import mkdtemp
from unittest.mock import patch

from bilqis_mlx.runtime.admission import _executable_factory_admission
from bilqis_mlx.runtime.bamf_bundle import (
    issue_initial_factory_foundation_authority,
    issue_initial_foundation_feature_authority,
)
from bilqis_mlx.runtime.bamf_bundle.feature.replay_support import FeatureMaterialization
import bilqis_mlx.runtime.bamf_bundle.feature_authority as feature_authority
from bilqis_mlx.runtime.bamf_bundle.genesis import foundation as genesis_foundation
from bilqis_mlx.runtime.state import _fingerprint
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.atlas_features import AtlasFeatures, FeatureSchema
from bilqis_mlx.semantics.atlas_projection import FrozenAtlasSnapshot
from bilqis_mlx.semantics.atlas_projection_parts.concepts import AbiEntry
from bilqis_mlx.semantics.atlas_projection_parts.releases import AtlasCounts
from bilqis_mlx.state_dag import persist


ATLAS_RELEASE = "d" * 64
ATLAS_BUNDLE = "e" * 64
SOURCE_BUNDLE = "f" * 64
ACTIVE_SET = "a" * 64


def feature_schema() -> FeatureSchema:
    return FeatureSchema((), (), source_bindings=())


def frozen_snapshot(selection: AtlasArtifactSelection) -> FrozenAtlasSnapshot:
    entry = AbiEntry(0, 0, 0, "fixture.semantic", None, "fixture", True, True, "fixture")
    counts = AtlasCounts(1, 1, 1, 1, 1, 1, 0, 0, 0, 0)
    return FrozenAtlasSnapshot(
        "bilqis.atlas.snapshot/v1", selection.bundle_id,
        selection.release_sha256, selection.source_bundle_id,
        "1" * 64, "2" * 64, "3" * 64, "4" * 64, "5" * 64, "6" * 64,
        ACTIVE_SET, counts, (), (entry,), (), (), (),
        ((entry.semantic_id, 0),), (),
    )


def source_features(*, release: str = ATLAS_RELEASE) -> AtlasFeatures:
    return AtlasFeatures(
        release, ATLAS_BUNDLE, SOURCE_BUNDLE, None, (), (), (), (), ())


@contextmanager
def genesis_feature_source_patch(features: AtlasFeatures | None = None):
    features = source_features() if features is None else features
    schema = feature_schema()

    def source_owned(selection):
        return frozen_snapshot(selection), schema

    with patch.multiple(
            genesis_foundation,
            _source_owned_feature_schema=source_owned,
            build_feature_manifest=lambda snapshot, feature_schema: features):
        yield


@contextmanager
def accepted_feature_source_patch(features: AtlasFeatures | None = None):
    """Replay one synthetic accepted Atlas source without production pin lookup."""
    features = source_features() if features is None else features
    selection = AtlasArtifactSelection(
        "/fixture/atlas", features.atlas_bundle_id,
        features.semantic_release, features.source_bundle_id)
    materialization = FeatureMaterialization(
        selection, frozen_snapshot(selection), feature_schema(), features)
    with patch.object(
            feature_authority, "_authenticate_features",
            return_value=features), patch.object(
            feature_authority, "_authenticate_feature_materialization",
            return_value=materialization):
        yield


def issue_feature_authority(features: AtlasFeatures | None = None):
    features = source_features() if features is None else features
    selection = AtlasArtifactSelection(
        "/fixture/atlas", features.atlas_bundle_id,
        features.semantic_release, features.source_bundle_id)
    with genesis_feature_source_patch(features):
        return issue_initial_foundation_feature_authority(selection)


def issue_factory_authority(release, graph, origin):
    root = Path(mkdtemp(prefix="bamf-genesis-source-"))
    _, release_file, admission = _executable_factory_admission(
        root, release, origin, _fingerprint(graph), graph)
    receipt = {
        "generation": 0,
        "factory_release_sha256": release.release_sha256,
        "factory_release_file": release_file,
        "factory_admission_v2": asdict(admission),
        "semantic_graph_sha256": _fingerprint(graph),
        "school": {"current_student": asdict(origin)},
    }
    persist(root, receipt)
    return issue_initial_factory_foundation_authority(root, graph)


__all__ = (
    "ACTIVE_SET", "ATLAS_BUNDLE", "ATLAS_RELEASE", "SOURCE_BUNDLE",
    "accepted_feature_source_patch", "frozen_snapshot",
    "genesis_feature_source_patch", "issue_factory_authority",
    "issue_feature_authority", "source_features",
)
