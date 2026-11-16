"""CP05 adapter that delegates BAMF behavior to the accepted C11 CLI."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.mission_control.operator import OperatorActionRequestV2

from .c11 import (
    parameter_flags, parameter_map, report_target, run_cli_json, same_lineage,
)
from .execution import C11ExecutionRuntime
from .model import (
    CommandAction, CommandMode, CommandPlan, ResolvedCommandTarget,
    intent_sha256, operation_directory_name, request_sha256,
)
from ..transport import _invalid

class C11CommandExecutor(C11ExecutionRuntime):
    """Preflight and execute only through the existing human operator boundary."""

    def __init__(self, run_dir: Path, *, store=None):
        self.run_dir = Path(run_dir).expanduser().resolve()
        self.store = store

    def _run_cli_json(self, argv):
        return run_cli_json(argv)

    def _resume_preflight(self, request: OperatorActionRequestV2) -> tuple[dict, tuple[str, ...]]:
        omit = frozenset({"atlas_admission_scope", "admission_policy"})
        argv = (
            "train", "--dry-run", "--resume", "--run-dir", str(self.run_dir),
            *parameter_flags(request.parameters, omit=omit),
        )
        return run_cli_json(tuple(argv)), tuple(argv)

    def _create_preflight(self, request: OperatorActionRequestV2) -> tuple[dict, tuple[str, ...]]:
        omit = frozenset({"atlas_admission_scope", "admission_policy"})
        argv = (
            "train", "--dry-run", "--run-dir", str(self.run_dir),
            *parameter_flags(request.parameters, omit=omit),
        )
        return run_cli_json(tuple(argv)), tuple(argv)

    def _validate_admission_scope(
        self, request: OperatorActionRequestV2, target: ResolvedCommandTarget,
    ) -> None:
        parameters = parameter_map(request.parameters)
        scope = parameters.get("atlas_admission_scope")
        if not isinstance(scope, str) or not scope:
            _invalid("CONTROL_PLANE_COMMAND_ADMISSION_SCOPE_REQUIRED")
        from bilqis_mlx.runtime.atlas_admission import read_atlas_enrollment_request_v2
        enrollment = read_atlas_enrollment_request_v2(Path(scope))
        if (enrollment.requested_run_id != target.run_id
                or enrollment.requested_run_seed != target.run_seed
                or enrollment.requested_topology_digest != target.topology_sha256
                or enrollment.source_approval.atlas_release_sha256
                != target.semantic_release_sha256):
            _invalid("CONTROL_PLANE_COMMAND_ADMISSION_TARGET_CONFLICT")

    @staticmethod
    def _action(request: OperatorActionRequestV2) -> CommandAction:
        try:
            action = CommandAction(request.action)
        except ValueError:
            _invalid("CONTROL_PLANE_COMMAND_ACTION_UNSUPPORTED")
        if action is CommandAction.PAUSE:
            _invalid("CONTROL_PLANE_COMMAND_ACTION_UNAVAILABLE")
        return action

    @staticmethod
    def _validate_parameters(action: CommandAction, parameters: dict) -> None:
        admission_keys = {"atlas_admission_scope", "admission_policy"}
        if action is CommandAction.STOP:
            if set(parameters) != {"operation_id"}:
                _invalid("CONTROL_PLANE_COMMAND_STOP_OPERATION_REQUIRED")
            operation_id = parameters["operation_id"]
            if not isinstance(operation_id, str):
                _invalid("CONTROL_PLANE_COMMAND_STOP_OPERATION_REQUIRED")
            operation_directory_name(operation_id)
            return
        if action is CommandAction.ADMISSION_LEASE:
            if set(parameters) - admission_keys:
                _invalid("CONTROL_PLANE_COMMAND_PARAMETER_UNSUPPORTED")
            policy = parameters.get("admission_policy")
            if policy is not None and policy != "atlas-release":
                _invalid("CONTROL_PLANE_COMMAND_ADMISSION_POLICY_INVALID")
            return
        if set(parameters) & admission_keys:
            _invalid("CONTROL_PLANE_COMMAND_ADMISSION_ACTION_REQUIRED")
        if (
            action in {CommandAction.STATUS, CommandAction.CHECKPOINT_VERIFY}
            and parameters
        ):
            _invalid("CONTROL_PLANE_COMMAND_PARAMETER_UNSUPPORTED")

    @staticmethod
    def _runtime_argv(dry_argv: tuple[str, ...], dry_run: bool) -> list[str]:
        actual = list(dry_argv)
        if not dry_run:
            actual.remove("--dry-run")
            actual.append("--human-run")
        return actual

    def _create_parts(self, request: OperatorActionRequestV2):
        report, dry_argv = self._create_preflight(request)
        target = report_target(self.run_dir, report, existing=False)
        mode = CommandMode.DRY_RUN if request.dry_run else CommandMode.MUTATING
        postcondition = (
            "create-preview" if request.dry_run else "accepted-generation")
        return report, target, mode, self._runtime_argv(
            dry_argv, request.dry_run), postcondition

    def _existing_parts(
        self, request: OperatorActionRequestV2, action: CommandAction,
        parameters: dict,
    ):
        if action is CommandAction.STOP:
            return self._stop_parts(parameters)
        report, dry_argv = self._resume_preflight(request)
        target = report_target(self.run_dir, report, existing=True)
        if action is CommandAction.STATUS:
            return report, target, CommandMode.READ_ONLY, [], "operator-status"
        if action is CommandAction.CHECKPOINT_VERIFY:
            return report, target, CommandMode.READ_ONLY, [], "checkpoint-verified"
        if action is CommandAction.ADMISSION_LEASE:
            return self._admission_parts(request, report, target, parameters)
        mode = CommandMode.DRY_RUN if request.dry_run else CommandMode.MUTATING
        postcondition = (
            "resume-preview" if request.dry_run else "operator-run-completed")
        return report, target, mode, self._runtime_argv(
            dry_argv, request.dry_run), postcondition

    def _stop_parts(self, parameters):
        operation_id = parameters["operation_id"]
        target_plan, _process = self._active_trainer_process(operation_id)
        current = self._current_target()
        if current is None or not same_lineage(target_plan.target, current):
            _invalid("CONTROL_PLANE_COMMAND_STOP_TARGET_CONFLICT")
        report = {
            "result": "STOP_READY",
            "ready_for_training": False,
            "neural_updates": False,
        }
        return (
            report,
            current,
            CommandMode.MUTATING,
            [operation_id],
            "operator-stop-requested",
        )

    def _admission_parts(self, request, report, target, parameters):
        if request.dry_run:
            _invalid("CONTROL_PLANE_COMMAND_ADMISSION_DRY_RUN_UNAVAILABLE")
        self._validate_admission_scope(request, target)
        scope = parameters["atlas_admission_scope"]
        actual = [
            "train", "--human-run", "--resume", "--run-dir", str(self.run_dir),
            "--admission-policy", "atlas-release",
            "--atlas-admission-scope", str(scope),
        ]
        return report, target, CommandMode.MUTATING, actual, "admission-lease"

    def _preflight(
        self, request: OperatorActionRequestV2, operation_id: str, *,
        require_authorization: bool,
    ) -> tuple[CommandPlan, dict]:
        action = self._action(request)
        parameters = parameter_map(request.parameters)
        self._validate_parameters(action, parameters)
        if action is CommandAction.CREATE:
            parts = self._create_parts(request)
        else:
            parts = self._existing_parts(request, action, parameters)
        report, target, mode, actual, postcondition = parts
        if require_authorization and mode is CommandMode.MUTATING and not request.human_authorized:
            _invalid("CONTROL_PLANE_COMMAND_HUMAN_AUTHORIZATION_REQUIRED")
        plan = CommandPlan(
            operation_id=operation_id,
            request_sha256=request_sha256(request),
            intent_sha256=intent_sha256(request),
            action=action,
            mode=mode,
            target=target,
            argv=tuple(actual),
            postcondition_kind=postcondition,
        )
        return plan, {
            "kind": "preflight",
            "action": action.value,
            "mode": mode.value,
            "target": target.to_record(),
            "c11_report": report,
        }
    def preview(
        self, request: OperatorActionRequestV2, operation_id: str,
    ) -> tuple[CommandPlan, dict]:
        """Resolve an exact plan without treating preview as human authorization."""
        return self._preflight(
            request, operation_id, require_authorization=False)

    def preflight(
        self, request: OperatorActionRequestV2, operation_id: str,
    ) -> tuple[CommandPlan, dict]:
        return self._preflight(
            request, operation_id, require_authorization=True)
