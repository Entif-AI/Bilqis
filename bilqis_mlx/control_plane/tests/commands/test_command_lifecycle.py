"""CP05 admission and idempotency behavior."""
from dataclasses import replace
import unittest

from bilqis_mlx.mission_control.operator import ActionParameter, ActionReceiptState
from bilqis_mlx.control_plane.command.model import CommandMode
from bilqis_mlx.control_plane.command.manager import CommandManager

from ..command_support import (
    CommandManagerTestCase, FakeExecutor, Launcher, meta, request,
)


class CommandLifecycleTests(CommandManagerTestCase):
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

    def test_late_authoritative_no_effect_proof_terminalizes_without_relaunch(self):
        manager, executor, launcher = self.manager(CommandMode.MUTATING)
        accepted = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))
        manager.store.write_worker_result(
            accepted.operation_id,
            returncode=None,
            error_ref="command-error:custody:" + "1" * 64,
            finished_at=102,
        )
        executor.reconcile_no_effect_value = {
            "kind": "reconciled-no-effect",
            "before": executor.preflight(request(), accepted.operation_id)[0].target.to_record(),
        }

        terminal = manager.status(accepted.operation_id)

        self.assertEqual(terminal.state, ActionReceiptState.FAILED_BEFORE_EFFECT)
        self.assertEqual(len(launcher.calls), 1)
        self.assertIsNotNone(manager.store.read_reconciliation(accepted.operation_id))

    def test_permanently_unresolvable_operation_remains_unknown_and_never_relaunches(self):
        manager, _executor, launcher = self.manager(CommandMode.MUTATING)
        accepted = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))
        manager.store.write_worker_result(
            accepted.operation_id,
            returncode=7,
            error_ref="command-error:7:" + "1" * 64,
            finished_at=102,
        )

        first = manager.status(accepted.operation_id)
        second = manager.status(accepted.operation_id)

        self.assertEqual(first.state, ActionReceiptState.OUTCOME_UNKNOWN)
        self.assertEqual(second.state, ActionReceiptState.OUTCOME_UNKNOWN)
        self.assertIsNone(manager.store.read_terminal(accepted.operation_id))
        self.assertEqual(len(launcher.calls), 1)

    def test_stale_trainer_identity_does_not_block_late_completion_proof(self):
        manager, executor, _launcher = self.manager(CommandMode.MUTATING)
        accepted = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))
        manager.store.write_trainer_process(
            accepted.operation_id, pid=43210, identity_sha256="9" * 64)
        executor.trainer_process_state_value = "inactive"
        executor.reconcile_value = {"kind": "authoritative-readback"}

        completed = manager.status(accepted.operation_id)

        self.assertEqual(completed.state, ActionReceiptState.COMPLETED)


if __name__ == "__main__":
    unittest.main()
