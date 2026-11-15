"""Real terminal and Electron fixture consume one immutable OperatorView."""
import json
from pathlib import Path
import unittest

from bilqis_mlx.mission_control.codec import canonical_json, decode_record
from bilqis_mlx.mission_control.consumers import decode_operator_view
from bilqis_mlx.mission_control.contracts.fixtures import representative_operator_view
from bilqis_mlx.mission_control.model import (
    ContractErrorCode, MissionControlContractError,
)
from bilqis_mlx.presentation.atlas_metrics import bamf_status, render_panel
from bilqis_mlx.mission_control.tests.samples import SAMPLES


class MissionControlConsumerFixtureTests(unittest.TestCase):
    def test_terminal_and_electron_bootstrap_share_exact_fixture_bytes(self):
        path = Path(__file__).resolve().parents[3] / (
            "apps/mission-control/fixtures/operator-view-v1.json"
        )
        expected = canonical_json(representative_operator_view())
        self.assertEqual(path.read_bytes(), expected)
        payload = json.loads(expected)
        decoded = decode_record(payload)
        terminal_view = bamf_status(payload)
        self.assertEqual(terminal_view, decoded)
        terminal = render_panel(terminal_view, {}, width=None)
        self.assertIn("ADMIN MAIN FRAME | run fixture-run | generation 7", terminal)
        self.assertIn("RECORD | operator-view:fixture-run:7 | coverage COMPLETE", terminal)

    def test_valid_non_operator_schema_has_deterministic_type_mismatch(self):
        non_operator = next(
            sample for sample in SAMPLES if type(sample).__name__ == "RunContext"
        )
        with self.assertRaises(MissionControlContractError) as raised:
            decode_operator_view(json.loads(canonical_json(non_operator)))
        self.assertEqual(raised.exception.code, ContractErrorCode.SCHEMA_TYPE_MISMATCH)

    def test_terminal_preserves_cp02_version_error_identity(self):
        payload = json.loads(canonical_json(representative_operator_view()))
        payload["schema_version"] = "bilqis.bamf.mission-control.operator-view/v999"
        with self.assertRaises(MissionControlContractError) as raised:
            bamf_status(payload)
        self.assertEqual(raised.exception.code, ContractErrorCode.SCHEMA_UNSUPPORTED)


if __name__ == "__main__":
    unittest.main()
