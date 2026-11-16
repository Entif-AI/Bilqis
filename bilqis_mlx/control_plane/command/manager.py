"""CP05 idempotent command admission, dispatch, and reconciliation."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.mission_control.model import MissionControlContractError
from bilqis_mlx.mission_control.operator import (
    ActionReceiptState, OperatorActionReceiptV2, OperatorActionRequestV2,
)

from .launch import launch_command_worker
from .model import CommandMode, ResolvedCommandTarget, intent_sha256, operation_id_for
from .receipts import (
    build_receipt, command_time_ms, error_ref, error_ref_from_exception,
    minimal_target,
)
from .store import CommandStore
from .status import CommandStatusMixin
from ..transport import _invalid


class CommandManager(CommandStatusMixin):
    """Exactly-once admission decision with at-most-once effect dispatch."""

    def __init__(
        self, run_dir: Path, store_root: Path, *,
        executor=None, launcher=None,
    ):
        self.run_dir = Path(run_dir).expanduser().resolve()
        self.store = CommandStore(store_root)
        if executor is None:
            from .executor import C11CommandExecutor
            executor = C11CommandExecutor(self.run_dir, store=self.store)
        self.executor = executor
        self.launcher = launcher or (
            lambda operation_id: launch_command_worker(
                store_root=self.store.root,
                run_dir=self.run_dir,
                operation_id=operation_id,
            )
        )

    def _rejection(
        self, request: OperatorActionRequestV2, operation_id: str,
        error: Exception | str, *, target: ResolvedCommandTarget | None = None,
    ) -> OperatorActionReceiptV2:
        target = target or minimal_target(self.run_dir)
        ref = (
            error_ref(error)
            if isinstance(error, str)
            else error_ref_from_exception(error)
        )
        return build_receipt(
            request,
            operation_id=operation_id,
            request_sha256=self._request_digest(request),
            state=ActionReceiptState.REJECTED,
            target_ref=target.ref,
            error_ref_value=ref,
        )

    @staticmethod
    def _request_digest(request: OperatorActionRequestV2) -> str:
        from .model import request_sha256
        return request_sha256(request)

    def submit(
        self, request: OperatorActionRequestV2, *,
        expected_target_ref: str | None = None,
    ) -> OperatorActionReceiptV2:
        if type(request) is not OperatorActionRequestV2:
            _invalid("CONTROL_PLANE_COMMAND_REQUEST_INVALID")
        operation_id = operation_id_for(request.idempotency_key)
        semantic = intent_sha256(request)
        with self.store.submission_lock():
            try:
                self.store.bind_request_id(
                    request.request_id, operation_id, semantic)
            except BilqisError as error:
                return self._rejection(request, operation_id, error)
        with self.store.operation_lock(operation_id):
            existing = self.store.read_submission(operation_id)
            if existing is not None:
                return self._retry_locked(
                    request, operation_id, semantic, existing)
            return self._admit_new_locked(
                request, operation_id, semantic, expected_target_ref)

    def _retry_locked(
        self, request, operation_id: str, semantic: str, existing,
    ) -> OperatorActionReceiptV2:
        _accepted_request, _raw_sha, existing_intent = existing
        if existing_intent != semantic:
            return self._rejection(
                request,
                operation_id,
                "CONTROL_PLANE_COMMAND_IDEMPOTENCY_CONFLICT",
                target=self._target_for(operation_id),
            )
        return self._status_locked(operation_id)

    def _admit_new_locked(
        self, request: OperatorActionRequestV2, operation_id: str, semantic: str,
        expected_target_ref: str | None,
    ) -> OperatorActionReceiptV2:
        self.store.write_submission(operation_id, request)
        try:
            plan, preflight = self.executor.preflight(request, operation_id)
        except (BilqisError, MissionControlContractError, OSError) as error:
            return self._persist_preflight_rejection(
                request, operation_id, error)
        if expected_target_ref is not None and plan.target.ref != expected_target_ref:
            return self._persist_preflight_rejection(
                request, operation_id,
                "CONTROL_PLANE_COMMAND_EXPECTED_TARGET_STALE",
                target=plan.target,
            )
        if plan.intent_sha256 != semantic:
            _invalid("CONTROL_PLANE_COMMAND_PLAN_IDENTITY_DRIFT")
        self.store.write_plan(plan)
        self.store.write_preflight(operation_id, preflight)
        accepted = build_receipt(
            request,
            operation_id=operation_id,
            request_sha256=plan.request_sha256,
            state=ActionReceiptState.ACCEPTED,
            target_ref=plan.target.ref,
        )
        self.store.write_accepted(operation_id, accepted)
        if plan.mode is not CommandMode.MUTATING:
            return self._complete_inert_locked(
                request, operation_id, plan, preflight)
        return self._dispatch_locked(
            request, operation_id, plan, accepted)

    def _persist_preflight_rejection(
        self, request, operation_id: str, error: Exception | str, *,
        target: ResolvedCommandTarget | None = None,
    ) -> OperatorActionReceiptV2:
        target = target or minimal_target(self.run_dir)
        self.store.write_preflight(operation_id, {
            "kind": "rejected-preflight",
            "target": target.to_record(),
            "error_ref": (
                error_ref(error) if isinstance(error, str)
                else error_ref_from_exception(error)
            ),
        })
        terminal = self._rejection(
            request, operation_id, error, target=target)
        self.store.write_terminal(operation_id, terminal)
        return terminal

    def _complete_inert_locked(
        self, request, operation_id: str, plan, preflight: dict,
    ) -> OperatorActionReceiptV2:
        try:
            postcondition = self.executor.inert_postcondition(plan, preflight)
            postcondition_ref = self.store.write_postcondition(
                operation_id, postcondition)
        except (BilqisError, MissionControlContractError, OSError) as error:
            terminal = build_receipt(
                request,
                operation_id=operation_id,
                request_sha256=plan.request_sha256,
                state=ActionReceiptState.FAILED,
                target_ref=plan.target.ref,
                error_ref_value=error_ref_from_exception(error),
            )
            self.store.write_terminal(operation_id, terminal)
            return terminal
        terminal = build_receipt(
            request,
            operation_id=operation_id,
            request_sha256=plan.request_sha256,
            state=ActionReceiptState.COMPLETED,
            target_ref=plan.target.ref,
            postcondition_ref=postcondition_ref,
            receipt_refs=(f"command-plan:{plan.digest}", postcondition_ref),
        )
        self.store.write_terminal(operation_id, terminal)
        return terminal

    def _dispatch_locked(
        self, request, operation_id: str, plan,
        accepted: OperatorActionReceiptV2,
    ) -> OperatorActionReceiptV2:
        try:
            self.store.write_dispatch(operation_id, reserved_at=command_time_ms())
        except (BilqisError, OSError):
            return accepted
        try:
            pid = self.launcher(operation_id)
        except OSError as error:
            terminal = build_receipt(
                request,
                operation_id=operation_id,
                request_sha256=plan.request_sha256,
                state=ActionReceiptState.FAILED,
                target_ref=plan.target.ref,
                error_ref_value=error_ref_from_exception(error),
            )
            self.store.write_terminal(operation_id, terminal)
            return terminal
        try:
            self.store.write_spawned(
                operation_id, pid=pid, spawned_at=command_time_ms())
        except (BilqisError, OSError):
            return accepted
        return accepted
