"""Neural-inert championship governance migration and checkpoint provenance."""
from __future__ import annotations

import copy as _copy
import dataclasses as _dataclasses

import bilqis_mlx.learning.championship_identity as _learning_championship_identity
import bilqis_mlx.learning.epoch_championships as _learning_epoch_championships
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints
import bilqis_mlx.runtime.release_adoption as _runtime_release_adoption
import bilqis_mlx.runtime.state as _runtime_state

from .governance import _championship_identity, _historical_championship_authority

_CHECKPOINT_ORIGIN_CONFLICT = "CHAMPIONSHIP_CHECKPOINT_ORIGIN_PROVENANCE_CONFLICT"


def _merge_checkpoint_origins(updated, proven, ambiguous):
    origin_map = dict(updated.get("championship_checkpoint_origins", {}))
    changed = False
    for sha, grade in proven.items():
        existing = origin_map.get(sha)
        if existing is not None and existing != grade:
            raise ValueError(_CHECKPOINT_ORIGIN_CONFLICT)
        if existing is None:
            origin_map[sha] = grade
            changed = True
    if updated.get("championship_checkpoint_origins") != origin_map:
        updated["championship_checkpoint_origins"] = origin_map
    if ambiguous:
        if updated.get("championship_checkpoint_origin_ambiguities") != ambiguous:
            changed = True
        updated["championship_checkpoint_origin_ambiguities"] = ambiguous
    else:
        if "championship_checkpoint_origin_ambiguities" in updated:
            changed = True
        updated.pop("championship_checkpoint_origin_ambiguities", None)
    return origin_map, changed


def _bind_current_checkpoint_origin(updated, school, origin_map, ambiguous):
    changed = False
    current_origin = origin_map.get(school.current_student.sha256)
    if current_origin is not None:
        if updated.get("last_retained_update_grade") != current_origin:
            changed = True
        updated["last_retained_update_grade"] = current_origin
    elif school.current_student.sha256 in ambiguous:
        if "last_retained_update_grade" in updated:
            changed = True
        updated.pop("last_retained_update_grade", None)
    return changed


def _backfill_epoch_history(epoch, historical_settled, origin_map):
    updated = _copy.deepcopy(epoch)
    changed = False
    ledger = updated.setdefault("settled_matchups", {})
    if not isinstance(ledger, dict):
        raise ValueError("CHAMPIONSHIP_SETTLED_MATCH_LEDGER_INVALID")
    for key, settlement in historical_settled.items():
        if key not in ledger:
            ledger[key] = settlement
            changed = True
    for role in updated.get("active_roles", {}).values():
        if role.get("origin_grade") is not None:
            continue
        grade = origin_map.get(role.get("checkpoint", {}).get("sha256"))
        if grade is not None:
            role["origin_grade"] = grade
            changed = True
    return updated, changed


def _normalize_epoch_identity(epoch, identity, updated, school, program):
    epoch, reset = _learning_championship_identity.enforce_school_identity(
        epoch, identity, generation=updated["generation"] + 1,
        student=_dataclasses.asdict(school.current_student))
    origins_invalidated = False
    if not reset:
        epoch, origins_invalidated = _learning_epoch_championships.sanitize_role_origins(
            epoch, grades={
                grade.id: tuple(capability.id for capability in grade.capabilities)
                for grade in program.grades})
    return epoch, reset, origins_invalidated


def _persist_migration(
        run_dir, updated, school, identity, origin_map, ambiguous,
        historical_settled, duplicate_count, reset, origins_invalidated,
):
    record = _runtime_checkpoints._advance(run_dir, updated, school, persist=False)
    migration = {
        "event": "SCHOOL_CHAMPIONSHIP_GOVERNANCE_MIGRATED",
        "generation": record["generation"],
        "grade": school.grade,
        "student_sha256": school.current_student.sha256,
        "optimizer_step": school.current_student.optimizer_step,
        "championship_school_identity_sha256": identity["sha256"],
        "checkpoint_origins_proven": len(origin_map),
        "checkpoint_origins_ambiguous": len(ambiguous),
        "settled_matchups_backfilled": len(historical_settled),
        "duplicate_historical_settlements_ignored": duplicate_count,
        "holistic_authority_reset": reset,
        "invalid_origin_roles_archived": origins_invalidated,
        "actual_neural_updates": 0,
    }
    record = _runtime_checkpoints._persist(
        run_dir, _runtime_checkpoints._with_delivery_outbox(record, (migration,)))
    _runtime_checkpoints._reconcile_delivery_outbox(run_dir, record)
    return record


def _migrate_championship_governance(run_dir, receipt, course):
    """Neural-inert rev7 migration from durable run evidence."""
    identity = _championship_identity(receipt, course)
    proven, ambiguous, historical_settled, duplicate_count = (
        _historical_championship_authority(run_dir))
    updated = _copy.deepcopy(receipt)
    changed = updated.get("championship_school_identity") != identity
    updated["championship_school_identity"] = identity
    origin_map, origin_changed = _merge_checkpoint_origins(
        updated, proven, ambiguous)
    changed = changed or origin_changed

    program = _runtime_release_adoption._schedule_for_receipt(run_dir, updated, course)
    school = _runtime_state._state_from_json(updated["school"], program)
    changed = (
        _bind_current_checkpoint_origin(updated, school, origin_map, ambiguous)
        or changed)

    reset = False
    origins_invalidated = False
    epoch = updated.get("mentor_epoch")
    if epoch is not None:
        epoch, epoch_changed = _backfill_epoch_history(
            epoch, historical_settled, origin_map)
        epoch, reset, origins_invalidated = _normalize_epoch_identity(
            epoch, identity, updated, school, program)
        changed = changed or epoch_changed or reset or origins_invalidated
        updated["mentor_epoch"] = epoch

    if not changed:
        return receipt
    return _persist_migration(
        run_dir, updated, school, identity, origin_map, ambiguous,
        historical_settled, duplicate_count, reset, origins_invalidated)


def _bind_checkpoint_origin(receipt, checkpoint):
    """Attach the last proven retained-update grade to a newly sealed checkpoint."""
    grade = receipt.get("last_retained_update_grade")
    if grade is None:
        return receipt
    if not isinstance(grade, str) or not grade:
        raise ValueError("CHAMPIONSHIP_LAST_RETAINED_GRADE_INVALID")
    origins = dict(receipt.get("championship_checkpoint_origins", {}))
    existing = origins.get(checkpoint.sha256)
    if existing is not None and existing != grade:
        raise ValueError(_CHECKPOINT_ORIGIN_CONFLICT)
    origins[checkpoint.sha256] = grade
    return {**receipt, "championship_checkpoint_origins": origins}
