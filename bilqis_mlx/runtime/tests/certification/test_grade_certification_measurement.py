"""Production #1334 measurement stays Factory-owned and inference-only."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_readout import ExecutionMode
from bilqis_mlx.runtime.grade_certification_measurement import (
    GradeCertificationMeasurementBackend,
)
from bilqis_mlx.runtime.tests.certification.test_grade_certification_contracts import (
    _request,
)


def _backend():
    backend = object.__new__(GradeCertificationMeasurementBackend)
    backend.run_dir = None
    backend.request = _request()
    backend.source_context = SimpleNamespace(
        execution_for=lambda _key: SimpleNamespace(exam_item_count=3))
    backend.student = SimpleNamespace(
        retained_state=SimpleNamespace(
            optimizer=SimpleNamespace(parameters="params")))
    backend.artifact_path = "/artifact"
    backend.generation_binding = "g" * 64
    backend.feature_context = SimpleNamespace(snapshot="snapshot")
    return backend


def test_trigger_scores_active_and_protected_scopes_without_teaching():
    backend = _backend()
    cohort = SimpleNamespace(
        digest="1" * 64,
        seed=7,
        rows=(
            {"capability": "C.ZETA"},
            {"capability": "C.ALPHA"},
            {"capability": "C.PRIOR"},
        ),
    )
    with patch.object(backend, "_draw", return_value=cohort), patch.object(
            backend, "_row_correct", return_value=True):
        measured = backend.trigger()
    assert tuple((item.owner, item.obligation_key) for item in measured.scores) == (
        ("ACTIVE", "C.ZETA"),
        ("ACTIVE", "C.ALPHA"),
        ("PROTECTED", "C.PRIOR"),
    )


def test_row_measurement_uses_forward_inference_and_source_resolved_gold_only():
    backend = _backend()
    compiled = object()
    authority = SimpleNamespace(goal="goal")
    plan = object()
    resolved = object()
    output = SimpleNamespace(
        committed=(SimpleNamespace(decision_id="route", value="A"),))
    targets = (SimpleNamespace(decision_id="route", value="A"),)
    with patch(
        "bilqis_mlx.runtime.grade_certification_measurement."
        "compile_factory_evaluation_batch",
        return_value=compiled,
    ), patch(
        "bilqis_mlx.runtime.grade_certification_measurement."
        "factory_task_authority",
        return_value=authority,
    ), patch(
        "bilqis_mlx.runtime.grade_certification_measurement."
        "task_goal_route_plan",
        return_value=plan,
    ), patch(
        "bilqis_mlx.runtime.grade_certification_measurement.forward_bamf",
        return_value=output,
    ) as forward, patch(
        "bilqis_mlx.runtime.grade_certification_measurement."
        "factory_task_training_goal",
        return_value=resolved,
    ), patch(
        "bilqis_mlx.runtime.grade_certification_measurement."
        "task_goal_training_targets",
        return_value=(targets, {"route": True}),
    ):
        assert backend._row_correct({"capability": "C.ZETA"}, 11)

    assert forward.call_args.args[3] is ExecutionMode.INFERENCE
    assert forward.call_args.args[4] is None


def test_backend_rejects_stale_injected_student_before_measurement(tmp_path):
    request = _request()
    student = SimpleNamespace(
        run_id=request.run_id,
        generation=request.accepted_generation,
        retained_state=SimpleNamespace(
            optimizer_step=request.optimizer_step,
            optimizer=SimpleNamespace(parameters="params"),
        ),
        topology=object(),
        extents=object(),
    )
    source_context = SimpleNamespace(
        release=SimpleNamespace(release_sha256=request.factory_release_sha256),
    )
    scope = SimpleNamespace(
        capabilities=request.assessment_capabilities,
        rubric_sha256=request.assessment_rubric_sha256,
        source_sha256=request.assessment_source_sha256,
        generator_version=request.assessment_generator_version,
        semantic_catalog_sha256=request.semantic_catalog_sha256,
    )
    with patch(
        "bilqis_mlx.runtime.grade_certification_measurement."
        "candidate_identity_digest",
        return_value="f" * 64,
        create=True,
    ), patch(
        "bilqis_mlx.runtime.grade_certification_measurement."
        "assessment_scope_contract",
        return_value=scope,
        create=True,
    ), patch(
        "bilqis_mlx.runtime.grade_certification_measurement."
        "execution_generation_digest",
        return_value="g" * 64,
    ), patch(
        "bilqis_mlx.runtime.grade_certification_measurement."
        "authenticate_bamf_execution_feature_context",
        return_value=SimpleNamespace(snapshot="snapshot"),
    ), pytest.raises(BilqisError):
        GradeCertificationMeasurementBackend(
            tmp_path, request, source_context, student, "/artifact")
