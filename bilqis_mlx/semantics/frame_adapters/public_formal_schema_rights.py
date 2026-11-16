"""A13 owner authority for current PUBLIC_FORMAL motif-schema rights."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib

from ..atlas.snapshot import AtlasArtifactSelection
from ..context_eligibility import (
    PUBLIC_FORMAL, ApprovedContextProjection, SourceFrontier, SourceGrant,
)
from ..frame_schema import FrameInstance, FrameSchema, SourceSpan
from ..atlas_projection import FrozenAtlasSnapshot
from ..released_frame_schemas import (
    _load_pinned_released_frame_schemas_from_snapshot,
    lookup_source_pinned_frame_schema,
)
from .common import _adapter_fail
from .public_formal_sources import _require_public_formal_projection_authority
from . import public_formal_schema_rights_registry as _registry


AUTHORITY_SCHEMA = "bilqis.public-formal-schema-rights-authority/v1"
IDENTITY_SCHEMA = "bilqis.public-formal-schema-rights-identity/v1"
_ISSUER = object()


def _fail(reason: str, adapter_id: str = "<schema-rights>") -> None:
    _adapter_fail(reason, adapter_id, SourceSpan(0, 0), "<schema>")


@dataclass(frozen=True, init=False)
class SourceSchemaRightsAuthority:
    """Opaque source-owner view of the current schema-right decision registry."""

    atlas_selection: AtlasArtifactSelection
    rights_epoch: int
    correction_generation: int
    registry_sha256: str
    schema: str = AUTHORITY_SCHEMA
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self) -> None:
        registry = _registry._load_registry()
        selection = self.atlas_selection
        if type(selection) is not AtlasArtifactSelection:
            _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_SOURCE_REQUIRED")
        selection.__post_init__()
        if (
            getattr(self, "_issuance", None) is not _ISSUER
            or (selection.bundle_id, selection.release_sha256, selection.source_bundle_id)
            != (
                registry["atlas_bundle_id"], registry["semantic_release"],
                registry["source_bundle_id"],
            )
            or self.rights_epoch != registry["rights_epoch"]
            or self.correction_generation != registry["correction_generation"]
            or self.registry_sha256 != _registry._REGISTRY_SHA256
            or self.schema != AUTHORITY_SCHEMA
        ):
            _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_AUTHORITY_INVALID")


def issue_source_schema_rights_authority(
    atlas_selection: AtlasArtifactSelection,
) -> SourceSchemaRightsAuthority:
    """Issue current rights only from the hash-pinned A13 owner registry."""
    if type(atlas_selection) is not AtlasArtifactSelection:
        _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_SOURCE_REQUIRED")
    atlas_selection.__post_init__()
    registry = _registry._load_registry()
    expected = (
        registry["atlas_bundle_id"], registry["semantic_release"],
        registry["source_bundle_id"],
    )
    if expected != (
        atlas_selection.bundle_id, atlas_selection.release_sha256,
        atlas_selection.source_bundle_id,
    ):
        _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_SOURCE_NOT_AUTHORIZED")
    authority = object.__new__(SourceSchemaRightsAuthority)
    for name, value in (
        ("atlas_selection", atlas_selection),
        ("rights_epoch", registry["rights_epoch"]),
        ("correction_generation", registry["correction_generation"]),
        ("registry_sha256", _registry._REGISTRY_SHA256),
        ("schema", AUTHORITY_SCHEMA),
        ("_issuance", _ISSUER),
    ):
        object.__setattr__(authority, name, value)
    authority.__post_init__()
    return authority


def source_schema_rights_frontier(
    authority: SourceSchemaRightsAuthority,
) -> SourceFrontier:
    """Project only the owner-current epochs; schema grants are rederived on use."""
    if type(authority) is not SourceSchemaRightsAuthority:
        _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_AUTHORITY_REQUIRED")
    authority.__post_init__()
    return SourceFrontier(
        authority.rights_epoch, authority.correction_generation, ())


def schema_source_handle(schema: FrameSchema) -> str:
    if type(schema) is not FrameSchema:
        _fail("FRAME_SCHEMA_REQUIRED")
    return f"source:motif-schema:{schema.identity}"


def schema_evidence_digest(schema: FrameSchema) -> str:
    if type(schema) is not FrameSchema:
        _fail("FRAME_SCHEMA_REQUIRED")
    return hashlib.sha256(schema.canonical_bytes()).hexdigest()


def _decision(authority, source_adapter_id, frame: FrameInstance, *, snapshot=None):
    from ..atlas_features.formal import source_family_for_adapter

    family = source_family_for_adapter(source_adapter_id)
    if snapshot is None:
        schema, _witness = lookup_source_pinned_frame_schema(
            frame.frame_schema_id, frame.frame_schema_revision, source_family=family,
            atlas_selection=authority.atlas_selection)
    else:
        selection = authority.atlas_selection
        if (type(snapshot) is not FrozenAtlasSnapshot
                or (snapshot.release_sha256, snapshot.bundle_id,
                    snapshot.source_bundle_id) != (
                        selection.release_sha256, selection.bundle_id,
                        selection.source_bundle_id)):
            _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_SOURCE_DRIFT", source_adapter_id)
        pinned = _load_pinned_released_frame_schemas_from_snapshot(
            family, selection, snapshot)
        witness = pinned.lookup(frame.frame_schema_id, frame.frame_schema_revision)
        body = next((
            item for item in pinned.manifest.bodies
            if (item.schema_id, item.revision)
            == (frame.frame_schema_id, frame.frame_schema_revision)
        ), None)
        if body is None:
            _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_EVIDENCE_DRIFT", source_adapter_id)
        schema = pinned.require_schema(body.parse(), witness)
    evidence = schema_evidence_digest(schema)
    matches = tuple(
        entry for entry in _registry._load_registry()["entries"]
        if (entry["family"], entry["schema_id"], entry["revision"])
        == (family, frame.frame_schema_id, frame.frame_schema_revision)
    )
    if len(matches) != 1 or matches[0]["evidence_sha256"] != evidence:
        _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_EVIDENCE_DRIFT", source_adapter_id)
    return schema, _registry._effective_revoked(matches[0], authority.rights_epoch)


def _current_source_schema_grant(
    authority: SourceSchemaRightsAuthority,
    source_adapter_id: str,
    projection: ApprovedContextProjection,
    frame: FrameInstance,
    *,
    snapshot=None,
) -> SourceGrant:
    """Materialize rights only for a frame already present in an approved source projection."""
    if type(authority) is not SourceSchemaRightsAuthority:
        _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_AUTHORITY_REQUIRED", source_adapter_id)
    authority.__post_init__()
    if (not isinstance(source_adapter_id, str) or not source_adapter_id
            or type(projection) is not ApprovedContextProjection
            or type(frame) is not FrameInstance):
        _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_SCOPE_INVALID", source_adapter_id)
    projection.__post_init__()
    _require_public_formal_projection_authority(projection, source_adapter_id)
    envelopes = tuple(
        envelope for envelope in projection.envelopes
        if envelope.frame == frame
    )
    if len(envelopes) != 1:
        _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_FRAME_NOT_APPROVED", source_adapter_id)
    envelope = envelopes[0]
    if (
        envelope.source_regime != PUBLIC_FORMAL
        or envelope.semantic_release != authority.atlas_selection.release_sha256
        or envelope.rights_epoch != authority.rights_epoch
        or envelope.correction_generation != authority.correction_generation
        or envelope.purpose is None
        or not envelope.frame_handle.startswith(
            "public-formal:" + source_adapter_id + ":")
    ):
        _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_SCOPE_INVALID", source_adapter_id)
    schema, revoked = _decision(
        authority, source_adapter_id, frame, snapshot=snapshot)
    return SourceGrant(
        schema_source_handle(schema), envelope.principal_id, envelope.tenant_id,
        envelope.source_regime, envelope.semantic_release, schema_evidence_digest(schema),
        (envelope.purpose,), (envelope.jurisdiction,), (envelope.scope,),
        authority.rights_epoch, authority.correction_generation,
        envelope.observed_at, envelope.effective_from, envelope.effective_until,
        revoked=revoked,
    )


def current_source_schema_grant(
    authority: SourceSchemaRightsAuthority,
    source_adapter_id: str,
    projection: ApprovedContextProjection,
    frame: FrameInstance,
) -> SourceGrant:
    """Cold public grant path; re-enters the independently pinned A01 owner."""
    return _current_source_schema_grant(
        authority, source_adapter_id, projection, frame)


def _current_source_schema_grant_from_snapshot(
    authority: SourceSchemaRightsAuthority,
    source_adapter_id: str,
    projection: ApprovedContextProjection,
    frame: FrameInstance,
    snapshot: FrozenAtlasSnapshot,
) -> SourceGrant:
    """Hot owner path after the exact immutable A01 snapshot is authenticated."""
    return _current_source_schema_grant(
        authority, source_adapter_id, projection, frame, snapshot=snapshot)


def source_schema_rights_identity(authority: SourceSchemaRightsAuthority) -> dict:
    if type(authority) is not SourceSchemaRightsAuthority:
        _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_AUTHORITY_REQUIRED")
    authority.__post_init__()
    return {
        "atlas_bundle_id": authority.atlas_selection.bundle_id,
        "semantic_release": authority.atlas_selection.release_sha256,
        "source_bundle_id": authority.atlas_selection.source_bundle_id,
        "rights_epoch": authority.rights_epoch,
        "correction_generation": authority.correction_generation,
        "registry_sha256": authority.registry_sha256,
        "schema": IDENTITY_SCHEMA,
    }


def validate_source_schema_rights_identity(
    value: dict,
    atlas_selection: AtlasArtifactSelection,
) -> SourceSchemaRightsAuthority:
    authority = issue_source_schema_rights_authority(atlas_selection)
    if type(value) is not dict or value != source_schema_rights_identity(authority):
        _fail("BAMF_CONTEXT_SCHEMA_RIGHTS_IDENTITY_INVALID")
    return authority


__all__ = (
    "SourceSchemaRightsAuthority", "current_source_schema_grant",
    "issue_source_schema_rights_authority", "schema_evidence_digest",
    "schema_source_handle", "source_schema_rights_frontier",
    "source_schema_rights_identity", "validate_source_schema_rights_identity",
)
