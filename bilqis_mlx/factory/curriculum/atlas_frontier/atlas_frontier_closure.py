"""A09.2 deterministic typed prerequisite closure over immutable snapshots."""
from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
import hashlib

from bilqis_mlx.factory.autonomy import (
    AutonomyPlan,
    EvidenceLedger,
    evidence_complete_capabilities,
    is_factory_release,
)
from .atlas_frontier_contracts import CurriculumSnapshot, _bytes, _fail
from .skos_curriculum import (
    IMPLEMENTATION_UNCOVERED,
    PROGRAM_BOUND,
    SOURCE_FAMILY_ADAPTERS,
    SemanticFamilyInventory,
    SourceFamilyAdapter,
)


_SHA256_HEX_LENGTH = 64


class ClosureStatus(str, Enum):
    READY = "READY"
    SOURCE_HELD = "SOURCE_HELD"
    IMPLEMENTATION_UNCOVERED = "IMPLEMENTATION_UNCOVERED"
    WAITING_FOR_EVIDENCE = "WAITING_FOR_EVIDENCE"


@dataclass(frozen=True, order=True)
class ClosureReason:
    code: str
    owner: str
    dependency_id: str = ""


@dataclass(frozen=True, order=True)
class CandidateClosure:
    semantic_id: str
    family_id: str
    source_evidence_sha256: str
    status: ClosureStatus
    prerequisites: tuple[str, ...]
    reasons: tuple[ClosureReason, ...]


@dataclass(frozen=True, order=True)
class SourceHold:
    source_id: str
    reason_code: str
    owner: str
    status: ClosureStatus = ClosureStatus.SOURCE_HELD


@dataclass(frozen=True)
class FrontierClosure:
    snapshot_sha256: str
    prerequisite_evidence_sha256: str
    rule_families: tuple[str, ...]
    constituent_order: tuple[str, ...]
    candidates: tuple[CandidateClosure, ...]
    source_holds: tuple[SourceHold, ...]
    closure_sha256: str
    schema: str = "bilqis.factory-frontier-closure/v1"

    def expected_digest(self) -> str:
        return hashlib.sha256(_bytes({
            field.name: getattr(self, field.name)
            for field in fields(self) if field.name != "closure_sha256"
        })).hexdigest()

    def verify(self) -> None:
        if self.closure_sha256 != self.expected_digest():
            _fail("BAMF_PLANNER_CLOSURE_DIGEST_MISMATCH")


def _rules(registry: tuple[SourceFamilyAdapter, ...]) -> dict[str, SourceFamilyAdapter]:
    if (type(registry) is not tuple
            or any(type(item) is not SourceFamilyAdapter for item in registry)):
        _fail("BAMF_PLANNER_DOMAIN_RULE_REGISTRY_INVALID")
    result = {item.family_id: item for item in registry}
    if len(result) != len(registry):
        _fail("BAMF_PLANNER_DOMAIN_RULE_REGISTRY_DUPLICATE")
    return result


def _sha(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == _SHA256_HEX_LENGTH
        and all(char in "0123456789abcdef" for char in value)
    )


def _graph(snapshot: CurriculumSnapshot) -> tuple[dict[str, tuple[str, ...]], tuple[str, ...]]:
    eligible = set(snapshot.source_eligible_concept_ids)
    graph = {item: [] for item in eligible}
    for edge in snapshot.prerequisite_edges:
        if edge.semantic_id not in eligible or edge.prerequisite_semantic_id not in eligible:
            _fail("BAMF_PLANNER_PREREQUISITE_NOT_SOURCE_ELIGIBLE")
        graph[edge.semantic_id].append(edge.prerequisite_semantic_id)
    normalized = {key: tuple(sorted(set(value))) for key, value in graph.items()}
    visiting, visited, order = set(), set(), []

    def visit(identity: str) -> None:
        if identity in visiting:
            _fail("BAMF_PLANNER_PREREQUISITE_CYCLE")
        if identity in visited:
            return
        visiting.add(identity)
        for prerequisite in normalized[identity]:
            visit(prerequisite)
        visiting.remove(identity)
        visited.add(identity)
        order.append(identity)

    for identity in sorted(eligible):
        visit(identity)
    return normalized, tuple(order)


def _source_holds(snapshot: CurriculumSnapshot) -> tuple[SourceHold, ...]:
    return tuple(sorted(SourceHold(
        f"{row.domain}/{row.table}/{row.key}", row.reason_code, row.owner)
        for row in snapshot.source_held_rows))


