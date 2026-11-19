"""Governed immutable-receipt ingress into the existing C10 projection plane."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json

from .akasha_outbox import AkashaEvent, AkashaEventKind
from .bamf_projection import (
    BamfProjectionEvent,
    ProjectionDomainContract,
    ProjectionReceipt,
    project_generation_outbox,
)
from ..errors import ErrorBus, SCHOOL


def _invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.BAMF_AKASHA.INVALID, reason=reason)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _timestamp(value: object) -> int:
    if not isinstance(value, str):
        _invalid("BAMF_C10_MATERIALIZATION_RECEIPT_INVALID")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _invalid("BAMF_C10_MATERIALIZATION_RECEIPT_INVALID")
    if parsed.tzinfo is None:
        _invalid("BAMF_C10_MATERIALIZATION_RECEIPT_INVALID")
    return int(parsed.timestamp())


def _materialization_receipt(receipt_bytes: bytes) -> dict:
    """Pin the source owner's versioned envelope without importing Falkor tooling."""
    try:
        receipt = json.loads(receipt_bytes)
    except (TypeError, ValueError):
        _invalid("BAMF_C10_MATERIALIZATION_RECEIPT_INVALID")
    required = {
        "schema", "version", "status", "timestamp", "graph", "owner",
        "canonical_rdf_sha256", "projection_version", "coverage_status",
        "semantic_coverage", "importer", "smoke_suite",
    }
    if (not isinstance(receipt, dict)
            or not required.issubset(receipt)
            or receipt["schema"] != "bilqis.skos.materialization/v1"
            or receipt["version"] != "1.0.0"
            or receipt["projection_version"] != "1.0.0"
            or receipt["status"] not in {"complete", "incomplete"}
            or not isinstance(receipt["graph"], str) or not receipt["graph"]
            or not isinstance(receipt["owner"], str) or not receipt["owner"]):
        _invalid("BAMF_C10_MATERIALIZATION_RECEIPT_INVALID")
    digests = (
        receipt["canonical_rdf_sha256"],
        receipt.get("semantic_coverage", {}).get("sha256"),
        receipt.get("importer", {}).get("implementation_sha256"),
        receipt.get("smoke_suite", {}).get("suite_sha256"),
    )
    if any(not isinstance(value, str) or len(value) != len(hashlib.sha256().hexdigest())
           or any(character not in "0123456789abcdef" for character in value)
           for value in digests):
        _invalid("BAMF_C10_MATERIALIZATION_RECEIPT_INVALID")
    if (receipt.get("semantic_coverage", {}).get("ref") != "coverage.json"
            or receipt.get("importer", {}).get("version") != "2.0.0"
            or receipt.get("smoke_suite", {}).get("suite_version") != "1.0.0"
            or receipt.get("smoke_suite", {}).get("passed") is not True):
        _invalid("BAMF_C10_MATERIALIZATION_RECEIPT_INVALID")
    _timestamp(receipt["timestamp"])
    return receipt


def materialization_event_from_receipt(receipt_bytes: bytes) -> AkashaEvent:
    """Project one exact #78 materialization receipt without owning its semantics."""
    if not isinstance(receipt_bytes, bytes):
        _invalid("BAMF_C10_MATERIALIZATION_RECEIPT_INVALID")
    receipt = _materialization_receipt(receipt_bytes)
    if receipt["status"] != "complete":
        _invalid("BAMF_C10_MATERIALIZATION_RECEIPT_INCOMPLETE")
    source_receipt_sha256 = _sha256(receipt_bytes)
    timestamp = _timestamp(receipt["timestamp"])
    payload = {
        "graph": receipt["graph"],
        "owner": receipt["owner"],
        "canonical_rdf_sha256": receipt["canonical_rdf_sha256"],
        "materialization_receipt_sha256": source_receipt_sha256,
        "projection_version": receipt["projection_version"],
        "coverage_status": receipt["coverage_status"],
        "semantic_coverage_sha256": receipt["semantic_coverage"]["sha256"],
        "importer_implementation_sha256": receipt["importer"]["implementation_sha256"],
        "smoke_suite_sha256": receipt["smoke_suite"]["suite_sha256"],
    }
    return AkashaEvent.from_payload(
        kind=AkashaEventKind.MATERIALIZATION,
        subject_id=f"semantic-materialization:{receipt['owner']}:{receipt['graph']}",
        source_receipt_sha256=source_receipt_sha256,
        payload=payload,
        source_time=timestamp,
        effective_time=timestamp,
        observed_at=timestamp,
        recorded_at=timestamp,
    )


def rebuild_immutable_events(
    events: tuple[AkashaEvent, ...],
    domain: ProjectionDomainContract,
) -> ProjectionReceipt:
    """Rebuild a disposable C10 projection from immutable event envelopes."""
    if (not isinstance(events, tuple)
            or any(not isinstance(event, AkashaEvent) for event in events)
            or not isinstance(domain, ProjectionDomainContract)):
        _invalid("BAMF_C10_GOVERNED_REBUILD_ARGUMENT_INVALID")
    bound = tuple(BamfProjectionEvent(
        event=event,
        source_id=domain.source_id,
        release_digest=domain.release_digest,
        model_digest=domain.model_digest,
        evaluator_digest=domain.evaluator_digest,
        rights_digest=domain.rights_digest,
        as_of=domain.as_of,
    ) for event in events)
    return project_generation_outbox(bound, domain)


__all__ = ("materialization_event_from_receipt", "rebuild_immutable_events")
