"""#1333 generic MAIN/RECOVERY cadence over the #1315 lawful frontier."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.salience_teacher import (
    PrioritySchoolContext,
    PriorityStudentIdentity,
)
from bilqis_mlx.runtime.active_grade_cadence import (
    issue_active_grade_cadence,
    record_active_grade_cadence_attempt,
)
from bilqis_mlx.runtime.active_grade_cadence_custody import read_current_cadence
from bilqis_mlx.runtime.active_grade_cadence_contracts import (
    ActiveGradeCadenceAuthorization,
    ActiveGradeCadenceDisposition,
    ActiveGradeCadencePhase,
    CADENCE_POLICY_EPOCH,
)


_SHA = "a" * 64


def _capability(capability_id, disposition="READY", semantics=None):
    return SimpleNamespace(
        capability_id=capability_id,
        semantic_ids=tuple(semantics or ("sem." + capability_id.lower(),)),
        disposition=SimpleNamespace(value=disposition),
    )


def _frontier(
        rows, *, active_state="INCOMPLETE_READY", exclusions=(), activation=None,
        policy_epoch=7):
    ready = tuple(item.capability_id for item in rows
                  if item.disposition.value == "READY")
    members = tuple(
        (item.capability_id, semantic)
        for item in rows for semantic in item.semantic_ids)
    return SimpleNamespace(
        run_id="run",
        active_grade_activation_sha256=activation or "1" * 64,
        active_grade_definition_sha256="2" * 64,
        policy_epoch=policy_epoch,
        capabilities=tuple(rows),
        active_grade_members=members,
        ready_capability_ids=ready,
        active_grade_state=SimpleNamespace(value=active_state),
        exclusions=tuple(exclusions),
    )


def _epoch(obligation_counts):
    plan = SimpleNamespace(digest=lambda: "3" * 64)
    return SimpleNamespace(
        current_release=object(), autonomy_plan=plan,
        evidence_ledger=SimpleNamespace(receipts=()),
        checkpoint=SimpleNamespace(sha256="4" * 64, optimizer_step=11),
        _obligation_counts=dict(obligation_counts),
    )


def _obligations(epoch):
    def resolve(_release, capability_id, *, plan):
        assert plan is epoch.autonomy_plan
        return tuple(SimpleNamespace(
            obligation_id=f"{capability_id}/o{index}", minimum_specimens=1)
            for index in range(epoch._obligation_counts[capability_id]))
    return resolve


def _attempt(run_dir, epoch, frontier, capability):
    issued = issue_active_grade_cadence(run_dir, epoch, frontier)
    assert capability in issued.authorized_capability_ids
    _record_attempt(run_dir, issued, capability)


def _record_attempt(run_dir, issued, capability):
    terminal = (issued.to_record(), capability)
    with patch(
            "bilqis_mlx.runtime.active_grade_cadence._terminal_attempts",
            return_value=(terminal,)):
        record_active_grade_cadence_attempt(run_dir, *terminal)


def test_main_pass_then_two_bounded_recovery_rounds(tmp_path):
    rows = tuple(_capability(item) for item in ("A", "B", "C", "D"))
    frontier = _frontier(rows)
    epoch = _epoch({"A": 3, "B": 2, "C": 1, "D": 1})
    with patch(
            "bilqis_mlx.runtime.active_grade_cadence_policy.obligations_for_capability",
            side_effect=_obligations(epoch)):
        first = issue_active_grade_cadence(tmp_path, epoch, frontier)
        assert first.phase is ActiveGradeCadencePhase.MAIN
        assert first.authorized_capability_ids == ("A", "B", "C", "D")
        for capability in ("A", "B", "C", "D"):
            _attempt(tmp_path, epoch, frontier, capability)

        recovery_one = issue_active_grade_cadence(tmp_path, epoch, frontier)
        assert recovery_one.phase is ActiveGradeCadencePhase.RECOVERY_1
        assert recovery_one.authorized_capability_ids == ("A", "B", "C")
        for capability in recovery_one.authorized_capability_ids:
            _attempt(tmp_path, epoch, frontier, capability)

        recovery_two = issue_active_grade_cadence(tmp_path, epoch, frontier)
        assert recovery_two.phase is ActiveGradeCadencePhase.RECOVERY_2
        assert recovery_two.authorized_capability_ids == ("A", "B", "D")
        for capability in recovery_two.authorized_capability_ids:
            _attempt(tmp_path, epoch, frontier, capability)

        boundary = issue_active_grade_cadence(tmp_path, epoch, frontier)
        assert boundary.phase is ActiveGradeCadencePhase.BOUNDARY
        assert boundary.authorized_capability_ids == ()
        assert boundary.disposition is ActiveGradeCadenceDisposition.RECOVERY_EXHAUSTED
        repeated = issue_active_grade_cadence(tmp_path, epoch, frontier)
        assert repeated.state.cadence_sha256 == boundary.state.cadence_sha256
        assert repeated.state.revision == boundary.state.revision


def test_unattempted_held_member_preserves_main_phase(tmp_path):
    frontier = _frontier((
        _capability("A"),
        _capability("B", "HELD_PREREQUISITE_EVIDENCE"),
    ))
    epoch = _epoch({"A": 1, "B": 1})
    with patch(
            "bilqis_mlx.runtime.active_grade_cadence_policy.obligations_for_capability",
            side_effect=_obligations(epoch)):
        _attempt(tmp_path, epoch, frontier, "A")
        held = issue_active_grade_cadence(tmp_path, epoch, frontier)
    assert held.phase is ActiveGradeCadencePhase.MAIN
    assert held.authorized_capability_ids == ()
    assert held.disposition is ActiveGradeCadenceDisposition.HELD


def test_complete_grade_short_circuits_to_boundary(tmp_path):
    frontier = _frontier(
        (_capability("Z", "EVIDENCE_COMPLETE"),), active_state="COMPLETE")
    epoch = _epoch({"Z": 1})
    with patch(
            "bilqis_mlx.runtime.active_grade_cadence_policy.obligations_for_capability",
            side_effect=_obligations(epoch)):
        result = issue_active_grade_cadence(tmp_path, epoch, frontier)
    assert result.phase is ActiveGradeCadencePhase.BOUNDARY
    assert result.disposition is ActiveGradeCadenceDisposition.GRADE_COMPLETE


def test_repeated_semantics_group_to_one_cadence_member_and_future_data_is_neutral(tmp_path):
    row = _capability("Z", semantics=("sem.z1", "sem.z2"))
    epoch = _epoch({"Z": 1})
    first = _frontier((row,))
    later = _frontier((row,), exclusions=(SimpleNamespace(capability_id="Q"),))
    with patch(
            "bilqis_mlx.runtime.active_grade_cadence_policy.obligations_for_capability",
            side_effect=_obligations(epoch)):
        before = issue_active_grade_cadence(tmp_path, epoch, first)
        after = issue_active_grade_cadence(tmp_path, epoch, later)
    assert before.authorized_capability_ids == ("Z",)
    assert after.authorized_capability_ids == ("Z",)
    assert after.state.member_census_sha256 == before.state.member_census_sha256
    assert after.state.phase_sha256 == before.state.phase_sha256


@pytest.mark.parametrize("stage", ["MAIN", "RECOVERY_1", "RECOVERY_2"])
def test_priority_school_context_accepts_only_native_cadence_phases(stage):
    context = PrioritySchoolContext(
        "a" * 64, ("descriptive-grade",), PriorityStudentIdentity("b" * 64),
        stage=stage)
    assert context.stage == stage


def test_priority_school_context_rejects_non_cadence_stage():
    with pytest.raises(BilqisError):
        PrioritySchoolContext(
            "a" * 64, ("descriptive-grade",), PriorityStudentIdentity("b" * 64),
            stage="GRADE_B_REMEDIATION")


def test_cadence_authorization_cannot_be_constructed_by_caller():
    with pytest.raises(BilqisError) as failure:
        ActiveGradeCadenceAuthorization()
    assert failure.value.context.get("reason") == (
        "BAMF_ACTIVE_GRADE_CADENCE_AUTHORIZATION_CALLER_CONSTRUCTION_FORBIDDEN")


def test_new_active_grade_activation_resets_recovery_exposure(tmp_path):
    rows = tuple(_capability(item) for item in ("A", "B", "C"))
    first = _frontier(rows)
    successor = _frontier(rows, activation="9" * 64)
    epoch = _epoch({"A": 3, "B": 2, "C": 1})
    with patch(
            "bilqis_mlx.runtime.active_grade_cadence_policy.obligations_for_capability",
            side_effect=_obligations(epoch)):
        for capability in ("A", "B", "C"):
            _attempt(tmp_path, epoch, first, capability)
        recovery = issue_active_grade_cadence(tmp_path, epoch, first)
        _attempt(tmp_path, epoch, first, recovery.authorized_capability_ids[0])
        assert dict(read_current_cadence(tmp_path).recovery_attempt_counts)
        reset = issue_active_grade_cadence(tmp_path, epoch, successor)
    assert reset.phase is ActiveGradeCadencePhase.MAIN
    assert reset.state.recovery_attempt_counts == ()


def test_cadence_policy_epoch_is_owned_by_1333_not_a09_frontier(tmp_path):
    rows = (_capability("Z"),)
    epoch = _epoch({"Z": 1})
    with patch(
            "bilqis_mlx.runtime.active_grade_cadence_policy.obligations_for_capability",
            side_effect=_obligations(epoch)):
        before = issue_active_grade_cadence(
            tmp_path, epoch, _frontier(rows, policy_epoch=7))
        after = issue_active_grade_cadence(
            tmp_path, epoch, _frontier(rows, policy_epoch=999))
    assert before.state.policy_epoch == CADENCE_POLICY_EPOCH
    assert after.state.policy_epoch == CADENCE_POLICY_EPOCH
    assert after.state.cadence_sha256 == before.state.cadence_sha256

