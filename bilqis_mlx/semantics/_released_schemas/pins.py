"""Released frame-schema pins with source-owned authority."""
from __future__ import annotations
from .._public_identity.facade_dependency import public_facade as _public_facade

def _public():
    return _public_facade("bilqis_mlx.semantics.released_frame_schemas")
import hmac
from pathlib import Path
from ..atlas.snapshot import AtlasArtifactSelection, load_pinned_atlas_snapshot
from ..frame_codec import _canonical_bytes
from ..frame_schema import FrameSchema, frame_schema_from_bytes
from .contracts import (
    _fail, _sha, _json, SOURCE_PIN_REGISTRY_SCHEMA, SOURCE_PIN_REGISTRY_SHA256,
    SOURCE_PIN_STATUS, _SHA,
)
from .models import ReleasedSchemaBodyWitness, VerifiedReleasedFrameSchemas
from .io import load_released_frame_schemas


def _source_pins() -> tuple[dict, ...]:
    """Repository-owned pin ledger, itself hash-pinned like the A01 registry."""
    path = Path(__file__).parents[1] / "frame_schema_source_pins_v1.json"
    if path.is_symlink() or not path.is_file():
        _public()._fail("FRAME_RELEASED_SOURCE_PIN_REGISTRY_MISSING")
    try:
        payload = path.read_bytes()
    except OSError:
        _public()._fail("FRAME_RELEASED_SOURCE_PIN_REGISTRY_MISSING")
    if not hmac.compare_digest(_public()._sha(payload), SOURCE_PIN_REGISTRY_SHA256):
        _public()._fail("FRAME_RELEASED_SOURCE_PIN_REGISTRY_INVALID")
    registry = _public()._json(payload)
    if (set(registry) != {"schema", "entries"}
            or registry["schema"] != SOURCE_PIN_REGISTRY_SCHEMA
            or payload != _public()._canonical_bytes(registry)
            or not isinstance(registry["entries"], list)
            or not registry["entries"]):
        _public()._fail("FRAME_RELEASED_SOURCE_PIN_REGISTRY_INVALID")
    required = {
        "family", "semantic_release", "atlas_bundle_id",
        "source_bundle_id", "schema_manifest_sha256",
        "schema_map_sha256", "source_receipt", "status"}
    for entry in registry["entries"]:
        if (not isinstance(entry, dict) or set(entry) != required
                or not isinstance(entry["family"], str)
                or not entry["family"]
                or any(not isinstance(entry[name], str)
                       or not _SHA.fullmatch(entry[name])
                       for name in (
                           "semantic_release", "atlas_bundle_id",
                           "source_bundle_id", "schema_manifest_sha256",
                           "schema_map_sha256"))
                or entry["status"] != SOURCE_PIN_STATUS
                or entry["source_receipt"]
                != "docs/evidence/bamf/A03.4/receipt.md"):
            _public()._fail("FRAME_RELEASED_SOURCE_PIN_REGISTRY_INVALID")
    entries = tuple(registry["entries"])
    if len({(entry["family"], entry["semantic_release"])
            for entry in entries}) != len(entries):
        _public()._fail("FRAME_RELEASED_SOURCE_PIN_REGISTRY_INVALID")
    return entries



