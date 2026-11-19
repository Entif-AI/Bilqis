"""C14.4 signed worker receipts and replay verification."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .contracts import (
    ARTIFACT_SCHEMA, LEDGER_SCHEMA, RECEIPT_SCHEMA, USAGE_SCHEMA, WORKER_SCHEMA,
    RemoteWorkManifest, canonical_bytes, content_digest, digest, finite, invalid,
    text, _PUBLIC_KEY, _SIG,
)


@dataclass(frozen=True)
class EnvironmentIdentity:
    hardware: str
    os: str
    mlx_version: str
    backend: str
    device_count: int

    def __post_init__(self) -> None:
        if (not all(text(value) for value in (
                    self.hardware, self.os, self.mlx_version, self.backend))
                or type(self.device_count) is not int or self.device_count < 1):
            invalid("BAMF_C14_ENVIRONMENT_IDENTITY_INVALID")

    @property
    def digest(self) -> str:
        return content_digest(asdict(self))


@dataclass(frozen=True)
class WorkerIdentity:
    worker_id: str
    public_key_hex: str
    environment: EnvironmentIdentity
    schema_version: str = field(default=WORKER_SCHEMA, init=False)

    def __post_init__(self) -> None:
        if (not text(self.worker_id)
                or type(self.public_key_hex) is not str
                or _PUBLIC_KEY.fullmatch(self.public_key_hex) is None
                or type(self.environment) is not EnvironmentIdentity
                or self.schema_version != WORKER_SCHEMA):
            invalid("BAMF_C14_WORKER_IDENTITY_INVALID")


@dataclass(frozen=True)
class ContributionArtifact:
    artifact_type: str
    payload: bytes
    base_binding_digest: str | None = None
    affected_parameter_ids: tuple[str, ...] = ()
    schema_version: str = field(default=ARTIFACT_SCHEMA, init=False)

    def __post_init__(self) -> None:
        if (not text(self.artifact_type)
                or type(self.payload) is not bytes or not self.payload
                or (self.base_binding_digest is not None
                    and not digest(self.base_binding_digest))
                or type(self.affected_parameter_ids) is not tuple
                or any(not text(item) for item in self.affected_parameter_ids)
                or self.affected_parameter_ids
                    != tuple(sorted(set(self.affected_parameter_ids)))
                or self.schema_version != ARTIFACT_SCHEMA):
            invalid("BAMF_C14_CONTRIBUTION_ARTIFACT_INVALID")

    @property
    def digest(self) -> str:
        return sha256(self.payload).hexdigest()


@dataclass(frozen=True)
class ResourceUsage:
    examples: int
    steps: int
    seconds: int
    payload_bytes: int
    schema_version: str = field(default=USAGE_SCHEMA, init=False)

    def __post_init__(self) -> None:
        if (any(type(value) is not int or value < 0 for value in (
                self.examples, self.steps, self.seconds, self.payload_bytes))
                or self.schema_version != USAGE_SCHEMA):
            invalid("BAMF_C14_RESOURCE_USAGE_INVALID")


@dataclass(frozen=True)
class WorkerReceipt:
    manifest_digest: str
    worker: WorkerIdentity
    artifact: ContributionArtifact
    claimed_score: float
    usage: ResourceUsage
    completed_at: int
    signature_hex: str
    schema_version: str = field(default=RECEIPT_SCHEMA, init=False)

    @classmethod
    def unsigned(
            cls, *, manifest: RemoteWorkManifest, worker: WorkerIdentity,
            artifact: ContributionArtifact, claimed_score: float,
            usage: ResourceUsage, completed_at: int,
    ) -> "WorkerReceipt":
        return cls(
            manifest.digest, worker, artifact, claimed_score, usage,
            completed_at, "0" * 128)

    def __post_init__(self) -> None:
        if (not digest(self.manifest_digest)
                or type(self.worker) is not WorkerIdentity
                or type(self.artifact) is not ContributionArtifact
                or not finite(self.claimed_score)
                or not 0.0 <= float(self.claimed_score) <= 1.0
                or type(self.usage) is not ResourceUsage
                or type(self.completed_at) is not int or self.completed_at < 0
                or type(self.signature_hex) is not str
                or _SIG.fullmatch(self.signature_hex) is None
                or self.schema_version != RECEIPT_SCHEMA):
            invalid("BAMF_C14_WORKER_RECEIPT_INVALID")

    def signing_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "manifest_digest": self.manifest_digest,
            "worker": {
                "worker_id": self.worker.worker_id,
                "public_key_hex": self.worker.public_key_hex,
                "environment": asdict(self.worker.environment),
                "schema_version": self.worker.schema_version,
            },
            "artifact": {
                "artifact_type": self.artifact.artifact_type,
                "digest": self.artifact.digest,
                "base_binding_digest": self.artifact.base_binding_digest,
                "affected_parameter_ids": self.artifact.affected_parameter_ids,
                "schema_version": self.artifact.schema_version,
            },
            "claimed_score": self.claimed_score,
            "usage": asdict(self.usage),
            "completed_at": self.completed_at,
        }

    def signing_bytes(self) -> bytes:
        return canonical_bytes(self.signing_payload())

    def with_signature(self, signature_hex: str) -> "WorkerReceipt":
        return WorkerReceipt(
            self.manifest_digest, self.worker, self.artifact,
            self.claimed_score, self.usage, self.completed_at, signature_hex)

    @property
    def canonical_json(self) -> str:
        from .wire import encode_receipt
        return encode_receipt(self)

    @classmethod
    def from_canonical_json(cls, value: str) -> "WorkerReceipt":
        from .wire import decode_receipt
        return decode_receipt(value)

    @property
    def digest(self) -> str:
        return content_digest({
            **self.signing_payload(), "signature_hex": self.signature_hex})


@dataclass(frozen=True)
class ReplayLedger:
    consumed_replay_ids: tuple[str, ...] = ()
    schema_version: str = field(default=LEDGER_SCHEMA, init=False)

    def __post_init__(self) -> None:
        if (type(self.consumed_replay_ids) is not tuple
                or any(not text(item) for item in self.consumed_replay_ids)
                or self.consumed_replay_ids
                    != tuple(sorted(set(self.consumed_replay_ids)))
                or self.schema_version != LEDGER_SCHEMA):
            invalid("BAMF_C14_REPLAY_LEDGER_INVALID")

    def consume(self, replay_id: str) -> "ReplayLedger":
        self.__post_init__()
        if replay_id in self.consumed_replay_ids:
            invalid("BAMF_C14_CONTRIBUTION_REPLAYED")
        return ReplayLedger(tuple(sorted((*self.consumed_replay_ids, replay_id))))

@dataclass(frozen=True)
class VerifiedRemoteReceipt:
    receipt_digest: str
    replay_ledger: ReplayLedger

def _verify_signature(receipt: WorkerReceipt) -> None:
    try:
        Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(receipt.worker.public_key_hex)
        ).verify(bytes.fromhex(receipt.signature_hex), receipt.signing_bytes())
    except (ValueError, InvalidSignature):
        invalid("BAMF_C14_WORKER_SIGNATURE_INVALID")


def verify_remote_receipt(
        manifest: RemoteWorkManifest, receipt: WorkerReceipt, *,
        now: int, replay_ledger: ReplayLedger) -> VerifiedRemoteReceipt:
    """Authenticate one result and prove it belongs to this frozen assignment."""
    if (type(manifest) is not RemoteWorkManifest
            or type(receipt) is not WorkerReceipt
            or type(now) is not int or now < 0
            or type(replay_ledger) is not ReplayLedger):
        invalid("BAMF_C14_REMOTE_VERIFY_INPUT_INVALID")
    manifest.__post_init__()
    receipt.__post_init__()
    replay_ledger.__post_init__()
    if now > manifest.expires_at or receipt.completed_at > manifest.expires_at:
        invalid("BAMF_C14_REMOTE_WORK_EXPIRED")
    if receipt.manifest_digest != manifest.digest:
        invalid("BAMF_C14_REMOTE_MANIFEST_MISMATCH")
    if manifest.mlx_identity != f"mlx:{receipt.worker.environment.mlx_version}":
        invalid("BAMF_C14_WORKER_MLX_IDENTITY_MISMATCH")
    if receipt.artifact.artifact_type != manifest.expected_artifact_type:
        invalid("BAMF_C14_REMOTE_ARTIFACT_TYPE_MISMATCH")
    budget, usage = manifest.resource_budget, receipt.usage
    if (usage.payload_bytes != len(receipt.artifact.payload)
            or usage.examples > budget.max_examples
            or usage.steps > budget.max_steps
            or usage.seconds > budget.max_seconds
            or usage.payload_bytes > budget.max_bytes):
        invalid("BAMF_C14_REMOTE_ARTIFACT_BUDGET_EXCEEDED")
    if manifest.contribution_class.value == "adapter_delta":
        if (receipt.artifact.base_binding_digest != manifest.base_binding_digest
                or not receipt.artifact.affected_parameter_ids):
            invalid("BAMF_C14_REMOTE_DELTA_BINDING_MISMATCH")
    elif (receipt.artifact.base_binding_digest is not None
            or receipt.artifact.affected_parameter_ids):
        invalid("BAMF_C14_REMOTE_ARTIFACT_SCOPE_INVALID")
    _verify_signature(receipt)
    return VerifiedRemoteReceipt(
        receipt.digest, replay_ledger.consume(manifest.replay_id))
