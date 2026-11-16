"""Pure #1320 cohort synthesis over A09's immutable lawful frontier."""
from __future__ import annotations
from dataclasses import replace
from bilqis_mlx.factory.atlas_frontier_closure import ClosureStatus, FrontierClosure
from bilqis_mlx.factory.atlas_frontier_contracts import CurriculumSnapshot, _fail
from bilqis_mlx.factory.atlas_frontier_selection_validation import validate_closure_structure
from bilqis_mlx.factory.executable_release import ExecutableFactoryRelease
from .contracts import (
    AcceptedLearnerFoot,
    CandidateDevelopmentEvidence,
    CandidateGradeDecision,
    CostEvidenceKind,
    GeneratedGradeInputs,
    GeneratedGradePolicy,
    GeneratedGradeProposal,
)
def synthesize_generated_grade(
    snapshot: CurriculumSnapshot,
    closure: FrontierClosure,
    current_release: ExecutableFactoryRelease,
    inputs: GeneratedGradeInputs,
) -> GeneratedGradeProposal:
    """Choose one bounded developmental contour without staging or admission."""
    if type(inputs) is not GeneratedGradeInputs:
        _fail("BAMF_GENERATED_GRADE_INPUT_AUTHORITY_REQUIRED")
    inputs.__post_init__()
    if inputs.input_sha256 != inputs.expected_digest():
        _fail("BAMF_GENERATED_GRADE_INPUT_DIGEST_INVALID")
    learner = inputs.learner
    candidate_evidence = inputs.candidate_evidence
    policy = inputs.policy
    _validate_inputs(snapshot, closure, current_release, learner, candidate_evidence, policy)
    graph = _graph(closure)
    order = {identity: index for index, identity in enumerate(closure.constituent_order)}
    rows = _grouped(closure)
    evidence = {item.semantic_id: item for item in candidate_evidence}
    decisions = {
        identity: _decision(identity, rows, graph, order, evidence, policy)
        for identity in sorted(rows)
    }
    capacity = min(policy.max_members, snapshot.budget.max_candidates,
                   snapshot.budget.max_identity_rows)
    selected_targets: list[str] = []
    members: set[str] = set()
    compute = 0
    deferred_reasons: dict[str, str] = {}
    eligible = [item for item in decisions.values()
                if item.disposition == "ELIGIBLE"]
    ranked = _pareto_ranked(eligible, policy)
    seen_neighborhoods: set[str] = set()
    for representative_only in (True, False):
        for item in ranked:
            if item.semantic_id in selected_targets:
                continue
            if representative_only and item.neighborhood_id in seen_neighborhoods:
                continue
            new_members = set(item.required_semantic_ids) - members
            next_compute = compute + sum(
                decisions[member].planning_compute_units for member in new_members)
            if len(members | new_members) > capacity:
                deferred_reasons[item.semantic_id] = "MEMBER_CAPACITY_BOUND"
                continue
            if next_compute > snapshot.budget.max_compute_units:
                deferred_reasons[item.semantic_id] = "PLANNING_COMPUTE_BOUND"
                continue
            selected_targets.append(item.semantic_id)
            members |= new_members
            compute = next_compute
            seen_neighborhoods.add(item.neighborhood_id)
    selected_set = set(selected_targets)
    for identity, item in tuple(decisions.items()):
        if identity in selected_set:
            decisions[identity] = replace(
                item, disposition="SELECTED_TARGET",
                reason_codes=("PARETO_A09_POLICY_SELECTED",))
        elif identity in members:
            decisions[identity] = replace(
                item, disposition="SELECTED_BRIDGE", reason_codes=("REQUIRED_CONSTITUENT_BRIDGE",))
        elif item.disposition == "ELIGIBLE":
            reason = deferred_reasons.get(identity)
            if reason is None:
                reason = ("NEIGHBORHOOD_REDUNDANT" if any(
                    decisions[selected].neighborhood_id == item.neighborhood_id
                    for selected in selected_targets) else "COMPARATOR_LOWER_PRIORITY")
            decisions[identity] = replace(
                item, disposition="DEFERRED_NEAR_FRONTIER",
                reason_codes=(reason,))
    member_ids = tuple(identity for identity in closure.constituent_order if identity in members)
    provisional = GeneratedGradeProposal(
        snapshot.snapshot_sha256,
        closure.closure_sha256,
        current_release.release_sha256,
        learner.digest(),
        learner.evidence_epoch,
        snapshot.policy_epoch,
        policy.digest(),
        inputs.input_sha256,
        inputs.a09_progress_sha256,
        inputs.a09_status,
        inputs.a09_handoff_sha256,
        inputs.a09_proposal_sha256,
        member_ids,
        tuple(decisions[identity] for identity in sorted(decisions)),
        tuple(sorted((item.source_id, item.reason_code, item.owner)
                     for item in closure.source_holds)),
        "0" * 64,
    )
    result = replace(provisional, proposal_sha256=provisional.expected_digest())
    result.verify()
    return result

