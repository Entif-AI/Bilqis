"""CP05 command status and crash-reconciliation behavior."""
from __future__ import annotations

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.mission_control.model import MissionControlContractError
from bilqis_mlx.mission_control.operator import ActionReceiptState, OperatorActionReceiptV2

from .receipts import build_receipt, minimal_target, pid_live
from ..transport import _invalid


class CommandStatusMixin:
    """Read command lifecycle without converting active work into terminal state."""

    def _target_for(self, operation_id: str):
        plan = self.store.read_plan(operation_id)
        return plan.target if plan is not None else minimal_target(self.run_dir)

    def status(self, operation_id: str) -> OperatorActionReceiptV2:
        with self.store.operation_lock(operation_id):
            return self._status_locked(operation_id)

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
        worker_live = (
            worker_result is None
            and spawned is not None
            and pid_live(spawned["pid"])
        )
        trainer_recorded = (
            worker_result is None
            and self.store.read_trainer_process(operation_id) is not None
        )
        if worker_live or trainer_recorded:
            state = (
                ActionReceiptState.PENDING
                if worker_live else ActionReceiptState.OUTCOME_UNKNOWN
            )
            return build_receipt(
                request,
                operation_id=operation_id,
                request_sha256=request_digest,
                state=state,
                target_ref=plan.target.ref,
            )

        try:
            reconciled = self.executor.reconcile(plan)
        except (BilqisError, MissionControlContractError, OSError):
            reconciled = None
        if reconciled is None:
            return build_receipt(
                request,
                operation_id=operation_id,
                request_sha256=request_digest,
                state=ActionReceiptState.OUTCOME_UNKNOWN,
                target_ref=plan.target.ref,
            )

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
