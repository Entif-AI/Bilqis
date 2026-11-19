"""Visit-level source preparation telemetry across the accepted session path."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.runtime.bamf_operator.session_parts.native_session import retention_result
from bilqis_mlx.runtime.bamf_operator.session import _emit_progress
from bilqis_mlx.runtime.bamf_operator.session_support import _resource_observation
from bilqis_mlx.runtime.source_execution import SourcePreparationMetrics


def test_resource_observation_reports_semantic_materialization_counts():
    cost = {
        "wall_seconds": 1.0,
        "optimizer_steps": 1,
        "candidate_optimizer_steps": 1,
        "c08_memory_budget_bytes": 64 * 1024 ** 3,
        "atlas_reload_count": 0,
        "feature_manifest_rebuild_count": 0,
        "visit_atlas_reload_count": 1,
        "visit_feature_manifest_rebuild_count": 1,
    }
    step = SimpleNamespace(
        transaction=SimpleNamespace(update_steps=1), realized_cost=cost)
    source_metrics = SourcePreparationMetrics(
        provider_draws=21, source_context_builds=1,
        compiled_source_builds=1)
    with patch(
            "bilqis_mlx.runtime.bamf_operator.session_support.shutil.disk_usage",
            return_value=SimpleNamespace(used=123)):
        resource = _resource_observation(Path("/run"), step, source_metrics)
    assert resource["atlas_reload_count"] == 0
    assert resource["feature_manifest_rebuild_count"] == 0
    assert resource["visit_atlas_reload_count"] == 1
    assert resource["visit_feature_manifest_rebuild_count"] == 1
    assert resource["provider_draw_count"] == 21
    assert resource["source_context_build_count"] == 1
    assert resource["compiled_source_build_count"] == 1


def test_retention_threads_source_metrics_into_resource_observation():
    source_metrics = SourcePreparationMetrics(
        provider_draws=1, source_context_builds=1,
        compiled_source_builds=1)
    context = SimpleNamespace(_source_preparation_metrics=source_metrics)
    step = SimpleNamespace(transaction="candidate")
    retained = SimpleNamespace(optimizer_step=12)
    evaluation = SimpleNamespace(
        candidate_state=retained,
        parent_state=SimpleNamespace(optimizer_step=11))
    decision = SimpleNamespace(
        accepted=True, to_record=lambda: {"decision": "ACCEPTED"})
    successor = object()
    evidence = {
        "persistence": {
            "bytes_written": 300,
            "file_fsyncs": 1,
            "directory_fsyncs": 1,
            "evidence_objects": 4,
            "persistence_seconds": 0.005,
        },
    }
    capture = SimpleNamespace(finalize=lambda **_kwargs: evidence)
    identity = SimpleNamespace(visit_id="visit:metrics", policy_key="policy:metrics")
    selection = SimpleNamespace(
        option_id="option:metrics", visit=SimpleNamespace(identity=identity))
    cache = SimpleNamespace(
        generation=1, accepted_manifest_sha256="a" * 64)
    resource = {
        "schema": "bilqis.bamf.c16.3-resource-observation/v1",
        "optimizer_steps": 1,
    }
    with patch(
            "bilqis_mlx.runtime.outcomes.issuance.build_outcome",
            return_value={}), patch(
            "bilqis_mlx.runtime.outcomes.issuance.credited_visit",
            side_effect=lambda visit, _outcome: visit), patch(
            "bilqis_mlx.runtime.outcomes.issuance.carry_credit_to_successor",
            side_effect=lambda _visit, successor, _parent: successor), patch(
            "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.evaluate_factory_retention_candidate",
            return_value=evaluation), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.issue_factory_retention_decision",
                return_value=decision), patch(
                    "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.candidate_identity_metrics_delta",
                    return_value={}), patch(
                        "bilqis_mlx.runtime.bamf_operator.session_parts.native_session._resource_observation",
                        return_value=resource) as observe, patch(
                            "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.derive_accepted_teacher_successor",
                            return_value=successor), patch(
                                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.bind_factory_baseline_successor",
                                return_value=successor), patch(
                                    "bilqis_mlx.runtime.bamf_operator.championship.bind_accepted_championship_successor",
                                    return_value=successor), patch(
                                    "bilqis_mlx.runtime.outcomes.issuance.build_outcome",
                                    return_value={}), patch(
                                        "bilqis_mlx.runtime.outcomes.issuance.credited_visit",
                                        side_effect=lambda visit, outcome: visit), patch(
                                            "bilqis_mlx.runtime.outcomes.issuance.carry_credit_to_successor",
                                            side_effect=lambda visit, next_successor, parent: next_successor):
        prepared = retention_result(
            Path("/run"), object(), context, "atlas", selection, "capability:metrics",
            cache, (step,), capture, 1, 1, {}, None, None,
            emit_progress=_emit_progress)
    observe.assert_called_once_with(
        Path("/run"), (step,), source_metrics, identity_metrics={})
    assert prepared.status == "ACCEPTED"
    assert prepared.successor is successor
    assert prepared.candidate_evidence is evidence
