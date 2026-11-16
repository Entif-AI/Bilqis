"""Issue and revalidate the current learner-relative teaching frontier."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory import candidate_realizations
from bilqis_mlx.factory.atlas_frontier_closure import ClosureStatus
from bilqis_mlx.factory.autonomy import evidence_complete_capabilities
from bilqis_mlx.semantics.domains import contract_digest

from bilqis_mlx.runtime.lawful_teaching_frontier_contracts import (
    LawfulTeachingFrontier,
    LawfulTeachingCapability,
    LawfulTeachingDisposition,
    LawfulTeachingHold,
    _is_issued,
    _issue_frontier,
)


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def _evidence_digest(plan, ledger) -> str:
    payload = json.dumps(
        {"plan": asdict(plan), "ledger": asdict(ledger)},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _semantic_ids(release, capability_id: str) -> tuple[str, ...]:
    definition = release.curriculum.capability_map[capability_id]
    identities = set((*definition.taught_roots, *definition.examined_roots))
    try:
        identities.add(candidate_realizations.realized_atlas_semantic_id(
            capability_id))
    except ValueError:
        pass
    return tuple(sorted(identities))


def _holds_for_capability(
        capability_id, semantic_ids, execution, snapshot, closure, plan,
        mastered):
    mastered = set(mastered)
    source_rows = tuple(
        row for row in snapshot.source_held_rows
        if row.semantic_id in semantic_ids)
    closure_rows = tuple(
        row for row in closure.candidates
        if row.semantic_id in semantic_ids)
    missing_prerequisites = tuple(sorted(
        set(execution.prerequisites) - mastered))
    missing_constituents = tuple(sorted(
        set(execution.composed_of) - mastered))
    holds = [
        LawfulTeachingHold(
            row.reason_code or "SOURCE_HELD",
            row.owner or "source:authority",
            row.semantic_id or f"{row.domain}/{row.table}/{row.key}")
        for row in source_rows
    ]
    implementation = capability_id in set(plan.blocked_capabilities)
    if implementation:
        holds.append(LawfulTeachingHold(
            "AUTONOMY_PLAN_BLOCKED", "factory:autonomy", capability_id))
    waiting = bool(missing_prerequisites or missing_constituents)
    for row in closure_rows:
        if row.status is ClosureStatus.IMPLEMENTATION_UNCOVERED:
            implementation = True
        elif row.status is ClosureStatus.WAITING_FOR_EVIDENCE:
            waiting = True
        elif row.status is ClosureStatus.SOURCE_HELD:
            source_rows = (*source_rows, row)
        holds.extend(
            LawfulTeachingHold(reason.code, reason.owner, reason.dependency_id)
            for reason in row.reasons)
    holds.extend(
        LawfulTeachingHold(
            "PREREQUISITE_EVIDENCE_REQUIRED", "learner:evidence", item)
        for item in missing_prerequisites)
    holds.extend(
        LawfulTeachingHold(
            "CONSTITUENT_EVIDENCE_REQUIRED", "learner:evidence", item)
        for item in missing_constituents)
    if source_rows:
        disposition = LawfulTeachingDisposition.HELD_SOURCE_RIGHTS
    elif implementation:
        disposition = LawfulTeachingDisposition.IMPLEMENTATION_UNCOVERED
    elif waiting:
        disposition = LawfulTeachingDisposition.HELD_PREREQUISITE_EVIDENCE
    else:
        disposition = LawfulTeachingDisposition.READY
    semantic_prerequisites = tuple(sorted({
        item for row in closure_rows for item in row.prerequisites
    }))
    return (
        disposition, tuple(sorted(set(holds))),
        missing_prerequisites, missing_constituents, semantic_prerequisites,
    )


def _capabilities(release, snapshot, closure, plan, mastered):
    bindings = release.source_bindings.by_capability
    curriculum = release.curriculum.capability_map
    result = []
    for capability_id, execution in sorted(
            release.execution_plan.capability_map.items()):
        if capability_id not in curriculum or capability_id not in bindings:
            _invalid("BAMF_LEARNER_FRONTIER_RELEASE_IDENTITY_INVALID")
        semantic_ids = _semantic_ids(release, capability_id)
        disposition, holds, missing_prerequisites, missing_constituents, (
            semantic_prerequisites
        ) = _holds_for_capability(
            capability_id, semantic_ids, execution, snapshot, closure, plan,
            mastered)
        result.append(LawfulTeachingCapability(
            capability_id=capability_id,
            semantic_ids=semantic_ids,
            admitted_release_sha256=release.release_sha256,
            source_binding_sha256=contract_digest(bindings[capability_id]),
            prerequisites=tuple(sorted(set(execution.prerequisites))),
            constituents=tuple(sorted(set(execution.composed_of))),
            semantic_prerequisites=semantic_prerequisites,
            evidence_complete_prerequisites=tuple(sorted(
                set(execution.prerequisites) - set(missing_prerequisites))),
            evidence_complete_constituents=tuple(sorted(
                set(execution.composed_of) - set(missing_constituents))),
            target_evidence_complete=capability_id in set(mastered),
            disposition=disposition,
            holds=holds,
        ))
    return tuple(result)


def _source_authority(planning_generation):
    from bilqis_mlx.factory.skos_curriculum import (
        issue_source_context_transition_authority,
    )
    return issue_source_context_transition_authority(
        planning_generation._authenticated_features.selection)


def _validate_epoch(epoch, planning_generation, source_context, parent):
    release = source_context.release
    snapshot, closure = epoch.snapshot, epoch.closure
    release.verify()
    snapshot.verify()
    closure.verify()
    source = _source_authority(planning_generation)
    if (
        epoch.current_release.release_sha256 != release.release_sha256
        or snapshot.admitted_factory_release_sha256 != release.release_sha256
        or closure.snapshot_sha256 != snapshot.snapshot_sha256
        or snapshot.rights_epoch != source.frontier.rights_epoch
        or snapshot.correction_generation
           != source.frontier.correction_generation
        or snapshot.policy_epoch != source.policy.policy_epoch
        or epoch.checkpoint.sha256
           != planning_generation.parent_candidate_identity_sha256
        or epoch.checkpoint.optimizer_step
           != parent.retained_state.optimizer_step
    ):
        _invalid("BAMF_LEARNER_FRONTIER_EPOCH_DRIFT")
    return source


def _issue_lawful_teaching_frontier_from_epoch(
        epoch, source_context, parent, planning_generation):
    """Seal one already-derived accepted A09 epoch for an internal consumer."""
    from bilqis_mlx.runtime.priority_planning_owner import PriorityPlanningEpoch
    if type(epoch) is not PriorityPlanningEpoch:
        _invalid("BAMF_LEARNER_FRONTIER_EPOCH_INVALID")
    source = _validate_epoch(
        epoch, planning_generation, source_context, parent)
    mastered = evidence_complete_capabilities(
        epoch.current_release, epoch.evidence_ledger,
        plan=epoch.autonomy_plan,
        current_checkpoint_sha256=epoch.checkpoint.sha256,
        current_optimizer_step=epoch.checkpoint.optimizer_step)
    capabilities = _capabilities(
        epoch.current_release, epoch.snapshot, epoch.closure,
        epoch.autonomy_plan, mastered)
    snapshot = epoch.snapshot
    if snapshot.admission_receipt_sha256 is None:
        _invalid("BAMF_LEARNER_FRONTIER_ADMISSION_RECEIPT_REQUIRED")
    return _issue_frontier(
        run_id=parent.run_id,
        accepted_generation=parent.generation,
        accepted_manifest_sha256=planning_generation.accepted_manifest_sha256,
        accepted_correction_frontier_sha256=(
            planning_generation.correction_frontier_sha256),
        accepted_checkpoint_sha256=epoch.checkpoint.sha256,
        accepted_optimizer_step=epoch.checkpoint.optimizer_step,
        candidate_identity_sha256=(
            planning_generation.parent_candidate_identity_sha256),
        admitted_release_sha256=epoch.current_release.release_sha256,
        admission_receipt_sha256=snapshot.admission_receipt_sha256,
        a09_snapshot_sha256=snapshot.snapshot_sha256,
        a09_closure_sha256=epoch.closure.closure_sha256,
        prerequisite_evidence_sha256=(
            epoch.closure.prerequisite_evidence_sha256),
        autonomy_plan_sha256=epoch.autonomy_plan.digest(),
        autonomy_evidence_sha256=_evidence_digest(
            epoch.autonomy_plan, epoch.evidence_ledger),
        rights_epoch=snapshot.rights_epoch,
        correction_generation=snapshot.correction_generation,
        policy_epoch=snapshot.policy_epoch,
        source_authority_registry_sha256=source.authority_registry_sha256,
        capabilities=capabilities,
        _source_context=source_context,
        _parent=parent,
        _planning_generation=planning_generation,
    )


def issue_lawful_teaching_frontier(
        run_dir, source_context, parent, atlas_artifact_path, *,
        planning_generation=None, progress=None):
    """Issue a sealed frontier from current accepted learner/source/A09 owners."""
    from bilqis_mlx.runtime.priority_source_offer import (
        _require_planning_generation,
        bind_priority_planning_generation,
    )
    if planning_generation is None:
        planning_generation = bind_priority_planning_generation(
            source_context, parent, atlas_artifact_path)
    _require_planning_generation(planning_generation, source_context, parent)
    from bilqis_mlx.runtime.priority_planning_owner import (
        build_priority_planning_epoch,
    )
    epoch = build_priority_planning_epoch(
        run_dir, source_context, atlas_artifact_path, progress)
    return _issue_lawful_teaching_frontier_from_epoch(
        epoch, source_context, parent, planning_generation)


def _require_lawful_teaching_frontier(
        frontier, source_context, parent, *, refresh_accepted):
    """Validate frontier derivation; optionally refresh mutable B13 custody."""
    if (
        not _is_issued(frontier)
        or frontier._source_context is not source_context
        or frontier._parent is not parent
    ):
        _invalid("BAMF_LEARNER_FRONTIER_INVALID")
    planning_generation = frontier._planning_generation
    if refresh_accepted:
        from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
            refresh_accepted_currentness,
        )
        refresh_accepted_currentness(
            planning_generation._accepted_currentness, parent)
    from bilqis_mlx.runtime.priority_source_offer import (
        _require_planning_generation,
    )
    _require_planning_generation(planning_generation, source_context, parent)
    from bilqis_mlx.runtime.atlas_flywheel_runtime import _accepted_checkpoint
    checkpoint = _accepted_checkpoint(Path(source_context.run_dir))
    from bilqis_mlx.runtime.autonomy_state import read_autonomy_state
    plan, ledger = read_autonomy_state(
        Path(source_context.run_dir), source_context.release)
    source = _source_authority(planning_generation)
    if (
        frontier.run_id != parent.run_id
        or frontier.accepted_generation != parent.generation
        or frontier.accepted_manifest_sha256
           != planning_generation.accepted_manifest_sha256
        or frontier.accepted_correction_frontier_sha256
           != planning_generation.correction_frontier_sha256
        or frontier.candidate_identity_sha256
           != planning_generation.parent_candidate_identity_sha256
        or frontier.admitted_release_sha256
           != source_context.release.release_sha256
        or frontier.accepted_checkpoint_sha256 != checkpoint.sha256
        or frontier.accepted_optimizer_step != checkpoint.optimizer_step
        or frontier.autonomy_plan_sha256 != plan.digest()
        or frontier.autonomy_evidence_sha256 != _evidence_digest(plan, ledger)
        or frontier.policy_epoch != source.policy.policy_epoch
        or frontier.rights_epoch != source.frontier.rights_epoch
        or frontier.correction_generation
           != source.frontier.correction_generation
        or frontier.source_authority_registry_sha256
           != source.authority_registry_sha256
    ):
        _invalid("BAMF_LEARNER_FRONTIER_STALE")
    return frontier


def require_bound_lawful_teaching_frontier(
        frontier, source_context, parent):
    """Revalidate non-neural frontier owners without a full B13 refresh."""
    return _require_lawful_teaching_frontier(
        frontier, source_context, parent, refresh_accepted=False)


def require_current_lawful_teaching_frontier(
        frontier, source_context, parent):
    """Fail closed if any accepted learner/source/policy/evidence owner moved."""
    return _require_lawful_teaching_frontier(
        frontier, source_context, parent, refresh_accepted=True)


__all__ = (
    "LawfulTeachingCapability",
    "LawfulTeachingDisposition",
    "LawfulTeachingFrontier",
    "LawfulTeachingHold",
    "issue_lawful_teaching_frontier",
    "require_bound_lawful_teaching_frontier",
    "require_current_lawful_teaching_frontier",
)
