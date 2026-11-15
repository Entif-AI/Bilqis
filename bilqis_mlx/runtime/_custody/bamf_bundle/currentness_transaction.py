"""Visit-scoped accepted-state currentness over one already authenticated parent."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

from bilqis_mlx.semantics.domains import contract_digest

from .bundle_currentness import (
    bind_bamf_bundle_currentness,
    require_bamf_bundle_currentness,
)
from .records import CompleteStudent, canonical, invalid, sha
from .source_authority_custody import (
    bind_source_authority_currentness,
    require_source_authority_currentness,
)


_ISSUER = object()


class VisitCurrentnessMetrics:
    """Observational counters for the expensive currentness surfaces in one visit."""

    def __init__(self):
        self._lock = Lock()
        self._values = {
            "deep_authentication_count": 0,
            "accepted_cache_currentness_count": 0,
            "full_candidate_identity_hashes": 0,
            "bundle_tree_scans": 0,
        }

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            if name not in self._values or type(amount) is not int or amount < 0:
                invalid("BAMF_CURRENTNESS_METRICS_INVALID")
            self._values[name] += amount

    def to_record(self) -> dict:
        with self._lock:
            return dict(self._values)


def _stat_identity(path: Path) -> tuple[int, int, int, int, int]:
    info = path.stat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _pointer_snapshot(
        run_dir: Path, expected_manifest_sha256: str, *,
        expected_run_id: str, expected_generation: int):
    from .publication import _pointer_lock, _read_pointer

    run_dir = Path(run_dir).resolve()
    with _pointer_lock(run_dir):
        pointer = _read_pointer(run_dir / "bamf-state.json")
        if (not isinstance(pointer, dict)
                or pointer.get("manifest_sha256") != expected_manifest_sha256
                or pointer.get("run_id") != expected_run_id
                or pointer.get("generation") != expected_generation
                or not isinstance(pointer.get("acceptance_sha256"), str)):
            invalid("B13_CURRENTNESS_POINTER_DRIFT")
        acceptance = run_dir / "bamf-acceptance" / f"{expected_manifest_sha256}.json"
        if acceptance.is_symlink() or not acceptance.is_file():
            invalid("B13_CURRENTNESS_ACCEPTANCE_DRIFT")
        try:
            acceptance_identity = _stat_identity(acceptance)
        except OSError:
            invalid("B13_CURRENTNESS_ACCEPTANCE_DRIFT")
    return sha(canonical(pointer)), pointer["acceptance_sha256"], acceptance_identity


def _retained_object_guard(parent: CompleteStudent) -> tuple:
    state = parent.retained_state
    optimizer = state.optimizer
    groups = []
    for group in ("parameters", "m", "v", "update_counts"):
        values = getattr(optimizer, group)
        groups.append((
            group,
            id(values),
            tuple((name, id(value)) for name, value in sorted(values.items())),
        ))
    return (
        id(state), id(optimizer), state.optimizer_step,
        id(state.policy), id(state.allocations), tuple(groups),
    )


@dataclass(frozen=True, init=False, eq=False)
class AcceptedCurrentnessTransaction:
    """One process-live proof reused while the accepted parent cannot change."""

    candidate_identity_sha256: str
    accepted_manifest_sha256: str
    generation_binding: str
    topology_digest: str
    extents_digest: str
    _run_dir: Path = field(repr=False)
    _parent: CompleteStudent = field(repr=False, compare=False)
    _cache: object = field(repr=False, compare=False)
    _pointer_sha256: str = field(repr=False)
    _acceptance_sha256: str = field(repr=False)
    _acceptance_identity: tuple = field(repr=False)
    _bundle_currentness: object = field(repr=False, compare=False)
    _source_currentness: object = field(repr=False, compare=False)
    _correction_frontier_sha256: str = field(repr=False)
    _retained_guard: tuple = field(repr=False, compare=False)
    _metrics: VisitCurrentnessMetrics = field(repr=False, compare=False)
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        invalid("B13_CURRENTNESS_CALLER_CONSTRUCTION_FORBIDDEN")


def _activate(transaction: AcceptedCurrentnessTransaction) -> None:
    object.__setattr__(transaction._cache, "_currentness_transaction", transaction)


def bind_accepted_currentness_transaction(
        run_dir: Path, parent: CompleteStudent, cache, *,
        metrics: VisitCurrentnessMetrics | None = None,
) -> AcceptedCurrentnessTransaction:
    """Deep-authenticate B13/C09 once and issue a reusable visit witness."""
    if type(parent) is not CompleteStudent:
        invalid("B13_CURRENTNESS_PARENT_INVALID")
    candidate_identity = getattr(cache, "_candidate_identity_sha256", None)
    if (cache.run_id != parent.run_id or cache.generation != parent.generation
            or not isinstance(candidate_identity, str) or len(candidate_identity) != 64):
        invalid("B13_CURRENTNESS_PARENT_DRIFT")
    metrics = metrics or VisitCurrentnessMetrics()
    run_dir = Path(run_dir).resolve()
    before = _pointer_snapshot(
        run_dir, cache.accepted_manifest_sha256,
        expected_run_id=cache.run_id, expected_generation=cache.generation)
    bundle = bind_bamf_bundle_currentness(
        run_dir / "bamf-bundles" / cache.accepted_manifest_sha256,
        expected_manifest_sha256=cache.accepted_manifest_sha256,
    )
    metrics.increment("bundle_tree_scans", 2)
    source = bind_source_authority_currentness(
        run_dir, parent.correction_frontier, cache._correction_registry)
    after = _pointer_snapshot(
        run_dir, cache.accepted_manifest_sha256,
        expected_run_id=cache.run_id, expected_generation=cache.generation)
    if before != after:
        invalid("B13_CURRENTNESS_POINTER_DRIFT")
    transaction = object.__new__(AcceptedCurrentnessTransaction)
    for name, value in (
        ("candidate_identity_sha256", candidate_identity),
        ("accepted_manifest_sha256", cache.accepted_manifest_sha256),
        ("generation_binding", cache.generation_binding),
        ("topology_digest", parent.topology.digest),
        ("extents_digest", parent.extents.digest),
        ("_run_dir", run_dir),
        ("_parent", parent),
        ("_cache", cache),
        ("_pointer_sha256", after[0]),
        ("_acceptance_sha256", after[1]),
        ("_acceptance_identity", after[2]),
        ("_bundle_currentness", bundle),
        ("_source_currentness", source),
        ("_correction_frontier_sha256", contract_digest(parent.correction_frontier)),
        ("_retained_guard", _retained_object_guard(parent)),
        ("_metrics", metrics),
        ("_issuance", _ISSUER),
    ):
        object.__setattr__(transaction, name, value)
    metrics.increment("deep_authentication_count")
    _activate(transaction)
    return transaction


def require_accepted_currentness(transaction, cache=None, parent=None):
    """O(1) process-local proof used by downstream consumers inside a boundary."""
    if (type(transaction) is not AcceptedCurrentnessTransaction
            or getattr(transaction, "_issuance", None) is not _ISSUER
            or (cache is not None and transaction._cache is not cache)
            or (parent is not None and transaction._parent is not parent)
            or getattr(transaction._cache, "_currentness_transaction", None)
            is not transaction
            or transaction._cache.accepted_manifest_sha256
            != transaction.accepted_manifest_sha256
            or transaction._cache.generation_binding != transaction.generation_binding
            or transaction._parent.topology.digest != transaction.topology_digest
            or transaction._parent.extents.digest != transaction.extents_digest
            or _retained_object_guard(transaction._parent) != transaction._retained_guard):
        invalid("B13_CURRENTNESS_TRANSACTION_DRIFT")
    return transaction


def refresh_accepted_currentness(transaction, parent: CompleteStudent):
    """Check all mutable accepted-state edges once before the next neural step."""
    require_accepted_currentness(transaction, transaction._cache, parent)
    pointer_sha256, acceptance_sha256, acceptance_identity = _pointer_snapshot(
        transaction._run_dir, transaction.accepted_manifest_sha256,
        expected_run_id=transaction._cache.run_id,
        expected_generation=transaction._cache.generation)
    if (pointer_sha256 != transaction._pointer_sha256
            or acceptance_sha256 != transaction._acceptance_sha256
            or acceptance_identity != transaction._acceptance_identity
            or contract_digest(parent.correction_frontier)
            != transaction._correction_frontier_sha256):
        invalid("B13_CURRENTNESS_TRANSACTION_DRIFT")
    require_bamf_bundle_currentness(transaction._bundle_currentness)
    require_source_authority_currentness(
        transaction._source_currentness, transaction._run_dir,
        parent.correction_frontier, transaction._cache._correction_registry)
    transaction._metrics.increment("accepted_cache_currentness_count")
    _activate(transaction)
    return transaction


def accepted_currentness_identity(transaction, parent: CompleteStudent):
    """Return the already paid-for accepted parent identity without tensor hashing."""
    require_accepted_currentness(transaction, transaction._cache, parent)
    from .accepted_runtime import AcceptedGenerationIdentity
    return AcceptedGenerationIdentity(
        run_id=parent.run_id,
        generation=parent.generation,
        manifest_sha256=transaction.accepted_manifest_sha256,
        topology_digest=transaction.topology_digest,
        extents_digest=transaction.extents_digest,
        optimizer_step=parent.retained_state.optimizer_step,
        candidate_identity_sha256=transaction.candidate_identity_sha256,
    )


def currentness_metrics(transaction) -> dict:
    require_accepted_currentness(transaction)
    return transaction._metrics.to_record()


__all__ = (
    "AcceptedCurrentnessTransaction",
    "VisitCurrentnessMetrics",
    "accepted_currentness_identity",
    "bind_accepted_currentness_transaction",
    "currentness_metrics",
    "refresh_accepted_currentness",
    "require_accepted_currentness",
)
