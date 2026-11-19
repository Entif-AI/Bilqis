"""C08.4 production dispatch over genuine Factory/B11 row authority."""
from pathlib import Path
from tempfile import TemporaryDirectory

import mlx.core as mx

from bilqis_mlx.runtime.atlas_resources import (
    DistributedRank,
    load_persisted_distributed_manifest,
)
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.runtime.c08_distributed_executor import (
    configure_mlx_distributed_execution,
)
from bilqis_mlx.runtime.factory_candidate_training import (
    execute_factory_candidate_step,
)
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import (
    visit_provenance,
)
from bilqis_mlx.runtime.tests.capability.factory.retention.factory_retention_live_support import (
    HP,
)

from .factory_training_bridge_support import FactoryTrainingBridgeFixture
from .factory_training_execution_support import (
    draw, observation, publish, split_budget,
)


class FactoryDistributedExecutionTests(FactoryTrainingBridgeFixture):
    def test_production_dispatch_uses_owner_manifest_and_real_b11_rows(self):
        rows, delivery = draw(self, "A.IDENTITY", 37129, 2)
        with TemporaryDirectory() as run_dir_value:
            run_dir = Path(run_dir_value)
            publish(self, run_dir)
            source_context = self.accepted_source_context(run_dir)
            parent = load_accepted_generation(run_dir)
            prepared = self.prepare("A.IDENTITY", 37129, 2)[1]
            _, delivery_observation = observation(
                run_dir, "A.IDENTITY", rows, 37129)
            device = str(mx.device_info()["device_name"])
            workers = (
                DistributedRank(0, "fixture-rank-0", device),
                DistributedRank(1, "fixture-rank-1", device),
            )
            binding = configure_mlx_distributed_execution(
                workers, hosts=("127.0.0.1",), partition_seed=29,
                backend="ring")
            profile = binding.profile
            result = execute_factory_candidate_step(
                run_dir, source_context, parent, str(self.artifact),
                self.feature_receipt.path, rows,
                capability="A.IDENTITY", delivery=delivery,
                requested_count=2, source_seed=37129, source_each=2,
                optimizer_step_seed=29,
                visit_provenance=visit_provenance("A.IDENTITY"),
                teacher_strategy={"policy": "c08-distributed-production"},
                teacher_hparams=HP, max_norm=1.0,
                observation=delivery_observation,
                memory_budget=split_budget(parent, prepared),
                distributed_profile=profile, distributed_executor=binding)

            digest = result.realized_cost["c08_distributed_logical_batch_digest"]
            manifest = load_persisted_distributed_manifest(run_dir, digest)
            self.assertEqual(manifest.retained_generation, parent.generation)
            self.assertEqual(
                manifest.retained_manifest_sha256, parent.manifest_sha256)
            self.assertEqual(
                manifest.logical_batch_digest, result.resource_plan.digest)
            self.assertEqual(
                load_persisted_distributed_manifest(
                    run_dir, manifest.logical_batch_digest),
                manifest)
            self.assertEqual(result.transaction.update_steps, 1)
            self.assertEqual(len(result.transaction.step_proofs), 1)
            self.assertEqual(len(result.transaction.training_authorities), 1)
            self.assertEqual(
                result.transaction.step_proofs[0].training_authority_sha256,
                result.transaction.training_authorities[0].digest)
