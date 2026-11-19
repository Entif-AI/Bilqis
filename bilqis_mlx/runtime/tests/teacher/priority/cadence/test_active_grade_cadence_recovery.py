"""Crash/replay and projection custody regressions for #1333 cadence."""
import shutil
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.active_grade_cadence import (
    issue_active_grade_cadence,
    record_active_grade_cadence_attempt,
)
from bilqis_mlx.runtime.active_grade_cadence_contracts import ActiveGradeCadencePhase
from bilqis_mlx.runtime.active_grade_cadence_custody import read_current_cadence

from bilqis_mlx.runtime.tests.teacher.priority.test_active_grade_cadence import (
    _capability,
    _epoch,
    _frontier,
    _obligations,
    _record_attempt,
)


def _obligation_patch(epoch):
    return patch(
        "bilqis_mlx.runtime.active_grade_cadence_policy.obligations_for_capability",
        side_effect=_obligations(epoch))


def test_terminal_event_replay_heals_stale_cadence_before_reissue(tmp_path):
    frontier = _frontier((_capability("A"), _capability("B")))
    epoch = _epoch({"A": 1, "B": 1})
    with _obligation_patch(epoch):
        issued = issue_active_grade_cadence(tmp_path, epoch, frontier)
        with patch(
                "bilqis_mlx.runtime.active_grade_cadence_replay."
                "authenticated_cadence_attempts",
                return_value=((issued.to_record(), "A"),)):
            cold = issue_active_grade_cadence(tmp_path, epoch, frontier)
    assert cold.authorized_capability_ids == ("B",)
    assert read_current_cadence(tmp_path).attempted_capability_ids == ("A",)


def test_projection_rebuild_after_activation_change_replays_terminal_attempt(tmp_path):
    rows = (_capability("A"), _capability("B"))
    first = _frontier(rows)
    successor = _frontier(rows, activation="9" * 64)
    epoch = _epoch({"A": 1, "B": 1})
    with _obligation_patch(epoch):
        issue_active_grade_cadence(tmp_path, epoch, first)
        issued = issue_active_grade_cadence(tmp_path, epoch, successor)
        terminal = (issued.to_record(), "A")
        shutil.rmtree(tmp_path / "active-grade-cadence")
        with patch(
                "bilqis_mlx.runtime.active_grade_cadence_replay."
                "authenticated_cadence_attempts", return_value=(terminal,)):
            rebuilt = issue_active_grade_cadence(tmp_path, epoch, successor)
    assert rebuilt.phase is ActiveGradeCadencePhase.MAIN
    assert rebuilt.authorized_capability_ids == ("B",)


def test_projection_rebuild_inside_recovery_preserves_round_and_exposure(tmp_path):
    rows = tuple(_capability(item) for item in ("A", "B", "C", "D"))
    frontier = _frontier(rows)
    epoch = _epoch({"A": 3, "B": 2, "C": 1, "D": 1})
    history = []
    with _obligation_patch(epoch):
        for capability in ("A", "B", "C", "D"):
            issued = issue_active_grade_cadence(tmp_path, epoch, frontier)
            history.append((issued.to_record(), capability))
            _record_attempt(tmp_path, issued, capability)
        recovery_one = issue_active_grade_cadence(tmp_path, epoch, frontier)
        for capability in recovery_one.authorized_capability_ids:
            issued = issue_active_grade_cadence(tmp_path, epoch, frontier)
            history.append((issued.to_record(), capability))
            _record_attempt(tmp_path, issued, capability)
        recovery_two = issue_active_grade_cadence(tmp_path, epoch, frontier)
        capability = recovery_two.authorized_capability_ids[0]
        history.append((recovery_two.to_record(), capability))
        _record_attempt(tmp_path, recovery_two, capability)
        expected_remaining = recovery_two.authorized_capability_ids[1:]
        expected_exposure = dict(read_current_cadence(tmp_path).recovery_attempt_counts)
        shutil.rmtree(tmp_path / "active-grade-cadence")
        with patch(
                "bilqis_mlx.runtime.active_grade_cadence_replay."
                "authenticated_cadence_attempts", return_value=tuple(history)):
            rebuilt = issue_active_grade_cadence(tmp_path, epoch, frontier)
    assert rebuilt.phase is ActiveGradeCadencePhase.RECOVERY_2
    assert rebuilt.authorized_capability_ids == expected_remaining
    assert dict(rebuilt.state.recovery_attempt_counts) == expected_exposure


