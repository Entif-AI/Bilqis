"""Canonical candidate-to-Factory realization for generated-grade evidence."""
from bilqis_mlx.factory import candidate_realizations
from bilqis_mlx.factory.candidate_staging import candidate_source_anchor

def _realization(epoch, semantic_id, rows):
    capabilities, anchors = [], []
    try:
        projection = candidate_realizations.project_authoritative_target(
            semantic_id, epoch.current_release, rows)
    except ValueError:
        projection = None
    if projection is not None:
        capabilities.extend(projection.added_capability_ids)
        anchors.extend(
            staged.source_anchor for staged in epoch.staged_candidates
            if staged.target_capability_id in projection.added_capability_ids)
    try:
        capability_id = candidate_realizations.realized_capability_id(semantic_id)
    except ValueError:
        capability_id = None
    if capability_id is not None:
        capabilities.append(capability_id)
    if capability_id in epoch.current_release.execution_plan.capability_map:
        anchors.append(epoch.current_release.source_bindings.by_capability[
            capability_id].source_anchor)
    for staged in epoch.staged_candidates:
        try:
            staged_semantic = candidate_realizations.realized_atlas_semantic_id(
                staged.target_capability_id)
        except ValueError:
            staged_semantic = None
        if staged_semantic == semantic_id or staged.source_sense_id == semantic_id:
            capabilities.append(staged.target_capability_id)
            anchors.append(staged.source_anchor)
    if capability_id is not None and not anchors:
        matches = tuple(item for item in epoch.candidate_frontier.candidates
                        if item.proposed_capability_id == capability_id)
        if len(matches) == 1:
            anchors.append(candidate_source_anchor(
                epoch.candidate_frontier, matches[0].candidate_id))
    return tuple(sorted(set(capabilities))), tuple(sorted(set(anchors)))
