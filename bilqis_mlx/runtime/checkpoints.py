"""Checkpoint custody, immutable generations and idempotent event delivery."""
from __future__ import annotations

import bilqis_mlx.curriculum.scheduler as _curriculum_scheduler
import bilqis_mlx.runtime.checkpoint_bundle as _checkpoint_bundle
import bilqis_mlx.runtime.checkpoint_outbox as _checkpoint_outbox
import bilqis_mlx.runtime.checkpoint_publication as _checkpoint_publication
import bilqis_mlx.runtime.checkpoint_recovery as _checkpoint_recovery
import bilqis_mlx.runtime.checkpoint_retention as _checkpoint_retention
import bilqis_mlx.runtime.state as _runtime_state
import bilqis_mlx.state_dag as _state_dag
import contextlib as _contextlib
import dataclasses as _dataclasses
import json as _json
import os as _os
import pathlib as _pathlib
import sys as _sys

from contextvars import ContextVar

_event_view = ContextVar("grade_a_event_view", default=None)
_ADVANCE_SOURCE_FIELDS = (
    "delivery_outbox", "generation", "model_bundle", "run_id", "school",
    "source_manifest_sha256", "teacher_source_sha256",
)


@_contextlib.contextmanager
def operator_view(callback):
    token = _event_view.set(callback)
    try:
        yield
    finally:
        _event_view.reset(token)


def _persist(run_dir: _pathlib.Path, receipt: dict):
    """Persist one logical generation through the immutable Merkle state DAG."""
    return _state_dag.persist(run_dir, receipt)


def _recover_orphaned_commit(run_dir: _pathlib.Path, latest: dict) -> dict:
    return _checkpoint_recovery.recover_orphaned_commit(
        run_dir, latest, verify_best_custody=_verify_best_custody,
        persist=_persist, reconcile_delivery_outbox=_reconcile_delivery_outbox,
        record_event=_record)


def _record(run_dir: _pathlib.Path, event: dict):
    path = run_dir / "events.jsonl"
    encoded = _runtime_state._canonical(event) + "\n"
    with path.open("a", encoding="utf-8") as stream:
        before = _os.fstat(stream.fileno())
        stream.write(encoded)
        stream.flush()
        _os.fsync(stream.fileno())
        after = _os.fstat(stream.fileno())
    from bilqis_mlx.runtime.priority_rejection_journal import note_journal_append
    note_journal_append(path, before, after, len(encoded.encode("utf-8")))
    if _event_view.get() is None:
        print(_json.dumps(event, sort_keys=True), flush=True)
    else:
        _notify_viewer(event)


def _notify_viewer(event: dict):
    """Send ephemeral operator telemetry without making it training evidence."""
    viewer = _event_view.get()
    if viewer is None:
        return
    try:
        viewer(event)
    except Exception as exc:
        print("DASHBOARD UNAVAILABLE: " + str(exc), file=_sys.stderr, flush=True)


def _bundle_pointer(run_dir: _pathlib.Path, name: str, parameters, optimizer, graph,
                    *, reserve_gib: float, model_topology=None):
    return _checkpoint_bundle.bundle_pointer(
        run_dir, name, parameters, optimizer, graph, reserve_gib=reserve_gib,
        model_topology=model_topology)


def _clean_staged_bundles(run_dir: _pathlib.Path) -> dict[str, tuple[str, ...]]:
    return _checkpoint_bundle.clean_staged_bundles(run_dir)


def _mentor_epoch_references(receipt):
    return _checkpoint_retention.mentor_epoch_references(receipt)


def _regression_recovery_checkpoint(receipt):
    return _checkpoint_retention.regression_recovery_checkpoint(receipt)


def _verify_frozen_soup_custody(run_dir, receipt):
    return _checkpoint_retention.verify_frozen_soup_custody(run_dir, receipt)


def _verify_best_custody(run_dir, receipt):
    return _checkpoint_retention.verify_best_custody(run_dir, receipt)


