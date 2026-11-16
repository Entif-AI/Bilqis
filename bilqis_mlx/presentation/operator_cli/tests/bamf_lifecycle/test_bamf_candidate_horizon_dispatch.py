"""BAMF resume forwards the operator-owned candidate horizon."""
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.presentation.operator_cli.command import _dispatch_bamf_resume
from bilqis_mlx.runtime.bamf_operator import BamfOperatorResult


def test_bamf_resume_forwards_explicit_candidate_horizon():
    args = SimpleNamespace(
        human_run=True,
        dry_run=False,
        minutes=90,
        max_visits=1,
        steps_per_visit=8,
        reserve_gib=100.0,
        source_prefetch_workers=2,
    )
    report = {"result": "READY_TO_RESUME"}
    run_dir = Path("/run")
    result = BamfOperatorResult("VISIT_LIMIT", 1, 0, 1, 0, 0)
    with patch(
            "bilqis_mlx.control_plane.active_endpoint.advertise_active_endpoint",
            return_value=nullcontext()), patch(
            "bilqis_mlx.runtime.bamf_operator.operate_bamf",
            return_value=result) as operate:
        handled, _code, _next = _dispatch_bamf_resume(args, run_dir, report)

    assert handled is True
    assert operate.call_args.args == (run_dir,)
    assert operate.call_args.kwargs["minutes"] == 90
    assert operate.call_args.kwargs["max_visits"] == 1
    assert operate.call_args.kwargs["steps_per_visit"] == 8
    assert operate.call_args.kwargs["reserve_gib"] == 100.0
    assert operate.call_args.kwargs["source_prefetch_workers"] == 2
    assert callable(operate.call_args.kwargs["progress"])


def test_bamf_resume_preserves_explicit_serial_and_single_worker_modes():
    report = {"result": "READY_TO_RESUME"}
    run_dir = Path("/run")
    result = BamfOperatorResult("VISIT_LIMIT", 1, 0, 1, 0, 0)
    for workers in (0, 1):
        args = SimpleNamespace(
            human_run=True, dry_run=False, minutes=90, max_visits=1,
            steps_per_visit=8, reserve_gib=100.0,
            source_prefetch_workers=workers)
        with patch(
                "bilqis_mlx.control_plane.active_endpoint.advertise_active_endpoint",
                return_value=nullcontext()), patch(
                "bilqis_mlx.runtime.bamf_operator.operate_bamf",
                return_value=result) as operate:
            handled, _code, _next = _dispatch_bamf_resume(args, run_dir, report)
        assert handled is True
        assert operate.call_args.kwargs["source_prefetch_workers"] == workers


def test_post_accept_admission_status_overrides_only_the_initial_fallback(capsys):
    args = SimpleNamespace(
        human_run=True, dry_run=False, minutes=90, max_visits=1,
        steps_per_visit=8, reserve_gib=100.0, source_prefetch_workers=0)
    report = {
        "result": "WAITING_FOR_EVIDENCE",
        "admission_policy": "atlas-release",
    }
    run_dir = Path("/run")
    result = BamfOperatorResult(
        "VISIT_LIMIT", 1, 1, 0, 2, 4,
        admission_status="FIXED_POINT", admission_advances=1)
    parent_graph = {"tokens": ["source"]}
    with patch(
            "bilqis_mlx.control_plane.active_endpoint.advertise_active_endpoint",
            return_value=nullcontext()), patch(
                "bilqis_mlx.runtime.bamf_operator.operate_bamf",
                return_value=result) as operate:
        handled, _code, _next = _dispatch_bamf_resume(
            args, run_dir, report, parent_graph=parent_graph)
    assert handled is True
    assert operate.call_args.kwargs["parent_graph"] is parent_graph
    assert '"admission_status": "FIXED_POINT"' in capsys.readouterr().out
