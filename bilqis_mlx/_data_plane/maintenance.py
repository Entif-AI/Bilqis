"""Reachability and retention maintenance for the shared data plane."""
from __future__ import annotations

import hashlib
import json
import zlib
from pathlib import Path

from .contracts import DataPlaneError, _error
from .file_retention import file_gc_report, file_inventory
from .migration import migrate_legacy_payloads, vacuum

_HEAD_SCHEMA = "bilqis.state-head/v1"
_OBJECT_FRONTIER_BATCH_RECORDS = 400


def _valid_digest(value) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def _pointer_digest(path: Path) -> str | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    digest = value.get("node_sha256") if value.get("schema") == _HEAD_SCHEMA else None
    return digest if _valid_digest(digest) else None


def _node_roots(plane, scan_roots) -> tuple[set[str], dict[str, int]]:
    roots: set[str] = set()
    tiers = {"current": 0, "history": 0, "bamf": 0, "pinned": 0}
    for root in (Path(value).expanduser().resolve() for value in scan_roots):
        if not root.exists():
            continue
        if root.is_file():
            paths = [root]
        else:
            paths = []
            for name in ("state.json", "bamf-state.json"):
                path = root / name
                if path.is_file():
                    paths.append(path)
            states = root / "states"
            if states.is_dir():
                paths.extend(sorted(states.glob("*.json")))
        for path in paths:
            name = path.name
            if name == "bamf-state.json":
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    raise ValueError(DataPlaneError.BAMF_POINTER_INVALID.value) from None
                digest = value.get("manifest_sha256")
                if _valid_digest(digest):
                    stored = plane._db.execute(
                        "SELECT 1 FROM nodes WHERE sha256=? UNION ALL "
                        "SELECT 1 FROM archived_nodes WHERE sha256=? LIMIT 1",
                        (digest, digest)).fetchone()
                    if stored is not None:
                        roots.add(digest)
                        tiers["bamf"] += 1
                else:
                    raise ValueError(DataPlaneError.BAMF_POINTER_INVALID.value)
            elif name == "state.json" or (
                    path.parent.name == "states" and name.removesuffix(".json").isdigit()):
                digest = _pointer_digest(path)
                if not digest:
                    raise ValueError(_error(DataPlaneError.STATE_POINTER_INVALID, path))
                roots.add(digest)
                tiers["current" if name == "state.json" else "history"] += 1
    for kind, digest in plane._db.execute(
            "SELECT kind,sha256 FROM retention_pins WHERE kind='node'"):
        roots.add(digest)
        tiers["pinned"] += 1
    return roots, tiers


def _state_field_refs(value, objects: set[str]) -> None:
    if isinstance(value, dict):
        kind = value.get("kind")
        if kind == "object/v1" and _valid_digest(value.get("sha256")):
            objects.add(value["sha256"])
        elif kind in {"teacher-misses/v1", "teacher-miss-exposures/v1"}:
            for digest in value.get("shards", {}).values():
                if _valid_digest(digest):
                    objects.add(digest)
        elif kind == "teacher-misses/v2":
            for prefixes in value.get("shards", {}).values():
                for digest in prefixes.values():
                    if _valid_digest(digest):
                        objects.add(digest)
        elif kind in {"object-list/v1", "teacher-context-map/v1"}:
            items = value.get("items", ())
            iterable = items.values() if isinstance(items, dict) else items
            for digest in iterable:
                if _valid_digest(digest):
                    objects.add(digest)
        for child in value.values():
            _state_field_refs(child, objects)
    elif isinstance(value, list):
        for child in value:
            _state_field_refs(child, objects)


def _node_refs(raw: bytes) -> tuple[set[str], set[str]]:
    objects: set[str] = set()
    files: set[str] = set()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return objects, files
    _state_field_refs(value, objects)
    if isinstance(value, dict):
        sidecars = value.get("sidecars")
        if isinstance(sidecars, dict):
            for binding in sidecars.values():
                if isinstance(binding, dict) and _valid_digest(binding.get("object_sha256")):
                    objects.add(binding["object_sha256"])
        tensors = value.get("tensors")
        if isinstance(tensors, dict) and _valid_digest(tensors.get("object_sha256")):
            files.add(tensors["object_sha256"])
    return objects, files


def _digests(value, found: set[str]) -> None:
    if _valid_digest(value):
        found.add(value)
    elif isinstance(value, dict):
        for child in value.values():
            _digests(child, found)
    elif isinstance(value, list):
        for child in value:
            _digests(child, found)


def _json_digests(raw: bytes) -> set[str]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return set()
    found: set[str] = set()
    _digests(value, found)
    return found


def _object_batch(plane, digests) -> dict[str, bytes]:
    """Read a bounded object frontier without one SQLite lookup per digest."""
    requested = tuple(dict.fromkeys(digests))
    if not requested:
        return {}
    placeholders = ",".join("?" for _ in requested)
    rows = plane._db.execute(
        f"SELECT sha256,payload,raw_bytes FROM objects WHERE sha256 IN ({placeholders})",
        requested,
    )
    result = {}
    for digest, compressed, raw_bytes in rows:
        raw = zlib.decompress(compressed)
        if len(raw) != raw_bytes or hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(_error(DataPlaneError.OBJECT_CORRUPTED, digest))
        result[digest] = raw
    for digest in requested:
        if digest in result:
            continue
        try:
            result[digest] = plane.get_object(digest)
        except ValueError:
            raise ValueError(_error(DataPlaneError.OBJECT_MISSING, digest)) from None
    return result


