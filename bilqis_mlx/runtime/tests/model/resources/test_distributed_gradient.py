"""C08.4 raw MLX rank execution and collective reduction."""
import copy
from types import SimpleNamespace
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.runtime.atlas_model import BamfGradientExecution
from bilqis_mlx.runtime.atlas_resources import (
    DistributedRank, DistributedStepManifest, partition_logical_batch,
    plan_microbatches,
)
from bilqis_mlx.runtime.c08_distributed_collective import (
    all_reduce_fp32_rank_mean, require_collective_matches_reference,
)
from bilqis_mlx.runtime.c08_distributed_gradient import (
    execute_distributed_rank, reduce_distributed_rank_gradients,
)
from bilqis_mlx.runtime.c08_distributed_evidence import DistributedB11Evidence
from bilqis_mlx.runtime.c08_distributed_outcome import (
    DistributedRuntimeAttestation, DistributedStepOutcome,
)
from bilqis_mlx.runtime.c08_distributed_coordinator import (
    logical_batch_from_distributed_outcome,
)
from bilqis_mlx.runtime.c08_gradient_accumulation import (
    accumulate_logical_batch_gradients,
)
from bilqis_mlx.runtime.tests.model.resources.helpers import (
    AtlasResourcesFixture, _rows,
)


class DistributedGradientTest(AtlasResourcesFixture):
    def _plan(self):
        return plan_microbatches(_rows(4), self.topology, self.budget)

    def _manifest(self, plan):
        return DistributedStepManifest(
            retained_generation=7, retained_manifest_sha256="a" * 64,
            curriculum_release="factory:test", source_release=plan.source_digest,
            logical_batch_digest=plan.digest, partition_seed=17, world_size=2,
            workers=(DistributedRank(0, "worker-a", "M3 Ultra"),
                     DistributedRank(1, "worker-b", "M2 Ultra")),
            mlx_version="0.test", backend="ring", numeric_precision="fp32")

    @staticmethod
    def _row(plan, value):
        execution = object.__new__(BamfGradientExecution)
        object.__setattr__(execution, "execution", SimpleNamespace(
            output=SimpleNamespace(generation_binding=plan.generation_binding)))
        object.__setattr__(
            execution, "gradients",
            {"weight": mx.array([value, value + 2.0], dtype=mx.float32)})
        object.__setattr__(
            execution, "loss_total", mx.array(value, dtype=mx.float32))
        return execution

    def _ranks(self, plan, manifest, values=(1.0, 3.0, 5.0, 7.0)):
        def evidence(_execution, *, manifest_digest, rank, row_index, row_id):
            return DistributedB11Evidence(
                manifest_digest, rank, row_index, row_id,
                "c" * 64, "fixture-run", 7, "a" * 64,
                ((0, 0),), (), (), (), (), (), (), ("weight",), (), "b" * 64,
                (("SOURCE", "fixture-source"),), "[]")
        with patch.object(BamfGradientExecution, "__post_init__", return_value=None), \
                patch("bilqis_mlx.runtime.c08_distributed_gradient.issue_distributed_b11_evidence",
                      side_effect=evidence):
            return tuple(execute_distributed_rank(
                plan, manifest, part,
                lambda index: self._row(plan, values[index]))
                for part in partition_logical_batch(plan, manifest))

    def test_rank_reduction_matches_single_worker_reference(self):
        plan = self._plan()
        manifest = self._manifest(plan)
        values = (1.0, 3.0, 5.0, 7.0)
        with patch.object(BamfGradientExecution, "__post_init__", return_value=None):
            single = accumulate_logical_batch_gradients(
                plan, lambda index: self._row(plan, values[index]))
        distributed = reduce_distributed_rank_gradients(
            plan, manifest, self._ranks(plan, manifest),
            communication_seconds=0.01)
        self.assertTrue(bool(mx.allclose(
            single.gradients["weight"], distributed.gradients["weight"],
            rtol=0.0, atol=1e-6)))
        self.assertTrue(bool(mx.allclose(
            single.weighted_mean_loss, distributed.weighted_mean_loss,
            rtol=0.0, atol=1e-6)))
        self.assertEqual(distributed.distributed_metadata.manifest, manifest)

    def test_missing_duplicate_and_stale_rank_results_fail_closed(self):
        plan = self._plan()
        manifest = self._manifest(plan)
        ranks = self._ranks(plan, manifest)
        stale = copy.copy(ranks[1])
        object.__setattr__(stale, "manifest_digest", "b" * 64)
        for results in ((ranks[0],), (ranks[0], ranks[0]), (ranks[0], stale)):
            with self.subTest(results=results), self.assertRaises(Exception):
                reduce_distributed_rank_gradients(plan, manifest, results)

    def test_collective_fp32_reduction_matches_reference(self):
        plan = self._plan()
        manifest = self._manifest(plan)
        ranks = self._ranks(plan, manifest)
        weighted_gradients = [
            rank.gradients["weight"] * (len(rank.row_indices) / 4)
            for rank in ranks]
        weighted_losses = [
            rank.mean_loss * (len(rank.row_indices) / 4) for rank in ranks]
        with patch.object(mx.distributed, "all_sum", side_effect=[
                weighted_gradients[0] + weighted_gradients[1],
                weighted_losses[0] + weighted_losses[1]]):
            collective_gradient, collective_loss, _seconds = (
                all_reduce_fp32_rank_mean(
                    ranks[0].gradients, ranks[0].mean_loss,
                    local_rows=len(ranks[0].row_indices), total_rows=4))
        reference = reduce_distributed_rank_gradients(plan, manifest, ranks)
        require_collective_matches_reference(
            reference.gradients, reference.weighted_mean_loss,
            collective_gradient, collective_loss)
        checked = reduce_distributed_rank_gradients(
            plan, manifest, ranks, collective_gradients=collective_gradient,
            collective_loss=collective_loss)
        self.assertTrue(bool(mx.allclose(
            checked.gradients["weight"], reference.gradients["weight"],
            rtol=0.0, atol=1e-6)))

    def test_coordinator_requires_exact_runtime_attestation_per_rank(self):
        plan = self._plan()
        manifest = self._manifest(plan)
        ranks = self._ranks(plan, manifest)
        reduced = reduce_distributed_rank_gradients(plan, manifest, ranks)
        evidence = tuple(item for result in ranks for item in result.evidence)
        attestations = tuple(DistributedRuntimeAttestation(
            manifest.digest, worker.rank, worker.worker_id, worker.device_family,
            manifest.mlx_version, manifest.backend, manifest.numeric_precision)
            for worker in manifest.workers)
        outcome = DistributedStepOutcome(
            manifest.digest, evidence, attestations, reduced.gradients,
            reduced.weighted_mean_loss, (0.1, 0.1), 0.01, (1, 1))
        logical_batch_from_distributed_outcome(plan, manifest, outcome)
        drift = list(attestations)
        drift[1] = DistributedRuntimeAttestation(
            manifest.digest, 1, "wrong-worker", manifest.workers[1].device_family,
            manifest.mlx_version, manifest.backend, manifest.numeric_precision)
        with self.assertRaises(Exception):
            logical_batch_from_distributed_outcome(
                plan, manifest, DistributedStepOutcome(
                    manifest.digest, evidence, tuple(drift), reduced.gradients,
                    reduced.weighted_mean_loss, (0.1, 0.1), 0.01, (1, 1)))
