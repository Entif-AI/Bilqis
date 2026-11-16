"""Small CP01 Unix-socket client used by CLI/Electron-equivalent fixtures."""
from __future__ import annotations

import json
from pathlib import Path
import socket

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.mission_control.codec import decode_record
from bilqis_mlx.mission_control.envelopes import EventEnvelope
from bilqis_mlx.mission_control.operator import (
    OperatorActionReceiptV2, OperatorActionRequestV2,
)
from bilqis_mlx.mission_control.query_contracts import (
    QUERY_PAGE_SCHEMA, QueryRequest,
)

from .contracts import (
    ControlPlaneState, ERROR_SCHEMA, HANDSHAKE_SCHEMA, HEALTH_SCHEMA, PROTOCOL_VERSION,
    SERVICE_IDENTITY_SCHEMA, SESSION_IDENTITY_SCHEMA,
)
from .event_stream import (
    EVENT_GAP_SCHEMA, EVENT_HEARTBEAT_SCHEMA, EVENT_SUBSCRIPTION_SCHEMA,
)


MAX_RESPONSE_BYTES = 64 * 1024


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID, reason=reason)


class ControlPlaneClient:
    def __init__(
        self, socket_path: Path, *, client_id: str = "local-client",
        protocol_version: str = PROTOCOL_VERSION, timeout: float = 2.0,
    ):
        self.socket_path = Path(socket_path)
        self.client_id = client_id
        self.protocol_version = protocol_version
        self.timeout = timeout
        self.state = ControlPlaneState.DISCONNECTED
        self._socket: socket.socket | None = None
        self._stream = None

    def _write_request(self, payload: dict) -> None:
        if self._stream is None:
            _invalid("CONTROL_PLANE_CLIENT_DISCONNECTED")
        self._stream.write(json.dumps(
            payload, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n")
        self._stream.flush()

    def _read_response(self) -> dict:
        if self._stream is None:
            _invalid("CONTROL_PLANE_CLIENT_DISCONNECTED")
        raw = self._stream.readline(MAX_RESPONSE_BYTES + 2)
        if not raw or len(raw) > MAX_RESPONSE_BYTES + 1:
            _invalid("CONTROL_PLANE_RESPONSE_INVALID")
        try:
            response = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            _invalid("CONTROL_PLANE_RESPONSE_INVALID")
        if not isinstance(response, dict):
            _invalid("CONTROL_PLANE_RESPONSE_INVALID")
        return response

    def _send(self, payload: dict) -> dict:
        self._write_request(payload)
        return self._read_response()

    def _validate_handshake(self, response: dict) -> None:
        if (response.get("schema") != HANDSHAKE_SCHEMA
                or type(response.get("accepted")) is not bool):
            _invalid("CONTROL_PLANE_HANDSHAKE_INVALID")
        if not response["accepted"]:
            return
        service = response.get("service")
        session = response.get("session")
        if (not isinstance(service, dict) or not isinstance(session, dict)
                or response.get("protocol_version") != self.protocol_version
                or service.get("schema") != SERVICE_IDENTITY_SCHEMA
                or session.get("schema") != SESSION_IDENTITY_SCHEMA
                or service.get("protocol_version") != self.protocol_version
                or session.get("protocol_version") != self.protocol_version
                or not isinstance(service.get("service_id"), str)
                or not service["service_id"]
                or session.get("service_id") != service["service_id"]
                or session.get("client_id") != self.client_id
                or not isinstance(session.get("session_id"), str)
                or not session["session_id"]):
            _invalid("CONTROL_PLANE_HANDSHAKE_IDENTITY_INVALID")

    def connect(self) -> dict:
        self.close()
        self.state = ControlPlaneState.CONNECTING
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(self.timeout)
        try:
            connection.connect(str(self.socket_path))
            self._socket = connection
            self._stream = connection.makefile("rwb")
            response = self._send({
                "type": "handshake",
                "protocol_version": self.protocol_version,
                "client_id": self.client_id,
            })
            self._validate_handshake(response)
            next_state = ControlPlaneState(response["state"])
        except PermissionError:
            connection.close()
            self._socket = None
            self._stream = None
            self.state = ControlPlaneState.UNAUTHORIZED
            raise
        except Exception:
            connection.close()
            self._socket = None
            self._stream = None
            self.state = ControlPlaneState.DISCONNECTED
            raise
        self.state = next_state
        if not response.get("accepted"):
            self.close(preserve_state=True)
        return response

    def request(self, surface: str) -> dict:
        if self._stream is None:
            _invalid("CONTROL_PLANE_CLIENT_DISCONNECTED")
        response = self._send({"type": surface})
        if response.get("schema") == HEALTH_SCHEMA and "state" in response:
            self.state = ControlPlaneState(response["state"])
        return response

    def query(self, request: QueryRequest) -> dict:
        if type(request) is not QueryRequest:
            _invalid("CONTROL_PLANE_QUERY_REQUEST_INVALID")
        response = self._send({
            "type": "query",
            "query": request.to_record(),
        })
        if (response.get("schema") == ERROR_SCHEMA
                and response.get("accepted") is False):
            return response
        if (response.get("schema") != QUERY_PAGE_SCHEMA
                or response.get("accepted") is not True):
            _invalid("CONTROL_PLANE_QUERY_RESPONSE_INVALID")
        return response

    def subscribe_events(
        self, *, after_cursor: str | None = None,
    ) -> "ControlPlaneEventSubscription":
        if self._stream is None:
            _invalid("CONTROL_PLANE_CLIENT_DISCONNECTED")
        self._write_request({
            "type": "event-subscribe",
            "after_cursor": after_cursor,
        })
        acknowledgement = self._read_response()
        return ControlPlaneEventSubscription(self, acknowledgement)

    def preview_command(self, request: OperatorActionRequestV2) -> dict:
        from bilqis_mlx.mission_control.codec import encode_record
        if type(request) is not OperatorActionRequestV2:
            _invalid("CONTROL_PLANE_COMMAND_REQUEST_INVALID")
        response = self._send({
            "type": "command-preview",
            "request": encode_record(request),
        })
        if response.get("schema") == ERROR_SCHEMA and response.get("accepted") is False:
            reason = response.get("reason")
            _invalid(reason if isinstance(reason, str) and reason else
                     "CONTROL_PLANE_COMMAND_PREVIEW_INVALID")
        return response

    def submit_command(
        self, request: OperatorActionRequestV2, *,
        expected_target_ref: str | None = None,
    ) -> OperatorActionReceiptV2:
        from bilqis_mlx.mission_control.codec import encode_record
        if type(request) is not OperatorActionRequestV2:
            _invalid("CONTROL_PLANE_COMMAND_REQUEST_INVALID")
        payload = {
            "type": "command-submit",
            "request": encode_record(request),
        }
        if expected_target_ref is not None:
            payload["expected_target_ref"] = expected_target_ref
        return self._decode_command_receipt(self._send(payload))

    def command_status(self, operation_id: str) -> OperatorActionReceiptV2:
        if not isinstance(operation_id, str) or not operation_id:
            _invalid("CONTROL_PLANE_COMMAND_OPERATION_REQUIRED")
        return self._decode_command_receipt(self._send({
            "type": "command-status",
            "operation_id": operation_id,
        }))

    def inspect_command(self, operation_id: str) -> dict:
        if not isinstance(operation_id, str) or not operation_id:
            _invalid("CONTROL_PLANE_COMMAND_OPERATION_REQUIRED")
        response = self._send({
            "type": "command-inspect",
            "operation_id": operation_id,
        })
        if response.get("schema") == ERROR_SCHEMA and response.get("accepted") is False:
            reason = response.get("reason")
            _invalid(reason if isinstance(reason, str) and reason else
                     "CONTROL_PLANE_COMMAND_INSPECTION_INVALID")
        return response

    @staticmethod
    def _decode_command_receipt(response: dict) -> OperatorActionReceiptV2:
        if response.get("schema") == ERROR_SCHEMA and response.get("accepted") is False:
            reason = response.get("reason")
            _invalid(
                reason if isinstance(reason, str) and reason
                else "CONTROL_PLANE_COMMAND_RESPONSE_INVALID")
        decoded = decode_record(response)
        if type(decoded) is not OperatorActionReceiptV2:
            _invalid("CONTROL_PLANE_COMMAND_RESPONSE_INVALID")
        return decoded

    def close(self, *, preserve_state: bool = False) -> None:
        if self._stream is not None:
            self._stream.close()
        if self._socket is not None:
            self._socket.close()
        self._stream = None
        self._socket = None
        if not preserve_state:
            self.state = ControlPlaneState.DISCONNECTED

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_exc):
        self.close()


class ControlPlaneEventSubscription:
    """Dedicated streaming view on one already-handshaken client connection."""

    def __init__(self, client: ControlPlaneClient, acknowledgement: dict):
        self.client = client
        self.acknowledgement = acknowledgement
        self.gap: dict | None = None
        self.latest_cursor: str | None = acknowledgement.get(
            "latest_cursor_sha256")
        self._closed = False
        schema = acknowledgement.get("schema")
        accepted = acknowledgement.get("accepted")
        if schema == EVENT_GAP_SCHEMA and accepted is False:
            self.gap = acknowledgement
            self._closed = True
        elif schema == ERROR_SCHEMA and accepted is False:
            reason = acknowledgement.get("reason")
            _invalid(
                reason if isinstance(reason, str) and reason
                else "CONTROL_PLANE_EVENT_SUBSCRIPTION_INVALID"
            )
        elif schema != EVENT_SUBSCRIPTION_SCHEMA or accepted is not True:
            _invalid("CONTROL_PLANE_EVENT_SUBSCRIPTION_INVALID")

    def __iter__(self):
        return self

    def __next__(self) -> EventEnvelope:
        if self._closed:
            raise StopIteration
        while True:
            record = self.client._read_response()
            schema = record.get("schema")
            if schema == EVENT_HEARTBEAT_SCHEMA:
                self.latest_cursor = record.get("latest_cursor_sha256")
                continue
            if schema == EVENT_GAP_SCHEMA:
                self.gap = record
                self._closed = True
                raise StopIteration
            decoded = decode_record(record)
            if type(decoded) is not EventEnvelope:
                _invalid("CONTROL_PLANE_EVENT_DELIVERY_INVALID")
            self.latest_cursor = decoded.position.cursor_sha256
            return decoded
