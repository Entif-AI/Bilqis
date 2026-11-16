"""Read-only CP05 projections for the GUI17 operator boundary."""
from __future__ import annotations

from bilqis_mlx.mission_control.codec import encode_record
from bilqis_mlx.mission_control.operator import OperatorActionRequestV2

from .model import (
    CommandMode, ResolvedCommandTarget, operation_directory_name, operation_id_for,
)
from ..transport import _invalid


COMMAND_PREVIEW_SCHEMA = "bilqis.bamf.control-plane.command-preview/v1"
COMMAND_INSPECTION_SCHEMA = "bilqis.bamf.control-plane.command-inspection/v1"
PUBLIC_TARGET_SCHEMA = "bilqis.bamf.control-plane.command-target-public/v1"
LOG_TAIL_BYTES = 4096


def _public_target(target: ResolvedCommandTarget) -> dict:
    """Project exact target identity without exposing the private run-directory path."""
    if type(target) is not ResolvedCommandTarget:
        _invalid("CONTROL_PLANE_COMMAND_TARGET_INVALID")
    return {
        "schema": PUBLIC_TARGET_SCHEMA,
        "target_ref": target.ref,
        "run_id": target.run_id,
        "run_seed": target.run_seed,
        "run_identity_sha256": target.run_identity_sha256,
        "generation": target.generation,
        "generation_manifest_sha256": target.generation_manifest_sha256,
        "optimizer_step": target.optimizer_step,
        "candidate_identity_sha256": target.candidate_identity_sha256,
        "factory_release_sha256": target.factory_release_sha256,
        "semantic_release_sha256": target.semantic_release_sha256,
        "topology_sha256": target.topology_sha256,
        "acceptance_sha256": target.acceptance_sha256,
        "source_identity": target.source_identity,
    }


def _target_from_value(value) -> ResolvedCommandTarget | None:
    if not isinstance(value, dict):
        return None
    try:
        return ResolvedCommandTarget.from_record(value)
    except Exception:
        return None


def _resource_profile(request: OperatorActionRequestV2, preflight: dict) -> dict:
    parameters = {parameter.key: parameter.value for parameter in request.parameters}
    report = preflight.get("c11_report")
    report = report if isinstance(report, dict) else {}
    return {
        "source_prefetch_workers": report.get("source_prefetch_workers"),
        "batch_size": parameters.get("batch_size"),
        "reserve_gib": parameters.get("reserve_gib"),
        "minutes": parameters.get("minutes"),
        "steps_per_visit": parameters.get("steps_per_visit"),
        "max_visits": parameters.get("max_visits"),
    }


def _public_preflight(request: OperatorActionRequestV2, preflight: dict) -> dict:
    report = preflight.get("c11_report")
    report = report if isinstance(report, dict) else {}
    optimizer = report.get("optimizer_hyperparameters")
    return {
        "kind": preflight.get("kind"),
        "result": report.get("result"),
        "admission_policy": report.get("admission_policy"),
        "optimizer_hyperparameters": optimizer if isinstance(optimizer, dict) else None,
        "source_prefetch_workers": report.get("source_prefetch_workers"),
        "generation_manifest_sha256": report.get("generation_manifest_sha256"),
        "ready_for_training": report.get("ready_for_training"),
        "neural_updates": report.get("neural_updates"),
        "resource_profile": _resource_profile(request, preflight),
    }


def _public_inspection_fields(value: dict) -> dict:
    allowed = (
        "generation", "generation_manifest_sha256", "optimizer_step",
        "candidate_identity_sha256", "factory_release_sha256",
        "semantic_release_sha256", "topology_sha256", "acceptance_sha256",
    )
    return {key: value.get(key) for key in allowed}


def _public_postcondition(value: dict | None) -> dict | None:
    if not isinstance(value, dict):
        return None
    result = {"kind": value.get("kind")}
    for key in ("before", "after", "target"):
        target = _target_from_value(value.get(key))
        if target is not None:
            result[key] = _public_target(target)
    inspection = value.get("inspection")
    if isinstance(inspection, dict):
        result["inspection"] = _public_inspection_fields(inspection)
    for key in ("admission_epoch", "cli_exit"):
        if key in value:
            result[key] = value.get(key)
    return result


def _log_tail(path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    data = path.read_bytes()
    tail = data[-LOG_TAIL_BYTES:]
    return tail.decode("utf-8", errors="replace")


def _public_logs(manager, operation_id: str) -> dict:
    return {
        "stdout_tail": _log_tail(manager.store.stdout_path(operation_id)),
        "stderr_tail": _log_tail(manager.store.stderr_path(operation_id)),
    }


def _consequence(mode: CommandMode | None) -> dict:
    mutating = mode is CommandMode.MUTATING
    return {
        "mutation": "MUTATING" if mutating else "NONE",
        "neural_mutation_permitted": mutating,
    }


def _projection(
    *, schema: str, request: OperatorActionRequestV2, plan, preflight: dict,
    receipt=None, postcondition: dict | None = None, logs: dict | None = None,
) -> dict:
    target = plan.target if plan is not None else _target_from_value(preflight.get("target"))
    mode = plan.mode if plan is not None else None
    target_public = _public_target(target) if target is not None else None
    return {
        "schema": schema,
        "operation_id": (
            plan.operation_id if plan is not None else operation_id_for(request.idempotency_key)
        ),
        "request": encode_record(request),
        "action": request.action,
        "mode": None if mode is None else mode.value,
        "target": target_public,
        "target_ref": None if target_public is None else target_public["target_ref"],
        "expected_postcondition": None if plan is None else plan.postcondition_kind,
        "consequence": _consequence(mode),
        "preflight": _public_preflight(request, preflight),
        "receipt": None if receipt is None else encode_record(receipt),
        "postcondition": _public_postcondition(postcondition),
        "logs": logs,
    }


def preview_command(manager, request: OperatorActionRequestV2) -> dict:
    """Resolve the exact CP05 plan without admitting, persisting, or dispatching it."""
    if type(request) is not OperatorActionRequestV2:
        _invalid("CONTROL_PLANE_COMMAND_REQUEST_INVALID")
    operation_id = operation_id_for(request.idempotency_key)
    executor = manager.executor
    preview = getattr(executor, "preview", None)
    if not callable(preview):
        _invalid("CONTROL_PLANE_COMMAND_PREVIEW_UNAVAILABLE")
    plan, preflight = preview(request, operation_id)
    return _projection(
        schema=COMMAND_PREVIEW_SCHEMA,
        request=request,
        plan=plan,
        preflight=preflight,
        logs=None,
    )


def inspect_command(manager, operation_id: str) -> dict:
    """Read/reconcile one durable operation and expose only bounded public facts."""
    operation_directory_name(operation_id)
    receipt = manager.status(operation_id)
    submission = manager.store.read_submission(operation_id)
    if submission is None:
        _invalid("CONTROL_PLANE_COMMAND_OPERATION_UNKNOWN")
    request, _request_digest, _intent = submission
    plan = manager.store.read_plan(operation_id)
    preflight = manager.store.read_preflight(operation_id) or {}
    postcondition = manager.store.read_postcondition(operation_id)
    return _projection(
        schema=COMMAND_INSPECTION_SCHEMA,
        request=request,
        plan=plan,
        preflight=preflight,
        receipt=receipt,
        postcondition=postcondition,
        logs=_public_logs(manager, operation_id),
    )
