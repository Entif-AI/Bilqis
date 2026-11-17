"""Training authorization, timing, interrupts, and experiment custody."""
from __future__ import annotations
from contextlib import contextmanager, nullcontext
from pathlib import Path
import json
import signal
import sys
from .settings import DEFAULT_RUN


def _guard_independent_no_retention(args):
    if not args.no_retention:
        return
    target = args.run_dir.expanduser().resolve()
    if target == DEFAULT_RUN.expanduser().resolve():
        raise ValueError("NO_RETENTION_REQUIRES_INDEPENDENT_RUN_DIR")
    saved_path = target / "state.json"
    if (saved_path.is_symlink() or
            (saved_path.is_file() and
             json.loads(saved_path.read_text(encoding="utf-8")).get(
                 "learning_experiment") is not None)):
        raise ValueError("LEARNING_EXPERIMENT_RESUME_REQUIRES_IDENTICAL_OPT_IN")


def _report_retention_plan(args):
    if args.no_retention:
        return
    from bilqis_mlx.learning.learning_experiment import Settings
    settings = Settings(
        probe_each=args.experiment_probe_each,
        mature_max_loss=args.experiment_mature_max_loss,
        introduction_extra_loss=args.experiment_introduction_extra_loss,
        protected_cap_limit=args.experiment_protected_cap_limit)
    print("DEFAULT RETENTION PLAN, NO NEURAL UPDATES: "+str(settings), file=sys.stderr)


def _timing_context(args):
    if not args.timing_trace:
        return None, nullcontext()
    from bilqis_mlx.runtime.timing_trace import TimingTrace, default_trace_path
    path = default_trace_path(args.run_dir)
    context = TimingTrace(
        path,
        metadata={
            "run_dir": str(args.run_dir),
            "max_visits": args.max_visits,
            "steps_per_visit": args.steps_per_visit,
            "batch_size": args.batch_size,
        })
    return path, context


def _report_timing_trace(path, *, stream):
    if path is not None and Path(path).exists():
        print("Timing trace: " + str(path), file=stream, flush=True)


@contextmanager
def _human_sigint_guard():
    """Treat one terminal interrupt as the stop request; ignore cleanup echoes."""
    previous = signal.getsignal(signal.SIGINT)
    interrupted = False

    def handle_interrupt(_signum, _frame):
        nonlocal interrupted
        if interrupted:
            return
        interrupted = True
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handle_interrupt)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, previous)


def _experiment_budget(args):
    if args.issue_349_experiment_root is None:
        return None
    from bilqis_mlx.runtime.experiment_runs import ExperimentRunBudget
    root = args.issue_349_experiment_root.expanduser().resolve()
    target = args.run_dir.expanduser().resolve()
    if target.parent != root:
        raise ValueError("ISSUE349_EXPERIMENT_RUN_MUST_BE_DIRECT_CHILD")
    owner = ExperimentRunBudget(root)
    if args.resume:
        owner.register(target)
    elif target.exists():
        owner.register(target)
        unexpected = tuple(
            entry.name for entry in target.iterdir()
            if entry.name != ".experiment-run.json")
        if unexpected:
            raise ValueError("ISSUE349_EXISTING_RUN_REQUIRES_RESUME")
        owner.assert_can_allocate(600_000_000)
    else:
        owner.create(target.name, required_bytes=600_000_000)
    owner.assert_within_budget()
    return owner


def _bamf_run_authority(args, run_id: str):
    """Adapt legacy experiment custody to the generic native BAMF authority type."""
    owner = _experiment_budget(args)
    if owner is None:
        return None
    from bilqis_mlx.runtime.run_authority import issue_experiment_run_authority
    return issue_experiment_run_authority(owner, args.run_dir, run_id)
