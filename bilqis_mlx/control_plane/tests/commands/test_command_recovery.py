"""CP05 ambiguous-outcome recovery and mutation quarantine behavior."""
import os
import unittest
from unittest.mock import patch

from bilqis_mlx.mission_control.operator import ActionParameter, ActionReceiptState
from bilqis_mlx.control_plane.command.model import CommandMode
from bilqis_mlx.control_plane.command.manager import CommandManager

from ..command_support import (
    CommandManagerTestCase, FakeExecutor, Launcher, request,
)


class CommandRecoveryLifecycleTests(CommandManagerTestCase):
    def test_unknown_outcome_quarantines_new_same_learner_mutation(self):
        manager, _executor, launcher = self.manager(CommandMode.MUTATING)
        accepted = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))
        manager.store.write_worker_result(
            accepted.operation_id,
            returncode=7,
            error_ref="command-error:7:" + "1" * 64,
            finished_at=102,
        )

        blocked = manager.submit(request(
            request_id="request-2",
            idempotency_key="idem-2",
            action="create",
            dry_run=False,
            human_authorized=True,
            requested_at=103,
        ))

        self.assertEqual(blocked.state, ActionReceiptState.REJECTED)
        self.assertEqual(len(launcher.calls), 1)
        self.assertIsNone(manager.store.read_dispatch(blocked.operation_id))

    def test_pending_same_learner_mutation_is_quarantined_before_ambiguity(self):
        executor = FakeExecutor(self.run_dir, CommandMode.MUTATING)
        launcher = Launcher(pid=os.getpid())
        manager = CommandManager(
            self.run_dir, self.store_root, executor=executor, launcher=launcher)
        accepted = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))
        self.assertEqual(
            manager.status(accepted.operation_id).state,
            ActionReceiptState.PENDING,
        )

        blocked = manager.submit(request(
            request_id="request-2",
            idempotency_key="idem-2",
            action="create",
            dry_run=False,
            human_authorized=True,
            requested_at=103,
        ))

        self.assertEqual(blocked.state, ActionReceiptState.REJECTED)
        self.assertEqual(len(launcher.calls), 1)
        self.assertIsNone(manager.store.read_dispatch(blocked.operation_id))

    def test_unknown_outcome_still_allows_read_only_reconciliation_surfaces(self):
        manager, executor, launcher = self.manager(CommandMode.MUTATING)
        accepted = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))
        manager.store.write_worker_result(
            accepted.operation_id,
            returncode=7,
            error_ref="command-error:7:" + "1" * 64,
            finished_at=102,
        )
        self.assertEqual(
            manager.status(accepted.operation_id).state,
            ActionReceiptState.OUTCOME_UNKNOWN,
        )

        executor.mode = CommandMode.DRY_RUN
        read_only = manager.submit(request(
            request_id="request-status",
            idempotency_key="idem-status",
            action="status",
            dry_run=True,
            requested_at=103,
        ))

        self.assertEqual(read_only.state, ActionReceiptState.COMPLETED)
        self.assertEqual(len(launcher.calls), 1)

    def test_unknown_outcome_does_not_blanket_block_stop_boundary(self):
        manager, executor, launcher = self.manager(CommandMode.MUTATING)
        accepted = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))
        manager.store.write_trainer_process(
            accepted.operation_id, pid=43210, identity_sha256="9" * 64)
        executor.trainer_process_state_value = "current"
        self.assertEqual(
            manager.status(accepted.operation_id).state,
            ActionReceiptState.OUTCOME_UNKNOWN,
        )

        stop = manager.submit(request(
            request_id="request-stop",
            idempotency_key="idem-stop",
            action="stop",
            parameters=(ActionParameter("operation_id", accepted.operation_id),),
            dry_run=False,
            human_authorized=True,
            requested_at=103,
        ))

        self.assertEqual(stop.state, ActionReceiptState.ACCEPTED)
        self.assertEqual(len(launcher.calls), 2)

    def test_unknown_outcome_stop_must_name_the_blocking_operation(self):
        manager, executor, launcher = self.manager(CommandMode.MUTATING)
        accepted = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))
        manager.store.write_trainer_process(
            accepted.operation_id, pid=43210, identity_sha256="9" * 64)
        executor.trainer_process_state_value = "current"

        blocked = manager.submit(request(
            request_id="request-stop-wrong",
            idempotency_key="idem-stop-wrong",
            action="stop",
            parameters=(ActionParameter(
                "operation_id", "operation:" + "a" * 64),),
            dry_run=False,
            human_authorized=True,
            requested_at=103,
        ))

        self.assertEqual(blocked.state, ActionReceiptState.REJECTED)
        self.assertEqual(len(launcher.calls), 1)

    def test_live_worker_or_current_trainer_never_reconciles_to_terminal(self):
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
        executor.trainer_process_state_value = "current"

    def test_unknown_process_identity_keeps_operation_unresolved(self):
        manager, executor, _launcher = self.manager(CommandMode.MUTATING)
        accepted = manager.submit(request(
            action="create", dry_run=False, human_authorized=True))
        manager.store.write_trainer_process(
            accepted.operation_id, pid=43210, identity_sha256="9" * 64)
        executor.trainer_process_state_value = "unknown"
        executor.reconcile_value = {"kind": "authoritative-readback"}

        receipt = manager.status(accepted.operation_id)

        self.assertEqual(receipt.state, ActionReceiptState.OUTCOME_UNKNOWN)
        self.assertIsNone(manager.store.read_terminal(accepted.operation_id))
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


if __name__ == "__main__":
    unittest.main()
