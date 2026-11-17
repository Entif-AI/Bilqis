"""R17 native resume binds run custody before lifecycle hydration or dispatch."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.presentation.operator_cli.command import _bamf_or_topology


def test_resume_binds_typed_run_authority_before_runtime_context():
    events = []
    authority = object()
    report = {"result": "READY_TO_RESUME"}
    with TemporaryDirectory() as temporary:
        run_dir = Path(temporary) / "run"
        run_dir.mkdir()
        (run_dir / "bamf-state.json").write_text("fixture", encoding="utf-8")
        args = SimpleNamespace(
            run_dir=run_dir,
            dry_run=False,
            verify_source=False,
            resume=True,
            bamf_v2_foundation_explicit=False,
            model_topology=None,
            admission_policy="staged",
            atlas_admission_scope=None,
            run_id=None,
            issue_349_experiment_root=Path(temporary),
        )

        def bind(*_args, **kwargs):
            events.append(("bind", kwargs["persist"]))

        def resume(*_args, **_kwargs):
            events.append(("resume", None))
            return report, {"graph": "accepted"}

        def dispatch(*_args, **kwargs):
            events.append(("dispatch", kwargs["run_authority"]))
            return True, 0, None

        with patch(
                "bilqis_mlx.runtime.bamf_bundle.inspect_accepted_generation",
                return_value=SimpleNamespace(run_id="future-run")), patch(
                "bilqis_mlx.presentation.operator_cli.lifecycle._bamf_run_authority",
                return_value=authority), patch(
                "bilqis_mlx.runtime.run_authority.bind_native_run_authority",
                side_effect=bind), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle._resume_runtime_context",
                side_effect=resume), patch(
                "bilqis_mlx.presentation.operator_cli.command._dispatch_bamf_resume",
                side_effect=dispatch):
            assert _bamf_or_topology(args) == (True, 0, None)

    assert events == [
        ("bind", True),
        ("resume", None),
        ("dispatch", authority),
    ]
