"""Terminal-attempt reconciliation and projection rebuild for #1333 cadence."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL

from .active_grade_cadence_contracts import (
    ActiveGradeCadencePhase,
    CADENCE_AUTHORIZATION_SCHEMA,
    CADENCE_POLICY_EPOCH,
    _issue_cadence_state,
)
from .active_grade_cadence_custody import persist_cadence_state
from .active_grade_cadence_policy import new_state


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def consume_attempt(run_dir, state, cadence_record, capability_id, *, replay=False):
    if (not isinstance(cadence_record, dict)
            or cadence_record.get("schema") != CADENCE_AUTHORIZATION_SCHEMA
            or cadence_record.get("run_id") != state.run_id
            or cadence_record.get("phase") != state.phase.value
            or cadence_record.get("phase_round") != state.phase_round
            or cadence_record.get("phase_sha256") != state.phase_sha256
            or (not replay
                and cadence_record.get("cadence_sha256") != state.cadence_sha256)
            or cadence_record.get("active_grade_activation_sha256")
            != state.active_grade_activation_sha256
            or cadence_record.get("active_grade_definition_sha256")
            != state.active_grade_definition_sha256
            or cadence_record.get("member_census_sha256") != state.member_census_sha256
            or cadence_record.get("policy_epoch") != state.policy_epoch
            or cadence_record.get("cadence_epoch") != state.cadence_epoch
            or cadence_record.get("deficit_evidence_sha256")
            != state.deficit_evidence_sha256
            or tuple(cadence_record.get("phase_capability_ids", ()))
            != state.phase_capability_ids
            or cadence_record.get("disposition") != "TEACHING"
            or (not replay and tuple(
                (item[0], item[1])
                for item in cadence_record.get("recovery_attempt_counts", ()))
                != state.recovery_attempt_counts)
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
    updated = _issue_cadence_state(
        run_id=state.run_id,
        revision=state.revision + 1,
        predecessor_sha256=state.cadence_sha256,
        active_grade_activation_sha256=state.active_grade_activation_sha256,
        active_grade_definition_sha256=state.active_grade_definition_sha256,
        policy_epoch=state.policy_epoch,
        cadence_epoch=state.cadence_epoch,
        member_census_sha256=state.member_census_sha256,
        phase=state.phase,
        phase_round=state.phase_round,
        phase_sha256=state.phase_sha256,
        phase_capability_ids=state.phase_capability_ids,
        attempted_capability_ids=attempted,
        deficit_evidence_sha256=state.deficit_evidence_sha256,
        recovery_attempt_counts=tuple(sorted(counts.items())),
    )
    persist_cadence_state(Path(run_dir), updated)
    return updated


def reconcile_terminal_attempts(run_dir, state, attempts):
    for cadence_record, capability_id in attempts:
        if cadence_record.get("phase_sha256") != state.phase_sha256:
            continue
        if capability_id in state.attempted_capability_ids:
            continue
        state = consume_attempt(
            run_dir, state, cadence_record, capability_id, replay=True)
    return state


def replay_seed(run_dir, previous, frontier, member_census_sha256, attempts):
    """Rebuild the latest phase projection from authenticated terminal custody."""
    candidates = []
    for index, (record, capability_id) in enumerate(attempts):
        if (not isinstance(record, dict)
                or record.get("schema") != CADENCE_AUTHORIZATION_SCHEMA
                or record.get("run_id") != frontier.run_id
                or record.get("active_grade_activation_sha256")
                != frontier.active_grade_activation_sha256
                or record.get("active_grade_definition_sha256")
                != frontier.active_grade_definition_sha256
                or record.get("member_census_sha256") != member_census_sha256
                or record.get("policy_epoch") != CADENCE_POLICY_EPOCH
                or capability_id not in record.get("authorized_capability_ids", ())):
            continue
        try:
            phase = ActiveGradeCadencePhase(record["phase"])
            phase_round = record["phase_round"]
            cadence_epoch = record["cadence_epoch"]
            phase_capability_ids = tuple(record["phase_capability_ids"])
            recovery_counts = tuple(
                (item[0], item[1]) for item in record["recovery_attempt_counts"])
        except (KeyError, TypeError, ValueError, IndexError):
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_REPLAY_RECORD_INVALID")
        if phase is ActiveGradeCadencePhase.BOUNDARY:
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_REPLAY_RECORD_INVALID")
        candidates.append((cadence_epoch, index, record, phase, phase_round,
                           phase_capability_ids, recovery_counts))
    if not candidates:
        return None
    newest_epoch = max(item[0] for item in candidates)
    current = [item for item in candidates if item[0] == newest_epoch]
    last_phase_sha256 = current[-1][2].get("phase_sha256")
    first = next(
        item for item in current
        if item[2].get("phase_sha256") == last_phase_sha256)
    cadence_epoch, _index, record, phase, phase_round, phase_capability_ids, recovery_counts = first
    return new_state(
        run_dir, previous, frontier,
        phase=phase, phase_round=phase_round,
        phase_capability_ids=phase_capability_ids,
        deficit_evidence_sha256=record.get("deficit_evidence_sha256"),
        member_census_sha256=member_census_sha256,
        recovery_attempt_counts=dict(recovery_counts),
        cadence_epoch=cadence_epoch,
        phase_sha256=record.get("phase_sha256"),
    )


__all__ = ("consume_attempt", "reconcile_terminal_attempts", "replay_seed")
