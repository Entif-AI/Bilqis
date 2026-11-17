"""Learner-relative developmental evidence compiled from accepted owners."""
import hashlib
from bilqis_mlx.factory._autonomy.contracts import release_capabilities
from bilqis_mlx.factory.atlas_frontier_closure import semantic_roots_for_mastered_capabilities
from bilqis_mlx.factory.atlas_frontier_contracts import _bytes
from bilqis_mlx.factory.atlas_frontier_selection import frontier_target_metrics
from .candidate_inputs import _realization
from .contracts import AcquisitionCostEvidence, CandidateDevelopmentEvidence, CostEvidenceKind
from .cost_inputs import _measured_cost_profile

def _reusable_constituent_value(
    semantic_id: str,
    graph: dict[str, set[str]],
) -> int:
    """Count compiled descendants that can reuse this semantic as a constituent."""
    reusable = 0
    for candidate in graph:
        if candidate == semantic_id:
            continue
        pending = list(graph[candidate])
        seen = set()
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            if current == semantic_id:
                reusable += 1
                break
            seen.add(current)
            pending.extend(graph.get(current, ()))
    return reusable


def _minimal_contrast_value(
    semantic_id: str,
    families: dict[str, set[str]],
    mastered_semantics: set[str],
) -> int:
    """Count candidate families already grounded by accepted mastered semantics."""
    mastered_families = {
        family
        for mastered in mastered_semantics
        for family in families.get(mastered, ())
    }
    return len(families[semantic_id].intersection(mastered_families))


def _development_context(epoch, foot):
    graph = {identity: set() for identity in epoch.closure.constituent_order}
    families = {identity: set() for identity in graph}
    for row in epoch.closure.candidates:
        graph[row.semantic_id].update(row.prerequisites)
        families[row.semantic_id].add(row.family_id)
    metrics = {item.semantic_id: item for item in frontier_target_metrics(
        epoch.snapshot, epoch.closure)}
    mastered_semantics = set(semantic_roots_for_mastered_capabilities(
        epoch.current_release, foot.mastered_capability_ids))
    mastered_family_ids = {
        family
        for identity in mastered_semantics
        for family in families.get(identity, set())
    }
    capability_definitions = {
        item.capability_id: item for item in release_capabilities(epoch.current_release)}
    semantic_specs = dict(epoch.current_release.curriculum.capability_map)
    for staged in epoch.staged_candidates:
        successor = getattr(staged, "successor", None)
        if successor is None:
            continue
        capability_definitions.update({
            item.capability_id: item for item in release_capabilities(successor)})
        semantic_specs.update(successor.curriculum.capability_map)
    return (
        graph, families, metrics, mastered_semantics, mastered_family_ids,
        capability_definitions, semantic_specs)


def _candidate_measurements(
    epoch, foot, learner, plan, semantic_id, graph, family_ids,
    capability_ids, capability_definitions, semantic_specs, rows,
):
    unmet = {
        reason.dependency_id
        for row in rows for reason in row.reasons
        if reason.code.startswith("PREREQUISITE_") and reason.dependency_id
    }
    prerequisite_capabilities = tuple(
        (prerequisite, _realization(
            epoch, prerequisite,
            tuple(item for item in epoch.closure.candidates
                  if item.semantic_id == prerequisite))[0])
        for prerequisite in sorted(graph[semantic_id]))
    measured_cost, learning_progress = _measured_cost_profile(
        epoch, learner, plan, foot, capability_ids, family_ids,
        prerequisite_capabilities)
    cost = measured_cost or AcquisitionCostEvidence(
        CostEvidenceKind.BOOTSTRAPPED,
        "a09-unmet-prerequisite-slope/v1",
        1 + len(unmet),
        None,
    )
    modality_complete = bool(capability_ids) and all(
        capability_id in capability_definitions for capability_id in capability_ids)
    answer_kinds = ({
        kind for capability_id in capability_ids
        for kind in capability_definitions[capability_id].answer_kinds
    } if modality_complete else set())
    ast_complete = bool(capability_ids) and all(
        capability_id in semantic_specs for capability_id in capability_ids)
    ast_burden = (sum(
        len(semantic_specs[capability_id].taught_roots)
        + len(semantic_specs[capability_id].prerequisites)
        + len(semantic_specs[capability_id].composed_of)
        for capability_id in capability_ids
    ) if ast_complete else None)
    return unmet, cost, learning_progress, modality_complete, answer_kinds, ast_burden


