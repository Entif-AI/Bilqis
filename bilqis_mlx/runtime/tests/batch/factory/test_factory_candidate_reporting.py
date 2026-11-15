"""B11.2 compact Factory reporting boundary."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.atlas_model import BamfGradientExecution
from bilqis_mlx.runtime.factory_candidate_training import (
    FactoryCandidateDiagnostics,
    _realized_candidate_cost,
    _reporting_diagnostics,
)


class FactoryCandidateReportingTests(unittest.TestCase):
    def test_heavy_gradient_execution_is_retained_only_by_explicit_opt_in(self):
        execution = object.__new__(BamfGradientExecution)

        self.assertIsNone(_reporting_diagnostics(execution, False))

        diagnostics = _reporting_diagnostics(execution, True)
        self.assertIs(type(diagnostics), FactoryCandidateDiagnostics)
        self.assertIs(diagnostics.gradient_execution, execution)
        self.assertEqual(
            diagnostics.schema_version,
            "bilqis.mlx.b11-factory-diagnostics/v1")

        with self.assertRaises(BilqisError):
            _reporting_diagnostics(execution, 1)

    def test_realized_cost_projects_stage_and_b11_observation_without_device_work(self):
        compiled = lambda positions: SimpleNamespace(
            compiled=SimpleNamespace(
                compiled=SimpleNamespace(rows=(SimpleNamespace(positions=positions),)))
        )
        prepared = SimpleNamespace(compiled_rows=(
            compiled((1, 2, 3)), compiled((1, 2))))
        resource = SimpleNamespace(estimated_peak_bytes=128)
        budget = SimpleNamespace(allocation_bytes=256)
        transaction = SimpleNamespace(update_steps=2)
        feature_context = SimpleNamespace(
            atlas_reload_count=1, feature_manifest_rebuild_count=1,
            visit_atlas_reload_count=1, visit_feature_manifest_rebuild_count=1)
        gradient = SimpleNamespace(_performance_observation={
            "b11_preflight_wall_seconds": 0.2,
            "b11_autodiff_wall_seconds": 0.4,
            "b11_provider_draw_count": 8,
            "b11_atlas_reload_count": 4,
        })
        stage = {
            "candidate_step_started_at": 0.75,
            "pre_neural_source_compile_wall_seconds": 0.1,
            "currentness_binding_wall_seconds": 0.3,
            "optimizer_admission_wall_seconds": 0.1,
            "motif_staging_wall_seconds": 0.0,
            "candidate_terminal_step": False,
        }
        loss = SimpleNamespace(item=lambda: 1.5)
        with patch(
                "bilqis_mlx.runtime.factory_candidate_training.time.perf_counter",
                return_value=2.0):
            cost = _realized_candidate_cost(
                1.0, 0.75, loss, prepared, resource, budget, transaction,
                feature_context, True, (2, 1, 1, 0, 0.8), stage, gradient)
        self.assertEqual(cost["candidate_step_wall_seconds"], 1.25)
        self.assertEqual(cost["b11_preflight_wall_seconds"], 0.2)
        self.assertEqual(cost["b11_autodiff_wall_seconds"], 0.4)
        self.assertEqual(cost["b11_provider_draw_count"], 8)
        self.assertEqual(cost["b11_atlas_reload_count"], 4)
        self.assertEqual(cost["c08_gradient_launches"], 2)
        self.assertEqual(cost["c08_vectorized_microbatches"], 1)
        self.assertEqual(cost["logical_rows"], 2)
        self.assertEqual(cost["compiled_positions"], 5)
        self.assertFalse(cost["candidate_terminal_step"])

        terminal_stage = {
            **stage,
            "motif_staging_wall_seconds": 0.3,
            "candidate_terminal_step": True,
        }
        with patch(
                "bilqis_mlx.runtime.factory_candidate_training.time.perf_counter",
                return_value=2.0):
            terminal = _realized_candidate_cost(
                1.0, 0.75, loss, prepared, resource, budget, transaction,
                feature_context, True, (2, 1, 1, 0, 0.8),
                terminal_stage, gradient)
        self.assertTrue(terminal["candidate_terminal_step"])
        self.assertEqual(terminal["motif_staging_wall_seconds"], 0.3)
