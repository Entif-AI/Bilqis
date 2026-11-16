"""Typed CP05 facts layered over durable command-storage primitives."""
from __future__ import annotations

import hashlib

from bilqis_mlx.mission_control.codec import decode_record, encode_record
from bilqis_mlx.mission_control.operator import (
    OperatorActionReceiptV2, OperatorActionRequestV2,
)

from .model import (
    CommandPlan, intent_sha256, request_sha256,
)
from .storage import CommandStorage, canonical_fact
from ..transport import _invalid


SUBMISSION_SCHEMA = "bilqis.bamf.control-plane.command-submission/v1"
PREFLIGHT_SCHEMA = "bilqis.bamf.control-plane.command-preflight/v1"
DISPATCH_SCHEMA = "bilqis.bamf.control-plane.command-dispatch-reserved/v1"
SPAWNED_SCHEMA = "bilqis.bamf.control-plane.command-worker-spawned/v1"
WORKER_RESULT_SCHEMA = "bilqis.bamf.control-plane.command-worker-result/v1"
TRAINER_PROCESS_SCHEMA = "bilqis.bamf.control-plane.command-trainer-process/v1"
POSTCONDITION_SCHEMA = "bilqis.bamf.control-plane.command-postcondition/v1"
SHA256_HEX_LENGTH = 64