def _candidate_development_evidence(
    epoch, foot, learner, plan, semantic_id, context,
):
    (graph, families, metrics, mastered_semantics, mastered_family_ids,
     capability_definitions, semantic_specs) = context
    rows = tuple(item for item in epoch.closure.candidates
                 if item.semantic_id == semantic_id)
    capability_ids, anchors = _realization(epoch, semantic_id, rows)
    family_ids = tuple(sorted(families[semantic_id]))
    neighborhood_id = hashlib.sha256(_bytes((
        "a09-family-prerequisite-neighborhood/v2",
        family_ids,
        tuple(sorted(graph[semantic_id])),
    ))).hexdigest()
    metric = metrics[semantic_id]
    (unmet, cost, learning_progress, modality_complete,
     answer_kinds, ast_burden) = _candidate_measurements(
        epoch, foot, learner, plan, semantic_id, graph, family_ids,
        capability_ids, capability_definitions, semantic_specs, rows)
    transfer = cost.transfer_savings
    reusable_constituent_value = _reusable_constituent_value(semantic_id, graph)
    minimal_contrast_value = _minimal_contrast_value(
        semantic_id, families, mastered_semantics)
    return CandidateDevelopmentEvidence(
            semantic_id=semantic_id,
            compiled_capability_ids=capability_ids,
            source_anchor_ids=anchors,
            neighborhood_id=neighborhood_id,
            coverage_factors=tuple(
                family for family in family_ids if family not in mastered_family_ids),
            acquisition_cost=cost,
            grounding_quality=(
                len(anchors) + len(answer_kinds)
                if anchors and modality_complete and answer_kinds else 0),
            answer_modality_burden=(
                len(answer_kinds) if modality_complete else None),
            ast_burden=ast_burden,
            entanglement=len(unmet),
            reusable_constituent_value=reusable_constituent_value,
            downstream_unlocks=metric.downstream_unlocks,
            minimal_contrast_value=minimal_contrast_value,
            transfer_breadth=None if transfer is None else len(transfer),
            learning_progress=learning_progress,
            fairness_age=None,
            a09_prerequisite_slope=metric.prerequisite_slope,
            a09_cursor_distance=metric.cursor_distance,
            a09_statuses=metric.statuses,
            a09_reason_receipts=metric.reason_receipts,
            planning_compute_units=max(1, 1 + len(unmet)),
            evidence_sha256=hashlib.sha256(_bytes({
                "semantic_id": semantic_id, "families": family_ids,
                "prerequisites": tuple(sorted(graph[semantic_id])),
                "capabilities": capability_ids, "anchors": anchors,
                "a09_metrics": metric,
                "acquisition_cost": cost,
                "reusable_constituent_value": reusable_constituent_value,
                "minimal_contrast_value": minimal_contrast_value,
                "learner": foot.evidence_sha256,
            })).hexdigest(),
        )


def _development_evidence(epoch, foot, learner, plan) -> tuple[CandidateDevelopmentEvidence, ...]:
    context = _development_context(epoch, foot)
    mastered_semantics = context[3]
    results = [
        _candidate_development_evidence(
            epoch, foot, learner, plan, semantic_id, context)
        for semantic_id in epoch.closure.constituent_order
        if semantic_id not in mastered_semantics
    ]
    return tuple(sorted(results, key=lambda item: item.semantic_id))