def _coverage(
    snapshot: CurriculumSnapshot, census: SemanticFamilyInventory,
):
    eligible = set(snapshot.source_eligible_concept_ids)
    families = set(snapshot.required_source_family_ids)
    if (type(census) is not SemanticFamilyInventory
            or census.digest != snapshot.frozen_census_sha256
            or census.semantic_release != snapshot.semantic_release
            or census.source_bundle_id != snapshot.source_bundle_id
            or census.source_coverage_sha256 != snapshot.source_coverage_sha256
            or census.source_eligible_concept_ids
               != snapshot.source_eligible_concept_ids
            or census.required_source_family_ids
               != snapshot.required_source_family_ids):
        _fail("BAMF_PLANNER_FROZEN_CENSUS_MISMATCH")
    result = {}
    for row in snapshot.coverage_rows:
        key = (row.semantic_id, row.family_id)
        if (row.semantic_id not in eligible or row.family_id not in families
                or key in result
                or len(row.source_evidence_sha256) != _SHA256_HEX_LENGTH
                or any(char not in "0123456789abcdef"
                       for char in row.source_evidence_sha256)):
            _fail("BAMF_PLANNER_COVERAGE_SIGNATURE_INVALID")
        result[key] = row
    if set(snapshot.required_source_family_ids) - {key[1] for key in result}:
        _fail("BAMF_PLANNER_REQUIRED_FAMILY_MISSING")
    if {key[0] for key in result} != eligible:
        _fail("BAMF_PLANNER_ELIGIBILITY_DENOMINATOR_INCOMPLETE")
    expected = {
        (item.semantic_id, item.family_id) for item in census.obligations
    }
    if set(result) != expected:
        _fail("BAMF_PLANNER_COVERAGE_DENOMINATOR_MISMATCH")
    return result


def _direct_status(snapshot: CurriculumSnapshot, rules: dict[str, SourceFamilyAdapter]):
    by_candidate = {}
    for row in snapshot.coverage_rows:
        if row.implementation_status == IMPLEMENTATION_UNCOVERED or row.family_id not in rules:
            status = ClosureStatus.IMPLEMENTATION_UNCOVERED
        elif row.implementation_status == PROGRAM_BOUND:
            status = ClosureStatus.READY
        else:
            _fail("BAMF_PLANNER_IMPLEMENTATION_STATUS_INVALID")
        by_candidate[(row.semantic_id, row.family_id)] = status
    return by_candidate


def _dependency_status(
    statuses: tuple[ClosureStatus, ...], *, evidence_complete: bool,
) -> ClosureStatus | None:
    if ClosureStatus.IMPLEMENTATION_UNCOVERED in statuses:
        return ClosureStatus.IMPLEMENTATION_UNCOVERED
    if not evidence_complete or ClosureStatus.WAITING_FOR_EVIDENCE in statuses:
        return ClosureStatus.WAITING_FOR_EVIDENCE
    return None


def _merge_status(current: ClosureStatus, dependency: ClosureStatus) -> ClosureStatus:
    precedence = {
        ClosureStatus.READY: 0,
        ClosureStatus.WAITING_FOR_EVIDENCE: 1,
        ClosureStatus.IMPLEMENTATION_UNCOVERED: 2,
    }
    return max((current, dependency), key=precedence.__getitem__)


def _semantic_roots_for_release(current_release, mastered: tuple[str, ...]) -> tuple[str, ...]:
    from . import candidate_realizations

    if hasattr(current_release, "course"):
        capability_map = current_release.course.capability_map
    else:
        capability_map = current_release.curriculum.capability_map
    roots = set()
    for capability_id in mastered:
        definition = capability_map.get(capability_id)
        if definition is None:
            _fail("BAMF_PLANNER_PREREQUISITE_EVIDENCE_INCOMPLETE")
        roots.update(definition.examined_roots)
        try:
            roots.add(candidate_realizations.realized_atlas_semantic_id(capability_id))
        except ValueError:
            pass
    return tuple(sorted(roots))


def semantic_roots_for_mastered_capabilities(
    current_release, mastered: tuple[str, ...],
) -> tuple[str, ...]:
    """A09-owned projection from current capability mastery to semantic roots."""
    return _semantic_roots_for_release(current_release, mastered)


