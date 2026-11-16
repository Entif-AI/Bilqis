"""Frozen, capability-vote-weighted grade soups from intact champion models.

Soup tensors are an advisory teacher only: no optimizer moments, student
substitution, graduation scores, or writes to underlying champion bundles.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

from bilqis_mlx.backup import digest_file
from bilqis_mlx.data_plane import verify_file_digest
from bilqis_mlx.runtime.disk import assert_headroom
from .championship_witnesses import maxed_role


SCHEMA = "bilqis.mlx.frozen-grade-soup/v1"
PARTITIONED_SCHEMA = "bilqis.mlx.partitioned-frozen-grade-soup/v2"


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                   separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def grade_soup_recipe(frontier: dict, grade: str,
                      admitted_capabilities: tuple[str, ...]) -> dict | None:
    """One vote per active capability champion, perfect or not yet perfect."""
    eligible = tuple(admitted_capabilities)
    if (not grade or not eligible or len(set(eligible)) != len(eligible) or
            any(not cap.startswith(grade + ".") for cap in eligible)):
        raise ValueError("GRADE_SOUP_INVALID_ADMITTED_CAPABILITIES")
    chosen = {}
    for entry in frontier.values():
        capability = entry.get("capability")
        if capability not in eligible:
            continue
        breadth, mastered = entry.get("breadth"), entry.get("perfect_capabilities")
        pointer = entry["checkpoint"]
        correct, total = entry.get("correct"), entry.get("total")
        if (type(correct) is not int or type(total) is not int or
                total <= 0 or not 0 <= correct <= total or
                type(breadth) is not int or breadth < 0 or
                not isinstance(mastered, list) or len(mastered) != breadth or
                len(set(mastered)) != breadth or
                ((correct == total) != (capability in mastered)) or
                not pointer.get("model_and_native_adamw") or
                len(pointer["sha256"]) != 64):
            raise ValueError("GRADE_SOUP_UNVERIFIED_CHAMPION")
        prior = chosen.get(capability)
        key = (-Fraction(correct, total), -breadth,
               pointer["optimizer_step"], pointer["sha256"])
        if prior is None or key < prior[0]:
            chosen[capability] = (key, entry)
    if not chosen:
        return None
    roles = [{"capability": capability,
              "rubric": chosen[capability][1]["rubric"],
              "correct": chosen[capability][1]["correct"],
              "total": chosen[capability][1]["total"],
              "maxed": maxed_role(chosen[capability][1]),
              "checkpoint_sha256": chosen[capability][1]["checkpoint"]["sha256"]}
             for capability in sorted(chosen)]
    counters = Counter(role["checkpoint_sha256"] for role in roles)
    pointers = {entry["checkpoint"]["sha256"]: entry["checkpoint"]
                for _, entry in chosen.values()}
    members = [{"checkpoint": dict(pointers[sha]), "votes": counters[sha]}
               for sha in sorted(counters)]
    count = len(roles)
    perfect = sorted(role["capability"] for role in roles
                     if role["maxed"])
    contract = {"schema": SCHEMA, "grade": grade, "vote_count": count,
                "coverage_peak": count, "covered_capabilities": sorted(chosen),
                "perfect_capabilities": perfect,
                "roles": roles, "members": members}
    return {**contract, "recipe_sha256": _digest(contract)}


def needs_refresh(existing: dict | None, recipe: dict | None) -> bool:
    if recipe is None:
        return False
    if existing is None:
        return True
    if (existing.get("schema") not in (SCHEMA, PARTITIONED_SCHEMA) or
            existing.get("grade") != recipe["grade"]):
        raise ValueError("GRADE_SOUP_EXISTING_SCHEMA_DRIFT")
    if recipe["vote_count"] < existing.get("coverage_peak", 0):
        raise ValueError("GRADE_SOUP_COVERAGE_PEAK_REGRESSED")
    return recipe["recipe_sha256"] != existing.get("recipe_sha256")


def partitioned_recipe(full_recipe: dict, member_graph_digests: dict[str, str]) -> tuple[dict, ...]:
    """Partition existing capability votes by *exact* source-graph identity.

    Historical semantic prefixes remain valid mentors; they are never
    misrepresented as native owners of newly appended output token rows.
    Each same-graph group gets its own immutable v1 weights-only snapshot.
    The aggregate v2 receipt retains the full original vote recipe.
    """
    if full_recipe.get("schema") != SCHEMA:
        raise ValueError("GRADE_SOUP_PARTITION_UNRECOGNIZED_RECIPE")
    shards = {}
    for member in full_recipe["members"]:
        sha = member["checkpoint"]["sha256"]
        graph = member_graph_digests.get(sha)
        if (not isinstance(graph, str) or len(graph) != 64 or
                any(c not in "0123456789abcdef" for c in graph)):
            raise ValueError("GRADE_SOUP_PARTITION_GRAPH_UNVERIFIED")
        shards.setdefault(graph, []).append(member)
    output = []
    for graph in sorted(shards):
        members = sorted(shards[graph],
                         key=lambda item: item["checkpoint"]["sha256"])
        shas = {item["checkpoint"]["sha256"] for item in members}
        roles = [role for role in full_recipe["roles"]
                 if role["checkpoint_sha256"] in shas]
        vote_count = sum(item["votes"] for item in members)
        if len(roles) != vote_count:
            raise ValueError("GRADE_SOUP_PARTITION_VOTE_DRIFT")
        shard = {
            "schema": SCHEMA, "grade": full_recipe["grade"],
            "vote_count": vote_count, "coverage_peak": vote_count,
            "covered_capabilities": sorted(role["capability"] for role in roles),
            "perfect_capabilities": sorted(
                role["capability"] for role in roles
                if role.get("maxed", role["correct"] == role["total"])),
            "roles": roles, "members": members,
        }
        output.append({**shard, "recipe_sha256": _digest(shard),
                       "source_graph_sha256": graph})
    if sum(shard["vote_count"] for shard in output) != full_recipe["vote_count"]:
        raise ValueError("GRADE_SOUP_PARTITION_LOST_VOTES")
    return tuple(output)


def soup_shards(snapshot: dict) -> tuple[dict, ...]:
    """Expose physically eligible frozen teachers, never a mixed tensor blob."""
    if snapshot.get("schema") == SCHEMA:
        return (snapshot,)
    if snapshot.get("schema") == PARTITIONED_SCHEMA:
        shards = snapshot.get("shards")
        if (not isinstance(shards, list) or len(shards) < 2 or
                any(sh.get("schema") != SCHEMA or sh.get("grade") != snapshot["grade"]
                    for sh in shards) or
                sum(sh["vote_count"] for sh in shards) != snapshot["vote_count"]):
            raise ValueError("GRADE_SOUP_PARTITIONED_SNAPSHOT_DRIFT")
        return tuple(shards)
    raise ValueError("GRADE_SOUP_SAVED_SCHEMA_DRIFT")


def soup_vote_count(snapshot: dict, question_grade: str, total_grades: int) -> float:
    if (not question_grade or type(total_grades) is not int or total_grades < 1 or
            type(snapshot.get("vote_count")) is not int or
            snapshot["vote_count"] < 1 or not snapshot.get("grade")):
        raise ValueError("GRADE_SOUP_INVALID_VOTE_SCOPE")
    base = snapshot["vote_count"]
    return float(base if question_grade == snapshot["grade"] else base / total_grades)


def weighted_average(mx, members) -> dict:
    """Average frozen FP32 tensors weighted by represented capability roles."""
    total = 0
    merged = None
    for votes, weights in members:
        if type(votes) is not int or votes < 1 or not isinstance(weights, dict):
            raise ValueError("GRADE_SOUP_INVALID_INGREDIENT")
        if merged is None:
            if not weights or any(value.dtype != mx.float32 for value in weights.values()):
                raise ValueError("GRADE_SOUP_REQUIRES_FP32_WEIGHTS")
            merged = {name: value * votes for name, value in weights.items()}
        else:
            if (set(weights) != set(merged) or
                    any(value.dtype != mx.float32 or value.shape != merged[name].shape
                        for name, value in weights.items())):
                raise ValueError("GRADE_SOUP_PARAMETER_GEOMETRY_DRIFT")
            merged = {name: value * votes + merged[name]
                      for name, value in weights.items()}
        total += votes
    if not total:
        raise ValueError("GRADE_SOUP_NO_INGREDIENTS")
    result = {key: value / total for key, value in merged.items()}
    mx.eval(result)
    return result


def save_frozen_soup(run_dir: Path, recipe: dict, weights: dict,
                     *, reserve_gib: float, token_count: int) -> dict:
    """Write a deterministic frozen weights-only snapshot before state commit."""
    import mlx.core as mx
    run_dir = Path(run_dir)
    root = run_dir / "soups"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("GRADE_SOUP_UNSAFE_DIRECTORY")
    if (recipe.get("schema") != SCHEMA or not recipe.get("recipe_sha256") or
            not weights or any(array.dtype != mx.float32 for array in weights.values()) or
            type(token_count) is not int or token_count < 1 or
            int(weights["embedding.weight"].shape[0]) != token_count):
        raise ValueError("GRADE_SOUP_INVALID_FROZEN_TENSORS")
    name = f"{recipe['grade']}-{recipe['recipe_sha256']}.safetensors"
    target = root / name
    required = sum(value.size * value.itemsize for value in weights.values())
    assert_headroom(target, required_bytes=required + 65536, reserve_gib=reserve_gib)
    root.mkdir(exist_ok=True)
    temporary = root / f".{recipe['grade']}-{uuid.uuid4().hex}.safetensors"
    try:
        mx.save_safetensors(str(temporary), weights)
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        saved_digest = digest_file(temporary)
        if target.exists() or target.is_symlink():
            if target.is_symlink() or digest_file(target) != saved_digest:
                raise ValueError("GRADE_SOUP_EXISTING_RECIPE_DRIFT")
        else:
            os.replace(temporary, target)
            folder = os.open(root, os.O_RDONLY)
            try:
                os.fsync(folder)
            finally:
                os.close(folder)
        verified = mx.load(str(target))
        if (set(verified) != set(weights) or
                any(not bool(mx.allclose(verified[key], value, atol=0, rtol=0))
                    for key, value in weights.items())):
            raise ValueError("GRADE_SOUP_WRITEBACK_TENSOR_DRIFT")
        return {**recipe, "filename": str(target.relative_to(run_dir)),
                "sha256": saved_digest, "token_count": token_count,
                "weight_bytes": required}
    finally:
        if temporary.exists():
            temporary.unlink()


def verify_frozen_soup(run_dir: Path, snapshot: dict) -> Path:
    """Read-only custody proof for a currently referenced immutable soup."""
    if snapshot.get("schema") == PARTITIONED_SCHEMA:
        for shard in soup_shards(snapshot):
            verify_frozen_soup(run_dir, shard)
        return Path(run_dir) / "soups"
    if snapshot.get("schema") != SCHEMA or not snapshot.get("recipe_sha256"):
        raise ValueError("GRADE_SOUP_SAVED_SCHEMA_DRIFT")
    expected = f"soups/{snapshot['grade']}-{snapshot['recipe_sha256']}.safetensors"
    if snapshot.get("filename") != expected or len(snapshot.get("sha256", "")) != 64:
        raise ValueError("GRADE_SOUP_SAVED_PATH_DRIFT")
    run_dir = Path(run_dir)
    path = run_dir / expected
    if path.parent.is_symlink() or path.is_symlink() or not path.is_file():
        raise ValueError("GRADE_SOUP_SAVED_ARTIFACT_MISSING")
    if not verify_file_digest(path, snapshot["sha256"]):
        raise ValueError("GRADE_SOUP_SAVED_ARTIFACT_CHANGED")
    return path


def retire_stale_soups(run_dir: Path, active_soups: dict) -> tuple[str, ...]:
    """Keep active and one previous frozen recipe per grade, no unbounded soup log."""
    run_dir = Path(run_dir)
    root = run_dir / "soups"
    if not root.exists():
        return ()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("GRADE_SOUP_RETIRE_UNSAFE_DIRECTORY")
    keep = set()
    for entry in active_soups.values():
        verify_frozen_soup(run_dir, entry)
        keep.update(shard["filename"] for shard in soup_shards(entry))
        previous = entry.get("previous")
        if previous:
            backups = previous if isinstance(previous, list) else [previous]
            for backup in backups:
                former = run_dir / backup["filename"]
                if (former.parent != root or former.is_symlink() or not former.is_file() or
                        not verify_file_digest(former, backup["sha256"])):
                    raise ValueError("GRADE_SOUP_PREVIOUS_BACKUP_DRIFT")
                keep.add(backup["filename"])
    files = []
    for item in sorted(root.iterdir()):
        if not re.fullmatch(r"[A-Z]+-[0-9a-f]{64}\.safetensors", item.name):
            continue  # Not our managed soup; never delete unknown files.
        if item.is_symlink() or not item.is_file():
            raise ValueError("GRADE_SOUP_RETIRE_UNSAFE_ARTIFACT")
        if str(item.relative_to(run_dir)) not in keep:
            files.append(item)
    for item in files:
        item.unlink()
    if files:
        folder = os.open(root, os.O_RDONLY)
        try:
            os.fsync(folder)
        finally:
            os.close(folder)
    return tuple(str(item.relative_to(run_dir)) for item in files)
