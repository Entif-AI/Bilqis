"""A09-owned frontier ranking facts shared with learner-relative cohort policy."""
from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib

from .atlas_frontier_closure import (
    CandidateClosure, ClosureReason, ClosureStatus, FrontierClosure,
)
from .atlas_frontier_contracts import CurriculumSnapshot, _bytes, _fail
from .atlas_frontier_selection_validation import validate_closure_structure


A09_FRONTIER_COMPARATOR_ORDER = (
    "prerequisite_slope",
    "downstream_unlocks_desc",
    "cursor_distance",
    "semantic_id",
)


@dataclass(frozen=True, order=True)
class DeferredClosure:
    semantic_id: str
    family_id: str
    status: ClosureStatus
    reasons: tuple[ClosureReason, ...]


@dataclass(frozen=True)
class FrontierDeltaSelection:
    snapshot_sha256: str
    closure_sha256: str
    admitted_release_sha256: str
    policy_epoch: int
    cursor: int
    selected_semantic_id: str
    selected_obligations: tuple[CandidateClosure, ...]
    introduced_capability_ids: tuple[str, ...]
    introduced_semantic_ids: tuple[str, ...]
    prerequisite_slope: int
    downstream_unlocks: int
    deferred: tuple[DeferredClosure, ...]
    requested_obligation_keys: tuple[tuple[str, str], ...]
    candidate_signature: str
    selection_sha256: str
    schema: str = "bilqis.factory-atlas-frontier-selection/v1"

    def expected_digest(self) -> str:
        return hashlib.sha256(_bytes({
            field.name: getattr(self, field.name)
            for field in fields(self) if field.name != "selection_sha256"
        })).hexdigest()

    def verify(self) -> None:
        if (self.schema != "bilqis.factory-atlas-frontier-selection/v1"
                or not self.selected_obligations
                or any(item.semantic_id != self.selected_semantic_id
                       for item in self.selected_obligations)
                or self.requested_obligation_keys
                   != tuple(sorted(set(self.requested_obligation_keys)))
                or self.selection_sha256 != self.expected_digest()):
            _fail("BAMF_PLANNER_SELECTION_INVALID")


@dataclass(frozen=True, order=True)
class FrontierTargetMetrics:
    semantic_id: str
    prerequisite_slope: int
    downstream_unlocks: int
    cursor_distance: int
    statuses: tuple[str, ...]
    reason_receipts: tuple[tuple[str, str, str, str, str], ...]


def _graph(closure: FrontierClosure) -> dict[str, tuple[str, ...]]:
    graph = {identity: set() for identity in closure.constituent_order}
    for item in closure.candidates:
        graph[item.semantic_id].update(item.prerequisites)
    return {key: tuple(sorted(value)) for key, value in graph.items()}


def _ancestors(identity: str, graph: dict[str, tuple[str, ...]]) -> frozenset[str]:
    result: set[str] = set()
    pending = list(graph[identity])
    while pending:
        current = pending.pop()
        if current in result:
            continue
        result.add(current)
        pending.extend(graph[current])
    return frozenset(result)


def _grouped(closure: FrontierClosure) -> dict[str, tuple[CandidateClosure, ...]]:
    result = {}
    for identity in closure.constituent_order:
        result[identity] = tuple(sorted(
            item for item in closure.candidates if item.semantic_id == identity))
        if not result[identity]:
            _fail("BAMF_PLANNER_SELECTION_CLOSURE_INCOMPLETE")
    return result


def _semantic_ready(rows: tuple[CandidateClosure, ...]) -> bool:
    return all(item.status is ClosureStatus.READY for item in rows)


def _marginal_unlocks(
    identity: str,
    groups: dict[str, tuple[CandidateClosure, ...]],
) -> int:
    count = 0
    for other, rows in groups.items():
        if other == identity or _semantic_ready(rows):
            continue
        blockers = {
            reason.dependency_id
            for row in rows for reason in row.reasons
            if reason.code.startswith("PREREQUISITE_") and reason.dependency_id
        }
        intrinsic = any(
            reason.code == "FAMILY_IMPLEMENTATION_UNCOVERED"
            for row in rows for reason in row.reasons)
        if not intrinsic and blockers == {identity}:
            count += 1
    return count


def _frontier_rank_components(
    identity: str,
    snapshot: CurriculumSnapshot,
    graph: dict[str, tuple[str, ...]],
    groups: dict[str, tuple[CandidateClosure, ...]],
    order: dict[str, int],
) -> tuple[int, int, int, str]:
    width = len(order)
    return (
        len(_ancestors(identity, graph)),
        -_marginal_unlocks(identity, groups),
        (order[identity] - snapshot.cursor) % width,
        identity,
    )


def frontier_target_metrics(
    snapshot: CurriculumSnapshot,
    closure: FrontierClosure,
) -> tuple[FrontierTargetMetrics, ...]:
    snapshot.verify()
    closure.verify()
    validate_closure_structure(snapshot, closure)
    graph = _graph(closure)
    groups = _grouped(closure)
    order = {identity: index for index, identity in enumerate(closure.constituent_order)}
    if not order:
        return ()
    result = []
    for identity, rows in groups.items():
        slope, neg_unlocks, cursor_distance, _ = _frontier_rank_components(
            identity, snapshot, graph, groups, order)
        result.append(FrontierTargetMetrics(
            semantic_id=identity,
            prerequisite_slope=slope,
            downstream_unlocks=-neg_unlocks,
            cursor_distance=cursor_distance,
            statuses=tuple(sorted({row.status.value for row in rows})),
            reason_receipts=tuple(sorted(
                (row.family_id, row.status.value, reason.code, reason.owner,
                 reason.dependency_id)
                for row in rows for reason in row.reasons)),
        ))
    return tuple(sorted(result, key=lambda item: item.semantic_id))


def _candidate_signature(
    identity: str,
    rows: tuple[CandidateClosure, ...],
    capabilities: tuple[str, ...],
    introduced: tuple[str, ...],
) -> str:
    return hashlib.sha256(_bytes({
        "semantic_id": identity,
        "obligations": tuple(
            (row.family_id, row.source_evidence_sha256, row.prerequisites)
            for row in rows),
        "introduced_capability_ids": capabilities,
        "introduced_semantic_ids": introduced,
    })).hexdigest()


def _ranked_ready_targets(
    snapshot: CurriculumSnapshot,
    closure: FrontierClosure,
    requested_obligation_keys: tuple[tuple[str, str], ...] = (),
) -> tuple[dict[str, tuple[CandidateClosure, ...]], list[tuple]]:
    graph = _graph(closure)
    groups = _grouped(closure)
    order = {identity: index for index, identity in enumerate(closure.constituent_order)}
    if not order:
        _fail("BAMF_PLANNER_NO_READY_DELTA")
    ranked = []
    requested = set(requested_obligation_keys)
    for identity, rows in groups.items():
        if not _semantic_ready(rows):
            continue
        obligation_digest = hashlib.sha256(_bytes(tuple(
            (row.family_id, row.source_evidence_sha256, row.prerequisites)
            for row in sorted(rows)))).hexdigest()
        if (identity, obligation_digest) in requested:
            continue
        ranked.append((*_frontier_rank_components(
            identity, snapshot, graph, groups, order), rows))
    return groups, ranked
