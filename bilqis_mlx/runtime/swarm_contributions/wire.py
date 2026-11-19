"""Canonical wire codecs for C14.4 remote manifests and signed receipts."""
from __future__ import annotations

from dataclasses import asdict
import json

from .contracts import (
    AcceptanceContract, ContributionClass, RemoteWorkManifest, ResourceBudget,
    canonical_bytes, invalid,
)
from .receipts import (
    ContributionArtifact, EnvironmentIdentity, ResourceUsage,
    WorkerIdentity, WorkerReceipt,
)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            invalid("BAMF_C14_WIRE_DUPLICATE_KEY")
        result[key] = value
    return result


def _load(value: str) -> dict:
    try:
        if type(value) is not str:
            invalid("BAMF_C14_WIRE_INVALID")
        payload = json.loads(value, object_pairs_hook=_unique_object)
        if type(payload) is not dict or canonical_bytes(payload).decode("utf-8") != value:
            invalid("BAMF_C14_WIRE_NONCANONICAL")
        return payload
    except (json.JSONDecodeError, UnicodeError, TypeError, ValueError):
        invalid("BAMF_C14_WIRE_INVALID")


def encode_manifest(manifest: RemoteWorkManifest) -> str:
    if type(manifest) is not RemoteWorkManifest:
        invalid("BAMF_C14_REMOTE_WORK_MANIFEST_INVALID")
    manifest.__post_init__()
    return canonical_bytes(manifest.canonical_payload()).decode("utf-8")


def decode_manifest(value: str) -> RemoteWorkManifest:
    raw = _load(value)
    try:
        budget = raw["resource_budget"]
        acceptance = raw["acceptance"]
        if type(budget) is not dict or type(acceptance) is not dict:
            invalid("BAMF_C14_REMOTE_WORK_MANIFEST_INVALID")
        manifest = RemoteWorkManifest.create(
            manifest_id=raw["manifest_id"],
            retained_generation=raw["retained_generation"],
            source_release=raw["source_release"],
            capability_id=raw["capability_id"],
            seed=raw["seed"],
            partition_id=raw["partition_id"],
            resource_budget=ResourceBudget(**budget),
            model_identity=raw["model_identity"],
            topology_identity=raw["topology_identity"],
            mlx_identity=raw["mlx_identity"],
            rights_scope=raw["rights_scope"],
            contribution_class=ContributionClass(raw["contribution_class"]),
            acceptance=AcceptanceContract(**acceptance),
            expires_at=raw["expires_at"],
            replay_id=raw["replay_id"],
            base_binding_digest=raw["base_binding_digest"],
        )
        if manifest.canonical_payload() != raw:
            invalid("BAMF_C14_REMOTE_WORK_MANIFEST_INVALID")
        return manifest
    except (KeyError, TypeError, ValueError):
        invalid("BAMF_C14_REMOTE_WORK_MANIFEST_INVALID")


def _receipt_payload(receipt: WorkerReceipt) -> dict:
    receipt.__post_init__()
    return {
        "schema_version": receipt.schema_version,
        "manifest_digest": receipt.manifest_digest,
        "worker": {
            "worker_id": receipt.worker.worker_id,
            "public_key_hex": receipt.worker.public_key_hex,
            "environment": asdict(receipt.worker.environment),
            "schema_version": receipt.worker.schema_version,
        },
        "artifact": {
            "artifact_type": receipt.artifact.artifact_type,
            "payload_hex": receipt.artifact.payload.hex(),
            "base_binding_digest": receipt.artifact.base_binding_digest,
            "affected_parameter_ids": list(receipt.artifact.affected_parameter_ids),
            "schema_version": receipt.artifact.schema_version,
        },
        "claimed_score": receipt.claimed_score,
        "usage": asdict(receipt.usage),
        "completed_at": receipt.completed_at,
        "signature_hex": receipt.signature_hex,
    }


def encode_receipt(receipt: WorkerReceipt) -> str:
    if type(receipt) is not WorkerReceipt:
        invalid("BAMF_C14_WORKER_RECEIPT_INVALID")
    return canonical_bytes(_receipt_payload(receipt)).decode("utf-8")


def decode_receipt(value: str) -> WorkerReceipt:
    raw = _load(value)
    try:
        worker = raw["worker"]
        environment = worker["environment"]
        artifact = raw["artifact"]
        usage = raw["usage"]
        if not all(type(item) is dict for item in (worker, environment, artifact, usage)):
            invalid("BAMF_C14_WORKER_RECEIPT_INVALID")
        result = WorkerReceipt(
            raw["manifest_digest"],
            WorkerIdentity(
                worker["worker_id"], worker["public_key_hex"],
                EnvironmentIdentity(**environment)),
            ContributionArtifact(
                artifact["artifact_type"], bytes.fromhex(artifact["payload_hex"]),
                artifact["base_binding_digest"],
                tuple(artifact["affected_parameter_ids"])),
            raw["claimed_score"],
            ResourceUsage(**{
                key: usage[key]
                for key in ("examples", "steps", "seconds", "payload_bytes")}),
            raw["completed_at"], raw["signature_hex"],
        )
        if _receipt_payload(result) != raw:
            invalid("BAMF_C14_WORKER_RECEIPT_INVALID")
        return result
    except (KeyError, TypeError, ValueError):
        invalid("BAMF_C14_WORKER_RECEIPT_INVALID")
