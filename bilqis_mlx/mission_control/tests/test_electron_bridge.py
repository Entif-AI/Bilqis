"""GUI20 consumes the accepted CP01 client without exposing its session identity."""
from __future__ import annotations

import os
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bilqis_mlx.control_plane import ControlPlaneService
from bilqis_mlx.control_plane.__main__ import _default_socket
from bilqis_mlx.control_plane.contracts import ControlPlaneState
from bilqis_mlx.control_plane.tests.support import start_service
from bilqis_mlx.errors import BilqisError, SCHOOL
from bilqis_mlx.mission_control.electron.bridge import (
    ElectronBridge, _safe_broker_error_code, _socket_path, stream_events,
)
from bilqis_mlx.mission_control.envelopes import EventEnvelope
from bilqis_mlx.mission_control.query_catalog import MissionControlQueryCatalog
from bilqis_mlx.mission_control.query_contracts import QueryFamily, QueryRequest
from bilqis_mlx.mission_control.tests.samples import SAMPLES
from bilqis_mlx.mission_control.codec import encode_record
from bilqis_mlx.control_plane.tests.command_support import request
from bilqis_mlx.paths import active_run_dir


class ElectronBridgeTests(unittest.TestCase):
    def test_private_broker_error_codes_are_bounded_and_do_not_include_exception_text(self):
        typed = BilqisError(
            SCHOOL.BAMF_CONTROL_PLANE.INVALID,
            {"reason": "token=super-secret /Users/operator/private-run"},
        )
        cases = (
            (typed, "BAMF_GUI20_CP01_CONTRACT_INVALID"),
            (PermissionError("/private/socket"), "BAMF_GUI20_CP01_UNAUTHORIZED"),
            (TimeoutError("slow /private/socket"), "BAMF_GUI20_CP01_TIMEOUT"),
            (ConnectionError("token=secret"), "BAMF_GUI20_CP01_TRANSPORT_UNAVAILABLE"),
            (RuntimeError("token=secret"), "BAMF_GUI20_CP01_UNAVAILABLE"),
        )
        for error, expected in cases:
            with self.subTest(expected=expected):
                code = _safe_broker_error_code(error)
                self.assertEqual(code, expected)
                self.assertNotIn("secret", code)
                self.assertNotIn("/private", code)

    def test_command_bridge_decodes_v2_and_never_exposes_private_session_identity(self):
        action = request(action="resume", dry_run=False, human_authorized=False)
        client = Mock()
        client.preview_command.return_value = {
            "schema": "bilqis.bamf.control-plane.command-preview/v1",
            "operation_id": "operation:" + "1" * 64,
        }
        client.inspect_command.return_value = {
            "schema": "bilqis.bamf.control-plane.command-inspection/v1",
            "operation_id": "operation:" + "1" * 64,
        }
        receipt = next(
            item for item in SAMPLES
            if item.schema_version == "bilqis.bamf.mission-control.operator-action-receipt/v2"
        )
        client.submit_command.return_value = receipt
        bridge = ElectronBridge()
        bridge.client = client

        preview = bridge.command_preview(encode_record(action))
        submitted = bridge.command_submit({
            "request": encode_record(action),
            "expected_target_ref": "command-target:" + "2" * 64,
        })
        inspection = bridge.command_inspect("operation:" + "1" * 64)

        self.assertEqual(preview["schema"], "bilqis.bamf.control-plane.command-preview/v1")
        self.assertEqual(
            submitted["schema_version"],
            "bilqis.bamf.mission-control.operator-action-receipt/v2",
        )
        self.assertEqual(
            inspection["schema"], "bilqis.bamf.control-plane.command-inspection/v1")
        client.preview_command.assert_called_once()
        client.submit_command.assert_called_once()
        client.inspect_command.assert_called_once_with("operation:" + "1" * 64)
        self.assertNotIn("session_id", repr((preview, submitted, inspection)))

    def test_event_stream_serializes_cp04_envelopes_without_private_session_state(self):
        event = next(item for item in SAMPLES if type(item) is EventEnvelope)
        client = Mock()
        client.connect.return_value = {"accepted": True}
        client.subscribe_events.return_value = iter((event,))
        output = StringIO()
        with patch(
            "bilqis_mlx.mission_control.electron.bridge.ControlPlaneClient",
            return_value=client,
        ), patch("sys.stdout", output):
            self.assertEqual(stream_events(), 0)
        serialized = output.getvalue()
        self.assertIn(event.event_id, serialized)
        self.assertIn(event.payload_record_id, serialized)
        self.assertNotIn("session_id", serialized)
        client.close.assert_called_once_with()

    def test_cp03_query_is_available_without_exposing_cp01_session_or_service_identity(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "cp.sock"
            service = ControlPlaneService(
                root / "missing-run", socket_path,
                query_source=lambda: MissionControlQueryCatalog(SAMPLES),
            )
            thread = start_service(service)
            try:
                with patch.dict(os.environ, {"BILQIS_CONTROL_PLANE_SOCKET": str(socket_path)}):
                    bridge = ElectronBridge()
                    bridge.connect()
                    page = bridge.query(QueryRequest(
                        QueryFamily.SEMANTIC, limit=32).to_record())
                    bridge.disconnect()
            finally:
                service.shutdown()
                thread.join(2)

        self.assertTrue(page["accepted"])
        self.assertEqual(page["family"], "semantic")
        self.assertGreater(page["total_matches"], 1)
        self.assertNotIn("service", page)
        self.assertNotIn("session", page)
        self.assertNotIn("session_id", repr(page))
        self.assertNotIn("service_id", repr(page))

    def test_real_cp01_handshake_and_health_are_sanitized_for_electron_main(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "cp.sock"
            service = ControlPlaneService(root / "missing-run", socket_path)
            thread = start_service(service)
            try:
                with patch.dict(os.environ, {"BILQIS_CONTROL_PLANE_SOCKET": str(socket_path)}):
                    bridge = ElectronBridge()
                    connected = bridge.connect()
                    status = bridge.status()
                    disconnected = bridge.disconnect()
            finally:
                service.shutdown()
                thread.join(2)

        self.assertEqual(connected["protocolVersion"], "bilqis.bamf.control-plane/v1")
        self.assertEqual(connected["state"], "learner-unavailable")
        self.assertTrue(connected["serviceLive"])
        self.assertTrue(connected["serviceReady"])
        self.assertFalse(connected["learnerReady"])
        self.assertFalse(connected["learnerActive"])
        self.assertEqual(status["state"], "learner-unavailable")
        self.assertTrue(status["serviceLive"])
        self.assertEqual(disconnected["state"], "disconnected")
        serialized = repr((connected, status, disconnected))
        self.assertNotIn(str(socket_path), serialized)
        self.assertNotIn(str(root / "missing-run"), serialized)
        self.assertNotIn("session_id", serialized)
        self.assertNotIn("service_id", serialized)

    def test_permission_failure_preserves_cp01_unauthorized_state(self):
        client = Mock()
        client.state = ControlPlaneState.UNAUTHORIZED
        client.connect.side_effect = PermissionError("private socket")
        bridge = ElectronBridge()
        with patch(
            "bilqis_mlx.mission_control.electron.bridge.ControlPlaneClient",
            return_value=client,
        ):
            status = bridge.connect()

        self.assertEqual(status["state"], "unauthorized")
        self.assertFalse(status["serviceLive"])
        self.assertNotIn("private socket", repr(status))
        client.close.assert_called_once_with(preserve_state=True)

    def test_query_timeout_discards_poisoned_cp01_client_before_retry(self):
        client = Mock()
        client.query.side_effect = TimeoutError("slow query")
        bridge = ElectronBridge()
        bridge.client = client

        with self.assertRaises(TimeoutError):
            bridge.query(QueryRequest(QueryFamily.RUN).to_record())

        self.assertIsNone(bridge.client)
        client.close.assert_called_once_with()

    def test_default_socket_path_matches_accepted_cp01_locator(self):
        with patch.dict(os.environ, {
                "BILQIS_CONTROL_PLANE_SOCKET": "", "RUN_DIR": "",
        }), patch(
                "bilqis_mlx.mission_control.electron.bridge.discover_active_endpoint",
                return_value=None):
            self.assertEqual(_socket_path(), _default_socket(active_run_dir()))

    def test_default_socket_path_prefers_discovered_active_operator(self):
        discovered = Path("/tmp/bilqis-active-operator.sock")
        endpoint = SimpleNamespace(
            run_dir=Path("/tmp/bilqis-active-run"), socket_path=discovered)
        with patch.dict(os.environ, {
                "BILQIS_CONTROL_PLANE_SOCKET": "", "RUN_DIR": ""}), patch(
                "bilqis_mlx.mission_control.electron.bridge.discover_active_endpoint",
                return_value=endpoint, create=True):
            self.assertEqual(_socket_path(), discovered.resolve())

    def test_bridge_autostarts_cp01_for_discovered_operator_run(self):
        from bilqis_mlx.control_plane.active_endpoint import advertise_active_endpoint

        with TemporaryDirectory(dir="/tmp") as directory:
            root = Path(directory)
            run_dir = root / "operator-run"
            run_dir.mkdir()
            socket_path = root / ".operator-run.control-plane.sock"
            registry = root / "registry"
            bridge = ElectronBridge()
            with patch.dict(os.environ, {
                    "BILQIS_ACTIVE_CONTROL_PLANE_DIR": str(registry),
                    "BILQIS_CONTROL_PLANE_SOCKET": "",
                    "RUN_DIR": "",
            }), advertise_active_endpoint(run_dir, socket_path=socket_path):
                connected = bridge.connect()
                self.assertTrue(connected["serviceLive"])
                self.assertEqual(connected["state"], "learner-unavailable")
                self.assertTrue(socket_path.exists())
            bridge.close()
            self.assertFalse(socket_path.exists())


if __name__ == "__main__":
    unittest.main()
