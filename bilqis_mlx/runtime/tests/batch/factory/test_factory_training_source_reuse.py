"""#1264 source-authority reuse acceptance at the Factory/B11 boundary."""
from pathlib import Path
from tempfile import TemporaryDirectory

from bilqis_mlx.learning.student_ops import train_bamf_factory_step
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

from .factory_training_bridge_support import FactoryTrainingBridgeFixture
from .factory_training_execution_support import draw, observation, publish


class FactoryTrainingSourceReuseTests(FactoryTrainingBridgeFixture):
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
