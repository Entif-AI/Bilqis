"""Authority-bound #1320 inputs derived from the existing A09 state machine."""
from __future__ import annotations

from dataclasses import replace
import hashlib

from bilqis_mlx.factory.atlas_delta_scope import AtlasDeltaScopeHandoff
from bilqis_mlx.factory.atlas_frontier import AtlasCoverageEpoch, AtlasLearnerEvidence, next_atlas_delta
from bilqis_mlx.factory.atlas_frontier_progress import FrontierStatus, plan_frontier_progress
from bilqis_mlx.factory.atlas_frontier_selection import frontier_target_metrics
from bilqis_mlx.factory.atlas_frontier_progress_validation import (
    credited_obligation_keys, current_obligations,
)
from bilqis_mlx.factory.autonomy import (
    AutonomyPlan, evidence_complete_capabilities, obligations_for_capability,
)
from bilqis_mlx.factory._autonomy.contracts import release_capabilities
from bilqis_mlx.factory import candidate_realizations
from bilqis_mlx.factory.candidate_staging import candidate_source_anchor
from bilqis_mlx.factory.atlas_frontier_contracts import _bytes, _fail

from .contracts import (
    AcceptedLearnerFoot, AcquisitionCostEvidence, CandidateDevelopmentEvidence,
    CostEvidenceKind, GeneratedGradeInputs, GeneratedGradePolicy, _issue_inputs,
)


def _a09_baselines(epoch: AtlasCoverageEpoch) -> tuple[str, ...]:
    current = current_obligations(epoch.closure)
    keys = set()
    if epoch.accepted_credit is not None:
        keys.update(key for key in epoch.accepted_credit.obligation_keys
                    if current.get(key[0]) == key[1])
    if epoch.prior is not None:
        keys.update(credited_obligation_keys(
            epoch.snapshot, epoch.closure, epoch.prior, current))
    return tuple(sorted(identity for identity, _digest in keys))


def _learner_foot(epoch, learner, plan) -> AcceptedLearnerFoot:
    mastered = evidence_complete_capabilities(
        epoch.current_release, learner.ledger, plan=plan,
        current_checkpoint_sha256=learner.checkpoint_sha256,
        current_optimizer_step=learner.optimizer_step)
    evidence_sha256 = hashlib.sha256(_bytes({
        "ledger": learner.ledger, "checkpoint": learner.checkpoint_sha256,
        "optimizer_step": learner.optimizer_step, "plan": plan.digest(),
        "baselines": _a09_baselines(epoch),
    })).hexdigest()
    return AcceptedLearnerFoot(
        learner.checkpoint_sha256, learner.optimizer_step,
        epoch.current_release.release_sha256, epoch.snapshot.policy_epoch,
        epoch.snapshot.qualification_epoch, _a09_baselines(epoch),
        tuple(sorted(mastered)), evidence_sha256)


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


def _measured_acquisition_cost(epoch, learner, plan, foot, capability_ids):
    """Use accepted teaching receipts only when they bind an exact live capability."""
    known = {item.capability_id for item in release_capabilities(epoch.current_release)}
    mastered = set(foot.mastered_capability_ids)
    matched = tuple(
        capability for capability in capability_ids
        if capability in known and capability in mastered)
    if not matched:
        return None
    obligation_ids = {
        obligation.obligation_id
        for capability in matched
        for obligation in obligations_for_capability(
            epoch.current_release, capability, plan=plan)
    }
    deltas = tuple(
        receipt.optimizer_step_delta
        for receipt in learner.ledger.interventions
        if receipt.obligation_id in obligation_ids
        and receipt.optimizer_step_delta is not None
    )
    if not deltas:
        return None
    return AcquisitionCostEvidence(
        CostEvidenceKind.MEASURED,
        "accepted-teaching-optimizer-steps/v1",
        sum(deltas),
        None,
    )


