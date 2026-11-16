"""C03 teacher-lineage projection for later atomic B13 custody consumption."""
from __future__ import annotations

from collections.abc import Mapping

from .teacher_lineage_records import (
    ADAPTATION_SCHEMA, HISTORICAL_REPLAY_HEAD, LINEAGE_SCHEMA, TEACHER_STATE_SCHEMA,
    SHA256_HEX_LENGTH, TeacherCustodyProjection, adaptation_authority_ref,
    adaptation_ref, canonical, digest, invalid, lineage_identity, student_ref,
    valid_hex,
)
from .teacher_vnext_replay import (
    TeacherEpoch, bind_teacher_successor, refresh_teacher_region,
)


def _lineage_payload(epoch: TeacherEpoch, *, adaptation: Mapping,
                     source_teacher_sha256: str) -> dict:
    prior = epoch.prior_teacher()
    current = epoch.teacher()
    return {
        "schema": LINEAGE_SCHEMA,
        "historical_replay": {"head": HISTORICAL_REPLAY_HEAD},
        "adaptation_authority": dict(adaptation),
        "student_sha256": epoch.student_sha256,
        "prior_region": epoch.prior_region,
        "current_region": epoch.current_region,
        "source_teacher_sha256": source_teacher_sha256,
        "prior_teacher_sha256": digest(prior),
        "current_teacher_sha256": digest(current),
        "prior_teacher": prior,
        "current_teacher": current,
    }


def _projection(epoch: TeacherEpoch, *, adaptation: Mapping,
                source_teacher_sha256: str, teacher_epoch: int,
                next_seed: int, cursor: str,
                last_visit: Mapping | None = None) -> TeacherCustodyProjection:
    if (type(teacher_epoch) is not int or teacher_epoch < 0
            or type(next_seed) is not int or next_seed < 0
            or not isinstance(cursor, str) or not cursor):
        invalid("TEACHER_CUSTODY_PROJECTION_INVALID")
    identity = lineage_identity(
        source_teacher_sha256, adaptation, epoch.student_sha256)
    state = {
        "schema": TEACHER_STATE_SCHEMA,
        "teacher_identity": identity,
        "teacher_epoch": teacher_epoch,
        "next_seed": next_seed,
        "cursor": cursor,
        "c03_lineage": _lineage_payload(
            epoch, adaptation=adaptation,
            source_teacher_sha256=source_teacher_sha256),
    }
    if last_visit is not None:
        from .teacher_visit_identity import TeacherVisitIdentity
        state["last_visit"] = TeacherVisitIdentity.from_record(last_visit).to_record()
    return TeacherCustodyProjection(state, identity, teacher_epoch)


def initialize_teacher_lineage(
        legacy_receipt: Mapping, new_student: Mapping, adaptation: Mapping, *,
        prior_region: str, next_seed: int, cursor: str) -> TeacherCustodyProjection:
    """Bind the historical teacher into the first BAMF student without importing weights."""
    if (not isinstance(legacy_receipt, Mapping)
            or not isinstance(legacy_receipt.get("teacher"), dict)
            or not isinstance(prior_region, str) or not prior_region):
        invalid("LEGACY_TEACHER_RECEIPT_INVALID")
    student = student_ref(new_student)
    authority = adaptation_ref(adaptation)
    teacher = legacy_receipt["teacher"]
    epoch = bind_teacher_successor(
        teacher, student,
        {"schema": "bilqis.bamf.teacher-binding/v1",
         "source_head": HISTORICAL_REPLAY_HEAD,
         "prior_region": prior_region})
    return _projection(
        epoch, adaptation=authority, source_teacher_sha256=digest(teacher),
        teacher_epoch=0, next_seed=next_seed, cursor=cursor)


