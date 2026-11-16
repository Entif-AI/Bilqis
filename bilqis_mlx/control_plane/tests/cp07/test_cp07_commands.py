"""CP07 accepted C11 disposable genesis through CP05's durable command flow."""
from unittest.mock import patch

from bilqis_mlx.control_plane import ControlPlaneClient, ControlPlaneService
from bilqis_mlx.control_plane.command.c11 import report_target
from bilqis_mlx.control_plane.command.executor import C11CommandExecutor
from bilqis_mlx.control_plane.command.manager import CommandManager
from bilqis_mlx.control_plane.command.worker import run_worker
from bilqis_mlx.control_plane.tests.command_support import Launcher, request
from bilqis_mlx.mission_control.operator import ActionParameter, ActionReceiptState
from bilqis_mlx.presentation.operator_cli.tests.bamf_lifecycle.create_resume_support import (
    BamfCreateResumeCase, TOPOLOGY,
)
from bilqis_mlx.runtime.bamf_bundle import inspect_accepted_generation

from ..support import start_service


class DisposableC11Executor(C11CommandExecutor):
    """Run real C11 genesis under the existing test-only source/shape fixture."""

    def __init__(self, run_dir, case):
        super().__init__(run_dir)
        self.case = case
        self.preview = None
        self.executions = 0

    def fixture_preflight(self, argv):
        with self.case.foundation_create_context():
            code, output, errors = self.case.invoke(list(argv)[1:])
        self.case.assertEqual((code, errors), (0, ""))
        records = self.case.output_records(output)
        self.preview = records[-1]
        return self.preview

    def execute(self, plan, *, stdout_path, stderr_path):
        self.executions += 1
        with self.case.foundation_create_context():
            code, output, errors = self.case.invoke(list(plan.argv)[1:])
        stdout_path.write_text(output, encoding="utf-8")
        stderr_path.write_text(errors, encoding="utf-8")
        return code, None if code == 0 else "cp07:fixture-create-failed"

    def _current_target(self):
        if not (self.run_dir / "bamf-state.json").exists():
            return None
        return report_target(self.run_dir, self.preview, existing=True)


class CP07CommandRecoveryTests(BamfCreateResumeCase):
    def _fixture_command_parameters(self):
        run_dir = self.root / "cp07-command-run"
        manifest = self.root / "manifest.json"
        manifest.write_text("{}", encoding="utf-8")
        parameters = [
            ActionParameter("model_topology", str(TOPOLOGY)),
            ActionParameter("atlas_release_manifest", str(manifest)),
        ]
        parameters.extend(ActionParameter(
            flag.removeprefix("--").replace("-", "_"), value,
        ) for flag, value in zip(self.FOUNDATION_ARGS[::2], self.FOUNDATION_ARGS[1::2]))
        return run_dir, tuple(parameters)

    def test_c11_genesis_dry_run_mutation_and_lost_ack_recovery(self):
        run_dir, parameters = self._fixture_command_parameters()
        executor = DisposableC11Executor(run_dir, self)
        store = self.root / "operations"
        socket = self.root / "cp.sock"
        launcher = Launcher()
        manager = CommandManager(run_dir, store, executor=executor, launcher=launcher)
        service = ControlPlaneService(run_dir, socket, command_manager=manager)
        thread = start_service(service)
        try:
            with patch("bilqis_mlx.control_plane.command.executor.run_cli_json",
                       side_effect=executor.fixture_preflight):
                with ControlPlaneClient(socket) as client:
                    dry = client.submit_command(request(
                        request_id="cp07-dry", idempotency_key="cp07-dry",
                        parameters=parameters))
                    self.assertEqual(dry.state, ActionReceiptState.COMPLETED)
                    self.assertIsNotNone(dry.postcondition_ref)
                    self.assertFalse(run_dir.exists())
                    self.assertEqual(executor.executions, 0)

                    action = request(
                        request_id="cp07-create", idempotency_key="cp07-create",
                        action="create", dry_run=False,
                        human_authorized=True, parameters=parameters)
                    accepted = client.submit_command(action)
                    self.assertEqual(accepted.state, ActionReceiptState.ACCEPTED)
                    self.assertEqual(len(launcher.calls), 1)

                # Simulate transport loss after admission. At-most-once dispatch
                # must not depend on the missing acknowledgement being recovered.
                with ControlPlaneClient(socket) as reconnect:
                    unknown = reconnect.command_status(accepted.operation_id)
                    self.assertEqual(unknown.state, ActionReceiptState.OUTCOME_UNKNOWN)
                    retry = reconnect.submit_command(action)
                    self.assertEqual(retry.state, ActionReceiptState.OUTCOME_UNKNOWN)
                    self.assertEqual(len(launcher.calls), 1)

                self.assertEqual(run_worker(
                    store_root=store, run_dir=run_dir,
                    operation_id=accepted.operation_id, executor=executor), 0)
                self.assertEqual(executor.executions, 1)
                inspection = inspect_accepted_generation(run_dir / "bamf-state.json")
                self.assertEqual(inspection.generation, 0)
                self.assertEqual(inspection.optimizer_step, 0)
                postcondition = manager.store.read_postcondition(accepted.operation_id)
                self.assertEqual(postcondition["after"]["generation"], 0)
                self.assertEqual(postcondition["after"]["optimizer_step"], 0)
                before = (run_dir / "bamf-state.json").read_bytes()
                with ControlPlaneClient(socket) as event_client:
                    subscription = event_client.subscribe_events()
                    with ControlPlaneClient(socket) as client:
                        completed = client.command_status(accepted.operation_id)
                        self.assertEqual(completed.state, ActionReceiptState.COMPLETED)
                        self.assertEqual(completed.operation_id, accepted.operation_id)
                        self.assertIsNotNone(completed.postcondition_ref)
                        self.assertEqual(client.submit_command(action), completed)
                        self.assertEqual(len(launcher.calls), 1)
                    notice = next(subscription)
                    self.assertEqual(notice.event_family, "operator.action.state")
                    self.assertEqual(notice.payload_record_id, completed.meta.record_id)
                    self.assertEqual(notice.meta.run.generation, 0)
        finally:
            service.shutdown()
            thread.join(2)

        # Service re-instantiation must recover terminal disposition from the
        # operation store and authenticated C11 generation, without relaunch.
        second_launcher = Launcher()
        second_manager = CommandManager(
            run_dir, store, executor=executor, launcher=second_launcher)
        second_service = ControlPlaneService(
            run_dir, socket, command_manager=second_manager)
        second_thread = start_service(second_service)
        try:
            with ControlPlaneClient(socket) as client:
                recovered = client.command_status(accepted.operation_id)
                self.assertEqual(recovered, completed)
                self.assertEqual(client.request("health")["learner"]["generation"], 0)
        finally:
            second_service.shutdown()
            second_thread.join(2)
        self.assertEqual(second_launcher.calls, [])
        self.assertEqual(executor.executions, 1)
        self.assertEqual((run_dir / "bamf-state.json").read_bytes(), before)
