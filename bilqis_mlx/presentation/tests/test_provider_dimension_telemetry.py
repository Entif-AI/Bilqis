"""Provider-dimension telemetry is generic; INTROOT stays a rendering alias."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from bilqis_mlx.presentation.numeric_scope import apply_profile_adoption


class _Board:
    def __init__(self):
        self.state = {}
        self.events = []

    def push(self, channel, payload, *, redraw):
        self.events.append((channel, payload, redraw))


class ProviderDimensionTelemetryTests(unittest.TestCase):
    def test_future_dimension_projects_without_numeric_alias(self):
        telemetry = SimpleNamespace(board=_Board(), _reset_score_era=Mock())
        dimensions = [{
            "provider_id": "fixture.future/v1",
            "provider_dimension_id": "lesson-intensity",
            "provider_dimension_value": "mid",
            "provider_dimension_terminal": False,
            "telemetry_projection": "INTENSITY",
        }]

        apply_profile_adoption(telemetry, "Z", {
            "event": "SCHOOL_EXECUTION_PROFILE_ADOPTED",
            "profile_id": "fixture/future",
            "provider_dimensions": dimensions,
            "optimizer_step": 9,
        })

        self.assertEqual(telemetry.board.state["provider_dimensions"], dimensions)
        self.assertNotIn("numeric_maximum", telemetry.board.state)
        self.assertNotIn("integer roots", telemetry.board.events[-1][1]["detail"])

    def test_introot_alias_is_derived_from_generic_dimension_value(self):
        telemetry = SimpleNamespace(board=_Board(), _reset_score_era=Mock())
        dimensions = [{
            "provider_id": "source.finite-numeric/v2",
            "provider_dimension_id": "numeric-root",
            "provider_dimension_value": "5",
            "provider_dimension_terminal": False,
            "telemetry_projection": "INTROOT",
        }]

        apply_profile_adoption(telemetry, "C", {
            "event": "SCHOOL_EXECUTION_PROFILE_ADOPTED",
            "profile_id": "school/numeric",
            "provider_dimensions": dimensions,
            "numeric_maximum": 4,
        })

        self.assertEqual(telemetry.board.state["numeric_maximum"], 5)
        self.assertIn("integer roots 0...5", telemetry.board.events[-1][1]["detail"])


if __name__ == "__main__":
    unittest.main()
