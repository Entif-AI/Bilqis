"""Read-only School50 adapter for the legacy Grade A and future school events.

The six panels use a grade-neutral telemetry contract. This module does not
score exams, influence teacher rewards, or touch neural state and checkpoints.
"""
from __future__ import annotations

import json
import os
from collections import deque
from pathlib import Path

from bilqis_mlx.presentation.school_telemetry import SchoolTelemetry, LETTER_TABLES
from bilqis_mlx.presentation.progression_projection import GraduationProjection
from bilqis_mlx.profiles.catalog import displayed_numeric_maximum
from bilqis_mlx.runtime.disk import headroom_snapshot
from bilqis_mlx.runtime.bamf_first_student import (
    load_bamf_foundation_dashboard_projection,
)
from bilqis_mlx.state_dag import read_current
from bilqis_mlx.source import AUDITED_PARENT
from ..compatibility.historical_live_release import historical_rubric_description
from bilqis_mlx.presentation.spiral_dashboard import Dashboard


def _bamf_foundation_dashboard_state(run_dir: Path):
    projection = load_bamf_foundation_dashboard_projection(run_dir)
    if projection is None:
        return None
    return {
        "generation": 0,
        "factory_release_sha256": projection.factory_release_sha256,
        "teacher": {"events": projection.teacher_events},
        "result": projection.last_run_status,
        "school": {
            "current_student": {
                "optimizer_step": projection.optimizer_step,
            },
            "active_grades": list(projection.active_grades),
            "grade_index": projection.active_grades.index(projection.current_grade),
            "visits": projection.grade_visits,
            "stage": projection.stage,
        },
    }


def _bamf_accepted_dashboard_state(run_dir: Path):
    pointer = run_dir / "bamf-state.json"
    if not pointer.exists() and not pointer.is_symlink():
        return None
    from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
    from bilqis_mlx.runtime.admission import _read_executable_factory_release_artifact
    student, _manifest = load_bamf_generation_authority(pointer)
    if student.generation == 0:
        return None
    release = _read_executable_factory_release_artifact(run_dir, {
        "factory_release_sha256": student.run_identity.factory_release_sha256,
        "factory_release_file": (
            "factory-releases/" + student.run_identity.factory_release_sha256 + ".json"),
    })
    active = [grade.grade_id for grade in release.execution_plan.grades]
    latest_capability = next((
        event.get("capability") for event in reversed(student.outbox)
        if isinstance(event, dict) and isinstance(event.get("capability"), str)
    ), None)
    current_grade = (
        release.execution_plan.capability_map[latest_capability].grade_id
        if latest_capability in release.execution_plan.capability_map
        else active[0])
    teacher = student.teacher_state
    return {
        "generation": student.generation,
        "factory_release_sha256": release.release_sha256,
        "teacher": {"events": teacher.get("teacher_epoch", 0)},
        "result": "PERSISTENT_BAMF_ACCEPTED",
        "school": {
            "current_student": {
                "optimizer_step": student.retained_state.optimizer_step,
            },
            "active_grades": active,
            "grade_index": active.index(current_grade),
            "visits": teacher.get("teacher_epoch", student.generation),
            "stage": "PERSISTENT_BAMF",
        },
    }


def _dashboard_state(run_dir: Path):
    state_path = run_dir / "state.json"
    bamf_pointer = run_dir / "bamf-state.json"
    if bamf_pointer.exists() or bamf_pointer.is_symlink():
        state = _bamf_accepted_dashboard_state(run_dir)
        if state is None:
            state = _bamf_foundation_dashboard_state(run_dir)
    else:
        state = read_current(run_dir) if state_path.exists() else None
    school = state["school"] if state else {}
    active = school.get("active_grades", ())
    grade_index = school.get("grade_index", 0)
    current_grade = active[grade_index] if 0 <= grade_index < len(active) else "NOT_ADMITTED"
    return state_path, state, school, active, current_grade


