"""Shared contracts for authenticated BAMF -> Model Forensics projection."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.mission_control import (
    AuthorityClass, CoverageState, DataValue, RecordMeta, RunRef, ValueOrigin,
    ValueState,
)

from .event_stream import EventFamily


def invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID, reason=reason)


def canonical(value) -> bytes:
    return (json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ) + "\n").encode("utf-8")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def is_digest(value) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def data_value(value, units: str | None = None) -> DataValue:
    return DataValue(ValueState.PRESENT, ValueOrigin.SOURCE_AUTHORITATIVE, value, units)


def missing_value() -> DataValue:
    return DataValue(ValueState.MISSING, None, None)


def accepted_student_sha256(generation: "AuthenticatedGeneration") -> str:
    """Recover C03's accepted student identity without loading numerical state."""
    if generation.manifest["generation"] == 0:
        digest = generation.run_identity.get("initial_candidate_identity_sha256")
    else:
        from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage

        digest = restore_teacher_lineage(generation.teacher_state).student_sha256
    if not is_digest(digest):
        invalid("CONTROL_PLANE_NATIVE_STUDENT_IDENTITY_INVALID")
    return digest


@dataclass(frozen=True)
class AuthenticatedGeneration:
    manifest_sha256: str
    acceptance_sha256: str
    manifest: dict
    acceptance: dict
    run_identity: dict
    teacher_state: dict
    outbox: tuple[dict, ...]
    learning_health_state: dict | None = None


@dataclass(frozen=True)
class NativeProjectionMaterial:
    records: tuple
    events: tuple[tuple[EventFamily, object, str], ...]
    generation_manifests: tuple[str, ...]
    accepted_learning_health_by_manifest: dict | None = None


def run_ref(generation: AuthenticatedGeneration) -> RunRef:
    manifest = generation.manifest
    acceptance = generation.acceptance
    identity = generation.run_identity
    factory_release = acceptance.get(
        "factory_release_sha256", identity.get("factory_release_sha256"))
    semantic_release = manifest["provenance"].get("release_digest")
    topology_sha = manifest["topology"].get("digest")
    if not all(is_digest(value) for value in (
        factory_release, semantic_release, topology_sha,
    )):
        invalid("CONTROL_PLANE_NATIVE_HISTORY_RUN_REF_INVALID")
    return RunRef(
        manifest["run_id"], identity["run_identity_sha256"],
        manifest["generation"], generation.manifest_sha256,
        acceptance["candidate_identity_sha256"], factory_release,
        semantic_release, topology_sha,
    )


def materialized_at(native: dict, generation: int) -> int:
    """Use authenticated source time; never reinterpret a generation as Unix time."""
    del generation
    value = native.get("recorded_at")
    return value if type(value) is int and value > 0 else 0


def record_meta(
    record_id: str, run: RunRef, generation: AuthenticatedGeneration, *,
    native: dict | None = None, evidence_refs=(), receipt_refs=(),
    coverage: CoverageState = CoverageState.COMPLETE,
) -> RecordMeta:
    native = {} if native is None else native
    materialized = materialized_at(native, run.generation)
    observed = native.get("observed_at")
    as_of = native.get("effective_time")
    if type(observed) is not int or observed < 0 or observed > materialized:
        observed = None
    if type(as_of) is not int or as_of < 0 or as_of > materialized:
        as_of = None
    return RecordMeta(
        record_id=record_id, run=run, materialized_at=materialized,
        observed_at=observed, as_of=as_of, coverage=coverage,
        authority=AuthorityClass.DERIVED,
        source_refs=(f"bamf-manifest:{generation.manifest_sha256}",),
        evidence_refs=tuple(evidence_refs),
        receipt_refs=(f"bamf-acceptance:{generation.acceptance_sha256}",
                      *tuple(receipt_refs)),
    )


def derived_event_id(native_event_id: str, role: str) -> str:
    if not is_digest(native_event_id) or not isinstance(role, str) or not role:
        invalid("CONTROL_PLANE_NATIVE_EVENT_ID_INVALID")
    return sha(canonical({
        "schema": "bilqis.bamf.mission-control.native-derived-event/v1",
        "native_event_id": native_event_id, "role": role,
    }))


def native_outbox_event_id(
    run_id: str, generation: int, index: int, payload: dict,
) -> str:
    material = json.dumps(
        ["school-generation-event/v1", run_id, generation, index, payload],
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return sha(material)


__all__ = (
    "AuthenticatedGeneration", "NativeProjectionMaterial", "canonical",
    "accepted_student_sha256", "data_value", "derived_event_id", "invalid",
    "is_digest", "materialized_at",
    "missing_value", "native_outbox_event_id", "record_meta", "run_ref", "sha",
)
