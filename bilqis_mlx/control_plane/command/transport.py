"""Read-only preview/inspection helpers for CP05 transport surfaces."""
from __future__ import annotations

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.mission_control.codec import decode_record
from bilqis_mlx.mission_control.model import MissionControlContractError, is_name
from bilqis_mlx.mission_control.operator import OperatorActionRequestV2

from .inspection import inspect_command, preview_command


def _error(service, session, error: Exception) -> dict:
    if isinstance(error, BilqisError):
        reason = error.context.get("reason") or error.code
    elif isinstance(error, MissionControlContractError):
        reason = "CONTROL_PLANE_COMMAND_CONTRACT_INVALID"
    else:
        reason = "CONTROL_PLANE_COMMAND_CONTRACT_INVALID"
    return service.rejected_request(session, str(reason))


def serve_command_preview(service, session, request: dict) -> dict:
    payload = request.get("request")
    if not isinstance(payload, dict):
        return service.rejected_request(
            session, "CONTROL_PLANE_COMMAND_REQUEST_INVALID")
    try:
        action = decode_record(payload)
        if type(action) is not OperatorActionRequestV2:
            return service.rejected_request(
                session, "CONTROL_PLANE_COMMAND_REQUEST_VERSION_REQUIRED")
        return preview_command(service._command_manager(), action)
    except (BilqisError, MissionControlContractError, OSError) as error:
        return _error(service, session, error)


def serve_command_inspection(service, session, request: dict) -> dict:
    operation_id = request.get("operation_id")
    if not is_name(operation_id):
        return service.rejected_request(
            session, "CONTROL_PLANE_COMMAND_OPERATION_REQUIRED")
    try:
        return inspect_command(service._command_manager(), operation_id)
    except (BilqisError, MissionControlContractError, OSError) as error:
        return _error(service, session, error)
