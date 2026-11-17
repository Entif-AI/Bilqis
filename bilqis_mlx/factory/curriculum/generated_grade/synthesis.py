"""Pure #1320 cohort synthesis over A09's immutable lawful frontier."""
from __future__ import annotations
from dataclasses import replace
from bilqis_mlx.factory.atlas_frontier_closure import FrontierClosure
from bilqis_mlx.factory.atlas_frontier_contracts import CurriculumSnapshot, _fail
from bilqis_mlx.factory.executable_release import ExecutableFactoryRelease
from .contracts import (
    AcceptedLearnerFoot,
    CandidateDevelopmentEvidence,
    CandidateGradeDecision,
    GeneratedGradeInputs,
    GeneratedGradePolicy,
    GeneratedGradeProposal,
)
from .proposal_contracts import (
    GENERATED_GRADE_INPUTS_V2,
    GENERATED_GRADE_PROPOSAL_V1,
    GENERATED_GRADE_PROPOSAL_V2,
)
from .synthesis_graph import decision_for as _decision
from .synthesis_graph import graph_for as _graph
from .synthesis_graph import grouped_rows as _grouped
from .synthesis_graph import validate_inputs as _validate_inputs
from .synthesis_ranking import a09_rank_key as _a09_rank_key
from .synthesis_ranking import pareto_ranked as _pareto_ranked
from .synthesis_ranking import rank_key as _rank_key


def _select_members(decisions, ranked, snapshot, policy):
    capacity = min(
        policy.max_members, snapshot.budget.max_candidates,
        snapshot.budget.max_identity_rows)
    selected_targets: list[str] = []
    members: set[str] = set()
    compute = 0
    deferred_reasons: dict[str, str] = {}
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
    return selected_targets, members, deferred_reasons


def _finalize_decisions(decisions, selected_targets, members, deferred_reasons):
    selected_set = set(selected_targets)
    for identity, item in tuple(decisions.items()):
        if identity in selected_set:
            decisions[identity] = replace(
                item, disposition="SELECTED_TARGET",
                reason_codes=("PARETO_A09_POLICY_SELECTED",))
        elif identity in members:
            decisions[identity] = replace(
                item, disposition="SELECTED_BRIDGE",
                reason_codes=("REQUIRED_CONSTITUENT_BRIDGE",))
        elif item.disposition == "ELIGIBLE":
            reason = deferred_reasons.get(identity)
            if reason is None:
                reason = ("NEIGHBORHOOD_REDUNDANT" if any(
                    decisions[selected].neighborhood_id == item.neighborhood_id
                    for selected in selected_targets) else "COMPARATOR_LOWER_PRIORITY")
            decisions[identity] = replace(
                item, disposition="DEFERRED_NEAR_FRONTIER",
                reason_codes=(reason,))


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
        for identity in sorted(evidence)
    }
    eligible = [item for item in decisions.values()
                if item.disposition == "ELIGIBLE"]
    ranked = _pareto_ranked(eligible, policy)
    selected_targets, members, deferred_reasons = _select_members(
        decisions, ranked, snapshot, policy)
    _finalize_decisions(decisions, selected_targets, members, deferred_reasons)
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
        predecessor_certification_sha256=(
            inputs.predecessor_certification_sha256),
        schema=(
            GENERATED_GRADE_PROPOSAL_V2
            if inputs.schema == GENERATED_GRADE_INPUTS_V2
            else GENERATED_GRADE_PROPOSAL_V1),
    )
    result = replace(provisional, proposal_sha256=provisional.expected_digest())
    result.verify()
    return result
