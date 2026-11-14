"""Private stdio broker exposing accepted CP01 state to Electron main only."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from bilqis_mlx.control_plane import ControlPlaneClient
from bilqis_mlx.control_plane.contracts import ControlPlaneState, PROTOCOL_VERSION
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.mission_control.contracts.codec import decode_record, encode_record
from bilqis_mlx.mission_control.contracts.operator import OperatorActionRequestV2
from bilqis_mlx.paths import active_run_dir


_CLIENT_ID = "mission-control-electron"
MAX_BROKER_REQUEST_BYTES = 64 * 1024
QUERY_ERROR_SCHEMA = "bamf.gui07.query-error/v1"


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID, reason=reason)


def _socket_path() -> Path:
    configured = os.environ.get("BILQIS_CONTROL_PLANE_SOCKET", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    run_dir = active_run_dir().expanduser().resolve()
    return run_dir.parent / f".{run_dir.name}.control-plane.sock"


def _public_status(payload: dict, *, connected: bool) -> dict:
    learner = payload.get("learner") if isinstance(payload.get("learner"), dict) else {}
    return {
        "schemaVersion": "bamf.gui20.cp01-status/v1",
        "state": payload.get("state", "disconnected"),
        "protocolVersion": payload.get("protocol_version", PROTOCOL_VERSION),
        "serviceLive": bool(payload.get("service_live", connected)),
        "serviceReady": bool(payload.get("service_ready", connected)),
        "learnerReady": bool(payload.get("learner_ready", learner.get("state") == "healthy")),
        "learnerActive": learner.get("operator_active"),
        "learnerState": learner.get("state"),
        "runId": learner.get("run_id"),
        "generation": learner.get("generation"),
        "optimizerStep": learner.get("optimizer_step"),
        "failureCode": learner.get("failure_code"),
    }


class ElectronBridge:
    def __init__(self) -> None:
        self.client: ControlPlaneClient | None = None

    def connect(self) -> dict:
        self.disconnect()
        client = ControlPlaneClient(_socket_path(), client_id=_CLIENT_ID)
        try:
            payload = client.connect()
        except Exception:
            state = client.state
            client.close(preserve_state=True)
            if state is ControlPlaneState.CONNECTING:
                state = ControlPlaneState.DISCONNECTED
            return _public_status({"state": state.value}, connected=False)
        if not payload.get("accepted"):
            client.close(preserve_state=True)
            return _public_status(payload, connected=False)
        self.client = client
        return _public_status(payload, connected=True)

    def query(self, payload: dict) -> dict:
        from ..query_contracts import QueryRequest
        from ..contracts.codec import decode_record
        from ..query_support import encode_query_page, matches_identity
        from ..query_contracts import QueryPage, QueryState
        from ..contracts.model import CoverageState
        from ..query_contracts import QueryLink
        if self.client is None:
            return {"schema": QUERY_ERROR_SCHEMA, "accepted": False, "reason": "CONTROL_PLANE_NOT_CONNECTED"}
        request = QueryRequest.from_mapping(payload)
        response = self.client.query(request)
        if response.get("accepted") is not True:
            return {"schema": QUERY_ERROR_SCHEMA, "accepted": False,
                    "reason": response.get("reason") or "CONTROL_PLANE_QUERY_UNAVAILABLE"}
        # Reconstruct the public page from typed records; transport sessions stay private.
        page = QueryPage(
            request, QueryState(response["state"]), CoverageState(response["coverage"]),
            response["total_matches"],
            tuple(decode_record(row) for row in response["records"]),
            tuple(decode_record(row) for row in response["markers"]),
            tuple(QueryLink(**row) for row in response["links"]), response["next_cursor"],
        )
        if not all(matches_identity(row, request) for row in page.records):
            ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID, reason="CONTROL_PLANE_QUERY_IDENTITY_MISMATCH")
        expected = encode_query_page(page)
        if any(response.get(key) != value for key, value in expected.items()):
            ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID, reason="CONTROL_PLANE_QUERY_IDENTITY_MISMATCH")
        return {**expected, "accepted": True}

    def status(self) -> dict:
        if self.client is None:
            return _public_status({}, connected=False)
        return _public_status(self.client.request("health"), connected=True)

    def command_preview(self, payload: dict) -> dict:
        if self.client is None:
            _invalid("CONTROL_PLANE_NOT_CONNECTED")
        request = decode_record(payload)
        if type(request) is not OperatorActionRequestV2:
            _invalid("CONTROL_PLANE_COMMAND_REQUEST_VERSION_REQUIRED")
        return self.client.preview_command(request)

    def command_submit(self, payload: dict) -> dict:
        if self.client is None:
            _invalid("CONTROL_PLANE_NOT_CONNECTED")
        if not isinstance(payload, dict):
            _invalid("CONTROL_PLANE_COMMAND_REQUEST_INVALID")
        request = decode_record(payload.get("request", {}))
        if type(request) is not OperatorActionRequestV2:
            _invalid("CONTROL_PLANE_COMMAND_REQUEST_VERSION_REQUIRED")
        expected = payload.get("expected_target_ref")
        if not isinstance(expected, str) or not expected:
            _invalid("CONTROL_PLANE_COMMAND_EXPECTED_TARGET_REQUIRED")
        return encode_record(self.client.submit_command(
            request, expected_target_ref=expected))

    def command_inspect(self, operation_id: str) -> dict:
        if self.client is None:
            _invalid("CONTROL_PLANE_NOT_CONNECTED")
        return self.client.inspect_command(operation_id)

    def disconnect(self) -> dict:
        if self.client is not None:
            self.client.close()
            self.client = None
        return _public_status({}, connected=False)


def _reply(identifier, *, result=None, error=None) -> None:
    payload = {"id": identifier, "ok": error is None}
    if error is None:
        payload["result"] = result
    else:
        payload["error"] = error
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def stream_events() -> int:
    client = ControlPlaneClient(_socket_path(), client_id=f"{_CLIENT_ID}-events")
    try:
        payload = client.connect()
        if not payload.get("accepted"):
            return 1
        subscription = client.subscribe_events()
        for event in subscription:
            sys.stdout.write(json.dumps(
                encode_record(event), sort_keys=True, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    except Exception:
        return 1
    finally:
        client.close()
    return 0


def main() -> int:
    bridge = ElectronBridge()
    for raw in sys.stdin:
        request = None
        if len(raw) > MAX_BROKER_REQUEST_BYTES:
            _reply(None, error="BAMF_GUI20_BROKER_REQUEST_INVALID")
            continue
        try:
            request = json.loads(raw)
            identifier = request["id"]
            operation = request["op"]
            if type(identifier) is not int or operation not in {
                    "connect", "status", "disconnect", "query",
                    "command-preview", "command-submit", "command-inspect"}:
                raise ValueError
            if operation == "query":
                result = bridge.query(request.get("query"))
            elif operation == "command-preview":
                result = bridge.command_preview(request.get("query"))
            elif operation == "command-submit":
                result = bridge.command_submit(request.get("query"))
            elif operation == "command-inspect":
                result = bridge.command_inspect(request.get("query"))
            else:
                result = getattr(bridge, operation)()
        except Exception:
            _reply(request.get("id") if isinstance(request, dict) else None,
                   error="BAMF_GUI20_CP01_UNAVAILABLE")
            continue
        _reply(identifier, result=result)
    bridge.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(stream_events() if "--events" in sys.argv[1:] else main())
