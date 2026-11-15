"""BAMF C16.3 candidate-horizon projection from authenticated rejections."""
from unittest.mock import patch

from bilqis_mlx.runtime.priority_rejection_replay import candidate_step_horizon


def _row(reason, ordinal, capability="cap"):
    return capability, f"visit-{ordinal}", reason, f"{ordinal:064x}"


def test_candidate_horizon_reuses_interference_shortening_policy():
    rows = (
        _row("PROTECTED_CAPABILITY_REGRESSION", 1),
        _row("ACTIVE_SCHOOL_GRADE_REGRESSION", 2),
    )
    with patch(
            "bilqis_mlx.runtime.priority_rejection_replay.current_rejections",
            return_value=rows):
        assert candidate_step_horizon("/run", object(), object(), "cap", 16) == 8

    rows += (
        _row("SAME_GRADE_NET_REGRESSION", 3),
        _row("PROTECTED_CAPABILITY_REGRESSION", 4),
    )
    with patch(
            "bilqis_mlx.runtime.priority_rejection_replay.current_rejections",
            return_value=rows):
        assert candidate_step_horizon("/run", object(), object(), "cap", 16) == 4


def test_no_gain_resets_interference_horizon_pressure():
    rows = (
        _row("PROTECTED_CAPABILITY_REGRESSION", 1),
        _row("ACTIVE_SCHOOL_GRADE_REGRESSION", 2),
        _row("NO_MEASURABLE_TARGET_GAIN", 3),
    )
    with patch(
            "bilqis_mlx.runtime.priority_rejection_replay.current_rejections",
            return_value=rows):
        assert candidate_step_horizon("/run", object(), object(), "cap", 16) == 16