def _initialize_board(board: Dashboard, run_dir: Path, state, school, active,
                      current_grade: str) -> tuple[int, str]:
    step = school.get(
        "current_student", {}).get("optimizer_step", AUDITED_PARENT.optimizer_step)
    phase = school.get("stage", "READY_FOR_HUMAN_START")
    board.run_name = run_dir.name
    board.mode = "READ-ONLY"
    board.push("state", {
        "mastery": {"phase": phase, "prefix": current_grade, "position": 0},
        "optimizer_step": step,
        "grade_visits": school.get("visits", 0),
        "teacher": state.get("teacher") if state else None,
        "last_run_status": state.get("result", "NOT_STARTED") if state else "NOT_STARTED",
    }, redraw=False)
    board.state["numeric_maximum"] = displayed_numeric_maximum(state)
    board.state["provider_dimensions"] = list(
        (state or {}).get("provider_dimensions", ()))
    board.school_telemetry = SchoolTelemetry(
        board, active_grades=active, champions=school.get("champions"))
    return step, phase


def _push_resource_and_contract(
        board: Dashboard, run_dir: Path, state, active, current_grade: str,
        *, reserve_gib: float) -> None:
    budget = headroom_snapshot(
        run_dir, required_bytes=600_000_000, reserve_gib=reserve_gib)
    ingest(board, {
        "event": "SCHOOL_RESOURCE_OBSERVED",
        "grade": current_grade if active else None,
        **{k: budget[k] for k in
           ("free_bytes", "reserve_bytes", "estimated_write_bytes")},
    })
    board.push("system", {
        "kind": "SOURCE",
        "detail": "Source-bound FP32 + own AdamW | immutable receipts",
    }, redraw=False)
    released = bool(state and state.get("factory_release_sha256"))
    board.push("system", {
        "kind": "RUBRIC",
        "detail": (
            "Grades " + "+".join(active) +
            ": fresh routine; fixed promotion; generalization inactive"
            if released else "Historical policy (lineage only): " + historical_rubric_description(state)),
    }, redraw=False)
    if state and (state.get("last_exam") or {}).get("cohort_sha256"):
        exam = state["last_exam"]
        board.push("system", {
            "kind": "COHORT",
            "detail": (
                f"Seed {exam['cohort_seed']} | SHA {exam['cohort_sha256'][:16]} | "
                f"rubric {exam['exam_rubric_sha256'][:12]}"),
        }, redraw=False)
    board.push("system", {
        "kind": "METRIC",
        "detail": (
            "NOT MEASURED: independent sentinel/CE/P(C)/margin; "
            "frozen soups advise training only, never examination scoring"),
    }, redraw=False)


def _push_saved_school_evidence(
        board: Dashboard, state, active, current_grade: str) -> None:
    if state and state.get("grade_soups"):
        from bilqis_mlx.learning.grade_soup import soup_vote_count, soup_shards
        for grade, soup in sorted(state["grade_soups"].items()):
            effective = soup_vote_count(soup, current_grade, len(active))
            shards = soup_shards(soup)
            active_catalogs = "/".join(str(shard["token_count"]) for shard in shards)
            board.push("system", {
                "kind": "GRADE SOUP", "grade": grade,
                "detail": (
                    f"Frozen {grade} recipe: "
                    f"{soup['vote_count']} mastered capability votes; "
                    f"{effective:.2f} votes for {current_grade} lessons | "
                    f"ingredient vocabularies {active_catalogs} | "
                    f"recipe {soup['recipe_sha256'][:12]}"),
            }, redraw=False)
    if state and state.get("capability_best"):
        for item in sorted(
                state["capability_best"].values(), key=lambda x: x["capability"]):
            model = item["checkpoint"]
            board.push("system", {
                "kind": "CAP BEST",
                "grade": item["capability"].split(".")[0],
                "detail": (
                    f"{item['capability']} {item['correct']}/{item['total']} "
                    f"at step {model['optimizer_step']} | {model['sha256'][:10]}"),
            }, redraw=False)


