"""C11 command adapter and owner-stop boundary."""
from pathlib import Path
import signal
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.mission_control.operator import ActionParameter
from bilqis_mlx.control_plane.command.executor import C11CommandExecutor
from bilqis_mlx.control_plane.command.model import (
    CommandAction, CommandMode, CommandPlan, operation_id_for,
)
from bilqis_mlx.control_plane.command.process import run_trainer
from bilqis_mlx.control_plane.command.store import CommandStore

from .command_support import DIGESTS, request, target


class C11CommandAdapterTests(unittest.TestCase):
    def test_trainer_is_interrupted_if_durable_process_custody_fails(self):
        class Process:
            pid = 43210

            def __init__(self):
                self.signals = []
                self.waits = 0

            def send_signal(self, value):
                self.signals.append(value)

            def wait(self):
                self.waits += 1
                return 130

        class FailingStore:
            def write_trainer_process(self, *_args, **_kwargs):
                raise OSError

        process = Process()
        with TemporaryDirectory() as temporary, patch(
            "bilqis_mlx.control_plane.command.process.subprocess.Popen",
            return_value=process,
        ):
            root = Path(temporary)
            returncode, error = run_trainer(
                argv=("train", "--human-run"),
                stdout_path=root / "trainer.stdout",
                stderr_path=root / "trainer.stderr",
                store=FailingStore(),
                operation_id=operation_id_for("custody-failure"),
                identity_resolver=lambda _pid: "9" * 64,
            )
        self.assertIsNone(returncode)
        self.assertTrue(error.startswith("command-error:custody:"))
        self.assertEqual(process.signals, [signal.SIGINT])
        self.assertEqual(process.waits, 1)

    def test_stop_targets_exact_active_trainer_operation_and_sends_sigint(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "run"
            store = CommandStore(root / "commands")
            target_operation = operation_id_for("active-owner-run")
            active_plan = CommandPlan(
                operation_id=target_operation,
                request_sha256="1" * 64,
                intent_sha256="2" * 64,
                action=CommandAction.RESUME,
                mode=CommandMode.MUTATING,
                target=target(run_dir),
                argv=("train", "--human-run"),
                postcondition_kind="operator-run-completed",
            )
            store.write_plan(active_plan)
            store.write_trainer_process(
                target_operation, pid=43210, identity_sha256="9" * 64)
            executor = C11CommandExecutor(run_dir, store=store)
            stop_request = request(
                idempotency_key="stop-owner-run",
                action="stop",
                dry_run=False,
                human_authorized=True,
                parameters=(ActionParameter("operation_id", target_operation),),
            )
            stop_operation = operation_id_for("stop-owner-run")
            with (
                patch.object(executor, "_pid_live", return_value=True),
                patch.object(
                    executor, "_process_identity_sha256",
                    return_value="9" * 64),
                patch.object(
                    executor, "_current_target", return_value=active_plan.target),
            ):
                plan, _preflight = executor.preflight(
                    stop_request, stop_operation)
                self.assertEqual(plan.action, CommandAction.STOP)
                self.assertEqual(plan.argv, (target_operation,))
                executor.verify_target_before_execute(plan)
                with patch(
                    "bilqis_mlx.control_plane.command.execution.os.kill"
                ) as send_signal:
                    returncode, error = executor.execute(
                        plan,
                        stdout_path=root / "stop.stdout",
                        stderr_path=root / "stop.stderr",
                    )
                send_signal.assert_called_once_with(43210, signal.SIGINT)
                self.assertEqual((returncode, error), (0, None))

    def test_mutation_requires_explicit_human_authorization(self):
        root = Path("/tmp/cp05-adapter-fixture")
        executor = C11CommandExecutor(root)
        report = {
            "run_identity": {
                "run_id": "run-a",
                "run_seed": 1,
                "run_identity_sha256": DIGESTS[0],
                "initial_candidate_identity_sha256": DIGESTS[1],
                "factory_release_sha256": DIGESTS[2],
                "initial_source_identity": "source:a",
            },
            "model_topology": {"digest": DIGESTS[3]},
            "atlas_release_manifest": {"release_sha256": DIGESTS[4]},
        }
        with patch.object(
            executor,
            "_create_preflight",
            return_value=(
                report,
                ("train", "--dry-run", "--run-dir", str(root)),
            ),
        ):
            with self.assertRaises(BilqisError) as caught:
                executor.preflight(
                    request(action="create", dry_run=False),
                    operation_id_for("adapter-idem"),
                )
        self.assertEqual(
            caught.exception.context["reason"],
            "CONTROL_PLANE_COMMAND_HUMAN_AUTHORIZATION_REQUIRED",
        )

    def test_pause_remains_unavailable_but_stop_reaches_runtime_validation(self):
        executor = C11CommandExecutor(Path("/tmp/cp05-adapter-fixture"))
        with self.assertRaises(BilqisError) as caught:
            executor.preflight(
                request(action="pause"),
                operation_id_for("idem-pause"),
            )
        self.assertEqual(
            caught.exception.context["reason"],
            "CONTROL_PLANE_COMMAND_ACTION_UNAVAILABLE",
        )
        with self.assertRaises(BilqisError) as caught:
            executor.preflight(
                request(action="stop", dry_run=False, human_authorized=True),
                operation_id_for("idem-stop"),
            )
        self.assertEqual(
            caught.exception.context["reason"],
            "CONTROL_PLANE_COMMAND_STOP_OPERATION_REQUIRED",
        )

    def test_authorized_mutation_plan_adds_human_run_and_removes_dry_run(self):
        root = Path("/tmp/cp05-adapter-fixture")
        executor = C11CommandExecutor(root)
        report = {
            "run_identity": {
                "run_id": "run-a",
                "run_seed": 1,
                "run_identity_sha256": DIGESTS[0],
                "initial_candidate_identity_sha256": DIGESTS[1],
                "factory_release_sha256": DIGESTS[2],
                "initial_source_identity": "source:a",
            },
            "model_topology": {"digest": DIGESTS[3]},
            "atlas_release_manifest": {"release_sha256": DIGESTS[4]},
        }
        with patch.object(
            executor,
            "_create_preflight",
            return_value=(
                report,
                ("train", "--dry-run", "--run-dir", str(root)),
            ),
        ):
            plan, _ = executor.preflight(
                request(
                    action="create",
                    dry_run=False,
                    human_authorized=True,
                ),
                operation_id_for("authorized-adapter-idem"),
            )
        self.assertIn("--human-run", plan.argv)
        self.assertNotIn("--dry-run", plan.argv)


if __name__ == "__main__":
    unittest.main()