def _validate_inputs(snapshot, closure, release, learner, candidate_evidence, policy) -> None:
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
            or set(evidence_ids) != set(candidate_ids)):
        _fail("BAMF_GENERATED_GRADE_EVIDENCE_CENSUS_INVALID")


def _graph(closure: FrontierClosure) -> dict[str, tuple[str, ...]]:
    result = {identity: () for identity in closure.constituent_order}
    for identity in result:
        rows = [item for item in closure.candidates if item.semantic_id == identity]
        prerequisite_sets = {item.prerequisites for item in rows}
        if len(prerequisite_sets) != 1:
            _fail("BAMF_GENERATED_GRADE_PREREQUISITE_DRIFT")
        result[identity] = next(iter(prerequisite_sets))
    return result


def _grouped(closure: FrontierClosure):
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

def _decision(identity, grouped_rows, graph, order, evidence, policy):
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
        identity,
        development.compiled_capability_ids,
        development.source_anchor_ids,
        tuple(sorted(item.family_id for item in rows)),
        prerequisites,
        unmet,
        required,
        development.neighborhood_id,
        development.coverage_factors,
        cost.status,
        cost.measure,
        cost.units,
        effective,
        closure_cost,
        savings,
        transfer,
        development.grounding_quality,
        development.answer_modality_burden,
        development.ast_burden,
        development.entanglement,
        development.reusable_constituent_value,
        development.downstream_unlocks,
        development.minimal_contrast_value,
        development.transfer_breadth,
        development.learning_progress,
        development.fairness_age,
        development.a09_prerequisite_slope,
        development.a09_cursor_distance,
        development.a09_statuses,
        development.a09_reason_receipts,
        development.planning_compute_units,
        tuple(sorted(item.source_evidence_sha256 for item in rows)),
        development.evidence_sha256,
        disposition,
        reasons,
    )


def _cost_rank(item: CandidateGradeDecision) -> int:
    if item.closure_acquisition_units is None:
        return 2
    return {
        CostEvidenceKind.MEASURED: 0,
        CostEvidenceKind.BOOTSTRAPPED: 1,
        CostEvidenceKind.UNKNOWN: 2,
    }[item.cost_status]


def _a09_rank_key(item: CandidateGradeDecision, policy: GeneratedGradePolicy):
    components = {
        "prerequisite_slope": item.a09_prerequisite_slope,
        "downstream_unlocks_desc": -item.downstream_unlocks,
        "cursor_distance": item.a09_cursor_distance,
        "semantic_id": item.semantic_id,
    }
    return tuple(components[name] for name in policy.comparator_order)


def _pareto_vector(
    item: CandidateGradeDecision, policy: GeneratedGradePolicy,
) -> tuple[int, ...]:
    components = {
        "cost_evidence_rank": _cost_rank(item),
        "closure_acquisition_units": (
            item.closure_acquisition_units
            if item.closure_acquisition_units is not None else 10**18),
        "coverage_factor_count_desc": -len(item.coverage_factors),
    }
    return tuple(components[name] for name in policy.pareto_dimensions)


def _dominates(
    left: CandidateGradeDecision, right: CandidateGradeDecision,
    policy: GeneratedGradePolicy,
) -> bool:
    a, b = _pareto_vector(left, policy), _pareto_vector(right, policy)
    return all(x <= y for x, y in zip(a, b)) and any(
        x < y for x, y in zip(a, b))


def _pareto_ranked(
    items: list[CandidateGradeDecision], policy: GeneratedGradePolicy,
) -> list[CandidateGradeDecision]:
    """Layer an unweighted cost/coverage Pareto frontier, then reuse A09 tie-breaks."""
    remaining = list(items)
    result: list[CandidateGradeDecision] = []
    while remaining:
        frontier = [
            item for item in remaining
            if not any(_dominates(other, item, policy)
                       for other in remaining if other is not item)
        ]
        frontier.sort(key=lambda item: _a09_rank_key(item, policy))
        result.extend(frontier)
        chosen = set(item.semantic_id for item in frontier)
        remaining = [item for item in remaining if item.semantic_id not in chosen]
    return result


def _rank_key(item: CandidateGradeDecision, policy: GeneratedGradePolicy):
    """Compatibility helper: A09 remains the deterministic within-frontier order."""
    return _a09_rank_key(item, policy)
