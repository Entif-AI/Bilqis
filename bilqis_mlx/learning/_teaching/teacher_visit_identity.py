"""C03-owned identity for one selected teacher visit.

The record names a visit; it is not an admission capability.  Production
authority still comes from the accepted B13 run and the C03 teacher state that
derives and records this identity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from collections.abc import Mapping

from .teacher_lineage_records import (
    SHA256_HEX_LENGTH, TeacherCustodyProjection, canonical, digest, invalid,
    valid_hex,
)

VISIT_IDENTITY_SCHEMA = "bilqis.bamf.c03-teacher-visit-identity/v1"
VISIT_RECEIPT_SCHEMA = "bilqis.bamf.c03-teacher-visit-receipt/v1"


def _name(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


@dataclass(frozen=True)
class TeacherVisitIdentity:
    run_identity_sha256: str
    run_seed: int
    generation: int
    accepted_manifest_sha256: str
    teacher_identity: str
    teacher_epoch: int
    student_sha256: str
    selection_seed: int
    cursor: str
    capability_id: str
    policy_key: str
    schema: str = VISIT_IDENTITY_SCHEMA

    def __post_init__(self) -> None:
        if (self.schema != VISIT_IDENTITY_SCHEMA
                or not valid_hex(self.run_identity_sha256, SHA256_HEX_LENGTH)
                or type(self.run_seed) is not int or self.run_seed < 0
                or type(self.generation) is not int or self.generation < 0
                or not valid_hex(self.accepted_manifest_sha256, SHA256_HEX_LENGTH)
                or not valid_hex(self.teacher_identity, SHA256_HEX_LENGTH)
                or type(self.teacher_epoch) is not int or self.teacher_epoch < 0
                or not valid_hex(self.student_sha256, SHA256_HEX_LENGTH)
                or type(self.selection_seed) is not int or self.selection_seed < 0
                or not all(_name(value) for value in (
                    self.cursor, self.capability_id, self.policy_key))):
            invalid("TEACHER_VISIT_IDENTITY_INVALID")

    @property
    def visit_id(self) -> str:
        return digest(asdict(self))

    def to_record(self) -> dict:
        return {**asdict(self), "visit_id": self.visit_id}

    @classmethod
    def from_record(cls, record: Mapping) -> "TeacherVisitIdentity":
        names = {
            "run_identity_sha256", "run_seed", "generation",
            "accepted_manifest_sha256", "teacher_identity", "teacher_epoch",
            "student_sha256", "selection_seed", "cursor", "capability_id",
            "policy_key", "schema",
        }
        if not isinstance(record, Mapping) or set(record) != names | {"visit_id"}:
            invalid("TEACHER_VISIT_IDENTITY_INVALID")
        identity = cls(**{name: record[name] for name in names})
        if record["visit_id"] != identity.visit_id:
            invalid("TEACHER_VISIT_IDENTITY_INVALID")
        return identity


def derive_teacher_visit_identity(
        teacher_state: Mapping, *, run_identity_sha256: str, run_seed: int,
        generation: int, accepted_manifest_sha256: str, capability_id: str,
        policy_key: str) -> TeacherVisitIdentity:
    """Derive the true visit name from B13 run lineage and persisted C03 state."""
    from .teacher_lineage import restore_teacher_lineage

    epoch = restore_teacher_lineage(teacher_state)
    return TeacherVisitIdentity(
        run_identity_sha256, run_seed, generation, accepted_manifest_sha256,
        teacher_state["teacher_identity"], teacher_state["teacher_epoch"],
        epoch.student_sha256, teacher_state["next_seed"],
        teacher_state["cursor"], capability_id, policy_key)


def record_teacher_visit_identity(
        teacher_state: Mapping,
        identity: TeacherVisitIdentity) -> TeacherCustodyProjection:
    """Persist a visit only when it is exactly derivable from current C03 state."""
    if type(identity) is not TeacherVisitIdentity:
        invalid("TEACHER_VISIT_IDENTITY_REQUIRED")
    expected = derive_teacher_visit_identity(
        teacher_state,
        run_identity_sha256=identity.run_identity_sha256,
        run_seed=identity.run_seed, generation=identity.generation,
        accepted_manifest_sha256=identity.accepted_manifest_sha256,
        capability_id=identity.capability_id, policy_key=identity.policy_key)
    if expected != identity:
        invalid("TEACHER_VISIT_IDENTITY_DRIFT")
    state = dict(teacher_state)
    state["last_visit"] = identity.to_record()
    return TeacherCustodyProjection(
        state, state["teacher_identity"], state["teacher_epoch"])


def teacher_visit_receipt_sha256(identity: TeacherVisitIdentity) -> str:
    """Content identity of one source-issued C03 visit receipt."""
    if type(identity) is not TeacherVisitIdentity:
        invalid("TEACHER_VISIT_IDENTITY_REQUIRED")
    raw = canonical(identity.to_record()).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def record_teacher_visit_receipt(identity: TeacherVisitIdentity) -> str:
    """Persist immutable proof that C03 actually issued this exact visit."""
    digest_value = teacher_visit_receipt_sha256(identity)
    from bilqis_mlx.data_plane import data_plane

    raw = canonical(identity.to_record()).encode("utf-8")
    data_plane().put_object(digest_value, raw)
    return digest_value


def require_teacher_visit_receipt(identity: TeacherVisitIdentity) -> str:
    """Require the source-side C03 receipt for an exact visit identity."""
    digest_value = teacher_visit_receipt_sha256(identity)
    from bilqis_mlx.data_plane import data_plane

    expected = canonical(identity.to_record()).encode("utf-8")
    try:
        actual = data_plane().get_object(digest_value)
    except ValueError:
        invalid("TEACHER_VISIT_RECEIPT_MISSING")
    if actual != expected:
        invalid("TEACHER_VISIT_RECEIPT_DRIFT")
    return digest_value


def teacher_visit_receipt_record(identity: TeacherVisitIdentity) -> dict:
    """Portable C03 issuance receipt copied into accepted B13 custody."""
    return {
        "schema": VISIT_RECEIPT_SCHEMA,
        "visit_id": identity.visit_id,
        "identity_sha256": teacher_visit_receipt_sha256(identity),
    }


def validate_teacher_visit_receipt_record(
        identity: TeacherVisitIdentity, receipt: Mapping) -> str:
    """Verify one artifact-carried receipt against the exact C03 visit identity."""
    expected = teacher_visit_receipt_record(identity)
    if not isinstance(receipt, Mapping) or dict(receipt) != expected:
        invalid("TEACHER_VISIT_RECEIPT_DRIFT")
    return expected["identity_sha256"]


def record_teacher_visit_authority(
        projection: TeacherCustodyProjection,
        identity: TeacherVisitIdentity) -> TeacherCustodyProjection:
    """Issue the source receipt and bind its portable copy into C03 teacher state."""
    if (type(projection) is not TeacherCustodyProjection
            or projection.teacher_state.get("last_visit") != identity.to_record()):
        invalid("TEACHER_VISIT_CUSTODY_INVALID")
    record_teacher_visit_receipt(identity)
    state = dict(projection.teacher_state)
    state["last_visit_receipt"] = teacher_visit_receipt_record(identity)
    return TeacherCustodyProjection(
        state, projection.teacher_identity, projection.teacher_epoch)


__all__ = (
    "TeacherVisitIdentity", "VISIT_IDENTITY_SCHEMA", "VISIT_RECEIPT_SCHEMA",
    "derive_teacher_visit_identity", "record_teacher_visit_identity",
    "record_teacher_visit_authority", "record_teacher_visit_receipt",
    "require_teacher_visit_receipt", "teacher_visit_receipt_record",
    "teacher_visit_receipt_sha256", "validate_teacher_visit_receipt_record",
)
