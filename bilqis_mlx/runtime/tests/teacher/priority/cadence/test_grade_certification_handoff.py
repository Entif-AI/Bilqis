"""#1334 consumes only issued #1333 boundary authority, never serialized metadata."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.active_grade_cadence import issue_active_grade_cadence
from bilqis_mlx.runtime.active_grade_certification_handoff import (
    ActiveGradeCertificationBoundary,
    certification_boundary_from_priority_result,
    require_current_certification_boundary,
)
from bilqis_mlx.runtime.accepted_priority_visit_contracts import _issue_result
from bilqis_mlx.runtime.tests.teacher.priority.test_active_grade_cadence import (
    _capability,
    _epoch,
    _frontier,
    _obligations,
)


def _boundary(tmp_path):
    frontier = _frontier(
        (_capability("Z", "EVIDENCE_COMPLETE"),), active_state="COMPLETE")
    epoch = _epoch({"Z": 1})
    with patch(
        "bilqis_mlx.runtime.active_grade_cadence_policy.obligations_for_capability",
        side_effect=_obligations(epoch),
    ):
        authorization = issue_active_grade_cadence(tmp_path, epoch, frontier)
    result = _issue_result(
        "NO_ADMISSIBLE_TEACHING", None, None, None, None,
        {"cadence": authorization.to_record()}, None, (), tmp_path,
        lawful_frontier=SimpleNamespace(exclusions=()),
        cadence_authorization=authorization,
    )
    return authorization, result


def test_issued_boundary_handoff_is_current_and_binds_disposition(tmp_path):
    authorization, result = _boundary(tmp_path)
    handoff = certification_boundary_from_priority_result(result)
    assert handoff.disposition.value == "GRADE_COMPLETE"
    assert handoff.cadence_sha256 == authorization.state.cadence_sha256
    assert require_current_certification_boundary(tmp_path, handoff) is handoff


def test_serialized_cadence_metadata_without_issued_authority_is_not_boundary(tmp_path):
    authorization, _ = _boundary(tmp_path)
    result = _issue_result(
        "NO_ADMISSIBLE_TEACHING", None, None, None, None,
        {"cadence": authorization.to_record()}, None, (), tmp_path,
        lawful_frontier=SimpleNamespace(exclusions=()),
    )
    assert certification_boundary_from_priority_result(result) is None


def test_boundary_handoff_cannot_be_constructed_or_reused_after_reauth(tmp_path):
    with pytest.raises(BilqisError):
        ActiveGradeCertificationBoundary()
    old, result = _boundary(tmp_path)
    handoff = certification_boundary_from_priority_result(result)
    current = old.state
    from bilqis_mlx.runtime.active_grade_cadence_policy import new_state
    frontier = _frontier(
        (_capability("Z", "EVIDENCE_COMPLETE"),), active_state="COMPLETE")
    new_state(
        tmp_path, current, frontier,
        phase=current.phase, phase_round=current.phase_round,
        phase_capability_ids=(),
        deficit_evidence_sha256="9" * 64,
        member_census_sha256=current.member_census_sha256,
        cadence_epoch=current.cadence_epoch + 1,
        recovery_attempt_counts=dict(current.recovery_attempt_counts),
    )
    with pytest.raises(BilqisError) as failure:
        require_current_certification_boundary(tmp_path, handoff)
    assert failure.value.context.get("reason") == (
        "BAMF_GRADE_CERTIFICATION_BOUNDARY_STALE")


def test_recovery_exhausted_is_not_a_grade_certification_boundary(tmp_path):
    frontier = _frontier((_capability("Z", "READY"),))
    epoch = _epoch({"Z": 1})
    with patch(
        "bilqis_mlx.runtime.active_grade_cadence_policy.obligations_for_capability",
        side_effect=_obligations(epoch),
    ):
        first = issue_active_grade_cadence(tmp_path, epoch, frontier)
    from bilqis_mlx.runtime.active_grade_cadence_policy import new_state
    from bilqis_mlx.runtime.active_grade_cadence_contracts import (
        ActiveGradeCadencePhase,
    )
    boundary_state = new_state(
        tmp_path, first.state, frontier,
        phase=ActiveGradeCadencePhase.BOUNDARY,
        phase_round=3,
        phase_capability_ids=(),
        deficit_evidence_sha256=first.state.deficit_evidence_sha256,
        member_census_sha256=first.state.member_census_sha256,
        cadence_epoch=first.state.cadence_epoch + 1,
        recovery_attempt_counts=dict(first.state.recovery_attempt_counts),
    )
    with patch(
        "bilqis_mlx.runtime.active_grade_cadence_policy.obligations_for_capability",
        side_effect=_obligations(epoch),
    ):
        authorization = issue_active_grade_cadence(tmp_path, epoch, frontier)
    assert authorization.state.cadence_sha256 == boundary_state.cadence_sha256
    assert authorization.disposition.value == "RECOVERY_EXHAUSTED"
    result = _issue_result(
        "NO_ADMISSIBLE_TEACHING", None, None, None, None,
        {"cadence": authorization.to_record()}, None, (), tmp_path,
        lawful_frontier=SimpleNamespace(exclusions=()),
        cadence_authorization=authorization,
    )
    assert certification_boundary_from_priority_result(result) is None
