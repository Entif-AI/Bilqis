"""Pure #1314 projection of one frozen active grade into teachable members."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory import candidate_realizations
from bilqis_mlx.factory.atlas_frontier_closure import ClosureStatus
from bilqis_mlx.semantics.domains import contract_digest

from .lawful_teaching_frontier_contracts import (
    ActiveGeneratedGradeState,
    LawfulTeachingCapability,
    LawfulTeachingDisposition,
    LawfulTeachingExclusion,
    LawfulTeachingExclusionCode,
    LawfulTeachingHold,
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
        identities.add(candidate_realizations.realized_atlas_semantic_id(capability_id))
    except ValueError:
        pass
    return tuple(sorted(identities))


def _holds_for_capability(
        capability_id, semantic_ids, execution, snapshot, closure, plan,
        mastered, *, semantic_scope_complete=True):
    mastered = set(mastered)
    source_rows = tuple(
        row for row in snapshot.source_held_rows if row.semantic_id in semantic_ids)
    closure_rows = tuple(
        row for row in closure.candidates if row.semantic_id in semantic_ids)
    missing_prerequisites = tuple(sorted(set(execution.prerequisites) - mastered))
    missing_constituents = tuple(sorted(set(execution.composed_of) - mastered))
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
    if not semantic_scope_complete:
        implementation = True
        holds.append(LawfulTeachingHold(
            "ACTIVE_GRADE_SEMANTIC_SCOPE_UNCOVERED",
            "runtime:active-generated-grade",
            capability_id,
        ))
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
    elif capability_id in mastered:
        disposition = LawfulTeachingDisposition.EVIDENCE_COMPLETE
    else:
        disposition = LawfulTeachingDisposition.READY
    semantic_prerequisites = tuple(sorted({
        item for row in closure_rows for item in row.prerequisites
    }))
    return (
        disposition, tuple(sorted(set(holds))), missing_prerequisites,
        missing_constituents, semantic_prerequisites,
    )


def _capabilities(
        release, snapshot, closure, plan, mastered, *, active_members=None):
    bindings = release.source_bindings.by_capability
    curriculum = release.curriculum.capability_map
    execution_map = release.execution_plan.capability_map
    projected = (
        tuple(
            (capability_id, _semantic_ids(release, capability_id))
            for capability_id in sorted(execution_map))
        if active_members is None else tuple(active_members))
    capability_ids = tuple(capability_id for capability_id, _ in projected)
    if (len(set(capability_ids)) != len(capability_ids)
            or any(capability_id not in execution_map for capability_id in capability_ids)
            or any(type(semantic_ids) is not tuple or not semantic_ids
                   for _capability_id, semantic_ids in projected)):
        _invalid("BAMF_ACTIVE_GENERATED_GRADE_MEMBER_DRIFT")
    result = []
    for capability_id, semantic_ids in projected:
        execution = execution_map[capability_id]
        if capability_id not in curriculum or capability_id not in bindings:
            _invalid("BAMF_LEARNER_FRONTIER_RELEASE_IDENTITY_INVALID")
        available_semantics = set(_semantic_ids(release, capability_id))
        if (len(set(semantic_ids)) != len(semantic_ids)
                or not set(semantic_ids).issubset(available_semantics)):
            _invalid("BAMF_ACTIVE_GENERATED_GRADE_MEMBER_DRIFT")
        disposition, holds, missing_prerequisites, missing_constituents, (
            semantic_prerequisites
        ) = _holds_for_capability(
            capability_id, semantic_ids, execution, snapshot, closure, plan, mastered,
            semantic_scope_complete=set(semantic_ids) == available_semantics)
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


def _exclusions(release, capabilities) -> tuple[LawfulTeachingExclusion, ...]:
    codes = {
        LawfulTeachingDisposition.EVIDENCE_COMPLETE:
            LawfulTeachingExclusionCode.ALREADY_COMPLETE,
        LawfulTeachingDisposition.HELD_PREREQUISITE_EVIDENCE:
            LawfulTeachingExclusionCode.PREREQUISITE_HELD,
        LawfulTeachingDisposition.HELD_SOURCE_RIGHTS:
            LawfulTeachingExclusionCode.SOURCE_HELD,
        LawfulTeachingDisposition.IMPLEMENTATION_UNCOVERED:
            LawfulTeachingExclusionCode.IMPLEMENTATION_UNCOVERED,
    }
    result = []
    active_ids = {item.capability_id for item in capabilities}
    for item in capabilities:
        if item.disposition is LawfulTeachingDisposition.READY:
            continue
        code = codes.get(item.disposition)
        if code is None:
            _invalid("BAMF_LEARNER_FRONTIER_INVALID")
        result.append(LawfulTeachingExclusion(
            item.capability_id, item.semantic_ids, code, item.holds))
    execution_map = release.execution_plan.capability_map
    for capability_id in sorted(set(execution_map) - active_ids):
        result.append(LawfulTeachingExclusion(
            capability_id,
            _semantic_ids(release, capability_id),
            LawfulTeachingExclusionCode.FUTURE_GENERATED_GRADE,
            (),
        ))
    return tuple(result)


def _active_member_projection(release, active):
    execution = release.execution_plan.capability_map
    curriculum = release.curriculum.capability_map
    bindings = release.source_bindings.by_capability
    by_capability: dict[str, list[str]] = {}
    order: list[str] = []
    for member in active.definition.members:
        capability_id = member.capability_id
        if (capability_id not in execution or capability_id not in curriculum
                or capability_id not in bindings
                or bindings[capability_id].source_anchor != member.source_anchor
                or member.semantic_id not in _semantic_ids(release, capability_id)):
            _invalid("BAMF_ACTIVE_GENERATED_GRADE_MEMBER_DRIFT")
        if capability_id not in by_capability:
            by_capability[capability_id] = []
            order.append(capability_id)
        by_capability[capability_id].append(member.semantic_id)
    return tuple((capability_id, tuple(by_capability[capability_id])) for capability_id in order)


def _active_grade_state(capabilities, planning_status=None) -> ActiveGeneratedGradeState:
    if capabilities and all(
            item.disposition is LawfulTeachingDisposition.EVIDENCE_COMPLETE
            for item in capabilities):
        status = getattr(planning_status, "value", planning_status)
        if status in {"FIXED_POINT", "COMPLETE_ATLAS_COVERAGE"}:
            return ActiveGeneratedGradeState.GLOBAL_FIXED_POINT
        return ActiveGeneratedGradeState.COMPLETE
    if any(item.disposition is LawfulTeachingDisposition.READY for item in capabilities):
        return ActiveGeneratedGradeState.INCOMPLETE_READY
    return ActiveGeneratedGradeState.INCOMPLETE_HELD
