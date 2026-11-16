"""CP01 Unix-transport ownership and isolation behavior."""
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
from threading import Event, Thread
import unittest
from unittest.mock import patch

import bilqis_mlx.control_plane.service as service_module
from bilqis_mlx.control_plane import ControlPlaneClient, ControlPlaneService
from bilqis_mlx.errors import BilqisError

from .support import start_service


class ControlPlaneTransportTests(unittest.TestCase):
    def test_transport_is_unix_only_and_occupied_path_fails_typed(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "cp.sock"
            service = ControlPlaneService(root / "missing-run", socket_path)
            self.assertEqual(service._server.socket.family, socket.AF_UNIX)
            service.server_close()

            socket_path.write_text("not-a-socket", encoding="utf-8")
            with self.assertRaises(BilqisError) as caught:
                ControlPlaneService(root / "missing-run", socket_path)
            self.assertEqual(
                caught.exception.code, "SCHOOL.BAMF_CONTROL_PLANE.INVALID")
            self.assertEqual(
                caught.exception.context["reason"],
                "CONTROL_PLANE_SOCKET_PATH_OCCUPIED")

    def test_second_service_cannot_steal_an_active_local_socket(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "cp.sock"
            first = ControlPlaneService(root / "missing-run", socket_path)
            thread = start_service(first)
            try:
                with self.assertRaises(BilqisError) as caught:
                    ControlPlaneService(root / "missing-run", socket_path)
                self.assertEqual(
                    caught.exception.context["reason"],
                    "CONTROL_PLANE_SOCKET_ALREADY_ACTIVE")
                with ControlPlaneClient(socket_path) as client:
                    self.assertEqual(
                        client.request("liveness")["service_state"], "healthy")
            finally:
                first.shutdown()
                thread.join(2)

    def test_concurrent_launch_loser_cannot_unlink_winner_socket(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "cp.sock"
            bound, release = Event(), Event()
            services, failures = [], []
            original_activate = (
                service_module._ThreadedUnixServer.server_activate)

            def blocked_activate(server):
                bound.set()
                release.wait(2)
                return original_activate(server)

            def launch_first():
                try:
                    services.append(
                        ControlPlaneService(root / "missing-run", socket_path))
                except Exception as error:
                    failures.append(error)

            with patch.object(
                    service_module._ThreadedUnixServer, "server_activate",
                    autospec=True, side_effect=blocked_activate):
                first = Thread(target=launch_first)
                first.start()
                self.assertTrue(bound.wait(1))
                with self.assertRaises(BilqisError) as caught:
                    ControlPlaneService(root / "missing-run", socket_path)
                self.assertEqual(
                    caught.exception.context["reason"],
                    "CONTROL_PLANE_SOCKET_ALREADY_ACTIVE")
                self.assertTrue(socket_path.exists())
                release.set()
                first.join(3)

            self.assertEqual((len(services), len(failures)), (1, 0))
            winner = services[0]
            thread = start_service(winner)
            try:
                with ControlPlaneClient(socket_path) as client:
                    self.assertEqual(
                        client.request("liveness")["service_state"], "healthy")
            finally:
                winner.shutdown()
                thread.join(2)

    def test_stale_socket_cleanup_refuses_to_unlink_replacement_identity(self):
        with TemporaryDirectory() as temporary:
            socket_path = Path(temporary) / "cp.sock"
            stale = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            stale.bind(str(socket_path))
            stale.close()
            replacement = []

            def replace_before_refusal(*_args):
                socket_path.unlink()
                winner = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                winner.bind(str(socket_path))
                winner.listen()
                replacement.append(winner)
                raise ConnectionRefusedError

            try:
                with patch.object(
                        socket.socket, "connect",
                        side_effect=replace_before_refusal):
                    with self.assertRaises(BilqisError) as caught:
                        service_module._prepare_socket_path(socket_path)
                self.assertEqual(
                    caught.exception.context["reason"],
                    "CONTROL_PLANE_SOCKET_CHANGED_DURING_STARTUP")
                self.assertTrue(socket_path.exists())
                self.assertEqual(
                    service_module._socket_identity(socket_path),
                    (socket_path.lstat().st_dev, socket_path.lstat().st_ino))
            finally:
                for winner in replacement:
                    winner.close()
                socket_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
