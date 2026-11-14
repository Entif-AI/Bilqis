"""Human-gated dispatch to the existing training owner."""
from __future__ import annotations
from contextlib import nullcontext
from pathlib import Path
import sys
from bilqis_mlx.errors import BilqisError
from .settings import GRADE_A_MANIFEST, ROOT
from .inspection import _print_status, status
from .preflight import _source_paths, preflight
from .parser import parse_args
from .lifecycle import _experiment_budget, _guard_independent_no_retention, _human_sigint_guard, _report_retention_plan, _report_timing_trace, _timing_context
from .terminal import _prepare_live_board, _render_stopped_board, _report_operator_blocked
from .explain import _explain_code


def dashboard(run_dir: Path):
    from bilqis_mlx.presentation.dashboard import render
    render(run_dir)
    return 0


def diagnostics(run_dir: Path):
    from bilqis_mlx.diagnostics.audit import audit_saved_run
    return _print_status(audit_saved_run(run_dir))


def _bamf_operator_admission_status(report):
    """Return safe admission terminal state that still permits retained learning."""
    if report.get("result") == "READY_TO_RESUME":
        return None
    if report.get("admission_policy") != "atlas-release":
        return False
    from bilqis_mlx.runtime.atlas_flywheel import AdmissionFlywheelStatus
    safe = {
        AdmissionFlywheelStatus.FIXED_POINT.value,
        AdmissionFlywheelStatus.WAITING_FOR_EVIDENCE.value,
        AdmissionFlywheelStatus.IMPLEMENTATION_UNCOVERED.value,
        AdmissionFlywheelStatus.LEASE_REQUIRED.value,
    }
    return report.get("result") if report.get("result") in safe else False


def _reject_fresh_external_legacy_fallthrough(args, run_dir: Path) -> None:
    legacy_pointer = run_dir / "state.json"
    if (args.resume or args.bamf_v2_foundation_explicit
            or args.model_topology is not None
            or legacy_pointer.exists() or legacy_pointer.is_symlink()):
        return
    target = run_dir.resolve()
    local_runs = (ROOT / "runs").resolve()
    if target != local_runs and local_runs not in target.parents:
        from .bamf_lifecycle_inputs import invalid
        invalid("BAMF_OPERATOR_FRESH_EXTERNAL_RUN_REQUIRES_FOUNDATION_INPUTS")