def _replay_dashboard_journal(board: Dashboard, run_dir: Path) -> None:
    board.log_hint = str(run_dir / "events.jsonl")
    # A detached observer must resume at the byte immediately after the last
    # event actually consumed, not a later stat().st_size. Otherwise events
    # appended during the initial replay can vanish between snapshot and tail.
    board.journal_offset = 0
    board.journal_identity = None
    events = run_dir / "events.jsonl"
    if not events.exists():
        return
    # The renderer itself retains only bounded row buffers. Read the journal
    # once without decoding old JSON, then decode only the same recent-record
    # window the dashboard is capable of displaying.
    with events.open("rb") as log:
        identity = os.fstat(log.fileno())
        board.journal_identity = (identity.st_dev, identity.st_ino)
        replay_limit = max(
            (rows.maxlen or 0 for rows in board.rows.values()), default=0)
        recent = deque(maxlen=max(1, replay_limit))
        while line := log.readline():
            recent.append((log.tell(), line))
        for end, line in recent:
            if not line.endswith(b"\n"):
                # Preserve a partially appended JSON line for the follower.
                board.journal_offset = end - len(line)
                break
            board.journal_offset = end
            if line.strip():
                try:
                    ingest(board, json.loads(line))
                except (ValueError, TypeError, KeyError) as exc:
                    board.push("system", {
                        "kind": "LOG",
                        "detail": f"Invalid telemetry event ignored: {str(exc)[:62]}",
                    }, redraw=False)


def _rebuild_graduation_projection(board: Dashboard, run_dir: Path) -> None:
    """Reconstruct run/lifetime graduation counters from the complete journal.

    The dashboard tables intentionally hydrate only their bounded recent-record
    window. Graduation totals are longitudinal counters, so they must not inherit
    that truncation. This pass is read-only and keeps no event rows in memory.
    """
    events = run_dir / "events.jsonl"
    if not events.exists():
        return
    projection = GraduationProjection()
    with events.open("rb") as log:
        while line := log.readline():
            if not line.endswith(b"\n"):
                break
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except (ValueError, TypeError):
                continue
            if event.get("event") == "SCHOOL_SESSION_STARTED":
                projection.begin_execution()
            projection.observe(event)
    board.school_telemetry.graduations = projection
    board.state["graduations"] = projection.summary()


def build(run_dir: Path, *, stream=None, reserve_gib: float = 100.) -> Dashboard:
    run_dir = Path(run_dir)
    board = Dashboard(stream=stream, redraw=False,
                      title="BILQIS", compact_header=True,
                      show_all_panels=True, tables=LETTER_TABLES)
    state_path, state, school, active, current_grade = _dashboard_state(run_dir)
    step, phase = _initialize_board(
        board, run_dir, state, school, active, current_grade)
    if state_path.exists() and isinstance((state or {}).get("mentor_epoch"), dict):
        board.attach_champion_source(run_dir)
    _push_resource_and_contract(
        board, run_dir, state, active, current_grade, reserve_gib=reserve_gib)
    _push_saved_school_evidence(board, state, active, current_grade)
    board.push("system", {"kind": "RESTART", "detail": "Saved run: train --human-run --resume"}, redraw=False)
    if state and state.get("bamf_operator_status") is not None:
        from .atlas_metrics import bamf_status
        board.bamf_operator_view = bamf_status(state["bamf_operator_status"])
    _replay_dashboard_journal(board, run_dir)
    _rebuild_graduation_projection(board, run_dir)
    if active and not board.rows["GRADES & MASTERY"]:
        board.rows["GRADES & MASTERY"].append({"grade": current_grade, "step": step,
                 "attempt": "-",
                 "start": "-", "latest": "-", "best": "-", "to100": "-",
                 "right_pct": "-", "outcome": phase})
    return board


def ingest(board: Dashboard, event: dict) -> None:
    """Incrementally update the same renderer used by past/future grades."""
    if event.get("event") == "BAMF_OPERATOR_STATUS_OBSERVED":
        from .atlas_metrics import bamf_status
        board.bamf_operator_view = bamf_status(event.get("receipt"))
        return
    board.school_telemetry.ingest(event)


def render(run_dir: Path, *, stream=None) -> None:
    build(run_dir, stream=stream).draw()