class CommandStore(CommandStorage):
    """One operation directory containing immutable typed lifecycle facts."""

    def write_submission(
        self, operation_id: str, request: OperatorActionRequestV2,
    ) -> None:
        if type(request) is not OperatorActionRequestV2:
            _invalid("CONTROL_PLANE_COMMAND_REQUEST_INVALID")
        self.write_fact(operation_id, "submission.json", {
            "schema": SUBMISSION_SCHEMA,
            "operation_id": operation_id,
            "request_sha256": request_sha256(request),
            "intent_sha256": intent_sha256(request),
            "request": encode_record(request),
        })

    def read_submission(
        self, operation_id: str,
    ) -> tuple[OperatorActionRequestV2, str, str] | None:
        payload = self.read_fact(operation_id, "submission.json")
        if payload is None:
            return None
        request = decode_record(payload.get("request", {}))
        if (
            payload.get("schema") != SUBMISSION_SCHEMA
            or payload.get("operation_id") != operation_id
            or type(request) is not OperatorActionRequestV2
            or request_sha256(request) != payload.get("request_sha256")
            or intent_sha256(request) != payload.get("intent_sha256")
        ):
            _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
        return request, payload["request_sha256"], payload["intent_sha256"]

    def write_plan(self, plan: CommandPlan) -> None:
        self.write_fact(plan.operation_id, "plan.json", plan.to_record())

    def read_plan(self, operation_id: str) -> CommandPlan | None:
        payload = self.read_fact(operation_id, "plan.json")
        if payload is None:
            return None
        try:
            plan = CommandPlan.from_record(payload)
        except (KeyError, TypeError, ValueError):
            _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
        if plan.operation_id != operation_id:
            _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
        return plan

    def write_preflight(self, operation_id: str, payload: dict) -> None:
        self.write_fact(operation_id, "preflight.json", {
            "schema": PREFLIGHT_SCHEMA,
            "operation_id": operation_id,
            "value": payload,
        })

    def read_preflight(self, operation_id: str) -> dict | None:
        payload = self.read_fact(operation_id, "preflight.json")
        if payload is None:
            return None
        if (
            payload.get("schema") != PREFLIGHT_SCHEMA
            or payload.get("operation_id") != operation_id
            or not isinstance(payload.get("value"), dict)
        ):
            _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
        return payload["value"]

    def _write_receipt(
        self, operation_id: str, name: str, receipt: OperatorActionReceiptV2,
    ) -> None:
        if (
            type(receipt) is not OperatorActionReceiptV2
            or receipt.operation_id != operation_id
        ):
            _invalid("CONTROL_PLANE_COMMAND_RECEIPT_INVALID")
        self.write_fact(operation_id, name, encode_record(receipt))

    def _read_receipt(
        self, operation_id: str, name: str,
    ) -> OperatorActionReceiptV2 | None:
        payload = self.read_fact(operation_id, name)
        if payload is None:
            return None
        receipt = decode_record(payload)
        if (
            type(receipt) is not OperatorActionReceiptV2
            or receipt.operation_id != operation_id
        ):
            _invalid("CONTROL_PLANE_COMMAND_RECEIPT_INVALID")
        return receipt

    def write_accepted(
        self, operation_id: str, receipt: OperatorActionReceiptV2,
    ) -> None:
        self._write_receipt(operation_id, "accepted.json", receipt)

    def read_accepted(
        self, operation_id: str,
    ) -> OperatorActionReceiptV2 | None:
        return self._read_receipt(operation_id, "accepted.json")

    def write_dispatch(self, operation_id: str, *, reserved_at: int) -> None:
        self.write_fact(operation_id, "dispatch.json", {
            "schema": DISPATCH_SCHEMA,
            "operation_id": operation_id,
            "reserved_at": reserved_at,
        })

    def read_dispatch(self, operation_id: str) -> dict | None:
        payload = self.read_fact(operation_id, "dispatch.json")
        if payload is None:
            return None
        if (
            payload.get("schema") != DISPATCH_SCHEMA
            or payload.get("operation_id") != operation_id
            or type(payload.get("reserved_at")) is not int
        ):
            _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
        return payload

    def write_spawned(
        self, operation_id: str, *, pid: int, spawned_at: int,
    ) -> None:
        self.write_fact(operation_id, "spawned.json", {
            "schema": SPAWNED_SCHEMA,
            "operation_id": operation_id,
            "pid": pid,
            "spawned_at": spawned_at,
        })

    def read_spawned(self, operation_id: str) -> dict | None:
        payload = self.read_fact(operation_id, "spawned.json")
        if payload is None:
            return None
        if (
            payload.get("schema") != SPAWNED_SCHEMA
            or payload.get("operation_id") != operation_id
            or type(payload.get("pid")) is not int
            or payload["pid"] <= 0
            or type(payload.get("spawned_at")) is not int
        ):
            _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
        return payload

    def write_trainer_process(
        self, operation_id: str, *, pid: int, identity_sha256: str,
    ) -> None:
        self.write_fact(operation_id, "trainer-process.json", {
            "schema": TRAINER_PROCESS_SCHEMA,
            "operation_id": operation_id,
            "pid": pid,
            "identity_sha256": identity_sha256,
        })

    def read_trainer_process(self, operation_id: str) -> dict | None:
        payload = self.read_fact(operation_id, "trainer-process.json")
        if payload is None:
            return None
        if (
            payload.get("schema") != TRAINER_PROCESS_SCHEMA
            or payload.get("operation_id") != operation_id
            or type(payload.get("pid")) is not int
            or payload["pid"] <= 0
            or not isinstance(payload.get("identity_sha256"), str)
            or len(payload["identity_sha256"]) != SHA256_HEX_LENGTH
        ):
            _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
        return payload

    def write_worker_result(
        self, operation_id: str, *, returncode: int | None,
        error_ref: str | None, finished_at: int,
    ) -> None:
        self.write_fact(operation_id, "worker-result.json", {
            "schema": WORKER_RESULT_SCHEMA,
            "operation_id": operation_id,
            "returncode": returncode,
            "error_ref": error_ref,
            "finished_at": finished_at,
        })

    def read_worker_result(self, operation_id: str) -> dict | None:
        payload = self.read_fact(operation_id, "worker-result.json")
        if payload is None:
            return None
        if (
            payload.get("schema") != WORKER_RESULT_SCHEMA
            or payload.get("operation_id") != operation_id
            or (
                payload.get("returncode") is not None
                and type(payload.get("returncode")) is not int
            )
            or (
                payload.get("error_ref") is not None
                and not isinstance(payload.get("error_ref"), str)
            )
            or type(payload.get("finished_at")) is not int
        ):
            _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
        return payload

    def write_postcondition(self, operation_id: str, value: dict) -> str:
        record = {
            "schema": POSTCONDITION_SCHEMA,
            "operation_id": operation_id,
            "value": value,
        }
        digest = hashlib.sha256(canonical_fact(record)).hexdigest()
        self.write_fact(
            operation_id, "postcondition.json",
            {**record, "sha256": digest},
        )
        return f"command-postcondition:{digest}"

    def read_postcondition(self, operation_id: str) -> dict | None:
        payload = self.read_fact(operation_id, "postcondition.json")
        if payload is None:
            return None
        digest = payload.get("sha256")
        record = {key: value for key, value in payload.items() if key != "sha256"}
        if (
            record.get("schema") != POSTCONDITION_SCHEMA
            or record.get("operation_id") != operation_id
            or not isinstance(record.get("value"), dict)
            or digest != hashlib.sha256(canonical_fact(record)).hexdigest()
        ):
            _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
        return record["value"]

    def write_terminal(
        self, operation_id: str, receipt: OperatorActionReceiptV2,
    ) -> None:
        self._write_receipt(operation_id, "terminal.json", receipt)

    def read_terminal(
        self, operation_id: str,
    ) -> OperatorActionReceiptV2 | None:
        return self._read_receipt(operation_id, "terminal.json")