def _bamf_or_topology(args):
    """Route BAMF v2 before legacy training while preserving C07 early failure."""
    run_dir = Path(args.run_dir).expanduser()
    bamf_pointer = run_dir / "bamf-state.json"
    # A topology path is shared historical syntax.  It becomes BAMF-v2 intent
    # only after the file has actually loaded as ModelTopologySpecV2.  The
    # seven parser-owned foundation flags, by contrast, are v2-only and must
    # seize fresh-command ownership before topology loading.
    fresh_v2_intent = not args.resume and args.bamf_v2_foundation_explicit
    if fresh_v2_intent:
        from .bamf_lifecycle_inputs import foundation_hyperparameters, invalid
        if not args.run_id or type(args.run_seed) is not int or args.run_seed < 0:
            invalid("BAMF_OPERATOR_FOUNDATION_IDENTITY_REQUIRED")
        foundation_hyperparameters(args, required=True, materialize=True)
        if args.model_topology is None:
            invalid("BAMF_OPERATOR_V2_TOPOLOGY_REQUIRED")
    if ((args.admission_policy != "staged" or args.atlas_admission_scope is not None)
            and args.model_topology is None
            and not bamf_pointer.exists() and not bamf_pointer.is_symlink()):
        from bilqis_mlx.runtime.atlas_admission import validate_atlas_command_request
        validate_atlas_command_request(args)
    interrupted_v2 = any(
        path.exists() or path.is_symlink()
        for path in (
            run_dir / "bamf-bundles",
            run_dir / "bamf-acceptance",
            run_dir / ".bamf-pointer.lock",
            run_dir / ".bamf-staging",
        )
    )
    if args.resume and isinstance(args.run_id, str) and args.run_id:
        from bilqis_mlx.runtime.bamf_bundle.publication.genesis_trust import _stored_trust
        interrupted_v2 = interrupted_v2 or _stored_trust(args.run_id) is not None
    if (args.resume and not bamf_pointer.exists() and not bamf_pointer.is_symlink()
            and interrupted_v2):
        from bilqis_mlx.runtime.bamf_bundle.publication.storage import (
            _validate_initial_generation_lifecycle_markers,
        )
        _validate_initial_generation_lifecycle_markers(run_dir)
        from .bamf_lifecycle_inputs import invalid
        invalid("BAMF_OPERATOR_INTERRUPTED_GENESIS_REQUIRES_CREATE_RETRY")
    resume_v2_intent = (
        args.resume
        and (bamf_pointer.exists() or bamf_pointer.is_symlink()
             or args.bamf_v2_foundation_explicit)
    )
    if resume_v2_intent:
        from .bamf_lifecycle import bamf_lifecycle
        report = bamf_lifecycle(args, None)
        admission_status = _bamf_operator_admission_status(report)
        if (args.human_run and not args.dry_run
                and admission_status is not False):
            from dataclasses import asdict
            from bilqis_mlx.runtime.bamf_operator import operate_bamf
            def progress(message):
                print("BAMF TRAINER: " + message, file=sys.stderr, flush=True)
            result = operate_bamf(
                run_dir, minutes=args.minutes,
                max_visits=args.max_visits, reserve_gib=args.reserve_gib,
                progress=progress)
            operator_report = asdict(result)
            if admission_status is not None:
                operator_report["admission_status"] = admission_status
            return True, _print_status(operator_report), None
        return True, _print_status(report), None

    _reject_fresh_external_legacy_fallthrough(args, run_dir)

    from bilqis_mlx.runtime.topology_lifecycle import topology_from_file
    try:
        topology = topology_from_file(args.model_topology)
    except BilqisError:
        if fresh_v2_intent:
            from .bamf_lifecycle_inputs import invalid
            invalid("BAMF_OPERATOR_V2_TOPOLOGY_REQUIRED")
        raise
    from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
    if fresh_v2_intent and not isinstance(topology, ModelTopologySpecV2):
        from .bamf_lifecycle_inputs import invalid
        invalid("BAMF_OPERATOR_V2_TOPOLOGY_REQUIRED")
    if (isinstance(topology, ModelTopologySpecV2)
            or (args.resume and (bamf_pointer.exists() or bamf_pointer.is_symlink()))):
        from .bamf_lifecycle import bamf_lifecycle
        return True, _print_status(bamf_lifecycle(args, topology)), topology
    return False, None, topology


