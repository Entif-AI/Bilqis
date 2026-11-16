"""Detached one-shot CP05 worker; C11 remains the actual BAMF action owner."""
from __future__ import annotations

import argparse
from pathlib import Path
import time

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.mission_control.model import MissionControlContractError
from bilqis_mlx.mission_control.operator import ActionReceiptState

from .executor import C11CommandExecutor
from .store import CommandStore
from .receipts import build_receipt, error_ref_from_exception
from ..transport import _invalid


INTERRUPTED_RETURN_CODE = 130


def _now() -> int:
    return int(time.time() * 1000)


def _complete_from_postcondition(
    store: CommandStore, operation_id: str, request, plan, postcondition: dict,
) -> None:
    postcondition_ref = store.write_postcondition(operation_id, postcondition)
    terminal = build_receipt(
        request,
        operation_id=operation_id,
        request_sha256=plan.request_sha256,
        state=ActionReceiptState.COMPLETED,
        target_ref=plan.target.ref,
        postcondition_ref=postcondition_ref,
        receipt_refs=(
            f"command-plan:{plan.digest}",
            postcondition_ref,
        ),
    )
    store.write_terminal(operation_id, terminal)


def _prepare_worker(store, executor, operation_id):
    with store.operation_lock(operation_id):
        if store.read_terminal(operation_id) is not None:
            return 0
        if store.read_worker_result(operation_id) is not None:
            return 0
        submission = store.read_submission(operation_id)
        accepted = store.read_accepted(operation_id)
        plan = store.read_plan(operation_id)
        dispatch = store.read_dispatch(operation_id)
        if (
            submission is None
            or accepted is None
            or plan is None
            or dispatch is None
        ):
            _invalid("CONTROL_PLANE_COMMAND_WORKER_FACTS_MISSING")
        request, request_digest, semantic_digest = submission
        if (
            plan.request_sha256 != request_digest
            or plan.intent_sha256 != semantic_digest
            or accepted.request_sha256 != request_digest
            or accepted.target_ref != plan.target.ref
        ):
            _invalid("CONTROL_PLANE_COMMAND_WORKER_IDENTITY_DRIFT")
        try:
            executor.verify_target_before_execute(plan)
        except (BilqisError, MissionControlContractError, OSError) as error:
            failure = build_receipt(
                request,
                operation_id=operation_id,
                request_sha256=request_digest,
                state=ActionReceiptState.FAILED,
                target_ref=plan.target.ref,
                error_ref_value=error_ref_from_exception(error),
            )
            store.write_terminal(operation_id, failure)
            store.write_worker_result(
                operation_id,
                returncode=None,
                error_ref=failure.error_ref,
                finished_at=_now(),
            )
            return 1
    return request, request_digest, plan


def _readback_after_execution(executor, plan, returncode, execution_error):
    postcondition = None
    if returncode == 0:
        try:
            postcondition = executor.postcondition_after_success(plan)
        except (BilqisError, MissionControlContractError, OSError) as error:
            execution_error = error_ref_from_exception(error)
    elif returncode == INTERRUPTED_RETURN_CODE:
        try:
            postcondition = executor.postcondition_after_interrupt(plan)
        except (BilqisError, MissionControlContractError, OSError) as error:
            if execution_error is None:
                execution_error = error_ref_from_exception(error)
    else:
        try:
            postcondition = executor.reconcile(plan)
        except (BilqisError, MissionControlContractError, OSError) as error:
            if execution_error is None:
                execution_error = error_ref_from_exception(error)
    return postcondition, execution_error


def _finalize_worker(
    store, operation_id, request, request_digest, plan,
    returncode, execution_error, postcondition,
) -> int:
    with store.operation_lock(operation_id):
        if store.read_terminal(operation_id) is not None:
            return 0
        if postcondition is not None:
            _complete_from_postcondition(
                store, operation_id, request, plan, postcondition)
        elif returncode is None:
            failure = build_receipt(
                request,
                operation_id=operation_id,
                request_sha256=request_digest,
                state=ActionReceiptState.FAILED,
                target_ref=plan.target.ref,
                error_ref_value=execution_error
                or error_ref_from_exception(
                    RuntimeError("COMMAND_WORKER_SPAWN_FAILED")),
            )
            store.write_terminal(operation_id, failure)
        store.write_worker_result(
            operation_id,
            returncode=returncode,
            error_ref=execution_error,
            finished_at=_now(),
        )
    return 0 if postcondition is not None else 2


def run_worker(
    *, store_root: Path, run_dir: Path, operation_id: str,
    executor=None,
) -> int:
    store = CommandStore(store_root)
    executor = executor or C11CommandExecutor(run_dir, store=store)
    with store.execution_lock(operation_id):
        prepared = _prepare_worker(store, executor, operation_id)
        if isinstance(prepared, int):
            return prepared
        request, request_digest, plan = prepared
        returncode, execution_error = executor.execute(
            plan,
            stdout_path=store.stdout_path(operation_id),
            stderr_path=store.stderr_path(operation_id),
        )
        postcondition, execution_error = _readback_after_execution(
            executor, plan, returncode, execution_error)
        return _finalize_worker(
            store,
            operation_id,
            request,
            request_digest,
            plan,
            returncode,
            execution_error,
            postcondition,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one already-admitted CP05 operation.")
    parser.add_argument("--store-root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--operation-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return run_worker(
        store_root=args.store_root,
        run_dir=args.run_dir,
        operation_id=args.operation_id,
    )


if __name__ == "__main__":
    raise SystemExit(main())
