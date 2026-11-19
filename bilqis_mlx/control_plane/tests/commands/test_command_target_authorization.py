"""CP05 target authorization and stale-preview guards."""
import unittest

from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL
from bilqis_mlx.mission_control.operator import ActionReceiptState
from bilqis_mlx.control_plane.command.model import CommandMode

from ..command_support import CommandManagerTestCase, request


class CommandTargetAuthorizationTests(CommandManagerTestCase):
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
