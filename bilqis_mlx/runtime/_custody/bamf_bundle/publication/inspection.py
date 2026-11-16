"""Lightweight accepted-generation identity inspection without MLX hydration."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from bilqis_mlx.data_plane import DataPlaneError, SHA256_HEX_LENGTH

from ..records import BAMF_POINTER_SCHEMA, canonical, invalid, sha
from ..run_identity import BamfRunIdentity
from .storage import ACCEPTANCE_DIR, _live_bundle_manifest, _read_pointer


@dataclass(frozen=True)
class AcceptedGenerationInspection:
    """Authenticated identity fields needed by read-only control surfaces."""

    run_id: str
    run_identity_sha256: str
    generation: int
    generation_manifest_sha256: str
    optimizer_step: int
    candidate_identity_sha256: str
    factory_release_sha256: str
    semantic_release_sha256: str
    topology_sha256: str
    acceptance_sha256: str


def inspect_accepted_generation(pointer_path: Path) -> AcceptedGenerationInspection:
    """Read accepted identity metadata without constructing model/optimizer tensors."""
    pointer_path = Path(pointer_path)
    pointer = _read_pointer(pointer_path)
    if pointer is None or pointer.get("schema") != BAMF_POINTER_SCHEMA:
        invalid(DataPlaneError.BUNDLE_ROOT_UNSAFE)
    manifest = _live_bundle_manifest(pointer_path.parent, pointer)
    acceptance_path = (
        pointer_path.parent / ACCEPTANCE_DIR
        / f"{pointer['manifest_sha256']}.json")
    if acceptance_path.is_symlink() or not acceptance_path.is_file():
        invalid("BAMF_GENERATION_ACCEPTANCE_MISSING")
    try:
        acceptance = json.loads(acceptance_path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        invalid("BAMF_GENERATION_ACCEPTANCE_INVALID")
    if (not isinstance(acceptance, dict)
            or acceptance.get("binding_sha256") != pointer["acceptance_sha256"]):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    candidate_identity_sha256 = acceptance.get("candidate_identity_sha256")
    provenance = manifest.get("provenance")
    semantic_release_sha256 = (
        provenance.get("release_digest") if isinstance(provenance, dict) else None)
    public_acceptance = {
        key: value for key, value in acceptance.items()
        if key != "binding_sha256"
    }
    if (sha(canonical(public_acceptance)) != pointer["acceptance_sha256"]
            or acceptance.get("run_id") != pointer["run_id"]
            or acceptance.get("generation") != pointer["generation"]
            or ("optimizer_step" in acceptance
                and acceptance["optimizer_step"] != manifest["optimizer"]["step"])):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    binding = manifest["sidecars"].get("run_identity")
    if not isinstance(binding, dict):
        invalid("BAMF_RUN_IDENTITY_REQUIRED")
    bundle = pointer_path.parent / pointer["bundle"]
    identity_path = bundle / binding.get("filename", "")
    if identity_path.is_symlink() or not identity_path.is_file():
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    raw = identity_path.read_bytes()
    if (sha(raw) != binding.get("sha256")
            or binding.get("sha256") != binding.get("object_sha256")):
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    try:
        identity = BamfRunIdentity.from_record(json.loads(raw))
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        invalid("BAMF_RUN_IDENTITY_INVALID")
    if identity.run_id != pointer["run_id"]:
        invalid("BAMF_RUN_IDENTITY_DRIFT")
    current_factory_release_sha256 = acceptance.get(
        "factory_release_sha256", identity.factory_release_sha256)
    if (not isinstance(candidate_identity_sha256, str)
            or len(candidate_identity_sha256) != SHA256_HEX_LENGTH
            or not isinstance(semantic_release_sha256, str)
            or len(semantic_release_sha256) != SHA256_HEX_LENGTH
            or not isinstance(current_factory_release_sha256, str)
            or len(current_factory_release_sha256) != SHA256_HEX_LENGTH
            or any(
                char not in "0123456789abcdef"
                for value in (
                    candidate_identity_sha256,
                    semantic_release_sha256,
                    current_factory_release_sha256,
                )
                for char in value
            )):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    if _read_pointer(pointer_path) != pointer:
        invalid("BAMF_GENERATION_POINTER_CHANGED_DURING_READ")
    return AcceptedGenerationInspection(
        run_id=pointer["run_id"],
        run_identity_sha256=identity.digest,
        generation=pointer["generation"],
        generation_manifest_sha256=pointer["manifest_sha256"],
        optimizer_step=manifest["optimizer"]["step"],
        candidate_identity_sha256=candidate_identity_sha256,
        factory_release_sha256=current_factory_release_sha256,
        semantic_release_sha256=semantic_release_sha256,
        topology_sha256=identity.initial_topology_digest,
        acceptance_sha256=pointer["acceptance_sha256"],
    )


__all__ = ("AcceptedGenerationInspection", "inspect_accepted_generation")
