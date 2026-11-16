"""CP05 local transport and C11 adapter boundary."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bilqis_mlx.mission_control.operator import ActionReceiptState
from bilqis_mlx.control_plane import ControlPlaneClient, ControlPlaneService
from bilqis_mlx.control_plane.command.model import CommandMode
from bilqis_mlx.control_plane.command.manager import CommandManager

from .command_support import FakeExecutor, Launcher, request
from .support import start_service


class CommandTransportTests(unittest.TestCase):
    def test_service_client_round_trip_uses_cp05_v2_receipt(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "run"
            manager = CommandManager(
                run_dir,
                root / "commands",
                executor=FakeExecutor(run_dir, CommandMode.DRY_RUN),
                launcher=Launcher(),
            )
            service = ControlPlaneService(
                run_dir, root / "cp.sock", command_manager=manager)
            thread = start_service(service)
            try:
                with ControlPlaneClient(root / "cp.sock") as client:
                    receipt = client.submit_command(request())
                    observed = client.command_status(receipt.operation_id)
                self.assertEqual(
                    receipt.state, ActionReceiptState.COMPLETED)
                self.assertEqual(observed, receipt)
            finally:
                service.shutdown()
                thread.join(2)

    def test_preview_and_inspection_expose_bounded_command_facts_without_run_path(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "private-run"
            manager = CommandManager(
                run_dir,
                root / "commands",
                executor=FakeExecutor(run_dir, CommandMode.DRY_RUN),
                launcher=Launcher(),
            )
            service = ControlPlaneService(
                run_dir, root / "cp.sock", command_manager=manager)
            thread = start_service(service)
            try:
                action = request()
                with ControlPlaneClient(root / "cp.sock") as client:
                    preview = client.preview_command(action)
                    receipt = client.submit_command(
                        action, expected_target_ref=preview["target_ref"])
                    inspection = client.inspect_command(receipt.operation_id)
                self.assertEqual(
                    preview["schema"],
                    "bilqis.bamf.control-plane.command-preview/v1",
                )
                self.assertEqual(preview["target_ref"], receipt.target_ref)
                self.assertEqual(
                    inspection["schema"],
                    "bilqis.bamf.control-plane.command-inspection/v1",
                )
                self.assertEqual(inspection["receipt"]["state"], "COMPLETED")
                serialized = repr((preview, inspection))
                self.assertNotIn(str(run_dir), serialized)
                self.assertNotIn("run_dir", serialized)
                self.assertNotIn("argv", serialized)
            finally:
                service.shutdown()
                thread.join(2)

    def test_returned_command_state_is_projected_into_cp04_events(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "run"
            manager = CommandManager(
                run_dir,
                root / "commands",
                executor=FakeExecutor(run_dir, CommandMode.MUTATING),
                launcher=Launcher(),
            )
            service = ControlPlaneService(
                run_dir, root / "cp.sock", command_manager=manager)
            opened = service.events.open_subscription(None)
            thread = start_service(service)
            try:
                with ControlPlaneClient(root / "cp.sock") as client:
                    receipt = client.submit_command(request(
                        action="create",
                        dry_run=False,
                        human_authorized=True,
                    ))
                event = opened.subscription.next_record(0.25)
                self.assertEqual(receipt.state, ActionReceiptState.ACCEPTED)
                self.assertEqual(event["event_family"], "operator.action.state")
                self.assertEqual(
                    event["payload_record_id"], receipt.meta.record_id)
            finally:
                opened.subscription.close()
                service.shutdown()
                thread.join(2)

    def test_default_store_is_outside_fresh_run_directory(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "run"
            service = ControlPlaneService(run_dir, root / "cp.sock")
            try:
                with self.assertRaises(ValueError):
                    service.command_store_path.relative_to(run_dir)
            finally:
                service.server_close()

    def test_service_restart_recovers_operation_by_id_without_relaunch(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "run"
            store = root / "commands"
            first_launcher = Launcher()
            first = CommandManager(
                run_dir,
                store,
                executor=FakeExecutor(run_dir, CommandMode.MUTATING),
                launcher=first_launcher,
            )
            service = ControlPlaneService(
                run_dir, root / "cp.sock", command_manager=first)
            thread = start_service(service)
            try:
                with ControlPlaneClient(root / "cp.sock") as client:
                    accepted = client.submit_command(request(
                        action="create",
                        dry_run=False,
                        human_authorized=True,
                    ))
            finally:
                service.shutdown()
                thread.join(2)

            restarted_executor = FakeExecutor(
                run_dir, CommandMode.MUTATING)
            restarted_executor.reconcile_value = {
                "kind": "authoritative-readback"}
            restarted_launcher = Launcher()
            restarted = CommandManager(
                run_dir,
                store,
                executor=restarted_executor,
                launcher=restarted_launcher,
            )
            service = ControlPlaneService(
                run_dir, root / "cp.sock", command_manager=restarted)
            thread = start_service(service)
            try:
                with ControlPlaneClient(root / "cp.sock") as client:
                    receipt = client.command_status(accepted.operation_id)
                self.assertEqual(
                    receipt.state, ActionReceiptState.COMPLETED)
                self.assertEqual(restarted_launcher.calls, [])
                self.assertEqual(len(first_launcher.calls), 1)
            finally:
                service.shutdown()
                thread.join(2)

if __name__ == "__main__":
    unittest.main()
