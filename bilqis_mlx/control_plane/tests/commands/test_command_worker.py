"""CP05 detached worker and ambiguity semantics."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL
from bilqis_mlx.mission_control.operator import ActionReceiptState
from bilqis_mlx.control_plane.command.model import CommandMode
from bilqis_mlx.control_plane.command.worker import run_worker
from bilqis_mlx.control_plane.command.manager import CommandManager

from ..command_support import DIGESTS, FakeExecutor, Launcher, request


class CommandWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run_dir = self.root / "run"
        self.store_root = self.root / "commands"
        self.executor = FakeExecutor(
            self.run_dir, CommandMode.MUTATING)
        self.manager = CommandManager(
            self.run_dir,
            self.store_root,
            executor=self.executor,
            launcher=Launcher(),
        )

    def tearDown(self):
        self.temporary.cleanup()

    def submit(self):
        return self.manager.submit(request(
            action="create", dry_run=False, human_authorized=True))

    def test_mutation_terminalizes_from_worker_readback(self):
        accepted = self.submit()
        self.assertEqual(accepted.state, ActionReceiptState.ACCEPTED)

        result = run_worker(
            store_root=self.store_root,
            run_dir=self.run_dir,
            operation_id=accepted.operation_id,
            executor=self.executor,
        )
        terminal = self.manager.status(accepted.operation_id)
        self.assertEqual(result, 0)
        self.assertEqual(terminal.state, ActionReceiptState.COMPLETED)
        self.assertEqual(self.executor.verify_calls, 1)
        self.assertEqual(self.executor.execute_calls, 1)

    def test_ambiguous_worker_failure_stays_outcome_unknown(self):
        self.executor.execute_result = (
            7, "command-error:7:" + DIGESTS[0])
        accepted = self.submit()
        result = run_worker(
            store_root=self.store_root,
            run_dir=self.run_dir,
            operation_id=accepted.operation_id,
            executor=self.executor,
        )

        self.assertEqual(result, 2)
        receipt = self.manager.status(accepted.operation_id)
        self.assertEqual(receipt.state, ActionReceiptState.OUTCOME_UNKNOWN)
        self.assertIsNone(
            self.manager.store.read_terminal(accepted.operation_id))

    def test_target_drift_before_execution_fails_without_effect(self):
        try:
            ErrorBus.raise_(
                SCHOOL.BAMF_CONTROL_PLANE.INVALID,
                reason="CONTROL_PLANE_COMMAND_TARGET_DRIFT",
            )
        except BilqisError as error:
            self.executor.verify_error = error
        accepted = self.submit()
        result = run_worker(
            store_root=self.store_root,
            run_dir=self.run_dir,
            operation_id=accepted.operation_id,
            executor=self.executor,
        )

        self.assertEqual(result, 1)
        self.assertEqual(
            self.manager.status(accepted.operation_id).state,
            ActionReceiptState.FAILED,
        )
        self.assertEqual(self.executor.execute_calls, 0)


if __name__ == "__main__":
    unittest.main()