def restore_teacher_lineage(
        teacher_state: Mapping, *, expected_adaptation: Mapping | None = None) -> TeacherEpoch:
    """Reconstruct exact TeacherEpoch while rejecting altered nested or outer custody."""
    expected_outer = {
        "schema", "teacher_identity", "teacher_epoch", "next_seed", "cursor", "c03_lineage",
    }
    priority_outer = {"priority_counter", "priority_last_selected"}
    actual_outer = set(teacher_state) if isinstance(teacher_state, Mapping) else set()
    if (not isinstance(teacher_state, Mapping)
            or actual_outer not in (
                expected_outer, expected_outer | {"last_visit"},
                expected_outer | priority_outer,
                expected_outer | priority_outer | {"last_visit"},
            )
            or teacher_state.get("schema") != TEACHER_STATE_SCHEMA
            or not valid_hex(teacher_state.get("teacher_identity"), SHA256_HEX_LENGTH)
            or type(teacher_state.get("teacher_epoch")) is not int
            or teacher_state["teacher_epoch"] < 0
            or type(teacher_state.get("next_seed")) is not int
            or teacher_state["next_seed"] < 0
            or not isinstance(teacher_state.get("cursor"), str)
            or not teacher_state["cursor"]):
        invalid("TEACHER_STATE_INVALID")
    if priority_outer <= actual_outer:
        counter = teacher_state["priority_counter"]
        selected = teacher_state["priority_last_selected"]
        if (type(counter) is not int or counter < 0 or not isinstance(selected, Mapping)
                or any(not isinstance(key, str) or not key or type(value) is not int
                       or not 0 < value <= counter for key, value in selected.items())):
            invalid("TEACHER_PRIORITY_ROTATION_INVALID")
    lineage = teacher_state["c03_lineage"]
    expected_lineage = {
        "schema", "historical_replay", "adaptation_authority", "student_sha256",
        "prior_region", "current_region", "source_teacher_sha256",
        "prior_teacher_sha256", "current_teacher_sha256",
        "prior_teacher", "current_teacher",
    }
    if (not isinstance(lineage, Mapping) or set(lineage) != expected_lineage
            or lineage.get("schema") != LINEAGE_SCHEMA
            or lineage.get("historical_replay") != {"head": HISTORICAL_REPLAY_HEAD}
            or not valid_hex(lineage.get("student_sha256"), SHA256_HEX_LENGTH)
            or not valid_hex(lineage.get("source_teacher_sha256"), SHA256_HEX_LENGTH)
            or not isinstance(lineage.get("prior_region"), str)
            or not isinstance(lineage.get("current_region"), str)
            or lineage.get("prior_region") == lineage.get("current_region")
            or not isinstance(lineage.get("prior_teacher"), dict)
            or not isinstance(lineage.get("current_teacher"), dict)
            or lineage.get("prior_teacher_sha256") != digest(lineage["prior_teacher"])
            or lineage.get("current_teacher_sha256") != digest(lineage["current_teacher"])):
        invalid("TEACHER_LINEAGE_INVALID")
    authority = adaptation_ref(lineage.get("adaptation_authority"))
    if expected_adaptation is not None and authority != adaptation_ref(expected_adaptation):
        invalid("ADAPTATION_AUTHORITY_DRIFT")
    identity = lineage_identity(
        lineage["source_teacher_sha256"], authority, lineage["student_sha256"])
    if identity != teacher_state["teacher_identity"]:
        invalid("TEACHER_LINEAGE_IDENTITY_DRIFT")
    if "last_visit" in teacher_state:
        from .teacher_visit_identity import TeacherVisitIdentity
        visit = TeacherVisitIdentity.from_record(teacher_state["last_visit"])
        if (visit.teacher_epoch > teacher_state["teacher_epoch"]
                or (visit.teacher_epoch == teacher_state["teacher_epoch"]
                    and (visit.teacher_identity != teacher_state["teacher_identity"]
                         or visit.student_sha256 != lineage["student_sha256"]))):
            invalid("TEACHER_VISIT_IDENTITY_DRIFT")
    return TeacherEpoch(
        lineage["prior_region"], lineage["current_region"], lineage["student_sha256"],
        HISTORICAL_REPLAY_HEAD, canonical(lineage["prior_teacher"]),
        canonical(lineage["current_teacher"]))


def priority_rotation_state(teacher_state: Mapping) -> tuple[int, dict[str, int]]:
    """Read C03's accepted grade-neutral fair-rotation clock."""
    restore_teacher_lineage(teacher_state)
    return (teacher_state.get("priority_counter", 0),
            dict(teacher_state.get("priority_last_selected", {})))


def advance_priority_rotation(teacher_state: Mapping, capability_id: str) -> dict:
    """Advance fairness only for one accepted C03 capability selection."""
    counter, selected = priority_rotation_state(teacher_state)
    if not isinstance(capability_id, str) or not capability_id:
        invalid("TEACHER_PRIORITY_ROTATION_INVALID")
    counter += 1
    selected[capability_id] = counter
    result = dict(teacher_state)
    result["priority_counter"] = counter
    result["priority_last_selected"] = dict(sorted(selected.items()))
    restore_teacher_lineage(result)
    return result


def bind_next_teacher_epoch(
        teacher_state: Mapping, new_student: Mapping, *,
        bank_identity: str, plasticity_identity: str) -> TeacherEpoch:
    """Reset checkpoint-local evidence for a changed retained student checkpoint."""
    previous = restore_teacher_lineage(teacher_state)
    student = student_ref(new_student)
    if student["student_sha256"] == previous.student_sha256:
        invalid("TEACHER_SUCCESSOR_REQUIRES_CHANGED_STUDENT")
    epoch = bind_teacher_successor(
        previous.teacher(), student,
        {"schema": "bilqis.bamf.teacher-binding/v1",
         "source_head": HISTORICAL_REPLAY_HEAD,
         "prior_region": previous.current_region})
    return refresh_teacher_region(
        epoch, bank_identity=bank_identity, plasticity_identity=plasticity_identity)


def advance_teacher_lineage(
        previous_state: Mapping, next_epoch: TeacherEpoch, *,
        next_seed: int, cursor: str) -> TeacherCustodyProjection:
    """Persist one accepted teacher/student epoch; rejected candidates keep prior state."""
    previous = restore_teacher_lineage(previous_state)
    lineage = previous_state["c03_lineage"]
    if (not isinstance(next_epoch, TeacherEpoch)
            or next_epoch.replay_head != HISTORICAL_REPLAY_HEAD
            or next_epoch.prior_region != previous.current_region
            or next_epoch.prior_teacher() != previous.teacher()
            or next_epoch.student_sha256 == previous.student_sha256):
        invalid("TEACHER_SUCCESSOR_EPOCH_INVALID")
    return _projection(
        next_epoch, adaptation=adaptation_ref(lineage["adaptation_authority"]),
        source_teacher_sha256=lineage["source_teacher_sha256"],
        teacher_epoch=previous_state["teacher_epoch"] + 1,
        next_seed=next_seed, cursor=cursor,
        last_visit=previous_state.get("last_visit"))


__all__ = (
    "ADAPTATION_SCHEMA", "HISTORICAL_REPLAY_HEAD", "LINEAGE_SCHEMA",
    "TeacherCustodyProjection", "adaptation_authority_ref", "advance_teacher_lineage",
    "advance_priority_rotation", "bind_next_teacher_epoch", "initialize_teacher_lineage",
    "priority_rotation_state", "restore_teacher_lineage",
)
