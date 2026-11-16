"""#1264 source-authority reuse acceptance at the Factory/B11 boundary."""
from pathlib import Path
from tempfile import TemporaryDirectory

from bilqis_mlx.learning.student_ops import train_bamf_factory_step
from bilqis_mlx.b11_observation import source_replay_observation
from bilqis_mlx.runtime.factory_training_bridge import _prepare_factory_source_rows
from bilqis_mlx.runtime.b11_source_execution_authority import (
    require_b11_source_execution_authority,
)
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import (
    visit_provenance,
)
from bilqis_mlx.runtime.tests.capability.factory.retention.factory_retention_live_support import (
    HP,
)

from ..factory_training_bridge_support import FactoryTrainingBridgeFixture
from ..factory_training_execution_support import draw, observation, publish


class FactoryTrainingSourceReuseTests(FactoryTrainingBridgeFixture):
    def test_source_batch_authority_is_the_only_provider_check_boundary(self):
        capability, seed, each = "A.IDENTITY", 37128, 2
        rows = tuple(self.context.draw_rows(
            seed=seed, capability=capability, each=each))
        before = self.context._source_preparation_metrics.provider_draws
        with source_replay_observation() as owner_observation:
            source_authority = self.context.bind_rows(
                rows, seed=seed, capability=capability, each=each)
        self.assertEqual(
            self.context._source_preparation_metrics.provider_draws - before, 1)
        self.assertEqual(owner_observation["provider_checks"], each)

        with source_replay_observation() as prepared_observation:
            _prepare_factory_source_rows(
                self.context, self.feature_context, rows,
                capability=capability, source_seed=seed, source_each=each,
                source_authority=source_authority)
        self.assertEqual(prepared_observation["provider_draws"], 0)
        self.assertEqual(prepared_observation["provider_checks"], 0)

    def test_a_identity_rows_carry_owner_issued_source_authority(self):
        _rows, prepared = self.prepare("A.IDENTITY", 37125, 2)

        for compiled in prepared.compiled_rows:
            authority = compiled.source_execution_authority
            self.assertIsNotNone(authority)
            self.assertIs(authority.snapshot, prepared.semantic_context.snapshot)
            self.assertIs(
                require_b11_source_execution_authority(
                    authority,
                    compiled.compiled.compiled.rows[0],
                    compiled.compiled.compiler_configs[0],
                    compiled.sources[0],
                ),
                authority,
            )

    def test_a_identity_candidate_step_reports_zero_hidden_b11_source_work(self):
        rows, delivery = draw(self, "A.IDENTITY", 37126, 2)
        with TemporaryDirectory() as run_dir_value:
            run_dir = Path(run_dir_value)
            publish(self, run_dir)
            source_context = self.accepted_source_context(run_dir)
            parent = load_accepted_generation(run_dir)
            _capture, delivery_observation = observation(
                run_dir, "A.IDENTITY", rows, 37126)

            result = train_bamf_factory_step(
                run_dir,
                source_context,
                parent,
                str(self.artifact),
                self.feature_receipt.path,
                rows,
                capability="A.IDENTITY",
                delivery=delivery,
                requested_count=4,
                source_seed=37126,
                source_each=2,
                optimizer_step_seed=23,
                visit_provenance=visit_provenance("A.IDENTITY"),
                teacher_strategy={"policy": "b11-source-reuse-cost"},
                teacher_hparams=HP,
                max_norm=1.0,
                observation=delivery_observation,
            )

            cost = result.realized_cost
            self.assertEqual(cost["atlas_reload_count"], 1)
            self.assertEqual(cost["feature_manifest_rebuild_count"], 1)
            self.assertEqual(cost["b11_source_authority_bound_rows"], 2)
            self.assertEqual(cost["b11_source_cold_requalification_rows"], 0)
            self.assertEqual(cost["b11_provider_draw_count"], 0)
            self.assertEqual(cost["b11_atlas_reload_count"], 0)
