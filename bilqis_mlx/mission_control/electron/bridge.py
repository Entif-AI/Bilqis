"""Private stdio broker exposing accepted CP01 state to Electron main only."""
from __future__ import annotations

from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
from threading import Thread

from bilqis_mlx.control_plane import ControlPlaneClient, ControlPlaneService
from bilqis_mlx.control_plane.active_endpoint import (
    advertise_active_endpoint, default_socket_path, discover_active_endpoint,
)
from bilqis_mlx.control_plane.contracts import ControlPlaneState, PROTOCOL_VERSION
from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL
from bilqis_mlx.mission_control.contracts.codec import decode_record, encode_record
from bilqis_mlx.mission_control.contracts.operator import OperatorActionRequestV2
from bilqis_mlx.paths import active_run_dir


_CLIENT_ID = "mission-control-electron"
_REQUEST_TIMEOUT_SECONDS = 8.0
MAX_BROKER_REQUEST_BYTES = 64 * 1024
QUERY_ERROR_SCHEMA = "bamf.gui07.query-error/v1"


def _safe_broker_error_code(error: BaseException) -> str:
    if isinstance(error, BilqisError):
        return "BAMF_GUI20_CP01_CONTRACT_INVALID"
    if isinstance(error, PermissionError):
        return "BAMF_GUI20_CP01_UNAUTHORIZED"
    if isinstance(error, TimeoutError):
        return "BAMF_GUI20_CP01_TIMEOUT"
    if isinstance(error, (ConnectionError, OSError)):
        return "BAMF_GUI20_CP01_TRANSPORT_UNAVAILABLE"
    if isinstance(error, (TypeError, ValueError, KeyError)):
        return "BAMF_GUI20_CP01_CONTRACT_INVALID"
    return "BAMF_GUI20_CP01_UNAVAILABLE"


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID, reason=reason)


def _socket_path() -> Path:
    return _control_plane_target()[1]


def _control_plane_target() -> tuple[Path, Path]:
    configured = os.environ.get("BILQIS_CONTROL_PLANE_SOCKET", "").strip()
    configured_run = os.environ.get("RUN_DIR", "").strip()
    run_dir = (Path(configured_run).expanduser().resolve()
               if configured_run else None)
    if configured:
        return (run_dir or active_run_dir().expanduser().resolve(),
                Path(configured).expanduser().resolve())
    if run_dir is not None:
        return run_dir, default_socket_path(run_dir)
    discovered = discover_active_endpoint()
    if discovered is not None:
        return (Path(discovered.run_dir).expanduser().resolve(),
                Path(discovered.socket_path).expanduser().resolve())
    run_dir = active_run_dir().expanduser().resolve()
    return run_dir, default_socket_path(run_dir)


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
        self._local_service: ControlPlaneService | None = None
        self._local_service_thread: Thread | None = None
        self._local_service_stack: ExitStack | None = None
        self._local_service_target: tuple[Path, Path] | None = None

    def _close_client(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    def _stop_local_service(self) -> None:
        service, thread = self._local_service, self._local_service_thread
        stack = self._local_service_stack
        self._local_service = None
        self._local_service_thread = None
        self._local_service_stack = None
        self._local_service_target = None
        if service is not None:
            service.shutdown()
        if thread is not None:
            thread.join(2.0)
        if stack is not None:
            stack.close()

    def _ensure_local_service(self, run_dir: Path, socket_path: Path) -> None:
        target = (run_dir, socket_path)
        if self._local_service is not None and self._local_service_target == target:
            return
        self._stop_local_service()
        from bilqis_mlx.control_plane.native_source import native_query_source
        service = ControlPlaneService(
            run_dir, socket_path,
            query_source=native_query_source(run_dir))
        stack = ExitStack()
        try:
            stack.enter_context(advertise_active_endpoint(
                run_dir, socket_path=socket_path, role="service"))
            thread = Thread(
                target=service.serve_forever,
                name="bilqis-mission-control-cp01", daemon=True)
            thread.start()
        except Exception:
            stack.close()
            service.server_close()
            raise
        self._local_service = service
        self._local_service_thread = thread
        self._local_service_stack = stack
        self._local_service_target = target

    def connect(self) -> dict:
        self._close_client()
        run_dir, socket_path = _control_plane_target()
        if (self._local_service is not None
                and self._local_service_target != (run_dir, socket_path)):
            self._stop_local_service()
        client = ControlPlaneClient(
            socket_path, client_id=_CLIENT_ID,
            timeout=_REQUEST_TIMEOUT_SECONDS)
        try:
            payload = client.connect()
        except PermissionError:
            state = client.state
            client.close(preserve_state=True)
            if state is ControlPlaneState.CONNECTING:
                state = ControlPlaneState.DISCONNECTED
            return _public_status({"state": state.value}, connected=False)
        except Exception:
            client.close(preserve_state=True)
            try:
                self._ensure_local_service(run_dir, socket_path)
                client = ControlPlaneClient(
                    socket_path, client_id=_CLIENT_ID,
                    timeout=_REQUEST_TIMEOUT_SECONDS)
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
        try:
            response = self.client.query(request)
        except OSError:
            # A timed-out socket-backed file object is not safely reusable.
            # Drop it so the next bootstrap retry starts from a fresh CP01
            # handshake instead of repeatedly querying a poisoned session.
            self._close_client()
            raise
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
        self._close_client()
        return _public_status({}, connected=False)

    def close(self) -> None:
        self._close_client()
        self._stop_local_service()


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
        except Exception as error:
            _reply(request.get("id") if isinstance(request, dict) else None,
                   error=_safe_broker_error_code(error))
            continue
        _reply(identifier, result=result)
    bridge.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(stream_events() if "--events" in sys.argv[1:] else main())
