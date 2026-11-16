"""Accepted acquisition-cost and transfer evidence for generated grades."""
from bilqis_mlx.factory._autonomy.contracts import release_capabilities
from bilqis_mlx.factory.autonomy import (
    EvidenceLedger, evidence_complete_capabilities, obligations_for_capability,
)
from .candidate_inputs import _realization
from .contracts import AcquisitionCostEvidence, CostEvidenceKind

_MIN_PROGRESS_OBSERVATIONS = 2

def _mastery_before_intervention(epoch, learner, plan, intervention):
    ledger = learner.ledger
    before = EvidenceLedger(
        ledger.factory_release_sha256,
        ledger.autonomy_plan_sha256,
        tuple(receipt for receipt in ledger.receipts
              if receipt.optimizer_step <= intervention.parent_optimizer_step),
        tuple(receipt for receipt in ledger.interventions
              if receipt.optimizer_step <= intervention.parent_optimizer_step),
        tuple(receipt for receipt in ledger.rejected_attempts
              if receipt.retained_optimizer_step <= intervention.parent_optimizer_step),
    )
    return set(evidence_complete_capabilities(
        epoch.current_release, before, plan=plan,
        current_checkpoint_sha256=intervention.parent_checkpoint_sha256,
        current_optimizer_step=intervention.parent_optimizer_step))


def _qualified_transfer_savings(cost_rows, prerequisite_capabilities):
    """Return only causal prerequisite comparisons with both control arms."""
    result = []
    for semantic_id, capability_ids in prerequisite_capabilities:
        capabilities = set(capability_ids)
        treatment = [cost for cost, mastered in cost_rows
                     if capabilities.intersection(mastered)]
        control = [cost for cost, mastered in cost_rows
                   if not capabilities.intersection(mastered)]
        if not treatment or not control:
            continue
        treatment_mean = (sum(treatment) + len(treatment) - 1) // len(treatment)
        control_mean = (sum(control) + len(control) - 1) // len(control)
        result.append((semantic_id, control_mean - treatment_mean))
    return tuple(sorted(result)) or None


def _measured_cost_profile(
    epoch, learner, plan, foot, capability_ids, family_ids,
    prerequisite_capabilities=(),
):
    """Estimate candidate cost from accepted completed same-family teaching history."""
    known = {item.capability_id for item in release_capabilities(epoch.current_release)}
    mastered = set(foot.mastered_capability_ids)
    candidate_families = set(family_ids)
    comparable: set[str] = {
        capability for capability in capability_ids
        if capability in known and capability in mastered
    }
    if not comparable:
        for semantic_id in epoch.closure.constituent_order:
            rows = tuple(row for row in epoch.closure.candidates
                         if row.semantic_id == semantic_id)
            if not candidate_families.intersection(row.family_id for row in rows):
                continue
            realized, _anchors = _realization(epoch, semantic_id, rows)
            comparable.update(capability for capability in realized
                              if capability in known and capability in mastered)
    if not comparable:
        return None, None
    costs = []
    cost_rows = []
    history_episodes = []
    for capability in sorted(comparable):
        obligation_ids = {
            obligation.obligation_id
            for obligation in obligations_for_capability(
                epoch.current_release, capability, plan=plan)
        }
        interventions = tuple(
            receipt for receipt in learner.ledger.interventions
            if receipt.obligation_id in obligation_ids
            and receipt.optimizer_step_delta is not None)
        ordered = tuple(sorted(
            interventions,
            key=lambda item: (
                item.parent_optimizer_step,
                item.optimizer_step,
                item.intervention_id,
            ),
        ))
        if ordered:
            episode_cost = sum(
                receipt.optimizer_step_delta for receipt in ordered)
            episode_start = ordered[0]
            costs.append(episode_cost)
            cost_rows.append((
                episode_cost,
                _mastery_before_intervention(
                    epoch, learner, plan, episode_start),
            ))
            history_episodes.append((
                episode_start.parent_optimizer_step,
                episode_start.optimizer_step,
                capability,
                episode_cost,
            ))
    if not costs:
        return None, None
    units = (sum(costs) + len(costs) - 1) // len(costs)
    evidence = AcquisitionCostEvidence(
        CostEvidenceKind.MEASURED,
        "accepted-teaching-family-mean-ceil/v1",
        units,
        _qualified_transfer_savings(cost_rows, prerequisite_capabilities),
    )
    ordered_history = tuple(sorted(history_episodes))
    progress = (
        None if len(ordered_history) < _MIN_PROGRESS_OBSERVATIONS
        else max(0, ordered_history[0][-1] - ordered_history[-1][-1]))
    return evidence, progress


def _measured_acquisition_cost(
    epoch, learner, plan, foot, capability_ids, family_ids,
    prerequisite_capabilities=(),
):
    return _measured_cost_profile(
        epoch, learner, plan, foot, capability_ids, family_ids,
        prerequisite_capabilities)[0]