def _development_evidence(epoch, foot, learner, plan) -> tuple[CandidateDevelopmentEvidence, ...]:
    graph = {identity: set() for identity in epoch.closure.constituent_order}
    families = {identity: set() for identity in graph}
    for row in epoch.closure.candidates:
        graph[row.semantic_id].update(row.prerequisites)
        families[row.semantic_id].add(row.family_id)
    metrics = {item.semantic_id: item for item in frontier_target_metrics(
        epoch.snapshot, epoch.closure)}
    results = []
    for semantic_id in epoch.closure.constituent_order:
        rows = tuple(item for item in epoch.closure.candidates
                     if item.semantic_id == semantic_id)
        capability_ids, anchors = _realization(epoch, semantic_id, rows)
        prerequisite_count = len(graph[semantic_id])
        family_ids = tuple(sorted(families[semantic_id]))
        neighborhood_id = hashlib.sha256(_bytes(("a09-family-neighborhood/v1",
                                                  family_ids))).hexdigest()
        metric = metrics[semantic_id]
        unmet = {
            reason.dependency_id
            for row in rows for reason in row.reasons
            if reason.code.startswith("PREREQUISITE_") and reason.dependency_id
        }
        measured_cost = _measured_acquisition_cost(
            epoch, learner, plan, foot, capability_ids)
        cost = measured_cost or AcquisitionCostEvidence(
            CostEvidenceKind.BOOTSTRAPPED,
            "a09-unmet-prerequisite-slope/v1",
            1 + len(unmet),
            None,
        )
        compute_units = max(1, 1 + len(unmet))
        results.append(CandidateDevelopmentEvidence(
            semantic_id=semantic_id,
            compiled_capability_ids=capability_ids,
            source_anchor_ids=anchors,
            neighborhood_id=neighborhood_id,
            coverage_factors=family_ids,
            acquisition_cost=cost,
            grounding_quality=len(anchors),
            answer_modality_burden=None,
            ast_burden=None,
            entanglement=None,
            reusable_constituent_value=None,
            downstream_unlocks=metric.downstream_unlocks,
            minimal_contrast_value=None,
            transfer_breadth=None,
            learning_progress=None,
            fairness_age=None,
            a09_prerequisite_slope=metric.prerequisite_slope,
            a09_cursor_distance=metric.cursor_distance,
            a09_statuses=metric.statuses,
            a09_reason_receipts=metric.reason_receipts,
            planning_compute_units=compute_units,
            evidence_sha256=hashlib.sha256(_bytes({
                "semantic_id": semantic_id, "families": family_ids,
                "prerequisites": tuple(sorted(graph[semantic_id])),
                "capabilities": capability_ids, "anchors": anchors,
                "a09_metrics": metric,
                "acquisition_cost": cost,
                "learner": foot.evidence_sha256,
            })).hexdigest(),
        ))
    return tuple(sorted(results, key=lambda item: item.semantic_id))


def _a09_receipt(epoch, learner, plan):
    result = next_atlas_delta(epoch, learner, plan)
    if isinstance(result, AtlasDeltaScopeHandoff):
        result.verify()
        progress = plan_frontier_progress(
            epoch.snapshot, epoch.closure, result.receipt.selection,
            current_release=epoch.current_release,
            selected_projection=result.receipt.projection,
            prior=epoch.prior, staged_receipt=result.receipt)
        return (
            progress, progress.status.value, result.handoff_sha256,
            result.proposal.proposal_sha256,
        )
    status = result if isinstance(result, FrontierStatus) else FrontierStatus.FIXED_POINT
    return None, status.value, None, None


def _compile_generated_grade_inputs(
    epoch: AtlasCoverageEpoch,
    learner: AtlasLearnerEvidence,
    plan: AutonomyPlan,
) -> GeneratedGradeInputs:
    """Internal issuer; production callers enter through accepted runtime custody."""
    if (type(epoch) is not AtlasCoverageEpoch or type(learner) is not AtlasLearnerEvidence
            or type(plan) is not AutonomyPlan):
        _fail("BAMF_GENERATED_GRADE_AUTHORITY_INPUT_INVALID")
    epoch.verify()
    if (learner.ledger.factory_release_sha256 != epoch.current_release.release_sha256
            or learner.ledger.autonomy_plan_sha256 != plan.digest()
            or plan.factory_release_sha256 != epoch.current_release.release_sha256):
        _fail("BAMF_GENERATED_GRADE_AUTHORITY_MISMATCH")
    foot = _learner_foot(epoch, learner, plan)
    policy = GeneratedGradePolicy(
        "a09-393-pareto-cohort/v1",
        max(1, epoch.snapshot.budget.max_candidates),
        max(0, min(
            epoch.snapshot.budget.max_candidates,
            epoch.snapshot.budget.max_identity_rows,
        ) - 1),
        epoch.snapshot.policy_epoch)
    evidence = _development_evidence(epoch, foot, learner, plan)
    progress, status, handoff_sha256, a09_proposal_sha256 = _a09_receipt(
        epoch, learner, plan)
    progress_sha256 = progress.progress_sha256 if progress is not None else None
    common = dict(
        learner=foot, candidate_evidence=evidence, policy=policy,
        a09_progress_sha256=progress_sha256, a09_status=status,
        a09_handoff_sha256=handoff_sha256,
        a09_proposal_sha256=(a09_proposal_sha256 if handoff_sha256 else None),
        schema="bilqis.generated-grade-inputs/v1")
    expected = hashlib.sha256(_bytes({
        "learner": foot, "candidate_evidence": evidence, "policy": policy,
        "a09_progress_sha256": progress_sha256, "a09_status": status,
        "a09_handoff_sha256": handoff_sha256,
        "a09_proposal_sha256": (a09_proposal_sha256 if handoff_sha256 else None),
        "schema": "bilqis.generated-grade-inputs/v1",
    })).hexdigest()
    return _issue_inputs(**common, input_sha256=expected)
