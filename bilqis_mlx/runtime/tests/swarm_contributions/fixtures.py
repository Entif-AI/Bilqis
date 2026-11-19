"""Public synthetic C14.4 fixtures."""
from hashlib import sha256

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bilqis_mlx.runtime.swarm_contributions import (
    AcceptanceContract, ContributionArtifact, ContributionClass,
    EnvironmentIdentity, RemoteWorkManifest, ResourceBudget, ResourceUsage,
    WorkerIdentity, WorkerReceipt,
)

GENERATION = "a" * 64
SOURCE = "b" * 64
TOPOLOGY = "c" * 64
MODEL = "d" * 64
ACCEPTANCE = "e" * 64
BINDING = "f" * 64
KEY = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("42" * 32))
PUBLIC = KEY.public_key().public_bytes_raw().hex()


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def manifest(
        kind: ContributionClass = ContributionClass.EVALUATION, *,
        base_binding_digest: str | None = None,
        rights_scope: str = "PUBLIC_FIXTURE") -> RemoteWorkManifest:
    if kind is ContributionClass.ADAPTER_DELTA and base_binding_digest is None:
        base_binding_digest = BINDING
    return RemoteWorkManifest.create(
        manifest_id="work:fixture-001",
        retained_generation=GENERATION,
        source_release=SOURCE,
        capability_id="capability:fixture",
        seed=73,
        partition_id="partition:0001",
        resource_budget=ResourceBudget(
            max_examples=32, max_steps=8, max_seconds=60, max_bytes=1_000_000),
        model_identity=MODEL,
        topology_identity=TOPOLOGY,
        mlx_identity="mlx:0.32.4",
        rights_scope=rights_scope,
        contribution_class=kind,
        acceptance=AcceptanceContract(
            contract_digest=ACCEPTANCE,
            minimum_score=0.0 if kind is ContributionClass.ADAPTER_DELTA else 0.75,
            requires_retention=True),
        expires_at=2_000,
        replay_id="replay:fixture-001",
        base_binding_digest=base_binding_digest)


def worker() -> WorkerIdentity:
    return WorkerIdentity(
        worker_id="worker:public-fixture",
        public_key_hex=PUBLIC,
        environment=EnvironmentIdentity(
            hardware="Apple M3 Ultra", os="macOS-fixture",
            mlx_version="0.32.4", backend="metal", device_count=1))


def receipt(
        work: RemoteWorkManifest, *, score: float = 1.0,
        artifact: ContributionArtifact | None = None) -> WorkerReceipt:
    artifact = artifact or ContributionArtifact(
        artifact_type=work.expected_artifact_type,
        payload=b"public synthetic result",
        base_binding_digest=work.base_binding_digest,
        affected_parameter_ids=("adapter.0.A",)
        if work.contribution_class is ContributionClass.ADAPTER_DELTA else ())
    unsigned = WorkerReceipt.unsigned(
        manifest=work, worker=worker(), artifact=artifact,
        claimed_score=score,
        usage=ResourceUsage(
            examples=2, steps=1, seconds=3,
            payload_bytes=len(artifact.payload)),
        completed_at=1_500)
    return unsigned.with_signature(KEY.sign(unsigned.signing_bytes()).hex())


def remote_worker_receipt(
        manifest_wire: str, *, score: float = 1.0,
        artifact: ContributionArtifact | None = None) -> WorkerReceipt:
    """Synthetic remote worker: receives only frozen manifest bytes, never run custody."""
    return receipt(
        RemoteWorkManifest.from_canonical_json(manifest_wire),
        score=score, artifact=artifact)
