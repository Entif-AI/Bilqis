"""Deterministic persistent Merkle treap for compact A09 history indexes."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .atlas_frontier_contracts import _bytes, _fail
from .atlas_frontier_progress_metrics import note_history_index_node_write

ZERO_DIGEST = "0" * 64


def _digest(value) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


@dataclass(frozen=True)
class IndexNode:
    key: str
    value: tuple
    priority: int
    left: "IndexNode | None" = None
    right: "IndexNode | None" = None
    digest: str = ZERO_DIGEST


def _priority(key: str) -> int:
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16)


def _node(key, value, priority, left=None, right=None):
    note_history_index_node_write()
    return IndexNode(
        key, value, priority, left, right,
        _digest((
            key, value,
            ZERO_DIGEST if left is None else left.digest,
            ZERO_DIGEST if right is None else right.digest,
        )))


def _split(root, key):
    if root is None:
        return None, None
    if key < root.key:
        left, middle = _split(root.left, key)
        return left, _node(root.key, root.value, root.priority, middle, root.right)
    middle, right = _split(root.right, key)
    return _node(root.key, root.value, root.priority, root.left, middle), right


def insert(root, key: str, value: tuple):
    if root is None:
        return _node(key, value, _priority(key))
    if key == root.key:
        if root.value != value:
            _fail("BAMF_PLANNER_HISTORY_INDEX_CONFLICT")
        return root
    priority = _priority(key)
    if (priority, key) > (root.priority, root.key):
        left, right = _split(root, key)
        return _node(key, value, priority, left, right)
    if key < root.key:
        return _node(
            root.key, root.value, root.priority,
            insert(root.left, key, value), root.right)
    return _node(
        root.key, root.value, root.priority,
        root.left, insert(root.right, key, value))


def upsert(root, key: str, value: tuple):
    """Persistently set one key while preserving deterministic tree shape."""
    if root is None:
        return _node(key, value, _priority(key))
    if key == root.key:
        return _node(key, value, root.priority, root.left, root.right)
    priority = _priority(key)
    if (priority, key) > (root.priority, root.key):
        left, right = _split(root, key)
        return _node(key, value, priority, left, right)
    if key < root.key:
        return _node(
            root.key, root.value, root.priority,
            upsert(root.left, key, value), root.right)
    return _node(
        root.key, root.value, root.priority,
        root.left, upsert(root.right, key, value))


def lookup(root, key: str):
    current = root
    while current is not None:
        if key == current.key:
            return current.value
        current = current.left if key < current.key else current.right
    return None


def root_digest(root) -> str:
    return ZERO_DIGEST if root is None else root.digest


def values(root) -> tuple[tuple, ...]:
    result = []
    _collect(root, result, value=True)
    return tuple(result)


def keys(root) -> tuple[str, ...]:
    result = []
    _collect(root, result, value=False)
    return tuple(result)


def _collect(root, result, *, value):
    if root is None:
        return
    _collect(root.left, result, value=value)
    result.append(root.value if value else root.key)
    _collect(root.right, result, value=value)


__all__ = (
    "IndexNode", "ZERO_DIGEST", "insert", "keys", "lookup",
    "root_digest", "upsert", "values",
)