def _advance(run_dir, old: dict, school: _curriculum_scheduler.SchoolState, *,
             teacher=None, model_bundle=None, last_exam=None, result=None,
             frontier=None, persist=True):
    # One snapshot captures teacher learning, school progress and model pointer.
    if old.get("delivery_outbox") is not None:
        # A generation's event IDs cannot be inherited by a successor. First
        # prove this generation was durably committed, then reconcile the
        # original intent or fail before state mutation. Uncommitted event
        # intents must never be published on the strength of a transient dict.
        old_path = (_pathlib.Path(run_dir) / "states" /
                    f"{old['generation']:07d}.json")
        if old_path.is_symlink() or not old_path.is_file():
            raise ValueError("HUMAN_TRAINER_OUTBOX_ADVANCE_UNCOMMITTED_SOURCE")
        durable = _state_dag.read_generation_fields(
            run_dir, old["generation"], _ADVANCE_SOURCE_FIELDS)
        if not _ordinary_outbox_lineage(durable, durable.get("delivery_outbox")):
            durable = _state_dag.read_generation(run_dir, old["generation"])
        # Only *durable* outbox events have delivery authority. Transient
        # callers may carry a subsequently edited copy of a committed event;
        # requiring payload-object equality here mistakes a working copy for
        # its signed owner. Instead bind the ordered event IDs, run and
        # checkpoint to the immutable snapshot, then validate its original
        # exact payloads against the journal below. Never publish the caller's
        # potentially edited copy, and never lose/ignore an extra event ID.
        source_outbox = durable.get("delivery_outbox")
        candidate_outbox = old["delivery_outbox"]
        source_ids = (tuple(event.get("event_id") for event in source_outbox)
                      if isinstance(source_outbox, list) and
                      all(isinstance(event, dict) for event in source_outbox)
                      else None)
        candidate_ids = (tuple(event.get("event_id") for event in candidate_outbox)
                         if isinstance(candidate_outbox, list) and
                         all(isinstance(event, dict) for event in candidate_outbox)
                         else None)
        if (durable.get("run_id") != old.get("run_id") or
                durable.get("generation") != old.get("generation") or
                not source_ids or candidate_ids != source_ids or
                durable.get("model_bundle") != old.get("model_bundle") or
                durable.get("school", {}).get("current_student") !=
                old.get("school", {}).get("current_student") or
                durable.get("source_manifest_sha256") !=
                old.get("source_manifest_sha256") or
                durable.get("teacher_source_sha256") !=
                old.get("teacher_source_sha256")):
            raise ValueError("HUMAN_TRAINER_OUTBOX_ADVANCE_SOURCE_DRIFT")
        # Reconcile the *committed* owner, not the caller's proposed in-memory
        # next-generation metadata. A resume-time championship repair can
        # legitimately change unrelated fields before _advance is invoked;
        # using that transient dict would falsely fail signed v1->v2 lineage.
        _reconcile_delivery_outbox(run_dir, durable)
    record = dict(old)
    record.pop("delivery_outbox", None)
    record["generation"] = old["generation"] + 1
    record["school"] = _dataclasses.asdict(school)
    if teacher is not None:
        record["teacher"] = teacher
    if model_bundle is not None:
        record["model_bundle"] = model_bundle
    if last_exam is not None:
        record["last_exam"] = last_exam
        record.pop("fixed_frontier_exam", None)
    if result is not None:
        record["result"] = result
    if frontier is not None:
        record["capability_best"] = frontier
    if persist:
        record.pop("_pending_visit_events", None)
        if old.get("delivery_outbox") is not None:
            event = {"event": "SCHOOL_STATE_ADVANCED",
                     "generation": record["generation"],
                     "source_generation": old["generation"],
                     "student_sha256": school.current_student.sha256,
                     "optimizer_step": school.current_student.optimizer_step}
            record = _persist(run_dir, _with_delivery_outbox(record, (event,)))
            _reconcile_delivery_outbox(run_dir, record)
            return record
        return _persist(run_dir, record)
    return record


def _boundary_delivery_events(record, pending, roles, exam_event):
    return _checkpoint_outbox.boundary_delivery_events(
        record, pending, roles, exam_event)


def _with_delivery_outbox(record: dict, events) -> dict:
    return _checkpoint_outbox.with_delivery_outbox(record, events)


def _require_outbox_lineage(condition: bool) -> None:
    if not condition:
        raise ValueError("HUMAN_TRAINER_OUTBOX_LINEAGE_DRIFT")


def _ordinary_outbox_lineage(record: dict, outbox) -> bool:
    return _checkpoint_outbox.ordinary_outbox_lineage(record, outbox)


def _outbox_source_generation(run_dir: _pathlib.Path, record: dict, outbox: list):
    return _checkpoint_outbox._source_generation(run_dir, record, outbox)


def _expected_outbox_events(record: dict, outbox: list, source_generation: int):
    return _checkpoint_outbox._expected_events(record, outbox, source_generation)


def _observed_outbox_events(run_dir: _pathlib.Path, expected: dict):
    return _checkpoint_outbox._observed_events(run_dir, expected)


def _reconcile_delivery_outbox(
        run_dir: _pathlib.Path, record: dict, *, publish_missing: bool = True):
    return _checkpoint_outbox.reconcile_delivery_outbox(
        run_dir, record, publish_missing=publish_missing, record_event=_record)


def _publish_boundary(run_dir, record, pending, roles, *, exam_event=None):
    return _checkpoint_publication.publish_boundary(
        run_dir, record, pending, roles, exam_event=exam_event,
        boundary_events=_boundary_delivery_events, with_outbox=_with_delivery_outbox,
        reconcile_outbox=_reconcile_delivery_outbox,
        mentor_refs=_mentor_epoch_references,
        regression_ref=_regression_recovery_checkpoint,
        quarantine=_quarantine_newer_uncommitted_bundles, record_event=_record)


def _quarantine_newer_uncommitted_bundles(run_dir: _pathlib.Path, retained: set[str],
                                          current_optimizer_step: int) -> tuple[str, ...]:
    return _checkpoint_bundle.quarantine_newer_uncommitted_bundles(
        run_dir, retained, current_optimizer_step, record_event=_record)
