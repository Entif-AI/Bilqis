"""Ranking helpers for generated-grade synthesis."""
from __future__ import annotations

from .contracts import CandidateGradeDecision, CostEvidenceKind, GeneratedGradePolicy


def _cost_rank(item: CandidateGradeDecision) -> int:
    if item.closure_acquisition_units is None:
        return 2
    return {
        CostEvidenceKind.MEASURED: 0,
        CostEvidenceKind.BOOTSTRAPPED: 1,
        CostEvidenceKind.UNKNOWN: 2,
    }[item.cost_status]


def a09_rank_key(item: CandidateGradeDecision, policy: GeneratedGradePolicy):
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
    unknown = 10**18

    def ascending(value):
        return value if value is not None else unknown

    def descending(value):
        return -value if value is not None else unknown

    components = {
        "a09_prerequisite_slope": item.a09_prerequisite_slope,
        "cost_evidence_rank": _cost_rank(item),
        "closure_acquisition_units": (
            item.closure_acquisition_units
            if item.closure_acquisition_units is not None else unknown),
        "answer_modality_burden": ascending(item.answer_modality_burden),
        "ast_burden": ascending(item.ast_burden),
        "entanglement": ascending(item.entanglement),
        "coverage_factor_count_desc": -len(item.coverage_factors),
        "reusable_constituent_value_desc": descending(
            item.reusable_constituent_value),
        "downstream_unlocks_desc": -item.downstream_unlocks,
        "minimal_contrast_value_desc": descending(item.minimal_contrast_value),
        "transfer_breadth_desc": descending(item.transfer_breadth),
        "learning_progress_desc": descending(item.learning_progress),
    }
    return tuple(components[name] for name in policy.pareto_dimensions)


def _dominates(
    left: CandidateGradeDecision, right: CandidateGradeDecision,
    policy: GeneratedGradePolicy,
) -> bool:
    a, b = _pareto_vector(left, policy), _pareto_vector(right, policy)
    return all(x <= y for x, y in zip(a, b)) and any(
        x < y for x, y in zip(a, b))


def pareto_ranked(
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
        frontier.sort(key=lambda item: a09_rank_key(item, policy))
        result.extend(frontier)
        chosen = {item.semantic_id for item in frontier}
        remaining = [item for item in remaining if item.semantic_id not in chosen]
    return result


def rank_key(item: CandidateGradeDecision, policy: GeneratedGradePolicy):
    """Compatibility helper: A09 remains the deterministic within-frontier order."""
    return a09_rank_key(item, policy)
