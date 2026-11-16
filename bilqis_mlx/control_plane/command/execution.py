"""Runtime execution and postcondition support for CP05/C11 commands."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import os
from pathlib import Path
import signal

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import inspect_accepted_generation

from .c11 import report_target, same_lineage
from .model import (
    CommandAction, CommandMode, CommandPlan, ResolvedCommandTarget,
)
from .process import process_identity_sha256, run_trainer
from ..transport import _invalid
class C11ExecutionRuntime:
    """Execute admitted C11 plans and verify their authoritative postconditions."""

    run_dir: Path
    store: object | None

    def _run_cli_json(self, argv):
        raise NotImplementedError

    @staticmethod
    def _pid_live(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    @staticmethod
    def _process_identity_sha256(pid: int) -> str | None:
        return process_identity_sha256(pid)

    def _active_trainer_process(self, operation_id: str):
        if self.store is None:
            _invalid("CONTROL_PLANE_COMMAND_STOP_UNAVAILABLE")
        target_plan = self.store.read_plan(operation_id)
        if target_plan is None or target_plan.action not in {
            CommandAction.CREATE, CommandAction.RESUME, CommandAction.OWNER_LAUNCH,
        }:
            _invalid("CONTROL_PLANE_COMMAND_STOP_TARGET_INVALID")
        if (
            self.store.read_terminal(operation_id) is not None
            or self.store.read_worker_result(operation_id) is not None
        ):
            _invalid("CONTROL_PLANE_COMMAND_STOP_TARGET_NOT_ACTIVE")
        process = self.store.read_trainer_process(operation_id)
        if (
            process is None
            or not self._pid_live(process["pid"])
            or self._process_identity_sha256(process["pid"])
            != process["identity_sha256"]
        ):
            _invalid("CONTROL_PLANE_COMMAND_STOP_TARGET_NOT_ACTIVE")
        return target_plan, process

    def inert_postcondition(self, plan: CommandPlan, preflight: dict) -> dict:
        if plan.mode is CommandMode.MUTATING:
            _invalid("CONTROL_PLANE_COMMAND_MUTATION_REQUIRED")
        if plan.action is CommandAction.STATUS:
            from bilqis_mlx.presentation.operator_cli.inspection import _inspect
            return {
                "kind": "operator-status",
                "target": plan.target.to_record(),
                "status": _inspect(self.run_dir),
            }
        if plan.action is CommandAction.CHECKPOINT_VERIFY:
            inspection = inspect_accepted_generation(self.run_dir / "bamf-state.json")
            if inspection is None:
                _invalid("CONTROL_PLANE_COMMAND_CHECKPOINT_UNAVAILABLE")
            return {
                "kind": "checkpoint-verified",
                "target": plan.target.to_record(),
                "inspection": asdict(inspection),
            }
        return preflight

    def execute(self, plan: CommandPlan, *, stdout_path: Path, stderr_path: Path
                ) -> tuple[int | None, str | None]:
        if not plan.requires_worker:
            _invalid("CONTROL_PLANE_COMMAND_WORKER_NOT_REQUIRED")
        if plan.action is CommandAction.STOP:
            try:
                _target_plan, process = self._active_trainer_process(plan.argv[0])
                os.kill(process["pid"], signal.SIGINT)
            except (OSError, BilqisError) as error:
                digest = hashlib.sha256(
                    f"{type(error).__name__}:{error}".encode("utf-8")).hexdigest()
                return None, f"command-error:stop:{digest}"
            return 0, None
        return run_trainer(
            argv=plan.argv,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            store=self.store,
            operation_id=plan.operation_id,
            identity_resolver=self._process_identity_sha256,
        )

    def _current_target(self) -> ResolvedCommandTarget | None:
        try:
            report = self._run_cli_json((
                "train", "--dry-run", "--resume", "--run-dir", str(self.run_dir)))
            return report_target(self.run_dir, report, existing=True)
        except (BilqisError, OSError):
            return None

    def verify_target_before_execute(self, plan: CommandPlan) -> None:
        """Fail closed if authority changed after durable ACCEPTED."""
        if plan.action is CommandAction.STOP:
            target_plan, _process = self._active_trainer_process(plan.argv[0])
            current = self._current_target()
            if (
                current is None
                or current != plan.target
                or not same_lineage(target_plan.target, current)
            ):
                _invalid("CONTROL_PLANE_COMMAND_TARGET_DRIFT")
            return
        if plan.action is CommandAction.CREATE:
            if (self.run_dir / "bamf-state.json").exists():
                _invalid("CONTROL_PLANE_COMMAND_TARGET_DRIFT")
            dry_argv = tuple(
                "--dry-run" if item == "--human-run" else item
                for item in plan.argv
            )
            report = self._run_cli_json(dry_argv)
            current = report_target(self.run_dir, report, existing=False)
        else:
            current = self._current_target()
        if current is None or current != plan.target:
            _invalid("CONTROL_PLANE_COMMAND_TARGET_DRIFT")

    def postcondition_after_success(self, plan: CommandPlan) -> dict:
        current = self._current_target()
        if current is None or not same_lineage(plan.target, current):
            _invalid("CONTROL_PLANE_COMMAND_POSTCONDITION_UNVERIFIED")
        result = {
            "kind": plan.postcondition_kind,
            "before": plan.target.to_record(),
            "after": current.to_record(),
            "cli_exit": 0,
        }
        if plan.action is CommandAction.ADMISSION_LEASE:
            from bilqis_mlx.runtime.atlas_lease_storage import classify_accepted_atlas_epoch
            result["admission_epoch"] = classify_accepted_atlas_epoch(self.run_dir)
            if result["admission_epoch"] == "staged":
                _invalid("CONTROL_PLANE_COMMAND_POSTCONDITION_UNVERIFIED")
        return result

    def postcondition_after_interrupt(self, plan: CommandPlan) -> dict:
        if plan.action not in {
            CommandAction.CREATE, CommandAction.RESUME, CommandAction.OWNER_LAUNCH,
        }:
            _invalid("CONTROL_PLANE_COMMAND_POSTCONDITION_UNVERIFIED")
        current = self._current_target()
        if current is None or not same_lineage(plan.target, current):
            _invalid("CONTROL_PLANE_COMMAND_POSTCONDITION_UNVERIFIED")
        return {
            "kind": "operator-run-interrupted",
            "before": plan.target.to_record(),
            "after": current.to_record(),
            "cli_exit": 130,
        }

    def reconcile(self, plan: CommandPlan) -> dict | None:
        """Read authoritative state only; never relaunch an admitted operation."""
        current = self._current_target()
        if current is None or not same_lineage(plan.target, current):
            return None
        if plan.action is CommandAction.CREATE:
            return {
                "kind": "reconciled-create",
                "before": plan.target.to_record(),
                "after": current.to_record(),
            }
        if plan.action is CommandAction.ADMISSION_LEASE:
            from bilqis_mlx.runtime.atlas_lease_storage import classify_accepted_atlas_epoch
            epoch = classify_accepted_atlas_epoch(self.run_dir)
            if epoch != "staged":
                return {
                    "kind": "reconciled-admission",
                    "before": plan.target.to_record(),
                    "after": current.to_record(),
                    "admission_epoch": epoch,
                }
            return None
        if plan.action in {CommandAction.RESUME, CommandAction.OWNER_LAUNCH} and (
            current.generation is not None
            and plan.target.generation is not None
            and current.optimizer_step is not None
            and plan.target.optimizer_step is not None
            and (
                current.generation > plan.target.generation
                or current.optimizer_step > plan.target.optimizer_step
            )
        ):
            return {
                "kind": "reconciled-progress",
                "before": plan.target.to_record(),
                "after": current.to_record(),
            }
        return None
