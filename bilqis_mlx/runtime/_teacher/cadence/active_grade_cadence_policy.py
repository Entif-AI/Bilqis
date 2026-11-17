"""Deterministic #1333 active-grade cadence policy and phase construction."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.autonomy import obligations_for_capability

from .active_grade_cadence_contracts import (
    ActiveGradeCadencePhase,
    CADENCE_POLICY_EPOCH,
    RECOVERY_WIDTH,
    _issue_cadence_state,
)
from .active_grade_cadence_custody import persist_cadence_state


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _digest(value) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def member_capabilities(frontier) -> tuple[str, ...]:
    result = tuple(item.capability_id for item in frontier.capabilities)
    if not result:
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_MEMBER_CENSUS_EMPTY")
    return result


def member_census_digest(frontier) -> str:
    return _digest({
        "schema": "bilqis.bamf.active-grade-member-census/v1",
        "members": [
            [item.capability_id, list(item.semantic_ids)]
            for item in frontier.capabilities
        ],
    })


def deficits(epoch, capability_ids: tuple[str, ...]) -> tuple[dict[str, int], str]:
    latest = {
        receipt.obligation_id: receipt
        for receipt in epoch.evidence_ledger.receipts
    }
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


def _phase_digest(*, activation_sha256, definition_sha256,
                  cadence_epoch, member_census_sha256, phase, phase_round,
                  capability_ids, deficit_evidence_sha256) -> str:
    return _digest({
        "schema": "bilqis.bamf.active-grade-cadence-phase/v1",
        "active_grade_activation_sha256": activation_sha256,
        "active_grade_definition_sha256": definition_sha256,
        "policy_epoch": CADENCE_POLICY_EPOCH,
        "cadence_epoch": cadence_epoch,
        "member_census_sha256": member_census_sha256,
        "phase": phase.value,
        "phase_round": phase_round,
        "capability_ids": list(capability_ids),
        "deficit_evidence_sha256": deficit_evidence_sha256,
    })


def new_state(run_dir, previous, frontier, *, phase, phase_round,
              phase_capability_ids, deficit_evidence_sha256,
              member_census_sha256, recovery_attempt_counts=None,
              attempted_capability_ids=(), cadence_epoch=None,
              phase_sha256=None):
    counts = (
        tuple(sorted((recovery_attempt_counts or {}).items()))
        if recovery_attempt_counts is not None
        else (() if previous is None else previous.recovery_attempt_counts))
    if cadence_epoch is None:
        cadence_epoch = 0 if previous is None else previous.cadence_epoch
    if phase_sha256 is None:
        phase_sha256 = _phase_digest(
            activation_sha256=frontier.active_grade_activation_sha256,
            definition_sha256=frontier.active_grade_definition_sha256,
            cadence_epoch=cadence_epoch,
            member_census_sha256=member_census_sha256,
            phase=phase,
            phase_round=phase_round,
            capability_ids=phase_capability_ids,
            deficit_evidence_sha256=deficit_evidence_sha256,
        )
    state = _issue_cadence_state(
        run_id=frontier.run_id,
        revision=0 if previous is None else previous.revision + 1,
        predecessor_sha256=(None if previous is None else previous.cadence_sha256),
        active_grade_activation_sha256=frontier.active_grade_activation_sha256,
        active_grade_definition_sha256=frontier.active_grade_definition_sha256,
        policy_epoch=CADENCE_POLICY_EPOCH,
        cadence_epoch=cadence_epoch,
        member_census_sha256=member_census_sha256,
        phase=phase,
        phase_round=phase_round,
        phase_sha256=phase_sha256,
        phase_capability_ids=tuple(phase_capability_ids),
        attempted_capability_ids=tuple(attempted_capability_ids),
        deficit_evidence_sha256=deficit_evidence_sha256,
        recovery_attempt_counts=counts,
    )
    persist_cadence_state(Path(run_dir), state)
    return state


def context_matches(state, frontier, member_census_sha256) -> bool:
    return (
        state.run_id == frontier.run_id
        and state.active_grade_activation_sha256
        == frontier.active_grade_activation_sha256
        and state.active_grade_definition_sha256
        == frontier.active_grade_definition_sha256
        and state.policy_epoch == CADENCE_POLICY_EPOCH
        and state.member_census_sha256 == member_census_sha256
    )


def recovery_members(state, ready, deficit_counts, member_order):
    exposure = dict(state.recovery_attempt_counts)
    order = {capability: index for index, capability in enumerate(member_order)}
    return tuple(sorted(
        ready,
        key=lambda capability: (
            -deficit_counts.get(capability, 0),
            exposure.get(capability, 0),
            order.get(capability, len(order)),
            capability,
        )))[:RECOVERY_WIDTH]


__all__ = (
    "context_matches", "deficits", "member_capabilities", "member_census_digest",
    "new_state", "recovery_members",
)
