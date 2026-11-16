"""CP05 admission and idempotency behavior."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL
from bilqis_mlx.mission_control.operator import (
    ActionParameter, ActionReceiptState,
)
from bilqis_mlx.control_plane.command.model import CommandMode
from bilqis_mlx.control_plane.command.manager import CommandManager

from ..command_support import FakeExecutor, Launcher, meta, request


class CommandLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run_dir = self.root / "run"
        self.store_root = self.root / "commands"

    def tearDown(self):
        self.temporary.cleanup()

    def manager(self, mode=CommandMode.DRY_RUN):
        executor = FakeExecutor(self.run_dir, mode)
        launcher = Launcher()
        return (
            CommandManager(
                self.run_dir,
                self.store_root,
                executor=executor,
                launcher=launcher,
            ),
            executor,
            launcher,
        )

    def test_dry_run_is_terminal_deterministic_and_never_launches_worker(self):
        manager, executor, launcher = self.manager()
        first = manager.submit(request())
        retry = manager.submit(request(
            request_id="request-2", requested_at=101))

        self.assertEqual(first.state, ActionReceiptState.COMPLETED)
        self.assertEqual(retry, first)
        self.assertEqual(executor.preflight_calls, 1)
        self.assertEqual(launcher.calls, [])
        self.assertIsNotNone(first.postcondition_ref)
        self.assertEqual(
            manager.store.read_accepted(first.operation_id).state,
            ActionReceiptState.ACCEPTED,
        )

    def test_idempotency_conflict_rejects_without_repeating_effect(self):
        manager, _executor, launcher = self.manager()
        original = manager.submit(request())
        conflict = manager.submit(request(
            request_id="request-conflict",
            parameters=(ActionParameter("minutes", 9),),
        ))

        self.assertEqual(original.state, ActionReceiptState.COMPLETED)
        self.assertEqual(conflict.state, ActionReceiptState.REJECTED)
        self.assertEqual(conflict.operation_id, original.operation_id)
        self.assertEqual(launcher.calls, [])

    def test_request_id_cannot_be_rebound_to_a_different_operation(self):
        manager, _executor, _launcher = self.manager()
        manager.submit(request())
        conflict = manager.submit(request(
            idempotency_key="different-idem",
            parameters=(ActionParameter("minutes", 3),),
        ))
        self.assertEqual(conflict.state, ActionReceiptState.REJECTED)

    def test_same_mutating_identity_never_launches_twice_after_lost_ack(self):
        manager, _executor, launcher = self.manager(CommandMode.MUTATING)
        action = request(
            action="create", dry_run=False, human_authorized=True)
        first = manager.submit(action)
        retry = manager.submit(replace(
            action,
            meta=meta("request:retry", 101),
            request_id="request-retry",
            requested_at=101,
        ))

        self.assertEqual(first.state, ActionReceiptState.ACCEPTED)
        self.assertEqual(retry.state, ActionReceiptState.OUTCOME_UNKNOWN)
        self.assertEqual(len(launcher.calls), 1)

    def test_restart_reconciles_by_readback_without_relaunch(self):
        manager, _executor, launcher = self.manager(CommandMode.MUTATING)
        accepted = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))
        restarted_executor = FakeExecutor(
            self.run_dir, CommandMode.MUTATING)
        restarted_executor.reconcile_value = {
            "kind": "authoritative-readback"}
        restarted_launcher = Launcher()
        restarted = CommandManager(
            self.run_dir,
            self.store_root,
            executor=restarted_executor,
            launcher=restarted_launcher,
        )

        terminal = restarted.status(accepted.operation_id)
        self.assertEqual(terminal.state, ActionReceiptState.COMPLETED)
        self.assertEqual(restarted_launcher.calls, [])
        self.assertEqual(len(launcher.calls), 1)

    def test_live_worker_or_recorded_trainer_never_reconciles_to_terminal(self):
        manager, executor, _launcher = self.manager(CommandMode.MUTATING)
        accepted = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))
        with (
            patch(
                "bilqis_mlx.control_plane.command.status.pid_live",
                return_value=True,
            ),
            patch.object(
                executor, "reconcile",
                side_effect=AssertionError("live operation must not reconcile"),
            ),
        ):
            pending = manager.status(accepted.operation_id)
        self.assertEqual(pending.state, ActionReceiptState.PENDING)
        self.assertIsNone(manager.store.read_terminal(accepted.operation_id))

        manager.store.write_trainer_process(
            accepted.operation_id, pid=43210, identity_sha256="9" * 64)
        with (
            patch(
                "bilqis_mlx.control_plane.command.status.pid_live",
                return_value=False,
            ),
            patch.object(
                executor, "reconcile",
                side_effect=AssertionError("recorded trainer must not reconcile"),
            ),
        ):
            unknown = manager.status(accepted.operation_id)
        self.assertEqual(unknown.state, ActionReceiptState.OUTCOME_UNKNOWN)
        self.assertIsNone(manager.store.read_terminal(accepted.operation_id))

    def test_target_conflict_rejects_before_dispatch(self):
        manager, executor, launcher = self.manager(CommandMode.MUTATING)
        try:
            ErrorBus.raise_(
                SCHOOL.BAMF_CONTROL_PLANE.INVALID,
                reason="CONTROL_PLANE_COMMAND_TARGET_CONFLICT",
            )
        except BilqisError as error:
            executor.preflight_error = error
        receipt = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))

        self.assertEqual(receipt.state, ActionReceiptState.REJECTED)
        self.assertEqual(launcher.calls, [])
        self.assertIsNone(manager.store.read_dispatch(receipt.operation_id))

    def test_expected_preview_target_blocks_stale_authorization_before_dispatch(self):
        manager, executor, launcher = self.manager(CommandMode.MUTATING)
        action = request(action="create", dry_run=False, human_authorized=True)
        stale = "command-target:" + "f" * 64
        receipt = manager.submit(action, expected_target_ref=stale)

        self.assertEqual(receipt.state, ActionReceiptState.REJECTED)
        self.assertEqual(executor.preflight_calls, 1)
        self.assertEqual(launcher.calls, [])
        self.assertIsNone(manager.store.read_dispatch(receipt.operation_id))
        self.assertNotEqual(receipt.target_ref, stale)

    def test_matching_preview_target_preserves_existing_single_dispatch_semantics(self):
        manager, executor, launcher = self.manager(CommandMode.MUTATING)
        action = request(action="create", dry_run=False, human_authorized=True)
        plan, _ = executor.preview(action, "operation:" + "a" * 64)
        executor.preflight_calls = 0
        receipt = manager.submit(action, expected_target_ref=plan.target.ref)

        self.assertEqual(receipt.state, ActionReceiptState.ACCEPTED)
        self.assertEqual(executor.preflight_calls, 1)
        self.assertEqual(len(launcher.calls), 1)


if __name__ == "__main__":
    unittest.main()