def _load_pinned_released_frame_schemas_from_snapshot(
    source_family: str, atlas_selection: AtlasArtifactSelection, snapshot,
) -> VerifiedReleasedFrameSchemas:
    """Verify A03 pins against an already-authenticated A01 snapshot."""
    if not isinstance(source_family, str) or not source_family:
        _public()._fail("FRAME_RELEASED_SOURCE_FAMILY_INVALID")
    if (not isinstance(atlas_selection, AtlasArtifactSelection)
            or (snapshot.release_sha256, snapshot.bundle_id, snapshot.source_bundle_id)
            != (atlas_selection.release_sha256, atlas_selection.bundle_id,
                atlas_selection.source_bundle_id)):
        _public()._fail("FRAME_RELEASED_SOURCE_PIN_NOT_REGISTERED")
    matches = tuple(entry for entry in _public()._source_pins()
                    if entry["family"] == source_family
                    and entry["semantic_release"] == snapshot.release_sha256
                    and entry["atlas_bundle_id"] == snapshot.bundle_id
                    and entry["source_bundle_id"] == snapshot.source_bundle_id)
    if len(matches) != 1:
        _public()._fail("FRAME_RELEASED_SOURCE_PIN_NOT_REGISTERED")
    entry = matches[0]
    path = (Path(__file__).parents[1] / "frame_schema_releases") / (
        "frame-schemas-" + entry["schema_manifest_sha256"] + ".json")
    if path.is_symlink() or not path.is_file():
        _public()._fail("FRAME_RELEASED_MANIFEST_SOURCE_MISSING")
    try:
        payload = path.read_bytes()
    except OSError:
        _public()._fail("FRAME_RELEASED_MANIFEST_SOURCE_MISSING")
    return _public().load_released_frame_schemas(
        payload, expected_sha256=entry["schema_manifest_sha256"],
        snapshot=snapshot,
        expected_semantic_release=entry["semantic_release"],
        expected_schema_map_sha256=entry["schema_map_sha256"])


def _load_pinned_released_frame_schemas(
    source_family: str, atlas_selection: AtlasArtifactSelection,
) -> VerifiedReleasedFrameSchemas:
    """Offline source-owner lookup; no caller-supplied schema registry or hash."""
    # The cold/public path re-enters the independent A01 pin before A03 can
    # gain authority. Hot owners may call the private snapshot-aware helper
    # only after A01 has already authenticated that exact immutable snapshot.
    snapshot = _public().load_pinned_atlas_snapshot(atlas_selection)
    return _load_pinned_released_frame_schemas_from_snapshot(
        source_family, atlas_selection, snapshot)



def lookup_source_pinned_frame_schema(
    schema_id: str, revision: int, *,
    source_family: str, atlas_selection: AtlasArtifactSelection,
) -> tuple[FrameSchema, ReleasedSchemaBodyWitness]:
    """Resolve an A03 body from repo pins, never from a caller-provided registry."""
    pinned = _public()._load_pinned_released_frame_schemas(
        source_family, atlas_selection)
    witness = pinned.lookup(schema_id, revision)
    body = next(item for item in pinned.manifest.bodies
                if (item.schema_id, item.revision)
                == (schema_id, revision))
    return pinned.require_schema(body.parse(), witness), witness



def verify_source_pinned_frame_schema(
    candidate: FrameSchema, *,
    source_family: str, atlas_selection: AtlasArtifactSelection,
) -> FrameSchema:
    """Production gate: re-enter A01/A03 pins on every candidate verification."""
    if type(candidate) is not FrameSchema:
        _public()._fail("FRAME_RELEASED_SCHEMA_BODY_INVALID")
    from ..released_frame_schemas import lookup_source_pinned_frame_schema

    canonical, _ = lookup_source_pinned_frame_schema(
        candidate.schema_id, candidate.revision,
        source_family=source_family, atlas_selection=atlas_selection)
    if candidate.canonical_bytes() != canonical.canonical_bytes():
        _public()._fail("FRAME_RELEASED_SCHEMA_BODY_MISMATCH")
    return canonical



def verify_source_pinned_frame_schema_bytes(
    payload: bytes, *,
    source_family: str, atlas_selection: AtlasArtifactSelection,
) -> FrameSchema:
    """JSON key order is ignored, but source-pinned role order and body are not."""
    candidate = _public().frame_schema_from_bytes(_public()._canonical_bytes(_public()._json(payload)))
    from ..released_frame_schemas import verify_source_pinned_frame_schema

    return verify_source_pinned_frame_schema(
        candidate, source_family=source_family,
        atlas_selection=atlas_selection)
