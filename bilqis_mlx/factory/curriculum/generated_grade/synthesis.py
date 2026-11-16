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
    mastered = set(learner.baselined_semantic_ids)
    decisions = {
        identity: _decision(identity, rows[identity], graph, order, mastered,
                            evidence, policy)
        for identity in sorted(rows)
        if identity not in mastered
    }
    capacity = min(policy.max_members, snapshot.budget.max_candidates,
                   snapshot.budget.max_identity_rows)
    selected_targets: list[str] = []
    members: set[str] = set()
    compute = 0
    deferred_reasons: dict[str, str] = {}
    eligible = [item for item in decisions.values()
                if item.disposition == "ELIGIBLE"]
    ranked = sorted(eligible, key=lambda item: _rank_key(item, policy))
    seen_neighborhoods: set[str] = set()
    for representative_only in (True, False):
        for item in ranked:
            if item.semantic_id in selected_targets:
                continue
            if representative_only and item.neighborhood_id in seen_neighborhoods:
                continue
            new_members = set(item.required_semantic_ids) - members - mastered
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
                reason_codes=("LEXICOGRAPHIC_POLICY_SELECTED",))
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
            or learner.evidence_epoch != snapshot.qualification_epoch):
        _fail("BAMF_GENERATED_GRADE_AUTHORITY_MISMATCH")
    candidate_ids = tuple(sorted({item.semantic_id for item in closure.candidates}))
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


def _effective_cost(identity, graph, order, mastered, evidence, policy):
    item = evidence[identity].acquisition_cost
    ancestors = _ancestors(identity, graph, order)
    if item.measure != policy.acquisition_cost_measure:
        _fail("BAMF_GENERATED_GRADE_COST_MEASURE_MISMATCH")
    if any(prerequisite not in ancestors for prerequisite, _ in item.transfer_savings):
        _fail("BAMF_GENERATED_GRADE_TRANSFER_NOT_CONSTITUENT")
    savings = sum(value for prerequisite, value in item.transfer_savings
                  if prerequisite in mastered)
    return None if item.units is None else max(0, item.units - savings)

def _decision(identity, rows, graph, order, mastered, evidence, policy):
    prerequisites = graph[identity]
    ancestors = _ancestors(identity, graph, order)
    unmet = tuple(item for item in ancestors if item not in mastered)
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
    savings = sum(value for prerequisite, value in cost.transfer_savings
                  if prerequisite in mastered)
    effective = _effective_cost(identity, graph, order, mastered, evidence, policy)
    closure_costs = [effective, *(
        _effective_cost(item, graph, order, mastered, evidence, policy)
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
        development.planning_compute_units,
        tuple(sorted(item.source_evidence_sha256 for item in rows)),
        development.evidence_sha256,
        disposition,
        reasons,
    )


def _rank_key(item: CandidateGradeDecision, policy: GeneratedGradePolicy):
    cost_rank = 2 if item.closure_acquisition_units is None else {
        CostEvidenceKind.MEASURED: 0,
        CostEvidenceKind.BOOTSTRAPPED: 1,
        CostEvidenceKind.UNKNOWN: 2,
    }[item.cost_status]
    cost_units = item.closure_acquisition_units or 0
    components = {
        "unmet_prerequisite_count": len(item.unmet_prerequisite_ids),
        "answer_modality_burden": item.answer_modality_burden,
        "ast_burden": item.ast_burden,
        "entanglement": item.entanglement,
        "cost_evidence_rank": cost_rank,
        "closure_acquisition_units": cost_units,
        "grounding_quality_desc": -item.grounding_quality,
        "reusable_constituent_value_desc": -item.reusable_constituent_value,
        "downstream_unlocks_desc": -item.downstream_unlocks,
        "minimal_contrast_value_desc": -item.minimal_contrast_value,
        "transfer_breadth_desc": -item.transfer_breadth,
        "learning_progress_desc": -item.learning_progress,
        "coverage_factor_count_desc": -len(item.coverage_factors),
        "fairness_age_desc": -item.fairness_age,
        "semantic_id": item.semantic_id,
    }
    return tuple(components[name] for name in policy.comparator_order)
