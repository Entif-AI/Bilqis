"""CP01 client-side state and handshake validation behavior."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.control_plane import (
    ControlPlaneClient, ControlPlaneState, PROTOCOL_VERSION,
)
from bilqis_mlx.errors import BilqisError


class ControlPlaneClientTests(unittest.TestCase):
    def test_disconnected_client_failure_uses_typed_error_control_plane(self):
        with TemporaryDirectory() as temporary:
            client = ControlPlaneClient(Path(temporary) / "missing.sock")
            with self.assertRaises(BilqisError) as caught:
                client.request("health")
        self.assertEqual(
            caught.exception.code, "SCHOOL.BAMF_CONTROL_PLANE.INVALID")
        self.assertEqual(
            caught.exception.context["reason"],
            "CONTROL_PLANE_CLIENT_DISCONNECTED")

    def test_permission_and_refusal_do_not_invent_restart_intent(self):
        with TemporaryDirectory() as temporary:
            socket_path = Path(temporary) / "cp.sock"
            unauthorized = ControlPlaneClient(socket_path)
            with patch("socket.socket.connect", side_effect=PermissionError):
                with self.assertRaises(PermissionError):
                    unauthorized.connect()
            self.assertEqual(
                unauthorized.state, ControlPlaneState.UNAUTHORIZED)

            disconnected = ControlPlaneClient(socket_path)
            with patch(
                    "socket.socket.connect",
                    side_effect=ConnectionRefusedError):
                with self.assertRaises(ConnectionRefusedError):
                    disconnected.connect()
            self.assertEqual(
                disconnected.state, ControlPlaneState.DISCONNECTED)

    def test_accepted_handshake_requires_correlated_identity(self):
        client = ControlPlaneClient(Path("/tmp/not-used"), client_id="expected")
        with self.assertRaises(BilqisError) as caught:
            client._validate_handshake({
                "schema": "bilqis.bamf.control-plane.handshake/v1",
                "accepted": True,
                "protocol_version": PROTOCOL_VERSION,
                "service": {
                    "schema": "bilqis.bamf.control-plane.service-identity/v1",
                    "service_id": "service-a",
                    "protocol_version": PROTOCOL_VERSION,
                },
                "session": {
                    "schema": "bilqis.bamf.control-plane.session-identity/v1",
                    "session_id": "session-a",
                    "service_id": "service-b",
                    "client_id": "expected",
                    "protocol_version": PROTOCOL_VERSION,
                },
            })
        self.assertEqual(
            caught.exception.context["reason"],
            "CONTROL_PLANE_HANDSHAKE_IDENTITY_INVALID")

    def test_malformed_accepted_handshake_closes_connection(self):
        client = ControlPlaneClient(Path("/tmp/not-used"))
        malformed = {
            "schema": "bilqis.bamf.control-plane.handshake/v1",
            "accepted": True,
            "state": "healthy",
            "protocol_version": PROTOCOL_VERSION,
            "service": {"service_id": "missing-schema"},
            "session": {"session_id": "missing-schema"},
        }
        with patch("socket.socket.connect", return_value=None), \
                patch.object(ControlPlaneClient, "_send", return_value=malformed):
            with self.assertRaises(BilqisError):
                client.connect()
        self.assertIsNone(client._socket)
        self.assertIsNone(client._stream)
        self.assertEqual(client.state, ControlPlaneState.DISCONNECTED)


if __name__ == "__main__":
    unittest.main()
