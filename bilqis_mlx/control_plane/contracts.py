"""CP01 transport/session contracts; no learner authority lives here."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


PROTOCOL_VERSION = "bilqis.bamf.control-plane/v1"
HANDSHAKE_SCHEMA = "bilqis.bamf.control-plane.handshake/v1"
HEALTH_SCHEMA = "bilqis.bamf.control-plane.health/v1"
ERROR_SCHEMA = "bilqis.bamf.control-plane.error/v1"
SERVICE_IDENTITY_SCHEMA = "bilqis.bamf.control-plane.service-identity/v1"
LEARNER_IDENTITY_SCHEMA = "bilqis.bamf.control-plane.learner-identity/v1"
SESSION_IDENTITY_SCHEMA = "bilqis.bamf.control-plane.session-identity/v1"


class ControlPlaneState(str, Enum):
    CONNECTING = "connecting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    INCOMPATIBLE_VERSION = "incompatible-version"
    UNAUTHORIZED = "unauthorized"
    LEARNER_UNAVAILABLE = "learner-unavailable"
    SERVICE_RESTARTING = "service-restarting"
    STALE = "stale"
    DISCONNECTED = "disconnected"


@dataclass(frozen=True)
class ServiceIdentity:
    service_id: str
    pid: int
    started_at: str
    socket_path: str
    run_dir: str
    protocol_version: str = PROTOCOL_VERSION
    schema: str = SERVICE_IDENTITY_SCHEMA

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "service_id": self.service_id,
            "pid": self.pid,
            "started_at": self.started_at,
            "socket_path": self.socket_path,
            "run_dir": self.run_dir,
            "protocol_version": self.protocol_version,
        }


@dataclass(frozen=True)
class LearnerIdentity:
    state: ControlPlaneState
    run_dir: str
    operator_active: bool | None = None
    run_id: str | None = None
    run_identity_sha256: str | None = None
    generation: int | None = None
    generation_manifest_sha256: str | None = None
    optimizer_step: int | None = None
    factory_release_sha256: str | None = None
    topology_sha256: str | None = None
    failure_code: str | None = None
    schema: str = LEARNER_IDENTITY_SCHEMA

    @property
    def ready(self) -> bool:
        return self.state is ControlPlaneState.HEALTHY

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "state": self.state.value,
            "run_dir": self.run_dir,
            "operator_active": self.operator_active,
            "run_id": self.run_id,
            "run_identity_sha256": self.run_identity_sha256,
            "generation": self.generation,
            "generation_manifest_sha256": self.generation_manifest_sha256,
            "optimizer_step": self.optimizer_step,
            "factory_release_sha256": self.factory_release_sha256,
            "topology_sha256": self.topology_sha256,
            "failure_code": self.failure_code,
        }


@dataclass(frozen=True)
class SessionIdentity:
    session_id: str
    client_id: str
    service_id: str
    protocol_version: str = PROTOCOL_VERSION
    schema: str = SESSION_IDENTITY_SCHEMA

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "session_id": self.session_id,
            "client_id": self.client_id,
            "service_id": self.service_id,
            "protocol_version": self.protocol_version,
        }
