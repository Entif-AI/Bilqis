"""Non-authorizing operator request and receipt contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import math

from .model import (
    RecordMeta, Scalar, WireRecord, is_name, is_sha256, is_text, is_time,
    is_wire_integer, require,
)


class ActionReceiptState(StrEnum):
    ACCEPTED = "ACCEPTED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"


@dataclass(frozen=True, order=True)
class ActionParameter:
    key: str
    value: Scalar | None

    def __post_init__(self) -> None:
        require(is_name(self.key), "ACTION_PARAMETER_KEY")
        require(self.value is None or type(self.value) in (str, int, float, bool),
                "ACTION_PARAMETER_VALUE")
        if type(self.value) is str:
            require(is_text(self.value), "ACTION_PARAMETER_TEXT")
        if type(self.value) is int:
            require(is_wire_integer(self.value), "ACTION_PARAMETER_INTEGER")
        if type(self.value) is float:
            require(math.isfinite(self.value), "ACTION_PARAMETER_FINITE")


@dataclass(frozen=True)
class OperatorActionRequest(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.operator-action-request/v1"
    meta: RecordMeta
    request_id: str
    idempotency_key: str
    action: str
    parameters: tuple[ActionParameter, ...]
    dry_run: bool
    requested_at: int

    def __post_init__(self) -> None:
        super().__post_init__()
        require(all(is_name(item) for item in (
            self.request_id, self.idempotency_key, self.action)), "ACTION_REQUEST_ID")
        require(type(self.parameters) is tuple
                and all(type(item) is ActionParameter for item in self.parameters),
                "ACTION_PARAMETERS")
        keys = tuple(item.key for item in self.parameters)
        require(len(keys) == len(set(keys)), "ACTION_PARAMETER_KEYS")
        require(type(self.dry_run) is bool and is_time(self.requested_at), "ACTION_REQUEST_STATE")


@dataclass(frozen=True)
class OperatorActionReceipt(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.operator-action-receipt/v1"
    meta: RecordMeta
    request_id: str
    operation_id: str
    state: ActionReceiptState
    acknowledged_at: int
    postcondition_ref: str | None
    error_ref: str | None

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_name(self.request_id) and is_name(self.operation_id), "ACTION_RECEIPT_ID")
        require(type(self.state) is ActionReceiptState and is_time(self.acknowledged_at),
                "ACTION_RECEIPT_STATE")
        require(self.postcondition_ref is None or is_name(self.postcondition_ref),
                "ACTION_POSTCONDITION")
        require(self.error_ref is None or is_name(self.error_ref), "ACTION_ERROR")
        if self.state is ActionReceiptState.COMPLETED:
            require(self.postcondition_ref is not None and bool(self.meta.receipt_refs),
                    "ACTION_COMPLETION_PROOF")
            require(self.error_ref is None, "ACTION_COMPLETION_ERROR")
        elif self.state in (ActionReceiptState.REJECTED, ActionReceiptState.FAILED):
            require(self.error_ref is not None and self.postcondition_ref is None,
                    "ACTION_FAILURE_PROOF")
        else:
            require(self.postcondition_ref is None and self.error_ref is None,
                    "ACTION_NONTERMINAL_PROOF")


@dataclass(frozen=True)
class OperatorActionRequestV2(WireRecord):
    """CP05 request: authorization is explicit and pre-run targets need not exist yet."""

    SCHEMA = "bilqis.bamf.mission-control.operator-action-request/v2"
    RUN_BOUND = False
    meta: RecordMeta
    request_id: str
    idempotency_key: str
    action: str
    parameters: tuple[ActionParameter, ...]
    dry_run: bool
    human_authorized: bool
    requested_at: int

    def __post_init__(self) -> None:
        super().__post_init__()
        require(all(is_name(item) for item in (
            self.request_id, self.idempotency_key, self.action)), "ACTION_REQUEST_ID")
        require(type(self.parameters) is tuple
                and all(type(item) is ActionParameter for item in self.parameters),
                "ACTION_PARAMETERS")
        keys = tuple(item.key for item in self.parameters)
        require(len(keys) == len(set(keys)), "ACTION_PARAMETER_KEYS")
        require(
            type(self.dry_run) is bool
            and type(self.human_authorized) is bool
            and is_time(self.requested_at),
            "ACTION_REQUEST_STATE",
        )


@dataclass(frozen=True)
class OperatorActionReceiptV2(WireRecord):
    """CP05 receipt binds request digest, resolved target and observed outcome."""

    SCHEMA = "bilqis.bamf.mission-control.operator-action-receipt/v2"
    RUN_BOUND = False
    meta: RecordMeta
    request_id: str
    request_sha256: str
    operation_id: str
    state: ActionReceiptState
    acknowledged_at: int
    target_ref: str
    postcondition_ref: str | None
    error_ref: str | None

    def __post_init__(self) -> None:
        super().__post_init__()
        require(
            is_name(self.request_id)
            and is_sha256(self.request_sha256)
            and is_name(self.operation_id)
            and is_name(self.target_ref),
            "ACTION_RECEIPT_ID",
        )
        require(type(self.state) is ActionReceiptState and is_time(self.acknowledged_at),
                "ACTION_RECEIPT_STATE")
        require(self.postcondition_ref is None or is_name(self.postcondition_ref),
                "ACTION_POSTCONDITION")
        require(self.error_ref is None or is_name(self.error_ref), "ACTION_ERROR")
        if self.state is ActionReceiptState.COMPLETED:
            require(self.postcondition_ref is not None and bool(self.meta.receipt_refs),
                    "ACTION_COMPLETION_PROOF")
            require(self.error_ref is None, "ACTION_COMPLETION_ERROR")
        elif self.state in (ActionReceiptState.REJECTED, ActionReceiptState.FAILED):
            require(self.error_ref is not None and self.postcondition_ref is None,
                    "ACTION_FAILURE_PROOF")
        else:
            require(self.postcondition_ref is None and self.error_ref is None,
                    "ACTION_NONTERMINAL_PROOF")