def _main(args):
    trace_path = None
    try:
        if args.action=="status":return status(args.run_dir)
        if args.action=="dashboard":return dashboard(args.run_dir)
        if args.action=="diagnostics":return diagnostics(args.run_dir)
        if args.action in ("explain", "explain-error"):
            return _explain_code(args.code)
        _guard_independent_no_retention(args)
        handled, result, topology = _bamf_or_topology(args)
        if handled:
            return result
        from bilqis_mlx.runtime.topology_lifecycle import operator_topology
        from bilqis_mlx.runtime.atlas_admission import validate_atlas_command_request
        from .bamf_preflight import reject_manifest_request
        if args.atlas_release_manifest is not None:
            reject_manifest_request('release-manifest-requires-held-bamf-v2-inspection')
        validate_atlas_command_request(args)
        if topology is not None:
            operator_topology(args.run_dir, resume=args.resume, requested=topology)
        if args.dry_run:
            _report_retention_plan(args)
            return preflight(args.run_dir,resume=args.resume,
                             verify_source=args.verify_source,
                             legacy_code_root=args.legacy_code_root,
                             champion_checkpoint=args.champion_checkpoint,
                             numeric_staircase=args.numeric_staircase,
                             boolean_composite=args.boolean_composite,
                             boolean_idboolops=args.boolean_idboolops,
                             full_grade_b=args.full_grade_b,
                             retention_enabled=not args.no_retention,
                             boolean_association_bridge=args.boolean_association_bridge, model_topology=topology)
        if args.verify_source:
            raise ValueError("VERIFY_SOURCE_REQUIRES_DRY_RUN")
        if not args.human_run:
            print("TRAINING REQUIRES EXPLICIT HUMAN OPERATOR: add --human-run; "
                  "ordinary and long-running training is human-operated. "
                  "User-authorized agent repair tests must be explicitly finite "
                  "and preserve the current student and own AdamW. "
                  "Use npm run train -- --dry-run for preflight.",file=sys.stderr)
            return 2
        if args.flash_mode and not args.resume:
            raise ValueError("FLASH_MODE_REQUIRES_RESUME")
        if (args.legacy_code_root is not None and
                not args.legacy_code_root.expanduser().resolve().is_relative_to(ROOT)):
            raise ValueError("HUMAN_TRAINER_EXTERNAL_SOURCE_ROOT_FORBIDDEN")
        from bilqis_mlx.runtime.checkpoints import operator_view
        from bilqis_mlx.presentation.dashboard import build, ingest
        board, on_event = _prepare_live_board(args, build, ingest)
        with operator_view(on_event):
            legacy_root, original_checkpoint = _source_paths(args.legacy_code_root, args.champion_checkpoint)
            trace_path, timing_context = _timing_context(args)
            with timing_context:
                experiment_budget = _experiment_budget(args)
                result = _invoke_learner(args, legacy_root, original_checkpoint, topology, experiment_budget)
            if trace_path is not None:
                result["timing_trace_file"] = str(trace_path)
        rendered = _render_stopped_board(board, build, args, result)
        if rendered is not None:
            return rendered
        return _print_status(result)
    except KeyboardInterrupt:
        print("HUMAN TRAINING INTERRUPTED: the last completed visit/checkpoint "
              "remains the resume point. Run npm run train -- --human-run --resume.",
              file=sys.stderr)
        _report_timing_trace(trace_path, stream=sys.stderr)
        return 130
    except (ValueError,RuntimeError,OSError,KeyError,IndexError) as err:
        return _report_operator_blocked(err, trace_path)


def main(argv=None):
    args=parse_args(argv)
    interrupt_guard = (
        _human_sigint_guard()
        if args.action == "train" and args.human_run and not args.dry_run
        else nullcontext()
    )
    with interrupt_guard:
        return _main(args)


def _invoke_learner(args, legacy_root, original_checkpoint, topology, experiment_budget):
    from bilqis_mlx.runtime.operating_loop import operate
    return operate(
        args.run_dir, legacy_root, original_checkpoint, GRADE_A_MANIFEST,
        resume=args.resume, minutes=args.minutes, model_topology=topology,
        steps_per_visit=args.steps_per_visit, max_visits=args.max_visits,
        batch_size=args.batch_size, reserve_gib=args.reserve_gib,
        numeric_staircase=args.numeric_staircase,
        boolean_composite=args.boolean_composite,
        boolean_idboolops=args.boolean_idboolops,
        full_grade_b=args.full_grade_b,
        retention_enabled=not args.no_retention,
        experiment_probe_each=args.experiment_probe_each,
        experiment_mature_max_loss=args.experiment_mature_max_loss,
        experiment_introduction_extra_loss=args.experiment_introduction_extra_loss,
        experiment_protected_cap_limit=args.experiment_protected_cap_limit,
        stagnation_grace_grade=args.stagnation_grace_grade,
        stagnation_grace_steps=args.stagnation_grace_steps,
        admit_next_grade_with_debt=args.admit_next_grade_with_debt,
        source_prefetch_workers=args.source_prefetch_workers,
        flash_mode=args.flash_mode,
        boolean_association_bridge=args.boolean_association_bridge,
        autonomous_curriculum=args.autonomous_curriculum,
        experiment_budget=experiment_budget)
