"""Staged BAMF runs stop cleanly when grade certification needs C07 policy authority."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError, SCHOOL
from bilqis_mlx.runtime.bamf_operator.session_parts.native_session import (
    priority_hold_result,
)
from bilqis_mlx.runtime.bamf_operator._session_execution import _terminal_visit_status


def test_grade_boundary_missing_signed_policy_becomes_typed_terminal_hold():
    selection = SimpleNamespace(
        status="NO_ADMISSIBLE_TEACHING",
        metadata={"cadence": {"disposition": "RECOVERY_EXHAUSTED"}},
        holds=(),
        exclusions=(),
    )
    emitted = []
    failure = BilqisError(
        SCHOOL.BAMF_CURRICULUM.INVALID,
        {"reason": "BAMF_GRADE_CERTIFICATION_POLICY_SELECTION_REQUIRED"},
    )

    with patch(
        "bilqis_mlx.runtime.grade_certification.run_grade_boundary_certification",
        side_effect=failure,
    ):
        result = priority_hold_result(
            Path("/run"), selection, object(), object(), Path("/atlas"), 100.0,
            emitted.append, emit_progress=lambda progress, message: progress(message),
        )

    assert result.status == "CERTIFICATION_POLICY_REQUIRED"
    assert result.selection is selection
    assert any("signed C07" in message for message in emitted)


def test_certification_policy_requirement_is_a_non_neural_terminal_status():
    assert _terminal_visit_status("CERTIFICATION_POLICY_REQUIRED") == (
        "CERTIFICATION_POLICY_REQUIRED"
    )


def test_unrelated_certification_failure_still_propagates():
    selection = SimpleNamespace(
        status="NO_ADMISSIBLE_TEACHING",
        metadata={"cadence": {"disposition": "GRADE_COMPLETE"}},
        holds=(),
        exclusions=(),
    )
    failure = BilqisError(
        SCHOOL.BAMF_CURRICULUM.INVALID,
        {"reason": "BAMF_GRADE_CERTIFICATION_CURRENTNESS_DRIFT"},
    )

    with patch(
        "bilqis_mlx.runtime.grade_certification.run_grade_boundary_certification",
        side_effect=failure,
    ), pytest.raises(BilqisError) as raised:
        priority_hold_result(
            Path("/run"), selection, object(), object(), Path("/atlas"), 100.0,
            lambda _message: None,
            emit_progress=lambda progress, message: progress(message),
        )

    assert raised.value is failure
