"""#1333 BAMF-native MAIN/RECOVERY cadence inside one active generated grade."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.autonomy import obligations_for_capability

from .active_grade_cadence_contracts import (
    ActiveGradeCadenceAuthorization,
    ActiveGradeCadenceDisposition,
    ActiveGradeCadencePhase,
    CADENCE_AUTHORIZATION_SCHEMA,
    MAX_RECOVERY_ROUNDS,
    RECOVERY_WIDTH,
    issue_cadence_authorization,
    issue_cadence_state,
)
from .active_grade_cadence_custody import (
    persist_cadence_state as _persist_state,
    read_current_cadence as _read_current,
)


_RECOVERY_PHASES = (
    ActiveGradeCadencePhase.RECOVERY_1,
    ActiveGradeCadencePhase.RECOVERY_2,
)
if len(_RECOVERY_PHASES) != MAX_RECOVERY_ROUNDS:
    raise RuntimeError("active-grade cadence recovery policy mismatch")


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _canonical(value) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False)


def _digest(value) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _member_capabilities(frontier) -> tuple[str, ...]:
    result = [item.capability_id for item in frontier.capabilities]
    if not result:
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_MEMBER_CENSUS_EMPTY")
    return tuple(result)


def _member_census_digest(frontier) -> str:
    return _digest({
        "schema": "bilqis.bamf.active-grade-member-census/v1",
        "members": [
            [item.capability_id, list(item.semantic_ids)]
            for item in frontier.capabilities
        ],
    })


def _deficits(epoch, capability_ids: tuple[str, ...]) -> tuple[dict[str, int], str]:
    latest = {}
    for receipt in epoch.evidence_ledger.receipts:
        latest[receipt.obligation_id] = receipt
    rows = []
    counts = {}
    checkpoint = epoch.checkpoint
    for capability_id in capability_ids:
        unmet = []
        for obligation in obligations_for_capability(
                epoch.current_release, capability_id, plan=epoch.autonomy_plan):
            receipt = latest.get(obligation.obligation_id)
            if (receipt is None or not receipt.passed
                    or receipt.specimen_count < obligation.minimum_specimens
                    or receipt.checkpoint_sha256 != checkpoint.sha256
                    or receipt.optimizer_step != checkpoint.optimizer_step):
                unmet.append(obligation.obligation_id)
        counts[capability_id] = len(unmet)
        rows.append([capability_id, unmet])
    return counts, _digest({
        "schema": "bilqis.bamf.active-grade-deficit-evidence/v1",
        "autonomy_plan_sha256": epoch.autonomy_plan.digest(),
        "checkpoint_sha256": checkpoint.sha256,
        "optimizer_step": checkpoint.optimizer_step,
        "rows": rows,
    })


def _phase_digest(*, previous_phase_sha256, activation_sha256, definition_sha256,
                  policy_epoch, member_census_sha256, phase, phase_round,
                  capability_ids, deficit_evidence_sha256) -> str:
    return _digest({
        "schema": "bilqis.bamf.active-grade-cadence-phase/v1",
        "previous_phase_sha256": previous_phase_sha256,
        "active_grade_activation_sha256": activation_sha256,
        "active_grade_definition_sha256": definition_sha256,
        "policy_epoch": policy_epoch,
        "member_census_sha256": member_census_sha256,
        "phase": phase.value,
        "phase_round": phase_round,
        "capability_ids": list(capability_ids),
        "deficit_evidence_sha256": deficit_evidence_sha256,
    })


def _new_state(run_dir, previous, frontier, *, phase, phase_round,
               phase_capability_ids, deficit_evidence_sha256,
               member_census_sha256, recovery_attempt_counts=None):
    counts = (
        tuple(sorted((recovery_attempt_counts or {}).items()))
        if recovery_attempt_counts is not None
        else (() if previous is None else previous.recovery_attempt_counts))
    phase_sha256 = _phase_digest(
        previous_phase_sha256=(None if previous is None else previous.phase_sha256),
        activation_sha256=frontier.active_grade_activation_sha256,
        definition_sha256=frontier.active_grade_definition_sha256,
        policy_epoch=frontier.policy_epoch,
        member_census_sha256=member_census_sha256,
        phase=phase,
        phase_round=phase_round,
        capability_ids=phase_capability_ids,
        deficit_evidence_sha256=deficit_evidence_sha256,
    )
    state = issue_cadence_state(
        run_id=frontier.run_id,
        revision=0 if previous is None else previous.revision + 1,
        predecessor_sha256=(None if previous is None else previous.cadence_sha256),
        active_grade_activation_sha256=frontier.active_grade_activation_sha256,
        active_grade_definition_sha256=frontier.active_grade_definition_sha256,
        policy_epoch=frontier.policy_epoch,
        member_census_sha256=member_census_sha256,
        phase=phase,
        phase_round=phase_round,
        phase_sha256=phase_sha256,
        phase_capability_ids=tuple(phase_capability_ids),
        attempted_capability_ids=(),
        deficit_evidence_sha256=deficit_evidence_sha256,
        recovery_attempt_counts=counts,
    )
    _persist_state(Path(run_dir), state)
    return state


def _context_matches(state, frontier, member_census_sha256) -> bool:
    return (
        state.run_id == frontier.run_id
        and state.active_grade_activation_sha256 == frontier.active_grade_activation_sha256
        and state.active_grade_definition_sha256 == frontier.active_grade_definition_sha256
        and state.policy_epoch == frontier.policy_epoch
        and state.member_census_sha256 == member_census_sha256
    )


def _recovery_members(state, ready, deficits, member_order):
    exposure = dict(state.recovery_attempt_counts)
    order = {capability: index for index, capability in enumerate(member_order)}
    return tuple(sorted(
        ready,
        key=lambda capability: (
            -deficits.get(capability, 0),
            exposure.get(capability, 0),
            order.get(capability, len(order)),
            capability,
        )))[:RECOVERY_WIDTH]


def _consume_attempt(run_dir, state, cadence_record, capability_id):
    if (not isinstance(cadence_record, dict)
            or cadence_record.get("schema") != CADENCE_AUTHORIZATION_SCHEMA
            or cadence_record.get("phase") != state.phase.value
            or cadence_record.get("phase_round") != state.phase_round
            or cadence_record.get("phase_sha256") != state.phase_sha256
            or cadence_record.get("cadence_sha256") != state.cadence_sha256
            or cadence_record.get("active_grade_activation_sha256")
            != state.active_grade_activation_sha256
            or cadence_record.get("active_grade_definition_sha256")
            != state.active_grade_definition_sha256
            or cadence_record.get("member_census_sha256") != state.member_census_sha256
            or cadence_record.get("policy_epoch") != state.policy_epoch
            or capability_id not in state.phase_capability_ids
            or capability_id not in set(cadence_record.get(
                "authorized_capability_ids", ()))):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_ATTEMPT_DRIFT")
    if capability_id in state.attempted_capability_ids:
        return state
    attempted = (*state.attempted_capability_ids, capability_id)
    counts = dict(state.recovery_attempt_counts)
    if state.phase in {
            ActiveGradeCadencePhase.RECOVERY_1,
            ActiveGradeCadencePhase.RECOVERY_2}:
        counts[capability_id] = counts.get(capability_id, 0) + 1
    updated = issue_cadence_state(
        run_id=state.run_id,
        revision=state.revision + 1,
        predecessor_sha256=state.cadence_sha256,
        active_grade_activation_sha256=state.active_grade_activation_sha256,
        active_grade_definition_sha256=state.active_grade_definition_sha256,
        policy_epoch=state.policy_epoch,
        member_census_sha256=state.member_census_sha256,
        phase=state.phase,
        phase_round=state.phase_round,
        phase_sha256=state.phase_sha256,
        phase_capability_ids=state.phase_capability_ids,
        attempted_capability_ids=attempted,
        deficit_evidence_sha256=state.deficit_evidence_sha256,
        recovery_attempt_counts=tuple(sorted(counts.items())),
    )
    _persist_state(Path(run_dir), updated)
    return updated


def _reconcile_terminal_attempts(run_dir, state):
    from .active_grade_cadence_replay import authenticated_cadence_attempts
    for cadence_record, capability_id in authenticated_cadence_attempts(Path(run_dir)):
        if cadence_record.get("phase_sha256") != state.phase_sha256:
            continue
        if capability_id in state.attempted_capability_ids:
            continue
        state = _consume_attempt(run_dir, state, cadence_record, capability_id)
    return state


def issue_active_grade_cadence(run_dir: Path, epoch, lawful_frontier):
    """Issue the current #1333 subset; #1315 remains the legality owner."""
    member_order = _member_capabilities(lawful_frontier)
    census = _member_census_digest(lawful_frontier)
    deficits, deficit_digest = _deficits(epoch, member_order)
    state = _read_current(Path(run_dir))
    context_changed = state is None or not _context_matches(
        state, lawful_frontier, census)
    boundary_evidence_changed = (
        state is not None
        and state.phase is ActiveGradeCadencePhase.BOUNDARY
        and state.deficit_evidence_sha256 != deficit_digest)
    if context_changed or boundary_evidence_changed:
        reset_exposure = (
            state is None
            or state.active_grade_activation_sha256
            != lawful_frontier.active_grade_activation_sha256)
        state = _new_state(
            run_dir, state, lawful_frontier,
            phase=ActiveGradeCadencePhase.MAIN, phase_round=0,
            phase_capability_ids=member_order,
            deficit_evidence_sha256=deficit_digest,
            member_census_sha256=census,
            recovery_attempt_counts=(
                {} if reset_exposure else dict(state.recovery_attempt_counts)),
        )
    state = _reconcile_terminal_attempts(run_dir, state)
    ready_set = set(lawful_frontier.ready_capability_ids)
    ready = tuple(capability for capability in member_order if capability in ready_set)
    complete = {
        item.capability_id for item in lawful_frontier.capabilities
        if getattr(item.disposition, "value", item.disposition) == "EVIDENCE_COMPLETE"
    }
    attempted = set(state.attempted_capability_ids)
    unsatisfied = tuple(
        capability for capability in state.phase_capability_ids
        if capability not in attempted and capability not in complete)
    authorized = tuple(capability for capability in unsatisfied if capability in ready_set)
    if authorized:
        return issue_cadence_authorization(
            state, authorized, ActiveGradeCadenceDisposition.TEACHING)
    active_state = getattr(lawful_frontier.active_grade_state, "value",
                           lawful_frontier.active_grade_state)
    if active_state in {"COMPLETE", "GLOBAL_FIXED_POINT"}:
        if state.phase is not ActiveGradeCadencePhase.BOUNDARY:
            state = _new_state(
                run_dir, state, lawful_frontier,
                phase=ActiveGradeCadencePhase.BOUNDARY,
                phase_round=MAX_RECOVERY_ROUNDS + 1,
                phase_capability_ids=(), deficit_evidence_sha256=deficit_digest,
                member_census_sha256=census)
        return issue_cadence_authorization(
            state, (), ActiveGradeCadenceDisposition.GRADE_COMPLETE)
    if unsatisfied:
        return issue_cadence_authorization(
            state, (), ActiveGradeCadenceDisposition.HELD)
    if not ready:
        return issue_cadence_authorization(
            state, (), ActiveGradeCadenceDisposition.HELD)
    if state.phase is ActiveGradeCadencePhase.BOUNDARY:
        return issue_cadence_authorization(
            state, (), ActiveGradeCadenceDisposition.RECOVERY_EXHAUSTED)
    if state.phase is ActiveGradeCadencePhase.MAIN:
        phase = _RECOVERY_PHASES[0]
        phase_round = 1
    elif state.phase in _RECOVERY_PHASES:
        index = _RECOVERY_PHASES.index(state.phase) + 1
        if index < len(_RECOVERY_PHASES):
            phase = _RECOVERY_PHASES[index]
            phase_round = index + 1
        else:
            phase = ActiveGradeCadencePhase.BOUNDARY
            phase_round = MAX_RECOVERY_ROUNDS + 1
    else:
        phase = ActiveGradeCadencePhase.BOUNDARY
        phase_round = MAX_RECOVERY_ROUNDS + 1
    members = (() if phase is ActiveGradeCadencePhase.BOUNDARY else
               _recovery_members(state, ready, deficits, member_order))
    state = _new_state(
        run_dir, state, lawful_frontier,
        phase=phase, phase_round=phase_round,
        phase_capability_ids=members,
        deficit_evidence_sha256=deficit_digest,
        member_census_sha256=census)
    disposition = (
        ActiveGradeCadenceDisposition.RECOVERY_EXHAUSTED
        if phase is ActiveGradeCadencePhase.BOUNDARY
        else ActiveGradeCadenceDisposition.TEACHING)
    return issue_cadence_authorization(state, members, disposition)


def record_active_grade_cadence_attempt(
        run_dir: Path, cadence_record: dict, capability_id: str) -> None:
    """Consume one terminal accepted/rejected opportunity idempotently."""
    if not isinstance(cadence_record, dict) or not isinstance(capability_id, str):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_ATTEMPT_INVALID")
    state = _read_current(Path(run_dir))
    if state is None:
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_ATTEMPT_DRIFT")
    _consume_attempt(run_dir, state, cadence_record, capability_id)


__all__ = (
    "issue_active_grade_cadence", "record_active_grade_cadence_attempt",
)
