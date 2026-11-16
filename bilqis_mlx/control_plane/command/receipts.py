"""Shared CP05 receipt and lifecycle helpers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.mission_control.model import AuthorityClass, CoverageState, RecordMeta
from bilqis_mlx.mission_control.operator import (
    ActionReceiptState, OperatorActionReceiptV2, OperatorActionRequestV2,
)

from .model import ResolvedCommandTarget


def command_time_ms() -> int:
    return int(time.time() * 1000)


def error_ref(code: str, detail: object = None) -> str:
    raw = json.dumps(
        {"code": code, "detail": detail},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return "command-error:" + hashlib.sha256(raw).hexdigest()


def error_ref_from_exception(error: Exception) -> str:
    if isinstance(error, BilqisError):
        return error_ref(error.code, dict(error.context))
    return error_ref(type(error).__name__, str(error))


def minimal_target(run_dir: Path) -> ResolvedCommandTarget:
    return ResolvedCommandTarget(
        run_dir=str(Path(run_dir).expanduser().resolve()),
        run_id=None,
        run_seed=None,
        run_identity_sha256=None,
        generation=None,
        generation_manifest_sha256=None,
        optimizer_step=None,
        candidate_identity_sha256=None,
        factory_release_sha256=None,
        semantic_release_sha256=None,
        topology_sha256=None,
        acceptance_sha256=None,
        source_identity=None,
    )


def build_receipt(
    request: OperatorActionRequestV2, *, operation_id: str,
    request_sha256: str, state: ActionReceiptState,
    target_ref: str, postcondition_ref: str | None = None,
    error_ref_value: str | None = None, receipt_refs: tuple[str, ...] = (),
) -> OperatorActionReceiptV2:
    timestamp = command_time_ms()
    meta = RecordMeta(
        record_id=f"cp05:{operation_id}:{state.value.lower()}",
        run=None,
        materialized_at=timestamp,
        observed_at=timestamp,
        as_of=timestamp,
        coverage=CoverageState.COMPLETE,
        authority=AuthorityClass.DERIVED,
        source_refs=("authority:c11-bamf-operator",),
        evidence_refs=(target_ref,),
        receipt_refs=receipt_refs,
    )
    return OperatorActionReceiptV2(
        meta=meta,
        request_id=request.request_id,
        request_sha256=request_sha256,
        operation_id=operation_id,
        state=state,
        acknowledged_at=timestamp,
        target_ref=target_ref,
        postcondition_ref=postcondition_ref,
        error_ref=error_ref_value,
    )


def pid_live(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
