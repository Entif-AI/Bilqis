"""Typed B13 feature-context records."""
from __future__ import annotations

from dataclasses import dataclass, field

from bilqis_mlx.semantics.atlas_features import FeatureSchema
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.atlas_projection import FrozenAtlasSnapshot

from ..records import invalid
from .receipt import AcceptedGenerationFeatureReceipt


_FEATURE_CONTEXT_ISSUER = object()


def _validate_materialized_context(selection, snapshot, schema, features) -> None:
    if (type(selection) is not AtlasArtifactSelection
            or type(snapshot) is not FrozenAtlasSnapshot
            or type(schema) is not FeatureSchema
            or features.semantic_release != selection.release_sha256
            or features.atlas_bundle_id != selection.bundle_id
            or features.source_bundle_id != selection.source_bundle_id
            or snapshot.release_sha256 != selection.release_sha256
            or snapshot.bundle_id != selection.bundle_id
            or snapshot.source_bundle_id != selection.source_bundle_id):
        invalid("BAMF_FEATURE_CONTEXT_INVALID")


@dataclass(frozen=True, init=False)
class AuthenticatedCandidateFeatureContext:
    """Source-replayed feature inputs for pre-acceptance evaluation only."""

    selection: AtlasArtifactSelection
    snapshot: FrozenAtlasSnapshot
    schema: FeatureSchema
    features: object
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        invalid("BAMF_FEATURE_CONTEXT_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self) -> None:
        if self._issuance is not _FEATURE_CONTEXT_ISSUER:
            invalid("BAMF_FEATURE_CONTEXT_INVALID")
        _validate_materialized_context(
            self.selection, self.snapshot, self.schema, self.features)


@dataclass(frozen=True, init=False)
class AuthenticatedGenerationFeatureContext:
    """Source-replayed feature inputs backed by accepted-generation custody."""

    selection: AtlasArtifactSelection
    snapshot: FrozenAtlasSnapshot
    schema: FeatureSchema
    features: object
    receipt: AcceptedGenerationFeatureReceipt
    atlas_reload_count: int
    feature_manifest_rebuild_count: int
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        invalid("BAMF_ACCEPTED_FEATURE_CONTEXT_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self) -> None:
        if self._issuance is not _FEATURE_CONTEXT_ISSUER:
            invalid("BAMF_ACCEPTED_FEATURE_CONTEXT_INVALID")
        _validate_materialized_context(
            self.selection, self.snapshot, self.schema, self.features)
        if (type(self.receipt) is not AcceptedGenerationFeatureReceipt
                or self.receipt.semantic_release != self.features.semantic_release
                or self.receipt.feature_sha256 != self.features.digest
                or type(self.atlas_reload_count) is not int
                or self.atlas_reload_count < 1
                or type(self.feature_manifest_rebuild_count) is not int
                or self.feature_manifest_rebuild_count < 1):
            invalid("BAMF_ACCEPTED_FEATURE_CONTEXT_INVALID")


def _issue_candidate_feature_context(
        selection, snapshot, schema, features) -> AuthenticatedCandidateFeatureContext:
    context = object.__new__(AuthenticatedCandidateFeatureContext)
    for name, value in (
            ("selection", selection), ("snapshot", snapshot), ("schema", schema),
            ("features", features), ("_issuance", _FEATURE_CONTEXT_ISSUER)):
        object.__setattr__(context, name, value)
    context.__post_init__()
    return context


def _issue_generation_feature_context(
        selection, snapshot, schema, features,
        receipt, *, atlas_reload_count=1,
        feature_manifest_rebuild_count=1) -> AuthenticatedGenerationFeatureContext:
    context = object.__new__(AuthenticatedGenerationFeatureContext)
    for name, value in (
            ("selection", selection), ("snapshot", snapshot), ("schema", schema),
            ("features", features), ("receipt", receipt),
            ("atlas_reload_count", atlas_reload_count),
            ("feature_manifest_rebuild_count", feature_manifest_rebuild_count),
            ("_issuance", _FEATURE_CONTEXT_ISSUER)):
        object.__setattr__(context, name, value)
    context.__post_init__()
    return context


@dataclass(frozen=True)
class AcceptedGenerationFeatureContext:
    """Typed B13 replay context for one accepted generation."""

    receipt: AcceptedGenerationFeatureReceipt
    features: object
    predecessor_features: object | None
    construction_predecessor: object | None
