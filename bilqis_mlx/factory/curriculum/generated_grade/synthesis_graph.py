"""Graph and decision helpers for generated-grade synthesis."""
from __future__ import annotations

from bilqis_mlx.factory.atlas_frontier_closure import ClosureStatus, FrontierClosure
from bilqis_mlx.factory.atlas_frontier_contracts import CurriculumSnapshot, _fail
from bilqis_mlx.factory.atlas_frontier_selection_validation import validate_closure_structure
from bilqis_mlx.factory.executable_release import ExecutableFactoryRelease

from .contracts import (
    AcceptedLearnerFoot,
    CandidateDevelopmentEvidence,
    CandidateGradeDecision,
    GeneratedGradePolicy,
)


def validate_inputs(snapshot, closure, release, learner, candidate_evidence, policy) -> None:
    if (type(snapshot) is not CurriculumSnapshot or type(closure) is not FrontierClosure
            or not isinstance(release, ExecutableFactoryRelease)
            or type(learner) is not AcceptedLearnerFoot
            or type(candidate_evidence) is not tuple
            or any(type(item) is not CandidateDevelopmentEvidence for item in candidate_evidence)
            or type(policy) is not GeneratedGradePolicy):
        _fail("BAMF_GENERATED_GRADE_INPUT_INVALID")
    snapshot.verify()
    closure.verify()
    release.verify()
    validate_closure_structure(snapshot, closure)
    if (closure.snapshot_sha256 != snapshot.snapshot_sha256
            or snapshot.admitted_factory_release_sha256 != release.release_sha256
            or learner.factory_release_sha256 != release.release_sha256
            or learner.policy_epoch != snapshot.policy_epoch
            or learner.evidence_epoch != snapshot.qualification_epoch
            or policy.policy_epoch != snapshot.policy_epoch):
        _fail("BAMF_GENERATED_GRADE_AUTHORITY_MISMATCH")
    candidate_ids = tuple(sorted(set(closure.constituent_order)))
    evidence_ids = tuple(item.semantic_id for item in candidate_evidence)
    if (evidence_ids != tuple(sorted(set(evidence_ids)))
            or not set(evidence_ids).issubset(candidate_ids)):
        _fail("BAMF_GENERATED_GRADE_EVIDENCE_CENSUS_INVALID")


def graph_for(closure: FrontierClosure) -> dict[str, tuple[str, ...]]:
    result = {identity: () for identity in closure.constituent_order}
    for identity in result:
        rows = [item for item in closure.candidates if item.semantic_id == identity]
        prerequisite_sets = {item.prerequisites for item in rows}
        if len(prerequisite_sets) != 1:
            _fail("BAMF_GENERATED_GRADE_PREREQUISITE_DRIFT")
        result[identity] = next(iter(prerequisite_sets))
    return result


def grouped_rows(closure: FrontierClosure):
    return {identity: tuple(item for item in closure.candidates
                            if item.semantic_id == identity)
            for identity in closure.constituent_order}


def _ancestors(identity: str, graph: dict[str, tuple[str, ...]], order) -> tuple[str, ...]:
    result: set[str] = set()
    pending = list(graph[identity])
    while pending:
        current = pending.pop()
        if current in result:
            continue
        result.add(current)
        pending.extend(graph[current])
    return tuple(sorted(result, key=order.__getitem__))


def _unmet_prerequisites(identity, rows, graph, order) -> tuple[str, ...]:
    """Use A09's learner-evidence closure, never admission credit, as mastery truth."""
    missing: set[str] = set()

    def visit(current: str) -> None:
        direct_missing = {
            reason.dependency_id
            for row in rows[current] for reason in row.reasons
            if reason.code.startswith("PREREQUISITE_") and reason.dependency_id
        }
        for prerequisite in graph[current]:
            if prerequisite not in direct_missing or prerequisite in missing:
                continue
            missing.add(prerequisite)
            visit(prerequisite)

    visit(identity)
    return tuple(sorted(missing, key=order.__getitem__))


def _effective_cost(identity, graph, order, unmet, evidence):
    item = evidence[identity].acquisition_cost
    ancestors = _ancestors(identity, graph, order)
    transfer = item.transfer_savings
    if transfer is not None and any(
            prerequisite not in ancestors for prerequisite, _ in transfer):
        _fail("BAMF_GENERATED_GRADE_TRANSFER_NOT_CONSTITUENT")
    savings = 0 if transfer is None else sum(
        value for prerequisite, value in transfer if prerequisite not in unmet)
    return None if item.units is None else max(0, item.units - savings)


def decision_for(identity, grouped_rows, graph, order, evidence, policy):
    rows = grouped_rows[identity]
    prerequisites = graph[identity]
    unmet = _unmet_prerequisites(identity, grouped_rows, graph, order)
    required = (*unmet, identity)
    unlawful = any(item.status in {
        ClosureStatus.SOURCE_HELD, ClosureStatus.IMPLEMENTATION_UNCOVERED,
    } for item in rows)
    reasons: tuple[str, ...] = ()
    disposition = "ELIGIBLE"
    if unlawful or any(not item.reasons and item.status not in {
            ClosureStatus.READY, ClosureStatus.WAITING_FOR_EVIDENCE} for item in rows):
        disposition, reasons = "DEFERRED_UNLAWFUL", ("A09_CLOSURE_NOT_LAWFUL",)
    elif evidence[identity].grounding_quality == 0:
        disposition, reasons = (
            "DEFERRED_UNGROUNDED", ("FACTORY_OBJECTIVE_GROUNDING_REQUIRED",))
    elif len(unmet) > policy.max_unmet_prerequisites:
        disposition, reasons = "DEFERRED_STEEP_CLOSURE", ("UNMET_PREREQUISITE_BOUND",)
    development = evidence[identity]
    cost = development.acquisition_cost
    transfer = cost.transfer_savings
    savings = 0 if transfer is None else sum(
        value for prerequisite, value in transfer if prerequisite not in unmet)
    effective = _effective_cost(identity, graph, order, unmet, evidence)
    closure_costs = [effective, *(
        _effective_cost(
            item, graph, order,
            _unmet_prerequisites(item, grouped_rows, graph, order), evidence)
        for item in unmet)]
    closure_cost = None if any(item is None for item in closure_costs) else sum(closure_costs)
    return CandidateGradeDecision(
        identity, development.compiled_capability_ids,
        development.source_anchor_ids, tuple(sorted(item.family_id for item in rows)),
        prerequisites, unmet, required, development.neighborhood_id,
        development.coverage_factors, cost.status, cost.measure, cost.units,
        effective, closure_cost, savings, transfer, development.grounding_quality,
        development.answer_modality_burden, development.ast_burden,
        development.entanglement, development.reusable_constituent_value,
        development.downstream_unlocks, development.minimal_contrast_value,
        development.transfer_breadth, development.learning_progress,
        development.fairness_age, development.a09_prerequisite_slope,
        development.a09_cursor_distance, development.a09_statuses,
        development.a09_reason_receipts, development.planning_compute_units,
        tuple(sorted(item.source_evidence_sha256 for item in rows)),
        development.evidence_sha256, disposition, reasons,
    )
