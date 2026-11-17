"""Generic frozen generated-cohort adviser artifacts for native BAMF.

These objects are derived teacher artifacts.  Championship state remains the
title authority and the causal student remains the only optimizer lineage.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import uuid

from bilqis_mlx.backup import digest_file
from bilqis_mlx.data_plane import verify_file_digest
from bilqis_mlx.runtime.disk import assert_headroom
from .grade_soup import weighted_average
from .championship_witnesses import championship_role_qualified


SCHEMA = "bilqis.mlx.frozen-generated-cohort-soup/v1"
PARTITIONED_SCHEMA = "bilqis.mlx.partitioned-generated-cohort-soup/v1"
POLICY_ID = "bilqis.bamf.generated-cohort-adviser-policy/v1"


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def cohort_soup_recipe(championship_state: dict, cohort_id: str,
                       admitted_capabilities: tuple[str, ...], *,
                       championship_epoch_sha256: str,
                       cohort_definition_sha256: str,
                       factory_release_sha256: str) -> dict | None:
    """Compile one logical vote per qualifying active title in one cohort."""
    eligible = tuple(admitted_capabilities)
    roles = championship_state.get("active_roles", {})
    if (not isinstance(cohort_id, str) or not cohort_id or not eligible
            or len(set(eligible)) != len(eligible)
            or not isinstance(roles, dict)
            or not isinstance(championship_epoch_sha256, str)
            or len(championship_epoch_sha256) != 64
            or not isinstance(cohort_definition_sha256, str)
            or len(cohort_definition_sha256) != 64
            or not isinstance(factory_release_sha256, str)
            or len(factory_release_sha256) != 64):
        raise ValueError("COHORT_SOUP_RECIPE_INPUT_INVALID")
    chosen = []
    for capability in sorted(eligible):
        role = roles.get(capability)
        if role is None:
            continue
        if (role.get("capability_group") != cohort_id
                or not championship_role_qualified(role)):
            continue
        pointer = role.get("checkpoint")
        if (not isinstance(pointer, dict)
                or not isinstance(pointer.get("sha256"), str)
                or len(pointer["sha256"]) != 64):
            raise ValueError("COHORT_SOUP_ROLE_CHECKPOINT_INVALID")
        chosen.append({
            "capability": capability,
            "checkpoint": dict(pointer),
            "checkpoint_origin_group": role["checkpoint_origin_group"],
            "complete_solver_provenance": dict(role["complete_solver_provenance"]),
        })
    if not chosen:
        return None
    counts = Counter(item["checkpoint"]["sha256"] for item in chosen)
    pointers = {item["checkpoint"]["sha256"]: item["checkpoint"] for item in chosen}
    members = [
        {"checkpoint": dict(pointers[sha256]), "votes": counts[sha256]}
        for sha256 in sorted(counts)
    ]
    contract = {
        "schema": SCHEMA,
        "teacher_policy": POLICY_ID,
        "championship_epoch_sha256": championship_epoch_sha256,
        "cohort_definition_sha256": cohort_definition_sha256,
        "factory_release_sha256": factory_release_sha256,
        "cohort_id": cohort_id,
        "vote_count": len(chosen),
        "covered_capabilities": [item["capability"] for item in chosen],
        "roles": chosen,
        "members": members,
    }
    return {**contract, "recipe_sha256": _digest(contract)}


def partitioned_recipes(full_recipe: dict,
                        member_custody: dict[str, dict]) -> tuple[dict, ...]:
    """Bind soup shards to exact accepted ancestry and compatible graphs."""
    if full_recipe.get("schema") != SCHEMA:
        raise ValueError("COHORT_SOUP_RECIPE_SCHEMA_INVALID")
    groups: dict[str, list[dict]] = {}
    for member in full_recipe["members"]:
        sha256 = member["checkpoint"]["sha256"]
        custody = member_custody.get(sha256)
        if not isinstance(custody, dict):
            raise ValueError("COHORT_SOUP_MEMBER_CUSTODY_INVALID")
        graph = custody.get("source_graph_sha256")
        manifest = custody.get("accepted_manifest_sha256")
        if (not isinstance(graph, str) or len(graph) != 64
                or any(char not in "0123456789abcdef" for char in graph)
                or not isinstance(manifest, str) or len(manifest) != 64
                or any(char not in "0123456789abcdef" for char in manifest)):
            raise ValueError("COHORT_SOUP_GRAPH_IDENTITY_INVALID")
        groups.setdefault(graph, []).append({
            **member,
            "accepted_manifest_sha256": manifest,
            "source_graph_sha256": graph,
        })
    result = []
    for graph, members in sorted(groups.items()):
        shas = {item["checkpoint"]["sha256"] for item in members}
        roles = [item for item in full_recipe["roles"]
                 if item["checkpoint"]["sha256"] in shas]
        contract = {
            key: value for key, value in full_recipe.items()
            if key not in {"recipe_sha256", "vote_count", "covered_capabilities",
                           "roles", "members"}
        }
        contract.update({
            "vote_count": sum(item["votes"] for item in members),
            "covered_capabilities": sorted(item["capability"] for item in roles),
            "roles": roles,
            "members": sorted(members, key=lambda item: item["checkpoint"]["sha256"]),
            "source_graph_sha256": graph,
        })
        result.append({**contract, "recipe_sha256": _digest(contract)})
    if sum(item["vote_count"] for item in result) != full_recipe["vote_count"]:
        raise ValueError("COHORT_SOUP_PARTITION_VOTE_DRIFT")
    return tuple(result)


def _parameter_signature(weights: dict) -> str:
    if not isinstance(weights, dict) or not weights:
        raise ValueError("COHORT_SOUP_WEIGHTS_REQUIRED")
    return _digest(tuple(
        (name, tuple(int(value) for value in array.shape), str(array.dtype))
        for name, array in sorted(weights.items())
    ))


def save_frozen_cohort_soup(run_dir: Path, recipe: dict, weights: dict, *,
                            reserve_gib: float) -> dict:
    """Atomically persist one immutable FP32 weights-only adviser."""
    import mlx.core as mx

    if (recipe.get("schema") != SCHEMA or not recipe.get("recipe_sha256")
            or not weights or any(array.dtype != mx.float32 for array in weights.values())):
        raise ValueError("COHORT_SOUP_FROZEN_INPUT_INVALID")
    run_dir = Path(run_dir)
    root = run_dir / "soups"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("COHORT_SOUP_UNSAFE_DIRECTORY")
    filename = f"cohort-{recipe['recipe_sha256']}.safetensors"
    target = root / filename
    required = sum(value.size * value.itemsize for value in weights.values())
    assert_headroom(target, required_bytes=required + 65536, reserve_gib=reserve_gib)
    root.mkdir(exist_ok=True)
    temporary = root / f".cohort-{uuid.uuid4().hex}.safetensors"
    try:
        mx.save_safetensors(str(temporary), weights)
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        saved = digest_file(temporary)
        if target.exists() or target.is_symlink():
            if target.is_symlink() or digest_file(target) != saved:
                raise ValueError("COHORT_SOUP_EXISTING_ARTIFACT_DRIFT")
        else:
            os.replace(temporary, target)
            folder = os.open(root, os.O_RDONLY)
            try:
                os.fsync(folder)
            finally:
                os.close(folder)
        snapshot = {
            **recipe,
            "filename": str(target.relative_to(run_dir)),
            "sha256": saved,
            "parameter_signature_sha256": _parameter_signature(weights),
            "weight_bytes": required,
        }
        verify_frozen_cohort_soup(run_dir, snapshot)
        return snapshot
    finally:
        if temporary.exists():
            temporary.unlink()


def verify_frozen_cohort_soup(run_dir: Path, snapshot: dict, *,
                              expected_weights: dict | None = None):
    """Fail closed before any cold-resumed adviser inference."""
    import mlx.core as mx

    if snapshot.get("schema") != SCHEMA or not snapshot.get("recipe_sha256"):
        raise ValueError("COHORT_SOUP_SNAPSHOT_INVALID")
    expected = f"soups/cohort-{snapshot['recipe_sha256']}.safetensors"
    if (snapshot.get("filename") != expected
            or not isinstance(snapshot.get("sha256"), str)
            or len(snapshot["sha256"]) != 64):
        raise ValueError("COHORT_SOUP_PATH_INVALID")
    path = Path(run_dir) / expected
    if path.parent.is_symlink() or path.is_symlink() or not path.is_file():
        raise ValueError("COHORT_SOUP_SAVED_ARTIFACT_MISSING")
    if not verify_file_digest(path, snapshot["sha256"]):
        raise ValueError("COHORT_SOUP_SAVED_ARTIFACT_CHANGED")
    weights = mx.load(str(path))
    if (not weights or any(array.dtype != mx.float32 for array in weights.values())
            or _parameter_signature(weights) != snapshot.get("parameter_signature_sha256")):
        raise ValueError("COHORT_SOUP_PARAMETER_GEOMETRY_DRIFT")
    if expected_weights is not None:
        if (set(weights) != set(expected_weights)
                or any(value.dtype != mx.float32 for value in expected_weights.values())
                or any(tuple(weights[name].shape) != tuple(expected_weights[name].shape)
                       or not bool(mx.array_equal(weights[name], expected_weights[name]))
                       for name in weights)):
            raise ValueError("COHORT_SOUP_TRUSTED_RECONSTRUCTION_DRIFT")
    return weights


def read_frozen_cohort_soup(run_dir: Path, recipe: dict, *,
                            expected_weights: dict | None = None) -> dict | None:
    """Read the immutable recipe receipt used for cold-resume verification."""
    if recipe.get("schema") != SCHEMA or not recipe.get("recipe_sha256"):
        raise ValueError("COHORT_SOUP_RECIPE_SCHEMA_INVALID")
    path = Path(run_dir) / "soups" / f"cohort-{recipe['recipe_sha256']}.json"
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("COHORT_SOUP_RECEIPT_UNSAFE")
    try:
        snapshot = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        raise ValueError("COHORT_SOUP_RECEIPT_INVALID") from None
    for key, value in recipe.items():
        if snapshot.get(key) != value:
            raise ValueError("COHORT_SOUP_RECEIPT_RECIPE_DRIFT")
    verify_frozen_cohort_soup(
        run_dir, snapshot, expected_weights=expected_weights)
    return snapshot


def seal_frozen_cohort_soup(run_dir: Path, snapshot: dict) -> Path:
    """Seal the content-addressed recipe receipt after tensor writeback proof."""
    verify_frozen_cohort_soup(run_dir, snapshot)
    run_dir = Path(run_dir)
    root = run_dir / "soups"
    target = root / f"cohort-{snapshot['recipe_sha256']}.json"
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":"),
                     allow_nan=False).encode()
    if target.exists() or target.is_symlink():
        if target.is_symlink() or target.read_bytes() != raw:
            raise ValueError("COHORT_SOUP_RECEIPT_DRIFT")
        return target
    temporary = root / f".cohort-{uuid.uuid4().hex}.json"
    try:
        temporary.write_bytes(raw)
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        folder = os.open(root, os.O_RDONLY)
        try:
            os.fsync(folder)
        finally:
            os.close(folder)
    finally:
        if temporary.exists():
            temporary.unlink()
    return target


def cohort_vote_count(snapshot: dict, target_cohort: str, cohort_count: int) -> float:
    """Versioned generic same/cross-cohort aggregate voice policy."""
    if (snapshot.get("teacher_policy") != POLICY_ID
            or not isinstance(target_cohort, str) or not target_cohort
            or type(cohort_count) is not int or cohort_count < 1
            or type(snapshot.get("vote_count")) is not int
            or snapshot["vote_count"] < 1):
        raise ValueError("COHORT_SOUP_VOTE_SCOPE_INVALID")
    base = snapshot["vote_count"]
    return float(base if snapshot["cohort_id"] == target_cohort else base / cohort_count)


__all__ = (
    "PARTITIONED_SCHEMA", "POLICY_ID", "SCHEMA", "cohort_soup_recipe",
    "cohort_vote_count", "partitioned_recipes", "read_frozen_cohort_soup",
    "save_frozen_cohort_soup", "seal_frozen_cohort_soup",
    "verify_frozen_cohort_soup", "weighted_average",
)
