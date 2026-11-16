"""Championship identity, historical authority, and receipt repair."""
from __future__ import annotations

import json as _json

import bilqis_mlx.learning.championship_identity as _learning_championship_identity
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints
import bilqis_mlx.runtime.release_adoption as _runtime_release_adoption
import bilqis_mlx.runtime.state as _runtime_state


def _championship_identity(receipt, course):
    return _learning_championship_identity.build_school_identity(
        course_sha256=(receipt.get("factory_admission_v2") or {}).get(
            "curriculum_sha256", course.digest()),
        semantic_graph_sha256=receipt["semantic_graph_sha256"],
        parameter_shapes=receipt["parameter_shapes"],
        factory_release_sha256=receipt["factory_release_sha256"])


def _live_championship_identity(receipt, course, graph, parameters):
    return _learning_championship_identity.build_school_identity(
        course_sha256=(receipt.get("factory_admission_v2") or {}).get(
            "curriculum_sha256", course.digest()),
        semantic_graph_sha256=_runtime_state._fingerprint(graph),
        parameter_shapes={name: list(value.shape) for name, value in parameters.items()},
        factory_release_sha256=receipt["factory_release_sha256"])


def _championship_pair_key(capability, left_sha256, right_sha256):
    return capability + "|" + "|".join(sorted((left_sha256, right_sha256)))


def _historical_championship_authority(run_dir):
    """Recover immutable matchup and checkpoint-origin facts from durable events."""
    origins = {}
    settled = {}
    duplicate_settlements = 0
    path = run_dir / "events.jsonl"
    if not path.is_file():
        return {}, {}, {}, 0
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            event = _json.loads(line)
            if (event.get("event") == "SCHOOL_TEACHER_VISIT_COMMITTED" and
                    type(event.get("retained_optimizer_updates")) is int and
                    event["retained_optimizer_updates"] > 0 and
                    isinstance(event.get("recovered_at_student_sha256"), str) and
                    isinstance(event.get("grade"), str) and event["grade"]):
                origins.setdefault(event["recovered_at_student_sha256"], set()).add(
                    event["grade"])
            epoch = event.get("championship_epoch")
            if not isinstance(epoch, dict):
                continue
            for decision in epoch.get("cross_origin_decisions", ()):
                if (not isinstance(decision, dict) or
                        decision.get("decision") not in ("TITLE_WON", "TITLE_DEFENDED")):
                    continue
                capability = decision.get("capability")
                incumbent = decision.get("incumbent_sha256")
                challenger = decision.get("challenger_sha256")
                if not all(isinstance(value, str) and value for value in
                           (capability, incumbent, challenger)):
                    raise ValueError("CHAMPIONSHIP_HISTORICAL_SETTLEMENT_INVALID")
                key = _championship_pair_key(capability, incumbent, challenger)
                record = {**decision,
                          "source_generation": event.get("generation"),
                          "historical_backfill": True}
                if key in settled:
                    duplicate_settlements += 1
                else:
                    settled[key] = record
    proven = {sha: next(iter(grades)) for sha, grades in origins.items()
              if len(grades) == 1}
    ambiguous = {sha: sorted(grades) for sha, grades in origins.items()
                 if len(grades) > 1}
    return proven, ambiguous, settled, duplicate_settlements


def _is_profile_revision_epoch_history_artifact(entry):
    return entry == {
        "kind": "profile-revision-school-identity-reset",
        "event": True,
    }


def _without_profile_revision_epoch_history_artifact(receipt):
    """Remove only the malformed administrative receipt emitted by 413239a.

    `championship_epoch_history` is typed mentor-epoch history.  One short-lived
    profile-revision producer incorrectly appended this non-epoch marker there.
    Preserve every real epoch and every other unknown value so unrelated drift
    still fails closed at its normal verifier.
    """
    history = list(receipt.get("championship_epoch_history", ()))
    cleaned = [
        entry for entry in history
        if not _is_profile_revision_epoch_history_artifact(entry)
    ]
    removed = len(history) - len(cleaned)
    if not removed:
        return receipt, 0
    return {**receipt, "championship_epoch_history": cleaned}, removed


def _repair_profile_revision_epoch_history(run_dir, receipt, course):
    """Persist the exact malformed-history cleanup before custody verification."""
    repaired, removed = _without_profile_revision_epoch_history_artifact(receipt)
    if not removed:
        return receipt
    program = _runtime_release_adoption._schedule_for_receipt(run_dir, repaired, course)
    school = _runtime_state._state_from_json(repaired["school"], program)
    record = _runtime_checkpoints._advance(run_dir, repaired, school, persist=False)
    event = {
        "event": "SCHOOL_PROFILE_REVISION_EPOCH_HISTORY_REPAIRED",
        "generation": record["generation"],
        "grade": school.grade,
        "removed_malformed_entries": removed,
        "student_sha256": school.current_student.sha256,
        "optimizer_step": school.current_student.optimizer_step,
        "actual_neural_updates": 0,
        "model_and_own_adamw_unchanged": True,
    }
    record = _runtime_checkpoints._persist(run_dir, _runtime_checkpoints._with_delivery_outbox(record, (event,)))
    _runtime_checkpoints._reconcile_delivery_outbox(run_dir, record)
    return record
