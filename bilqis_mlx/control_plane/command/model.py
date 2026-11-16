"""CP05 command identity, target, and execution-plan domain model."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.mission_control.codec import canonical_json
from bilqis_mlx.mission_control.model import RunRef, is_name, is_sha256, is_wire_integer
from bilqis_mlx.mission_control.operator import OperatorActionRequestV2


COMMAND_TARGET_SCHEMA = "bilqis.bamf.control-plane.command-target/v1"
COMMAND_PLAN_SCHEMA = "bilqis.bamf.control-plane.command-plan/v1"
OPERATION_PREFIX = "operation:"


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID, reason=reason)


def _canonical(payload: dict) -> bytes:
    try:
        return (json.dumps(
            payload, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ) + "\n").encode("utf-8")
    except (TypeError, ValueError):
        _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")


def _sha(payload: dict) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


class CommandAction(StrEnum):
    CREATE = "create"
    RESUME = "resume"
    OWNER_LAUNCH = "owner-launch"
    STATUS = "status"
    CHECKPOINT_VERIFY = "checkpoint-verify"
    ADMISSION_LEASE = "admission-lease"
    PAUSE = "pause"
    STOP = "stop"


class CommandMode(StrEnum):
    READ_ONLY = "read-only"
    DRY_RUN = "dry-run"
    MUTATING = "mutating"


@dataclass(frozen=True)
class ResolvedCommandTarget:
    """Exact pre-mutation target witness; absent fields stay absent, never guessed."""

    run_dir: str
    run_id: str | None
    run_seed: int | None
    run_identity_sha256: str | None
    generation: int | None
    generation_manifest_sha256: str | None
    optimizer_step: int | None
    candidate_identity_sha256: str | None
    factory_release_sha256: str | None
    semantic_release_sha256: str | None
    topology_sha256: str | None
    acceptance_sha256: str | None
    source_identity: str | None
    schema: str = COMMAND_TARGET_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != COMMAND_TARGET_SCHEMA or not is_name(self.run_dir):
            _invalid("CONTROL_PLANE_COMMAND_TARGET_INVALID")
        if self.run_id is not None and not is_name(self.run_id):
            _invalid("CONTROL_PLANE_COMMAND_TARGET_INVALID")
        for value in (self.run_seed, self.generation, self.optimizer_step):
            if value is not None and (
                    not is_wire_integer(value) or value < 0):
                _invalid("CONTROL_PLANE_COMMAND_TARGET_INVALID")
        if self.source_identity is not None and not is_name(self.source_identity):
            _invalid("CONTROL_PLANE_COMMAND_TARGET_INVALID")
        digests = (
            self.run_identity_sha256, self.generation_manifest_sha256,
            self.candidate_identity_sha256, self.factory_release_sha256,
            self.semantic_release_sha256, self.topology_sha256,
            self.acceptance_sha256,
        )
        if any(value is not None and not is_sha256(value) for value in digests):
            _invalid("CONTROL_PLANE_COMMAND_TARGET_INVALID")

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "run_dir": self.run_dir,
            "run_id": self.run_id,
            "run_seed": self.run_seed,
            "run_identity_sha256": self.run_identity_sha256,
            "generation": self.generation,
            "generation_manifest_sha256": self.generation_manifest_sha256,
            "optimizer_step": self.optimizer_step,
            "candidate_identity_sha256": self.candidate_identity_sha256,
            "factory_release_sha256": self.factory_release_sha256,
            "semantic_release_sha256": self.semantic_release_sha256,
            "topology_sha256": self.topology_sha256,
            "acceptance_sha256": self.acceptance_sha256,
            "source_identity": self.source_identity,
        }

    @property
    def digest(self) -> str:
        return _sha(self.to_record())

    @property
    def ref(self) -> str:
        return f"command-target:{self.digest}"

    def run_ref(self) -> RunRef | None:
        values = (
            self.run_id,
            self.run_identity_sha256,
            self.generation,
            self.generation_manifest_sha256,
            self.candidate_identity_sha256,
            self.factory_release_sha256,
            self.semantic_release_sha256,
            self.topology_sha256,
        )
        if any(value is None for value in values):
            return None
        return RunRef(
            run_id=self.run_id,
            run_identity_sha256=self.run_identity_sha256,
            generation=self.generation,
            generation_manifest_sha256=self.generation_manifest_sha256,
            candidate_identity_sha256=self.candidate_identity_sha256,
            factory_release_sha256=self.factory_release_sha256,
            semantic_release_sha256=self.semantic_release_sha256,
            topology_sha256=self.topology_sha256,
        )

    @classmethod
    def from_record(cls, record: dict) -> "ResolvedCommandTarget":
        if not isinstance(record, dict):
            _invalid("CONTROL_PLANE_COMMAND_TARGET_INVALID")
        expected = {
            "schema", "run_dir", "run_id", "run_seed", "run_identity_sha256",
            "generation", "generation_manifest_sha256", "optimizer_step",
            "candidate_identity_sha256",
            "factory_release_sha256", "semantic_release_sha256",
            "topology_sha256", "acceptance_sha256", "source_identity",
        }
        if set(record) != expected:
            _invalid("CONTROL_PLANE_COMMAND_TARGET_INVALID")
        return cls(**record)


@dataclass(frozen=True)
class CommandPlan:
    """Immutable accepted plan. A worker executes exactly this plan, at most once."""

    operation_id: str
    request_sha256: str
    intent_sha256: str
    action: CommandAction
    mode: CommandMode
    target: ResolvedCommandTarget
    argv: tuple[str, ...]
    postcondition_kind: str
    schema: str = COMMAND_PLAN_SCHEMA

    def __post_init__(self) -> None:
        if (self.schema != COMMAND_PLAN_SCHEMA
                or not is_name(self.operation_id)
                or not is_sha256(self.request_sha256)
                or not is_sha256(self.intent_sha256)
                or type(self.action) is not CommandAction
                or type(self.mode) is not CommandMode
                or type(self.target) is not ResolvedCommandTarget
                or type(self.argv) is not tuple
                or not all(is_name(item) for item in self.argv)
                or not is_name(self.postcondition_kind)):
            _invalid("CONTROL_PLANE_COMMAND_PLAN_INVALID")

    @property
    def requires_worker(self) -> bool:
        return self.mode is CommandMode.MUTATING

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "operation_id": self.operation_id,
            "request_sha256": self.request_sha256,
            "intent_sha256": self.intent_sha256,
            "action": self.action.value,
            "mode": self.mode.value,
            "target": self.target.to_record(),
            "argv": list(self.argv),
            "postcondition_kind": self.postcondition_kind,
        }

    @property
    def digest(self) -> str:
        return _sha(self.to_record())

    @classmethod
    def from_record(cls, record: dict) -> "CommandPlan":
        if not isinstance(record, dict):
            _invalid("CONTROL_PLANE_COMMAND_PLAN_INVALID")
        expected = {
            "schema", "operation_id", "request_sha256", "intent_sha256",
            "action", "mode",
            "target", "argv", "postcondition_kind",
        }
        if set(record) != expected or type(record.get("argv")) is not list:
            _invalid("CONTROL_PLANE_COMMAND_PLAN_INVALID")
        return cls(
            operation_id=record["operation_id"],
            request_sha256=record["request_sha256"],
            intent_sha256=record["intent_sha256"],
            action=CommandAction(record["action"]),
            mode=CommandMode(record["mode"]),
            target=ResolvedCommandTarget.from_record(record["target"]),
            argv=tuple(record["argv"]),
            postcondition_kind=record["postcondition_kind"],
            schema=record["schema"],
        )


def operation_id_for(idempotency_key: str) -> str:
    if not is_name(idempotency_key):
        _invalid("CONTROL_PLANE_COMMAND_IDEMPOTENCY_INVALID")
    digest = hashlib.sha256(
        ("bilqis-cp05\0" + idempotency_key).encode("utf-8")).hexdigest()
    return f"operation:{digest}"


def operation_directory_name(operation_id: str) -> str:
    if (
        not operation_id.startswith(OPERATION_PREFIX)
        or not is_sha256(operation_id[len(OPERATION_PREFIX):])
    ):
        _invalid("CONTROL_PLANE_COMMAND_OPERATION_INVALID")
    return operation_id[len(OPERATION_PREFIX):]


def request_sha256(request: OperatorActionRequestV2) -> str:
    if type(request) is not OperatorActionRequestV2:
        _invalid("CONTROL_PLANE_COMMAND_REQUEST_INVALID")
    return hashlib.sha256(canonical_json(request)).hexdigest()


def intent_sha256(request: OperatorActionRequestV2) -> str:
    """Hash semantic effect while excluding submission identity and timestamps."""
    if type(request) is not OperatorActionRequestV2:
        _invalid("CONTROL_PLANE_COMMAND_REQUEST_INVALID")
    parameters = sorted(
        ((parameter.key, parameter.value) for parameter in request.parameters),
        key=lambda item: item[0],
    )
    payload = {
        "action": request.action,
        "parameters": parameters,
        "dry_run": request.dry_run,
        "human_authorized": request.human_authorized,
    }
    return hashlib.sha256(_canonical(payload)).hexdigest()