def _verified_evidence_context(
    snapshot: CurriculumSnapshot,
    current_release,
    evidence_ledger: EvidenceLedger | None,
    autonomy_plan: AutonomyPlan | None,
    checkpoint_sha256: str | None,
    optimizer_step: int | None,
) -> tuple[frozenset[str], str]:
    mastered: tuple[str, ...] = ()
    semantic_roots: tuple[str, ...] = ()
    supplied = any(item is not None for item in (
        current_release, evidence_ledger, autonomy_plan,
        checkpoint_sha256, optimizer_step,
    ))
    if supplied:
        if (not is_factory_release(current_release)
                or type(evidence_ledger) is not EvidenceLedger
                or type(autonomy_plan) is not AutonomyPlan
                or not _sha(checkpoint_sha256)
                or type(optimizer_step) is not int or optimizer_step < 0
                or snapshot.admitted_factory_release_sha256 is None
                or current_release.release_sha256
                   != snapshot.admitted_factory_release_sha256):
            _fail("BAMF_PLANNER_PREREQUISITE_EVIDENCE_STALE")
        try:
            current_release.verify()
            mastered = evidence_complete_capabilities(
                current_release, evidence_ledger, plan=autonomy_plan,
                current_checkpoint_sha256=checkpoint_sha256,
                current_optimizer_step=optimizer_step,
            )
            semantic_roots = _semantic_roots_for_release(current_release, mastered)
        except (TypeError, ValueError):
            _fail("BAMF_PLANNER_PREREQUISITE_EVIDENCE_INVALID")
    digest = hashlib.sha256(_bytes({
        "factory_release_sha256": (
            current_release.release_sha256 if supplied else None),
        "autonomy_plan_sha256": autonomy_plan.digest() if supplied else None,
        "checkpoint_sha256": checkpoint_sha256 if supplied else None,
        "optimizer_step": optimizer_step if supplied else None,
        "mastered": mastered,
        "semantic_roots": semantic_roots,
    })).hexdigest()
    return frozenset(semantic_roots), digest


def resolve_frontier_closure(
    snapshot: CurriculumSnapshot,
    census: SemanticFamilyInventory,
    domain_rule_registry: tuple[SourceFamilyAdapter, ...] = SOURCE_FAMILY_ADAPTERS,
    *,
    current_release=None,
    evidence_ledger: EvidenceLedger | None = None,
    autonomy_plan: AutonomyPlan | None = None,
    checkpoint_sha256: str | None = None,
    optimizer_step: int | None = None,
) -> FrontierClosure:
    """Return grade-neutral, constituent-first closure without ranking or admission."""
    if type(snapshot) is not CurriculumSnapshot:
        _fail("BAMF_PLANNER_SNAPSHOT_INPUT_INVALID")
    snapshot.verify()
    rules = _rules(domain_rule_registry)
    evidence_semantic_ids, evidence_sha256 = _verified_evidence_context(
        snapshot,
        current_release,
        evidence_ledger,
        autonomy_plan,
        checkpoint_sha256,
        optimizer_step,
    )
    graph, order = _graph(snapshot)
    direct = _direct_status(snapshot, rules)
    resolved: dict[str, tuple[ClosureStatus, ...]] = {}
    candidates = []
    rows = _coverage(snapshot, census)
    for semantic_id in order:
        current = []
        for family_id in sorted(key[1] for key in rows if key[0] == semantic_id):
            row = rows[(semantic_id, family_id)]
            status = direct[(semantic_id, family_id)]
            reasons = []
            if status is ClosureStatus.IMPLEMENTATION_UNCOVERED:
                reasons.append(ClosureReason(
                    "FAMILY_IMPLEMENTATION_UNCOVERED", f"family:{family_id}"))
            elif status is ClosureStatus.WAITING_FOR_EVIDENCE:
                reasons.append(ClosureReason("LEARNING_EVIDENCE_REQUIRED", "learner:evidence"))
            for prerequisite in graph[semantic_id]:
                blocked = _dependency_status(
                    resolved[prerequisite],
                    evidence_complete=prerequisite in evidence_semantic_ids,
                )
                if blocked is not None:
                    status = _merge_status(status, blocked)
                    reasons.append(ClosureReason(
                        "PREREQUISITE_" + blocked.value, "factory:prerequisite", prerequisite))
            candidates.append(CandidateClosure(
                semantic_id, family_id, row.source_evidence_sha256, status,
                graph[semantic_id], tuple(sorted(set(reasons)))))
            current.append(status)
        resolved[semantic_id] = tuple(current)
    provisional = FrontierClosure(
        snapshot.snapshot_sha256, evidence_sha256, tuple(sorted(rules)), order,
        tuple(sorted(candidates)), _source_holds(snapshot), "0" * 64)
    result = FrontierClosure(
        provisional.snapshot_sha256, provisional.prerequisite_evidence_sha256,
        provisional.rule_families,
        provisional.constituent_order, provisional.candidates,
        provisional.source_holds, provisional.expected_digest())
    result.verify()
    return result
