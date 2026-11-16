"""Owner-derived inputs for the BAMF operator lifecycle boundary."""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.paths import active_run_dir
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactIdentity
from bilqis_mlx.semantics.atlas.snapshot_contracts import (
    ATLAS_SOURCE_PIN_REGISTRY_SCHEMA, ATLAS_SOURCE_PIN_REGISTRY_SHA256,
    _require_registered_source_pin,
)
from bilqis_mlx.semantics.atlas_projection import ATLAS_MANIFEST_SCHEMA, _canonical_bytes


def invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_OPERATOR.INVALID, reason=reason)


def _source_pin_identity(bundle_id: str, release_sha256: str) -> AtlasArtifactIdentity:
    path = Path(__file__).resolve().parents[2] / "semantics/atlas_source_pins_v1.json"
    raw = path.read_bytes()
    try:
        registry = json.loads(raw)
    except (OSError, ValueError, UnicodeError):
        invalid("BAMF_OPERATOR_ATLAS_MANIFEST_SOURCE_INVALID")
    if (sha256(raw).hexdigest() != ATLAS_SOURCE_PIN_REGISTRY_SHA256
            or registry.get("schema") != ATLAS_SOURCE_PIN_REGISTRY_SCHEMA
            or not isinstance(registry.get("entries"), list)):
        invalid("BAMF_OPERATOR_ATLAS_MANIFEST_SOURCE_INVALID")
    matches = tuple(
        entry for entry in registry["entries"]
        if entry.get("bundle_id") == bundle_id
        and entry.get("release_sha256") == release_sha256)
    if len(matches) != 1:
        invalid("BAMF_OPERATOR_ATLAS_MANIFEST_NOT_SOURCE_PINNED")
    identity = AtlasArtifactIdentity(
        bundle_id, release_sha256, matches[0]["source_bundle_id"])
    _require_registered_source_pin(identity)
    return identity


def atlas_manifest_identity(path: Path) -> AtlasArtifactIdentity:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        invalid("BAMF_OPERATOR_ATLAS_MANIFEST_INVALID")
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw)
    except (OSError, ValueError, UnicodeError):
        invalid("BAMF_OPERATOR_ATLAS_MANIFEST_INVALID")
    if (not isinstance(manifest, dict)
            or manifest.get("schema") != ATLAS_MANIFEST_SCHEMA
            or raw != _canonical_bytes(manifest)
            or not isinstance(manifest.get("release_sha256"), str)):
        invalid("BAMF_OPERATOR_ATLAS_MANIFEST_INVALID")
    return _source_pin_identity(sha256(raw).hexdigest(), manifest["release_sha256"])


def foundation_hyperparameters(args, *, required: bool, materialize: bool = True):
    values = (
        args.learning_rate, args.adam_beta1, args.adam_beta2,
        args.adam_eps, args.weight_decay,
    )
    if not any(value is not None for value in values):
        if required:
            invalid("BAMF_OPERATOR_FOUNDATION_OPTIMIZER_REQUIRED")
        return None
    if any(value is None for value in values):
        invalid("BAMF_OPERATOR_FOUNDATION_OPTIMIZER_INCOMPLETE")
    record = {
        "learning_rate": args.learning_rate,
        "betas": (args.adam_beta1, args.adam_beta2),
        "eps": args.adam_eps,
        "weight_decay": args.weight_decay,
    }
    learning_rate = record["learning_rate"]
    beta1, beta2 = record["betas"]
    eps = record["eps"]
    weight_decay = record["weight_decay"]
    values = (learning_rate, beta1, beta2, eps, weight_decay)
    if (any(type(value) not in (int, float) or not math.isfinite(value)
            for value in values)
            or learning_rate <= 0
            or not 0 <= beta1 < 1 or not 0 <= beta2 < 1
            or eps <= 0 or weight_decay < 0):
        invalid("BAMF_OPERATOR_FOUNDATION_OPTIMIZER_INVALID")
    if not materialize:
        return record
    from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters
    return AdamWHyperparameters(
        record["learning_rate"], record["betas"],
        record["eps"], record["weight_decay"])


def source_foundation(source_run=None):
    """Load source graph/Factory bytes without allocating or evaluating MLX arrays."""
    from bilqis_mlx.runtime.admission import _read_executable_factory_release_artifact
    from bilqis_mlx.runtime.mlx_checkpoint import _read_catalog
    from bilqis_mlx.runtime.state import _fingerprint
    from bilqis_mlx.state_dag import read_current

    source = source_run_dir(source_run)
    current = read_current(source)
    release = _read_executable_factory_release_artifact(source, current)
    relative = current.get("model_bundle")
    if not isinstance(relative, str):
        invalid("BAMF_OPERATOR_SOURCE_BUNDLE_REQUIRED")
    bundle = (source / relative).resolve()
    if bundle.parent != (source / "bundles").resolve() or not bundle.is_dir():
        invalid("BAMF_OPERATOR_SOURCE_BUNDLE_INVALID")
    try:
        manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        graph = _read_catalog(bundle, manifest["semantic_catalog"])
    except (OSError, KeyError, ValueError, TypeError):
        invalid("BAMF_OPERATOR_SOURCE_BUNDLE_INVALID")
    release.verify_semantic_catalog(graph)
    if _fingerprint(graph) != current.get("semantic_graph_sha256"):
        invalid("BAMF_OPERATOR_SOURCE_GRAPH_DRIFT")
    return source, release, graph


def source_run_dir(requested=None) -> Path:
    """Return the current source-run path without reconstructing mutable source state."""
    if requested is None:
        return active_run_dir().resolve()
    return Path(requested).expanduser().resolve()


def validate_foundation_authority(source, release, graph, atlas) -> None:
    """Replay the read-only B13 and A01 authorities used by real create."""
    from bilqis_mlx.runtime.bamf_bundle import (
        issue_initial_factory_foundation_authority,
        issue_initial_foundation_feature_authority,
    )
    from bilqis_mlx.semantics.atlas.snapshot import resolve_atlas_artifact_selection

    authority = issue_initial_factory_foundation_authority(source, graph)
    if authority.release != release:
        invalid("BAMF_OPERATOR_SOURCE_FACTORY_AUTHORITY_DRIFT")
    selection = resolve_atlas_artifact_selection(atlas)
    feature_authority = issue_initial_foundation_feature_authority(selection)
    if feature_authority.selection.identity != atlas:
        invalid("BAMF_OPERATOR_ATLAS_SOURCE_AUTHORITY_DRIFT")


__all__ = (
    "atlas_manifest_identity", "foundation_hyperparameters",
    "invalid", "source_foundation", "source_run_dir", "validate_foundation_authority",
)