def reachability(plane, scan_roots) -> dict:
    node_roots, tiers = _node_roots(plane, scan_roots)
    parent_by_node = dict(plane._db.execute(
        "SELECT sha256,parent_sha256 FROM nodes UNION ALL "
        "SELECT sha256,parent_sha256 FROM archived_nodes"))
    node_ids = set(parent_by_node)
    object_ids = {row[0] for row in plane._db.execute(
        "SELECT sha256 FROM objects UNION SELECT sha256 FROM archived_objects")}
    file_ids = set(file_inventory(plane))
    reachable_nodes: set[str] = set()
    reachable_objects: set[str] = set()
    reachable_files: set[str] = set()
    pending_nodes = list(node_roots)
    pending_objects = [
        digest for _key, digest in plane._db.execute(
            "SELECT key,value FROM meta WHERE key LIKE 'object_reference_v1:%'")
        if _valid_digest(digest)
    ]
    for kind, digest in plane._db.execute("SELECT kind,sha256 FROM retention_pins"):
        if kind == "node":
            pending_nodes.append(digest)
        elif kind == "object":
            pending_objects.append(digest)
        elif kind == "file":
            reachable_files.add(digest)

    def classify(digests) -> None:
        for candidate in digests:
            if candidate in node_ids and candidate not in reachable_nodes:
                pending_nodes.append(candidate)
            if candidate in object_ids and candidate not in reachable_objects:
                pending_objects.append(candidate)
            if candidate in file_ids:
                reachable_files.add(candidate)

    while pending_nodes or pending_objects:
        if pending_objects:
            frontier = []
            while pending_objects and len(frontier) < _OBJECT_FRONTIER_BATCH_RECORDS:
                digest = pending_objects.pop()
                if digest not in reachable_objects:
                    frontier.append(digest)
            for digest, raw in _object_batch(plane, frontier).items():
                reachable_objects.add(digest)
                classify(_json_digests(raw))
            continue
        digest = pending_nodes.pop()
        if digest in reachable_nodes:
            continue
        try:
            raw = plane.get_node(digest)
        except ValueError:
            raise ValueError(_error(DataPlaneError.NODE_MISSING, digest)) from None
        reachable_nodes.add(digest)
        obj, files = _node_refs(raw)
        reachable_files.update(files)
        classify(obj | _json_digests(raw))
        parent = parent_by_node.get(digest)
        if _valid_digest(parent) and parent not in reachable_nodes:
            pending_nodes.append(parent)
    return {"nodes": reachable_nodes, "objects": reachable_objects,
            "files": reachable_files, "root_tiers": tiers}


def gc_report(plane, scan_roots, *, apply: bool = False) -> dict:
    live = reachability(plane, scan_roots)
    node_rows = {row[0]: row[1] for row in plane._db.execute(
        "SELECT sha256,length(payload) FROM nodes UNION ALL "
        "SELECT sha256,compressed_bytes FROM archived_nodes")}
    object_rows = {row[0]: row[1] for row in plane._db.execute(
        "SELECT sha256,length(payload) FROM objects UNION ALL "
        "SELECT sha256,compressed_bytes FROM archived_objects")}
    dead_nodes = set(node_rows) - live["nodes"]
    dead_objects = set(object_rows) - live["objects"]
    report = {
        "reachable_nodes": len(live["nodes"]), "unreachable_nodes": len(dead_nodes),
        "reachable_objects": len(live["objects"]), "unreachable_objects": len(dead_objects),
        "reclaimable_node_bytes": sum(node_rows[x] for x in dead_nodes),
        "reclaimable_object_bytes": sum(object_rows[x] for x in dead_objects),
        "root_tiers": live["root_tiers"], "applied": apply,
    }
    if not apply:
        return report
    with plane.transaction():
        for digest in dead_nodes:
            plane._db.execute("DELETE FROM nodes WHERE sha256=?", (digest,))
            plane._db.execute("DELETE FROM archived_nodes WHERE sha256=?", (digest,))
        for digest in dead_objects:
            plane._db.execute("DELETE FROM objects WHERE sha256=?", (digest,))
            plane._db.execute("DELETE FROM archived_objects WHERE sha256=?", (digest,))
    return report




def pin(plane, kind: str, digest: str, tier: str, reason: str) -> None:
    if kind not in {"node", "object", "file"} or not _valid_digest(digest):
        raise ValueError(DataPlaneError.RETENTION_PIN_INVALID.value)
    if tier not in {"current", "recovery", "champion", "soup", "evidence", "operator"}:
        raise ValueError(DataPlaneError.RETENTION_TIER_INVALID.value)
    with plane.transaction():
        plane._db.execute(
            "INSERT OR REPLACE INTO retention_pins(kind,sha256,tier,reason) VALUES(?,?,?,?)",
            (kind, digest, tier, reason))