def test_new_learner_evidence_reopens_exhausted_grade_main_cadence(tmp_path):
    rows = tuple(_capability(item) for item in ("A", "B", "C", "D"))
    frontier = _frontier(rows)
    first_epoch = _epoch({"A": 3, "B": 2, "C": 1, "D": 1})
    history = []
    with _obligation_patch(first_epoch):
        for _round in range(3):
            issued = issue_active_grade_cadence(tmp_path, first_epoch, frontier)
            for capability in issued.authorized_capability_ids:
                current = issue_active_grade_cadence(tmp_path, first_epoch, frontier)
                history.append((current.to_record(), capability))
                _record_attempt(tmp_path, current, capability)
        exhausted = issue_active_grade_cadence(tmp_path, first_epoch, frontier)
        assert exhausted.phase is ActiveGradeCadencePhase.BOUNDARY
    second_epoch = _epoch({"A": 3, "B": 2, "C": 1, "D": 1})
    second_epoch.checkpoint = type(first_epoch.checkpoint)(
        sha256="8" * 64, optimizer_step=12)
    with _obligation_patch(second_epoch):
        refreshed = issue_active_grade_cadence(tmp_path, second_epoch, frontier)
        assert refreshed.phase is ActiveGradeCadencePhase.MAIN
        assert refreshed.disposition.value == "TEACHING"
        assert refreshed.state.cadence_epoch == exhausted.state.cadence_epoch + 1
        assert refreshed.state.deficit_evidence_sha256 != (
            exhausted.state.deficit_evidence_sha256)
        shutil.rmtree(tmp_path / "active-grade-cadence")
        with patch(
                "bilqis_mlx.runtime.active_grade_cadence_replay."
                "authenticated_cadence_attempts", return_value=tuple(history)):
            rebuilt = issue_active_grade_cadence(tmp_path, second_epoch, frontier)
    assert rebuilt.phase is ActiveGradeCadencePhase.MAIN
    assert rebuilt.disposition.value == "TEACHING"
    assert rebuilt.authorized_capability_ids


def test_projection_writer_refuses_attempt_without_authenticated_terminal_custody(tmp_path):
    frontier = _frontier((_capability("A"), _capability("B")))
    epoch = _epoch({"A": 1, "B": 1})
    with _obligation_patch(epoch):
        issued = issue_active_grade_cadence(tmp_path, epoch, frontier)
        with pytest.raises(BilqisError) as failure:
            record_active_grade_cadence_attempt(
                tmp_path, issued.to_record(), "A")
    assert failure.value.context.get("reason") == (
        "BAMF_ACTIVE_GRADE_CADENCE_TERMINAL_AUTHORITY_MISSING")


def test_custody_heals_stale_pointer_and_ignores_writer_temp(tmp_path):
    frontier = _frontier((_capability("A"), _capability("B")))
    epoch = _epoch({"A": 1, "B": 1})
    with _obligation_patch(epoch):
        issued = issue_active_grade_cadence(tmp_path, epoch, frontier)
        _record_attempt(tmp_path, issued, "A")
    tip = read_current_cadence(tmp_path)
    pointer = tmp_path / "active-grade-cadence/current.json"
    pointer.write_text(
        '{\n  "cadence_sha256": "' + issued.state.cadence_sha256 +
        '",\n  "schema": "bilqis.bamf.active-grade-cadence-pointer/v1"\n}\n',
        encoding="utf-8")
    states = tmp_path / "active-grade-cadence/states"
    orphan = states / f".{tip.cadence_sha256}.json.{'f' * 32}.tmp"
    orphan.write_text("partial", encoding="utf-8")
    healed = read_current_cadence(tmp_path)
    assert healed.cadence_sha256 == tip.cadence_sha256
    assert healed.attempted_capability_ids == ("A",)


def test_boundary_rebuild_ignores_orphaned_writer_temp(tmp_path):
    rows = tuple(_capability(item) for item in ("A", "B", "C", "D"))
    frontier = _frontier(rows)
    epoch = _epoch({"A": 3, "B": 2, "C": 1, "D": 1})
    history = []
    with _obligation_patch(epoch):
        for _round in range(3):
            issued = issue_active_grade_cadence(tmp_path, epoch, frontier)
            for capability in issued.authorized_capability_ids:
                current = issue_active_grade_cadence(tmp_path, epoch, frontier)
                history.append((current.to_record(), capability))
                _record_attempt(tmp_path, current, capability)
        exhausted = issue_active_grade_cadence(tmp_path, epoch, frontier)
        assert exhausted.phase is ActiveGradeCadencePhase.BOUNDARY
        boundaries = tmp_path / "active-grade-cadence-boundaries"
        receipt = next(boundaries.glob("*.json"))
        orphan = boundaries / ("." + receipt.name + "." + "f" * 32 + ".tmp")
        orphan.write_text("partial", encoding="utf-8")
        shutil.rmtree(tmp_path / "active-grade-cadence")
        with patch(
                "bilqis_mlx.runtime.active_grade_cadence_replay."
                "authenticated_cadence_attempts", return_value=tuple(history)):
            rebuilt = issue_active_grade_cadence(tmp_path, epoch, frontier)
    assert rebuilt.phase is ActiveGradeCadencePhase.BOUNDARY
    assert rebuilt.disposition.value == "RECOVERY_EXHAUSTED"
