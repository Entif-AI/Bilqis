"""C08.4 distributed reduction enters the native B12 candidate boundary once."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_candidate import (
    CandidateCustodyIdentity, CandidateState, begin_candidate,
)
from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.learning.atlas_engram_transaction import MotifAllocationSnapshot
from bilqis_mlx.learning.atlas_plasticity import (
    GroupEligibility, IdentityRowAge, PlasticityPolicy,
)
from bilqis_mlx.runtime.atlas_candidate_step import production_candidate_step
from bilqis_mlx.runtime.atlas_model import BamfGradientExecution
from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters, AdamWStateTree
from bilqis_mlx.runtime.atlas_resources import (
    BatchPlan, DistributedExecutionProfile, DistributedRank,
    partition_logical_batch,
)
from bilqis_mlx.runtime.c08_distributed_manifest import issue_distributed_step_manifest
from bilqis_mlx.runtime.atlas_training_contracts import (
    BamfTrainingRow, _issue_training_batch,
)
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.c08_distributed_gradient import (
    execute_distributed_rank, reduce_distributed_rank_gradients,
)
from bilqis_mlx.runtime.c08_distributed_evidence import DistributedB11Evidence
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, Initializer, ModelTopologySpecV2, ParameterGroup,
    ParameterSpec,
)


BANK = "identity.bank.0"
DECLARED = (ParameterSpec(
    BANK, (2, 2), Initializer.EMBEDDING,
    ParameterGroup.IDENTITY_ROW_AGE, True),)
SHAPE_PATCHES = (
    "bilqis_mlx.runtime.topology_v2.validation.expected_bamf_shapes",
    "bilqis_mlx.runtime.backbone_identity.expected_bamf_shapes",
    "bilqis_mlx.learning.atlas_participation_census.expected_bamf_shapes",
    "bilqis_mlx.learning._retention.atlas_participation_census.expected_bamf_shapes",
    "bilqis_mlx.runtime.model_topology_v2.expected_bamf_shapes",
)


class DistributedCandidateStepTests(TestCase):
    def setUp(self):
        values = mx.array([[.5, -.25], [1., 2.]], dtype=mx.float32)
        optimizer = AdamWStateTree(
            {BANK: values}, {BANK: mx.ones_like(values) * .1},
            {BANK: mx.ones_like(values) * .01},
            {BANK: mx.array([2, 3], dtype=mx.uint64)})
        allocations = MotifAllocationSnapshot(MotifManifest("b" * 64))
        self.extents = GenerationExtents(
            1, 1, "a" * 64, allocations.manifest.digest, "c" * 64)
        self.parent = CandidateState(
            optimizer,
            PlasticityPolicy(
                "ADAPTIVE", 7,
                (IdentityRowAge(0, 0, 7), IdentityRowAge(0, 1, 2))),
            allocations, 11,
            CandidateCustodyIdentity(
                "fixture-run", 0, "6" * 64, ModelTopologySpecV2().digest,
                self.extents.digest))
        self.hp = AdamWHyperparameters(.001, (.9, .95), 1e-8, .01)
        for path in SHAPE_PATCHES:
            item = patch(path, return_value=DECLARED)
            item.start()
            self.addCleanup(item.stop)

    def _distributed_fixture(self):
        spec = ModelTopologySpecV2()
        generation = execution_generation_digest(
            self.parent.optimizer.parameters, spec=spec, extents=self.extents)
        rows = tuple(BamfTrainingRow(
            None, None, None, SimpleNamespace(row_id=row_id, optimizer_step_seed=7))
            for row_id in ("row:a", "row:b"))
        batch = _issue_training_batch("4" * 64, generation, "5" * 64, "A.TEST", rows)
        plan = BatchPlan(
            groups=((0,), (1,)), logical_row_ids=("row:a", "row:b"),
            microbatch_size=1, estimated_peak_bytes=100, resident_bytes=50,
            optimizer_step_seed=7, generation_binding=generation,
            topology_digest=spec.digest, memory_budget_digest="6" * 64,
            source_digest="7" * 64)
        profile = DistributedExecutionProfile(
            partition_seed=17, workers=(
                DistributedRank(0, "worker-a", "M3 Ultra"),
                DistributedRank(1, "worker-b", "M2 Ultra")),
            mlx_version="0.test", backend="ring", numeric_precision="fp32")
        manifest = issue_distributed_step_manifest(
            self.parent, batch, plan, profile)
        return spec, generation, batch, plan, manifest

    def _logical_execution(self, generation, plan, manifest):
        def execute_row(_index):
            observed = SimpleNamespace(
                output=SimpleNamespace(generation_binding=generation),
                custody_run_id=self.parent.custody.run_id,
                custody_generation=self.parent.custody.generation,
                custody_manifest_sha256=self.parent.custody.manifest_sha256,
                visible_identity_rows=((0, 0),), feedback_identity_rows=(),
                feature_rows=(), local_slot_rows=(),
                dense_parameter_names=(BANK,),
                semantic_denominator_identity_rows=(),
                semantic_denominator_feature_rows=(), motif_reads=(),
                role_read_feature_rows=(), training_authority=None)
            result = object.__new__(BamfGradientExecution)
            object.__setattr__(result, "execution", observed)
            object.__setattr__(
                result, "gradients", {BANK: mx.ones((2, 2), dtype=mx.float32)})
            object.__setattr__(result, "loss_total", mx.array(1.0, dtype=mx.float32))
            return result

        authority = SimpleNamespace(digest="8" * 64)
        authority.__post_init__ = lambda: None
        def evidence(_execution, *, manifest_digest, rank, row_index, row_id):
            return DistributedB11Evidence(
                manifest_digest, rank, row_index, row_id, generation,
                self.parent.custody.run_id, self.parent.custody.generation,
                self.parent.custody.manifest_sha256, ((0, 0),), (), (), (), (), (),
                (), (BANK,), (), authority.digest,
                (("SOURCE", "fixture-source"),), "[]")
        with patch.object(BamfGradientExecution, "__post_init__", return_value=None), \
                patch("bilqis_mlx.runtime.c08_distributed_gradient.issue_distributed_b11_evidence",
                      side_effect=evidence):
            rank_results = tuple(
                execute_distributed_rank(plan, manifest, part, execute_row)
                for part in partition_logical_batch(plan, manifest))
        logical = reduce_distributed_rank_gradients(plan, manifest, rank_results)
        metadata = logical.distributed_metadata
        object.__setattr__(logical, "distributed_metadata", type(metadata)(
            metadata.manifest, metadata.compute_seconds_per_worker,
            metadata.communication_seconds, metadata.peak_memory_per_worker,
            (authority, authority)))
        return logical, authority

    def test_accepted_distributed_candidate_advances_exactly_one_optimizer_step(self):
        candidate = begin_candidate(self.parent)
        spec, generation, batch, plan, manifest = self._distributed_fixture()
        logical, _authority = self._logical_execution(generation, plan, manifest)
        eligible = GroupEligibility(
            mode="FULL", eligible_parameter_names=(BANK,),
            frozen_parameter_names=(), admitted_identity_rows=((0, 0),),
            fast_identity_rows=((0, 0),), established_identity_rows=())
        kwargs = dict(
            group_eligible=eligible, spec=spec, extents=self.extents,
            run_id=self.parent.custody.run_id,
            generation=self.parent.custody.generation + 1,
            parent_manifest_sha256=self.parent.custody.manifest_sha256,
            parent_candidate_identity_sha256=candidate_identity_digest(self.parent),
            parent_optimizer_step=self.parent.optimizer_step,
            topology_digest=self.parent.custody.topology_digest,
            candidate_step_ordinal=1, teacher_hparams=self.hp, max_norm=1.)
        with patch(
                "bilqis_mlx.runtime.atlas_candidate_step.bind_logical_batch_training_authority",
                return_value=None):
            result = production_candidate_step(
                candidate, loss_bearing_target=True,
                logical_batch_execution=logical, training_batch=batch,
                logical_batch_plan=plan, **kwargs)
        self.assertEqual(result.update_steps, 1)
        self.assertEqual(len(result.step_proofs), 1)
        self.assertFalse(bool(mx.array_equal(
            result.optimizer.parameters[BANK],
            self.parent.optimizer.parameters[BANK])))
