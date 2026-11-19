"""C10.1 append-only Akasha projection intents and idempotent SQLite outbox.

Transport is at-least-once; stable event IDs permit semantic deduplication
at the eventual Akasha receiver. C10.2 owns visibility/redaction policy.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from contextlib import contextmanager
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from pathlib import Path
import re
import sqlite3

from ...errors import ErrorBus, SCHOOL


AKASHA_EVENT_SCHEMA = "bilqis.c10.akasha-event/v1"
AKASHA_PROJECTION_SCHEMA = "bilqis.c10.akasha-projection/v1"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_DELIVERY_STATUSES = frozenset({"FAILED", "DELIVERED"})


def _invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.BAMF_AKASHA.INVALID, reason=reason)


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical(value: object) -> str:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError):
        _invalid("BAMF_C10_PAYLOAD_NOT_CANONICAL")


def _sha(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value))


def _name(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _time(value: object) -> bool:
    return type(value) is int and value >= 0


def _unknown_time_allowed(kind, payload: dict) -> bool:
    """Only accepted production-owner envelopes may lack source-owned clocks."""
    return (
        (kind in OWNER_FIXTURE_KINDS and payload.get("verification_mode") is None)
        or (kind is AkashaEventKind.FACTORY_RELEASE
            and payload.get("owner_event_type") is not None)
        or (kind is AkashaEventKind.MOTIF_CANDIDATE
            and payload.get("transition_sha256") is not None)
        or (kind is AkashaEventKind.TEACHER_VISIT
            and payload.get("visit_id") is not None)
    )


def _event_times(kind, payload: dict, values) -> bool:
    """Preserve legacy timed contracts; owner-backed unknown time is all-or-none."""
    values = tuple(values)
    if all(_time(value) for value in values):
        return True
    return _unknown_time_allowed(kind, payload) and all(value is None for value in values)


class AkashaEventKind(str, Enum):
    MATERIALIZATION = "MATERIALIZATION"
    BANK_ALLOCATION = "BANK_ALLOCATION"
    PLASTICITY_EPOCH = "PLASTICITY_EPOCH"
    PACKAGE_EXPORT = "PACKAGE_EXPORT"
    TEACHER_VISIT = "TEACHER_VISIT"
    FACTORY_RELEASE = "FACTORY_RELEASE"
    CAPABILITY_OUTCOME = "CAPABILITY_OUTCOME"
    SOURCE_CORRECTION = "SOURCE_CORRECTION"
    REVALIDATION = "REVALIDATION"
    REQUALIFICATION = "REQUALIFICATION"
    CAPABILITY_GRADUATION = "CAPABILITY_GRADUATION"
    MOTIF_CANDIDATE = "MOTIF_CANDIDATE"
    PROCESS_FAULT = "PROCESS_FAULT"
    CHECKPOINT_PUBLICATION = "CHECKPOINT_PUBLICATION"


NATIVE_EVENT_KINDS = MappingProxyType({
    'SCHOOL_TEACHER_VISIT_COMMITTED': AkashaEventKind.TEACHER_VISIT,
    'SCHOOL_FACTORY_RELEASE_MIGRATED': AkashaEventKind.FACTORY_RELEASE,
    'SCHOOL_CAPABILITY_BEST_COMMITTED': AkashaEventKind.CAPABILITY_OUTCOME,
})


OWNER_FIXTURE_KINDS = (AkashaEventKind.BANK_ALLOCATION, AkashaEventKind.PLASTICITY_EPOCH, AkashaEventKind.PACKAGE_EXPORT)

_OWNER_FIXTURE_FIELDS = frozenset({
    "owner_source_event_id", "producer_id", "artifact_schema",
    "artifact_sha256", "verification_mode",
})
_PRODUCTION_FIELDS = MappingProxyType({
    AkashaEventKind.BANK_ALLOCATION: frozenset({
        "run_id", "generation", "transition_kind", "feature_sha256",
        "factory_release_sha256", "admission_receipt_sha256",
    }),
    AkashaEventKind.PLASTICITY_EPOCH: frozenset({
        "run_id", "generation", "optimizer_step", "mode",
        "parent_policy_sha256", "policy_sha256",
        "parent_acceptance_receipt_sha256", "admission_receipt_sha256",
    }),
    AkashaEventKind.PACKAGE_EXPORT: frozenset({
        "package_digest", "generation_id", "semantic_release",
        "source_owner", "clearance_sha256", "rights_epoch",
        "correction_generation",
    }),
})
_FACTORY_ACCEPTANCE_FIELDS = frozenset({
    "run_id", "generation", "owner_event_type",
    "predecessor_factory_release_sha256", "factory_release_sha256",
    "transition_sha256", "admission_receipt_sha256",
})
_MOTIF_ACCEPTANCE_FIELDS = frozenset({
    "run_id", "generation", "motif_candidate_sha256",
    "approved_context_sha256", "candidate_allocation_sha256",
    "transition_sha256", "added_pages", "admission_receipt_sha256",
})
_TEACHER_ACCEPTANCE_FIELDS = frozenset({
    "run_id", "generation", "visit_id", "accepted_manifest_sha256",
    "teacher_identity", "student_sha256", "capability_id", "policy_key",
    "admission_receipt_sha256",
})


_REQUIRED_FIELDS = MappingProxyType({
    **{kind: _OWNER_FIXTURE_FIELDS
       for kind in OWNER_FIXTURE_KINDS},
    **{kind: frozenset({
        "native_event_id", "native_event_digest", "run_id", "generation",
        "native_event_type"})
       for kind in (
           AkashaEventKind.TEACHER_VISIT, AkashaEventKind.FACTORY_RELEASE,
           AkashaEventKind.CAPABILITY_OUTCOME)},
    AkashaEventKind.SOURCE_CORRECTION: frozenset({
        "correction_event_id", "source_owner", "dependency_key",
        "old_digest", "new_digest"}),
    AkashaEventKind.REVALIDATION: frozenset({
        "artifact_id", "old_digest", "new_digest", "eligible"}),
    AkashaEventKind.REQUALIFICATION: frozenset({
        "capability_id", "retained_generation_sha256", "status"}),
    AkashaEventKind.CAPABILITY_GRADUATION: frozenset({
        "capability_id", "generation_sha256", "assessment_receipt_sha256"}),
    AkashaEventKind.MOTIF_CANDIDATE: frozenset({
        "motif_id", "source_refs", "eligibility_digest"}),
    AkashaEventKind.PROCESS_FAULT: frozenset({
        "fault_id", "original_source_event_id", "correction_event_id",
        "remediation_id", "derived_path"}),
    AkashaEventKind.CHECKPOINT_PUBLICATION: frozenset({
        "checkpoint_digest", "generation_sha256", "manifest_digest"}),
    AkashaEventKind.MATERIALIZATION: frozenset({
        "graph", "owner", "canonical_rdf_sha256",
        "materialization_receipt_sha256", "projection_version",
        "coverage_status", "semantic_coverage_sha256",
        "importer_implementation_sha256", "smoke_suite_sha256",
    }),
})
_DIGEST_FIELDS = frozenset({
    "native_event_digest", "artifact_sha256",
    "old_digest", "new_digest", "retained_generation_sha256",
    "generation_sha256", "assessment_receipt_sha256",
    "eligibility_digest", "checkpoint_digest", "manifest_digest",
    "feature_sha256", "factory_release_sha256", "admission_receipt_sha256",
    "parent_policy_sha256", "policy_sha256", "parent_acceptance_receipt_sha256",
    "package_digest",
    "semantic_release", "clearance_sha256",
    "canonical_rdf_sha256", "materialization_receipt_sha256",
    "semantic_coverage_sha256", "importer_implementation_sha256",
    "smoke_suite_sha256",
    "predecessor_factory_release_sha256", "transition_sha256",
    "motif_candidate_sha256", "approved_context_sha256",
    "candidate_allocation_sha256",
})
_NONEMPTY_LIST_FIELDS = frozenset({"source_refs", "derived_path"})


def _payload_form(kind, payload):
    production_owner = kind in OWNER_FIXTURE_KINDS and payload.get("verification_mode") is None
    accepted_factory = (
        kind is AkashaEventKind.FACTORY_RELEASE
        and payload.get("owner_event_type") is not None)
    accepted_motif = (
        kind is AkashaEventKind.MOTIF_CANDIDATE
        and payload.get("transition_sha256") is not None)
    accepted_teacher = (
        kind is AkashaEventKind.TEACHER_VISIT
        and payload.get("visit_id") is not None)
    required = (
        _PRODUCTION_FIELDS[kind] if production_owner
        else _FACTORY_ACCEPTANCE_FIELDS if accepted_factory
        else _MOTIF_ACCEPTANCE_FIELDS if accepted_motif
        else _TEACHER_ACCEPTANCE_FIELDS if accepted_teacher
        else _REQUIRED_FIELDS[kind])
    return required, production_owner, accepted_factory, accepted_motif, accepted_teacher


def _requires_projection_binding(kind, payload) -> bool:
    _, production_owner, accepted_factory, accepted_motif, accepted_teacher = _payload_form(
        kind, payload)
    return production_owner or accepted_factory or accepted_motif or accepted_teacher


def _validate_required_payload(payload, required):
    if not required.issubset(payload):
        _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    for key in required:
        value = payload[key]
        if value is None or value == "" or value == []:
            _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
        if key in _DIGEST_FIELDS and not _sha(value):
            _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
        if (key in _NONEMPTY_LIST_FIELDS
                and (not isinstance(value, list)
                     or not value
                     or any(not _name(item) for item in value))):
            _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")


def _validate_production_owner_payload(kind, payload):
    if (kind in (AkashaEventKind.BANK_ALLOCATION, AkashaEventKind.PLASTICITY_EPOCH)
            and (not _name(payload["run_id"])
                 or type(payload["generation"]) is not int
                 or payload["generation"] < 1)):
        _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    if (kind is AkashaEventKind.BANK_ALLOCATION
            and payload["transition_kind"] != "PARAMETER_EXTENSION"):
        _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    if (kind is AkashaEventKind.PLASTICITY_EPOCH
            and (type(payload["optimizer_step"]) is not int
                 or payload["optimizer_step"] < 0
                 or not _name(payload["mode"]))):
        _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    if (kind is AkashaEventKind.PACKAGE_EXPORT
            and (not _name(payload["generation_id"])
                 or not _name(payload["source_owner"])
                 or type(payload["rights_epoch"]) is not int
                 or payload["rights_epoch"] < 0
                 or type(payload["correction_generation"]) is not int
                 or payload["correction_generation"] < 0)):
        _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")


def _payload_for(kind: AkashaEventKind, payload_json: str) -> dict:
    try:
        payload = json.loads(payload_json)
    except (TypeError, ValueError):
        _invalid("BAMF_C10_PAYLOAD_NOT_CANONICAL")
    if (not isinstance(payload, dict)
            or any(not isinstance(key, str) for key in payload)
            or payload_json != _canonical(payload)):
        _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    required, production_owner, accepted_factory, accepted_motif, accepted_teacher = _payload_form(
        kind, payload)
    _validate_required_payload(payload, required)
    if kind in OWNER_FIXTURE_KINDS and not production_owner:
        if (payload['verification_mode'] != 'DISPOSABLE_CONTRACT'
                or any(not _name(payload[key]) for key in ('owner_source_event_id', 'producer_id', 'artifact_schema'))):
            _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    if production_owner:
        _validate_production_owner_payload(kind, payload)
    if (kind in NATIVE_EVENT_KINDS.values()
            and not accepted_factory and not accepted_teacher):
        if (type(payload['generation']) is not int or payload['generation'] < 0
                or not _name(payload['run_id']) or not _sha(payload['native_event_id'])
                or not _name(payload['native_event_type'])
                or NATIVE_EVENT_KINDS.get(payload['native_event_type']) is not kind):
            _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    if accepted_factory:
        if (not _name(payload['run_id'])
                or type(payload['generation']) is not int or payload['generation'] < 1
                or payload['owner_event_type'] != 'BAMF_FACTORY_RELEASE_ADOPTION_COMMITTED'):
            _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    if accepted_motif:
        if (not _name(payload['run_id'])
                or type(payload['generation']) is not int or payload['generation'] < 1
                or type(payload['added_pages']) is not int
                or payload['added_pages'] not in (0, 1)):
            _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    if accepted_teacher:
        if (not _name(payload["run_id"])
                or type(payload["generation"]) is not int
                or payload["generation"] < 0
                or not _sha(payload["visit_id"])
                or not _sha(payload["accepted_manifest_sha256"])
                or not _sha(payload["teacher_identity"])
                or not _sha(payload["student_sha256"])
                or not _name(payload["capability_id"])
                or not _name(payload["policy_key"])):
            _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    if (kind is AkashaEventKind.REVALIDATION
            and type(payload["eligible"]) is not bool):
        _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    if (kind is AkashaEventKind.REQUALIFICATION
            and payload["status"] not in (
                "QUALIFIED", "REQUALIFICATION_REQUIRED")):
        _invalid("BAMF_C10_PROJECTION_FIELDS_INVALID")
    return payload
