"""CP05 command status and crash-reconciliation behavior."""
from __future__ import annotations

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.mission_control.model import MissionControlContractError
from bilqis_mlx.mission_control.operator import ActionReceiptState, OperatorActionReceiptV2

from .receipts import build_receipt, error_ref, minimal_target, pid_live
from ..transport import _invalid


class CommandStatusMixin:
    """Read command lifecycle without converting active work into terminal state."""

    def _target_for(self, operation_id: str):
        plan = self.store.read_plan(operation_id)
        return plan.target if plan is not None else minimal_target(self.run_dir)

    def status(self, operation_id: str) -> OperatorActionReceiptV2:
        with self.store.operation_lock(operation_id):
            return self._status_locked(operation_id)

    def _active_operation_receipt(
            self, operation_id, request, request_digest, plan, worker_result, spawned):
        worker_live = (
            worker_result is None
            and spawned is not None
            and pid_live(spawned["pid"])
        )
        trainer_state = "inactive"
        if (
            worker_result is None
            and self.store.read_trainer_process(operation_id) is not None
        ):
            trainer_state = self.executor.trainer_process_state(operation_id)
        if not worker_live and trainer_state == "inactive":
            return None
        state = (
            ActionReceiptState.PENDING
            if worker_live and trainer_state != "unknown"
            else ActionReceiptState.OUTCOME_UNKNOWN
        )
        return build_receipt(
            request,
            operation_id=operation_id,
            request_sha256=request_digest,
            state=state,
            target_ref=plan.target.ref,
        )

    def _completed_reconciliation(self, operation_id, request, request_digest, plan):
        try:
            reconciled = self.executor.reconcile(plan)
        except (BilqisError, MissionControlContractError, OSError):
            return None
        if reconciled is None:
            return None
        postcondition_ref = self.store.write_postcondition(operation_id, reconciled)
        terminal = build_receipt(
            request,
            operation_id=operation_id,
            request_sha256=request_digest,
            state=ActionReceiptState.COMPLETED,
            target_ref=plan.target.ref,
            postcondition_ref=postcondition_ref,
            receipt_refs=(f"command-plan:{plan.digest}", postcondition_ref),
        )
        self.store.write_terminal(operation_id, terminal)
        return terminal

    def _failed_before_effect_reconciliation(
            self, operation_id, request, request_digest, plan, worker_result):
        try:
            no_effect = self.executor.reconcile_no_effect(plan, worker_result)
        except (BilqisError, MissionControlContractError, OSError):
            return None
        if no_effect is None:
            return None
        reconciliation_ref = self.store.write_reconciliation(operation_id, no_effect)
        terminal = build_receipt(
            request,
            operation_id=operation_id,
            request_sha256=request_digest,
            state=ActionReceiptState.FAILED_BEFORE_EFFECT,
            target_ref=plan.target.ref,
            error_ref_value=error_ref("CONTROL_PLANE_COMMAND_FAILED_BEFORE_EFFECT"),
            receipt_refs=(f"command-plan:{plan.digest}", reconciliation_ref),
        )
        self.store.write_terminal(operation_id, terminal)
        return terminal

    def _status_locked(self, operation_id: str) -> OperatorActionReceiptV2:
        terminal = self.store.read_terminal(operation_id)
        if terminal is not None:
            return terminal
        submission = self.store.read_submission(operation_id)
        accepted = self.store.read_accepted(operation_id)
        plan = self.store.read_plan(operation_id)
        if submission is None or accepted is None or plan is None:
            _invalid("CONTROL_PLANE_COMMAND_OPERATION_UNKNOWN")
        request, request_digest, _semantic = submission
        if self.store.read_dispatch(operation_id) is None:
            return accepted

        worker_result = self.store.read_worker_result(operation_id)
        spawned = self.store.read_spawned(operation_id)
        active = self._active_operation_receipt(
            operation_id, request, request_digest, plan, worker_result, spawned)
        if active is not None:
            return active

        completed = self._completed_reconciliation(
            operation_id, request, request_digest, plan)
        if completed is not None:
            return completed

        failed = self._failed_before_effect_reconciliation(
            operation_id, request, request_digest, plan, worker_result)
        if failed is not None:
            return failed

        return build_receipt(
            request,
            operation_id=operation_id,
            request_sha256=request_digest,
            state=ActionReceiptState.OUTCOME_UNKNOWN,
            target_ref=plan.target.ref,
        )
