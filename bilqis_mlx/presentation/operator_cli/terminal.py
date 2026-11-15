"""Live terminal events and operator stop/recovery messages."""
from __future__ import annotations
from bilqis_mlx.compatibility.cli_preflight import historical_session_stop
import sys
from .lifecycle import _report_timing_trace


def human_stop_summary(result: dict) -> str:
    """A legible termination receipt for the human-operated live terminal."""
    explanations = {
        "TIME_LIMIT_REACHED": "The requested time budget was reached.",
        "VISIT_LIMIT_REACHED": "The explicitly configured --max-visits cap was reached.",
        "WHOLE_SCHOOL_MASTERED": "Every grade in the explicitly complete school program passed at one whole student.",
        "AWAITING_TEACHER_SOUP": "Whole-school consolidation requires a separately verified frozen teacher-soup continuation.",
        "STAGNATION_REVIEW_REQUIRED": "The remaining required capabilities showed no fresh measured improvement for the full stagnation window and also failed repeated recovery rounds; they remain unqualified mastery debt for the next measured recovery run.",
        "DISK_RESERVE_REACHED": "Free space cannot cover the protected disk reserve plus another checkpoint.",
        "ATLAS_ADMISSION_ADOPTED_COLD_RESUME": "The admitted successor is now accepted B13 custody; the process stopped before stale in-memory model or optimizer state could be reused.",
    }
    reason = result["stop_reason"]
    grade_wait = (
        reason.startswith("GRADE_") and
        reason.endswith("_AWAITING_NEXT_GRADE"))
    debt_wait = "_PROMOTED_WITH_DEBT_" in reason
    explanation = (
        ("The current admitted grade earned automatic progression from a "
         "stable >=90% promotion sweep while retaining imperfect semantics "
         "as mastery debt; awaiting the next factory-admitted curriculum grade.")
        if debt_wait else
        ("The current admitted grade is mastered; awaiting the next "
         "factory-admitted curriculum grade.")
        if grade_wait else explanations[reason])
    message = ("TRAINING STOPPED NORMALLY: " + reason + "\n" +
               explanation +
               f" Completed {result['visits_this_command']} visits in "
               f"{result['elapsed_seconds']:.1f} seconds, "
               f"optimizer step {result['optimizer_step']}.")
    if reason == "DISK_RESERVE_REACHED":
        message += (f"\nDisk: {result['disk_free_gib']:.2f} GiB free, "
                    f"{result['disk_reserve_gib']:.1f} GiB reserve + "
                    f"{result['disk_next_visit_gib']:.2f} GiB estimated next checkpoint. "
                    "No checkpoint cleanup or reserve reduction was performed.")
    quarantined = result.get("stagnation_quarantined") or ()
    if quarantined:
        message += ("\nStagnation review: withheld for this completed run: " +
                    ", ".join(quarantined) +
                    ". These capabilities still count against graduation and "
                    "will be eligible for measured re-entry on resume.")
    grace = result.get("stagnation_grace")
    if grace and result.get("optimizer_step", 0) < grace.get("until_optimizer_step", 0):
        remaining = grace["until_optimizer_step"] - result["optimizer_step"]
        message += ("\nStagnation grace: " + grace["grade"] +
                    " quarantine actuator suppressed for " + str(remaining) +
                    " more retained optimizer steps; diagnostics remain active.")
    if result.get("flash_mode"):
        message += ("\nFlash mode: fresh routine scheduling assessments remained active; "
                    "championship and promotion qualification work was deferred. "
                    "A saved ASSESS_* boundary remains real debt and will be evaluated on resume. "
                    "If flash reaches an all-perfect curriculum, a non-flash authoritative exam "
                    "is still required before qualification can advance.")
    if not grade_wait and reason not in (
            "WHOLE_SCHOOL_MASTERED", "AWAITING_TEACHER_SOUP"):
        message += ("\nTo continue: " +
                    result.get("safe_resume_command",
                               "npm run train -- --human-run --resume") +
                    " --minutes 90")
    return message + "\nHistorical dashboard: npm run dashboard"


def _prepare_live_board(args, build, ingest):
    visual = sys.stdout.isatty()
    board = build(args.run_dir, reserve_gib=args.reserve_gib) if visual else None
    live_mode = "FLASH" if args.flash_mode else "LIVE"
    def on_event(event):
        ingest(board, event)
        runtime_phase = event.get("_runtime_phase")
        if isinstance(runtime_phase, str) and runtime_phase:
            board.state["phase"] = runtime_phase
        if (event.get("event") != "SCHOOL_SESSION_STOPPED" and
                not historical_session_stop(event.get("event"))):
            board.mode = live_mode
            board.state["stop"] = "RUNNING"
        if event.get("_dashboard_redraw", True):
            board.draw()
    if board is not None:
        board.time_budget_seconds = (
            args.minutes * 60 if type(args.minutes) is int and args.minutes > 0
            else None
        )
        board.school_telemetry.begin_execution(
            grade=board.state.get("prefix"), step=board.state.get("step"))
        board.mode = (("FLASH | " if args.flash_mode else "") +
                      ("RESUMING" if args.resume else "STARTING"))
        board.state["stop"] = "PREPARING"
        board.state["attempted_steps"] = 0
        board.state["retained_steps"] = 0
        board.state["retained_visits"] = 0
        board.state["_rate_sample_eligible"] = True
        system_rows = board.rows["SYSTEM & QUALIFICATION"]
        previous = [row for row in system_rows if row.get("kind") != "STOP"]
        system_rows.clear()
        system_rows.extend(previous)
        board.draw()
    return board, on_event if visual else None


def _render_stopped_board(board, build, args, result: dict) -> int | None:
    if board is None:
        return None
    board = build(args.run_dir, reserve_gib=args.reserve_gib)
    board.time_budget_seconds = (
        args.minutes * 60 if type(args.minutes) is int and args.minutes > 0
        else None)
    elapsed = result.get("elapsed_seconds")
    if isinstance(elapsed, (int, float)) and elapsed >= 0:
        board.started = board.clock() - elapsed
    board.mode = "STOPPED | " + result["stop_reason"]
    board.draw()
    print("\n" + human_stop_summary(result), flush=True)
    _report_timing_trace(result.get("timing_trace_file"), stream=sys.stdout)
    return 0


def _report_operator_blocked(err, trace_path) -> int:
    print("OPERATOR BLOCKED: " + str(err), file=sys.stderr)
    context = getattr(err, "context", None)
    if context:
        details = ", ".join(
            f"{key}={value}" for key, value in sorted(context.items()))
        print("DETAILS: " + details, file=sys.stderr)
    from bilqis_mlx.runtime.operator_recovery import recovery_advice
    advice = recovery_advice(err)
    if advice.explanation:
        print("CAUSE: " + advice.explanation, file=sys.stderr)
    if advice.safe_check:
        print("SAFE CHECK: " + advice.safe_check, file=sys.stderr)
    print("RECOVERY: " + advice.disposition + " | " + advice.next_action,
          file=sys.stderr)
    if advice.manual_ref:
        print("FIELD MANUAL: " + advice.manual_ref, file=sys.stderr)
    _report_timing_trace(trace_path, stream=sys.stderr)
    return 2
