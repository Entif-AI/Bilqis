"""Authority-bound #1320 inputs derived from the existing A09 state machine."""
from __future__ import annotations

from dataclasses import replace
import hashlib

from bilqis_mlx.factory.atlas_delta_scope import AtlasDeltaScopeHandoff
from bilqis_mlx.factory.atlas_frontier import AtlasCoverageEpoch, AtlasLearnerEvidence, next_atlas_delta
from bilqis_mlx.factory.atlas_frontier_progress import FrontierStatus, plan_frontier_progress
from bilqis_mlx.factory.atlas_frontier_progress_validation import (
    credited_obligation_keys, current_obligations,
)
from bilqis_mlx.factory.autonomy import AutonomyPlan, evidence_complete_capabilities
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
        tuple(mastered), evidence_sha256)


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


def _development_evidence(epoch, foot) -> tuple[CandidateDevelopmentEvidence, ...]:
    graph = {identity: set() for identity in epoch.closure.constituent_order}
    families = {identity: set() for identity in graph}
    for row in epoch.closure.candidates:
        graph[row.semantic_id].update(row.prerequisites)
        families[row.semantic_id].add(row.family_id)
    dependents = {identity: 0 for identity in graph}
    for prerequisites in graph.values():
        for prerequisite in prerequisites:
            dependents[prerequisite] += 1
    mastered = set(foot.mastered_capability_ids)
    results = []
    for semantic_id in epoch.closure.constituent_order:
        rows = tuple(item for item in epoch.closure.candidates
                     if item.semantic_id == semantic_id)
        capability_ids, anchors = _realization(epoch, semantic_id, rows)
        prerequisite_count = len(graph[semantic_id])
        family_ids = tuple(sorted(families[semantic_id]))
        neighborhood_id = hashlib.sha256(_bytes((family_ids, tuple(sorted(
            graph[semantic_id]))))).hexdigest()
        structural_cost = 1 + prerequisite_count
        results.append(CandidateDevelopmentEvidence(
            semantic_id=semantic_id,
            compiled_capability_ids=capability_ids,
            source_anchor_ids=anchors,
            neighborhood_id=neighborhood_id,
            coverage_factors=family_ids,
            acquisition_cost=AcquisitionCostEvidence(
                CostEvidenceKind.BOOTSTRAPPED,
                "structural-burden-units/v1", structural_cost),
            grounding_quality=len(anchors),
            answer_modality_burden=0 if capability_ids else 1,
            ast_burden=prerequisite_count,
            entanglement=dependents[semantic_id],
            reusable_constituent_value=1 + dependents[semantic_id],
            downstream_unlocks=dependents[semantic_id],
            minimal_contrast_value=len(family_ids),
            transfer_breadth=0,
            learning_progress=sum(capability in mastered for capability in capability_ids),
            fairness_age=1,
            planning_compute_units=max(1, structural_cost),
            evidence_sha256=hashlib.sha256(_bytes({
                "semantic_id": semantic_id, "families": family_ids,
                "prerequisites": tuple(sorted(graph[semantic_id])),
                "capabilities": capability_ids, "anchors": anchors,
                "learner": foot.evidence_sha256,
            })).hexdigest(),
        ))
    return tuple(results)


def _a09_receipt(epoch, learner, plan):
    result = next_atlas_delta(epoch, learner, plan)
    if isinstance(result, AtlasDeltaScopeHandoff):
        result.verify()
        progress = plan_frontier_progress(
            epoch.snapshot, epoch.closure, result.receipt.selection,
            current_release=epoch.current_release,
            selected_projection=result.receipt.projection,
            prior=epoch.prior, staged_receipt=result.receipt)
        return progress, result.handoff_sha256, result.proposal.proposal_sha256
    status = result if isinstance(result, FrontierStatus) else FrontierStatus.FIXED_POINT
    marker = hashlib.sha256(_bytes({
        "snapshot": epoch.snapshot.snapshot_sha256,
        "closure": epoch.closure.closure_sha256,
        "status": status.value,
    })).hexdigest()
    return None, None, marker


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
        "learner-relative-lexicographic/v1",
        max(1, epoch.snapshot.budget.max_candidates), 1,
        "structural-burden-units/v1")
    evidence = _development_evidence(epoch, foot)
    progress, handoff_sha256, a09_proposal_sha256 = _a09_receipt(epoch, learner, plan)
    progress_sha256 = (progress.progress_sha256 if progress is not None else
                       hashlib.sha256(_bytes((epoch.snapshot.snapshot_sha256,
                                              epoch.closure.closure_sha256,
                                              a09_proposal_sha256))).hexdigest())
    status = progress.status.value if progress is not None else "A09_STATUS_ONLY"
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
