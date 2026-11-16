"""Boundary publication and retention cleanup for immutable generations."""
from __future__ import annotations

import bilqis_mlx.data_plane as _data_plane
import bilqis_mlx.learning.capability_frontier as _learning_capability_frontier
import bilqis_mlx.learning.grade_soup as _learning_grade_soup


def publish_boundary(run_dir, record, pending, roles, *, exam_event,
                     boundary_events, with_outbox, reconcile_outbox,
                     mentor_refs, regression_ref, quarantine, record_event):
    """Publish visits only after model and teacher are durably recoverable."""
    school = record["school"]
    active_grade = (exam_event["grade"] if exam_event is not None else
                    school["active_grades"][school["grade_index"]])
    if record.get("delivery_outbox") is not None:
        if pending or roles or exam_event is not None:
            expect = with_outbox(record, boundary_events(record, pending, roles, exam_event))
            if expect["delivery_outbox"] != record["delivery_outbox"]:
                raise ValueError("HUMAN_TRAINER_OUTBOX_BOUNDARY_ARGUMENT_DRIFT")
        reconcile_outbox(run_dir, record)
    else:
        for event in boundary_events(record, pending, roles, exam_event):
            record_event(run_dir, event)
    retained = _learning_capability_frontier.pinned(
        record.get("capability_best", {}), school["current_student"], school["champions"])
    if record.get("curriculum_parent"):
        retained |= _learning_capability_frontier.pinned({}, record["curriculum_parent"], {})
    for peak in record.get("whole_student_peaks", ()):
        retained |= _learning_capability_frontier.pinned({}, peak["checkpoint"], {})
    for source in mentor_refs(record):
        retained |= _learning_capability_frontier.pinned({}, source, {})
    retained |= _learning_capability_frontier.pinned(
        record.get("graduation_perfect", {}), school["current_student"], school["champions"])
    abandoned = regression_ref(record)
    if abandoned is not None:
        retained |= _learning_capability_frontier.pinned({}, abandoned, {})
    for item in record.get("historical_grade_champions", {}).values():
        retained |= _learning_capability_frontier.pinned({}, item, {})
    if record.get("legacy_frontier_pending_replay"):
        retained |= _learning_capability_frontier.pinned(
            record.get("historical_capability_best", {}), school["current_student"],
            school["champions"])
    quarantine(run_dir, retained, school["current_student"]["optimizer_step"])
    removed = _learning_capability_frontier.retire_bundles(run_dir, retained)
    if removed:
        record_event(run_dir, {"event": "SCHOOL_CHECKPOINTS_RETIRED", "grade": active_grade,
                               "generation": record["generation"], "count": len(removed),
                               "protected_count": len(retained)})
    retired_soups = _learning_grade_soup.retire_stale_soups(
        run_dir, _data_plane.live_grade_soups(record))
    if retired_soups:
        record_event(run_dir, {"event": "SCHOOL_OLD_GRADE_SOUPS_RETIRED",
                               "generation": record["generation"],
                               "grade": active_grade, "count": len(retired_soups)})
