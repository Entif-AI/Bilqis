"""CP01 handshake, state, health, and protocol-boundary behavior."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

from bilqis_mlx.control_plane import (
    ControlPlaneClient, ControlPlaneService, ControlPlaneState, PROTOCOL_VERSION,
)
from bilqis_mlx.control_plane.contracts import ERROR_SCHEMA
from bilqis_mlx.control_plane.discovery import discover_learner

from .support import start_service


class ControlPlaneProtocolTests(unittest.TestCase):
    def test_cp01_state_vocabulary_is_distinct_and_complete(self):
        self.assertEqual(
            [item.value for item in ControlPlaneState],
            [
                "connecting", "healthy", "degraded", "incompatible-version",
                "unauthorized", "learner-unavailable", "service-restarting",
                "stale", "disconnected",
            ])

    def test_handshake_precedes_health_and_version_mismatch_fails_closed(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "cp.sock"
            service = ControlPlaneService(root / "missing-run", socket_path)
            thread = start_service(service)
            raw = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            raw.connect(str(socket_path))
            stream = raw.makefile("rwb")
            stream.write(b'{"type":"health"}\n')
            stream.flush()
            rejected = json.loads(stream.readline())
            self.assertEqual(rejected["state"], "connecting")
            self.assertEqual(rejected["reason"], "CONTROL_PLANE_HANDSHAKE_REQUIRED")
            stream.close()
            raw.close()

            wrong = ControlPlaneClient(
                socket_path, protocol_version="bilqis.bamf.control-plane/v0")
            response = wrong.connect()
            self.assertFalse(response["accepted"])
            self.assertEqual(response["state"], "incompatible-version")
            self.assertEqual(response["protocol_version"], PROTOCOL_VERSION)
            service.shutdown()
            thread.join(2)

    def test_health_distinguishes_live_service_from_unavailable_learner(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "cp.sock"
            service = ControlPlaneService(root / "missing-run", socket_path)
            thread = start_service(service)
            with ControlPlaneClient(socket_path, client_id="electron-fixture") as client:
                health = client.request("health")
                self.assertEqual(health["service_state"], "healthy")
                self.assertTrue(health["service_live"])
                self.assertTrue(health["service_ready"])
                self.assertFalse(health["learner_ready"])
                self.assertFalse(health["learner_active"])
                self.assertEqual(
                    health["learner"]["state"], "learner-unavailable")
                self.assertEqual(health["state"], "learner-unavailable")
            self.assertEqual(os.stat(socket_path).st_mode & 0o777, 0o600)
            service.shutdown()
            thread.join(2)

    def test_explicit_restart_intent_is_distinct_from_disconnected_transport(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "cp.sock"
            service = ControlPlaneService(root / "missing-run", socket_path)
            thread = start_service(service)
            client = ControlPlaneClient(socket_path)
            client.connect()
            service.prepare_restart()
            restarting = client.request("health")
            self.assertEqual(
                restarting["state"], ControlPlaneState.SERVICE_RESTARTING.value)
            self.assertEqual(
                restarting["service_state"],
                ControlPlaneState.SERVICE_RESTARTING.value)
            self.assertTrue(restarting["service_live"])
            self.assertFalse(restarting["service_ready"])
            client.close()
            service.shutdown()
            thread.join(2)

    def test_discovery_distinguishes_stale_from_degraded_learner_state(self):
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            (run_dir / "bamf-state.json").write_text("{}", encoding="utf-8")
            with patch(
                    "bilqis_mlx.runtime.bamf_bundle.inspect_accepted_generation",
                    side_effect=FileNotFoundError):
                stale = discover_learner(run_dir)
            with patch(
                    "bilqis_mlx.runtime.bamf_bundle.inspect_accepted_generation",
                    side_effect=ValueError("invalid fixture")):
                degraded = discover_learner(run_dir)
        self.assertEqual(stale.state, ControlPlaneState.STALE)
        self.assertEqual(degraded.state, ControlPlaneState.DEGRADED)

    def test_operator_activity_preserves_unobservable_as_unknown(self):
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            target = run_dir / "lock-target"
            target.write_text("", encoding="utf-8")
            (run_dir / ".bamf-operator.lock").symlink_to(target)
            observed = discover_learner(run_dir)
        self.assertEqual(
            observed.state, ControlPlaneState.LEARNER_UNAVAILABLE)
        self.assertIsNone(observed.operator_active)

    def test_dangling_operator_lock_is_unknown_not_inactive(self):
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            (run_dir / ".bamf-operator.lock").symlink_to(
                run_dir / "missing-lock-target")
            observed = discover_learner(run_dir)
        self.assertEqual(
            observed.state, ControlPlaneState.LEARNER_UNAVAILABLE)
        self.assertIsNone(observed.operator_active)

    def test_unsupported_cp02_operation_uses_transport_error_envelope(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "cp.sock"
            service = ControlPlaneService(root / "missing-run", socket_path)
            thread = start_service(service)
            try:
                with ControlPlaneClient(socket_path) as client:
                    response = client.request("snapshot")
                    self.assertEqual(
                        client.state, ControlPlaneState.LEARNER_UNAVAILABLE)
                self.assertEqual(response["schema"], ERROR_SCHEMA)
                self.assertFalse(response["accepted"])
                self.assertEqual(
                    response["reason"],
                    "CONTROL_PLANE_CP01_OPERATION_UNSUPPORTED")
                self.assertNotIn("state", response)
                self.assertNotIn("learner", response)
                self.assertNotIn("surface", response)
            finally:
                service.shutdown()
                thread.join(2)

    def test_direct_python_entrypoint_starts_without_gui(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "entry.sock"
            process = subprocess.Popen(
                [
                    sys.executable, "-m", "bilqis_mlx.control_plane",
                    "--run-dir", str(root / "missing-run"),
                    "--socket", str(socket_path),
                ],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            try:
                deadline = time.monotonic() + 3
                while not socket_path.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(socket_path.exists())
                with ControlPlaneClient(socket_path, client_id="cli-fixture") as client:
                    self.assertEqual(client.state, ControlPlaneState.LEARNER_UNAVAILABLE)
                    self.assertEqual(
                        client.request("liveness")["service_state"], "healthy")
            finally:
                process.send_signal(signal.SIGINT)
                process.wait(timeout=3)
            self.assertEqual(process.returncode, 0)


if __name__ == "__main__":
    unittest.main()
