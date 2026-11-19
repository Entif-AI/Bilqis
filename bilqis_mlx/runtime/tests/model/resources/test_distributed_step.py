"""C08.4 distributed-step execution identity, partition, and reduction."""
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.runtime.atlas_resources import (
    DistributedRank, DistributedStepManifest,
    DistributedStepTelemetry, TopologyObservation, TopologyUnavailable, best_topology,
    core_backend_name, inspect_distributed_backends, partition_logical_batch,
    plan_microbatches, require_distributed_backend,
    validate_distributed_resume, distributed_manifest_record,
    load_distributed_manifest, load_persisted_distributed_manifest,
    persist_distributed_manifest,
    validate_runtime_rank,
)
from bilqis_mlx.runtime.tests.model.resources.helpers import (
    AtlasResourcesFixture, _rows,
)


class DistributedStepTest(AtlasResourcesFixture):
    def _plan(self):
        return plan_microbatches(_rows(4), self.topology, self.budget)

    def _manifest(self, plan, *, seed=17):
        return DistributedStepManifest(
            retained_generation=7,
            retained_manifest_sha256="a" * 64,
            curriculum_release="factory:test",
            source_release=plan.source_digest,
            logical_batch_digest=plan.digest,
            partition_seed=seed,
            world_size=2,
            workers=(
                DistributedRank(0, "worker-a", "M3 Ultra"),
                DistributedRank(1, "worker-b", "M2 Ultra"),
            ),
            mlx_version="0.test",
            backend="ring",
            numeric_precision="fp32",
        )

    def test_partition_is_deterministic_disjoint_and_complete(self):
        plan = self._plan()
        manifest = self._manifest(plan)
        first = partition_logical_batch(plan, manifest)
        second = partition_logical_batch(plan, manifest)
        self.assertEqual(first, second)
        flattened = tuple(sorted(i for part in first for i in part.row_indices))
        self.assertEqual(flattened, tuple(range(len(plan.logical_row_ids))))
        self.assertTrue(
            set(first[0].row_indices).isdisjoint(first[1].row_indices))

    def test_backend_substitution_is_execution_identity_not_batch_identity(self):
        plan = self._plan()
        ring = self._manifest(plan)
        nccl = replace(ring, backend="nccl")
        self.assertEqual(ring.logical_batch_digest, nccl.logical_batch_digest)
        self.assertNotEqual(ring.digest, nccl.digest)

    def test_backend_capability_probe_does_not_initialize_group(self):
        with patch.object(
                mx.distributed, "is_available",
                side_effect=lambda backend: backend in ("ring", "jaccl")) as available, \
                patch.object(mx.distributed, "init") as initialize:
            capabilities = inspect_distributed_backends()
            self.assertEqual(
                {item.backend for item in capabilities if item.available},
                {"ring", "jaccl"})
            self.assertEqual(require_distributed_backend("jaccl-ring"), "jaccl")
        initialize.assert_not_called()
        self.assertEqual(core_backend_name("jaccl-ring"), "jaccl")
        self.assertGreaterEqual(available.call_count, 5)

    def test_cold_resume_validates_topology_without_changing_batch_identity(self):
        plan = self._plan()
        manifest = self._manifest(plan)
        record = json.loads(json.dumps(distributed_manifest_record(manifest)))
        resumed = load_distributed_manifest(record)
        self.assertEqual(resumed, manifest)
        validate_distributed_resume(
            resumed,
            world_size=2,
            backend="ring",
            device_families=("M3 Ultra", "M2 Ultra"),
            mlx_version="0.test",
        )
        for drift in (
            dict(world_size=1, backend="ring",
                 device_families=("M3 Ultra", "M2 Ultra"), mlx_version="0.test"),
            dict(world_size=2, backend="nccl",
                 device_families=("M3 Ultra", "M2 Ultra"), mlx_version="0.test"),
            dict(world_size=2, backend="ring",
                 device_families=("M3 Ultra", "M3 Ultra"), mlx_version="0.test"),
        ):
            with self.subTest(drift=drift), self.assertRaises(Exception):
                validate_distributed_resume(manifest, **drift)
        self.assertEqual(manifest.logical_batch_digest, plan.digest)

    def test_runtime_rank_binds_initialized_group_and_host_metadata(self):
        plan = self._plan()
        manifest = self._manifest(plan)
        partition = partition_logical_batch(plan, manifest)[1]

        class Group:
            def size(self):
                return 2

            def rank(self):
                return 1

        validate_runtime_rank(
            manifest, partition, Group(), backend="ring",
            device_family="M2 Ultra", mlx_version="0.test",
            numeric_precision="fp32")
        drifts = (
            dict(backend="nccl", device_family="M2 Ultra",
                 mlx_version="0.test", numeric_precision="fp32"),
            dict(backend="ring", device_family="M3 Ultra",
                 mlx_version="0.test", numeric_precision="fp32"),
            dict(backend="ring", device_family="M2 Ultra",
                 mlx_version="0.other", numeric_precision="fp32"),
            dict(backend="ring", device_family="M2 Ultra",
                 mlx_version="0.test", numeric_precision="bf16"),
        )
        for kwargs in drifts:
            with self.subTest(kwargs=kwargs), self.assertRaises(Exception):
                validate_runtime_rank(manifest, partition, Group(), **kwargs)

        class WrongWorld(Group):
            def size(self):
                return 1

        with self.assertRaises(Exception):
            validate_runtime_rank(
                manifest, partition, WrongWorld(), backend="ring",
                device_family="M2 Ultra", mlx_version="0.test")

        class WrongRank(Group):
            def rank(self):
                return 0

        with self.assertRaises(Exception):
            validate_runtime_rank(
                manifest, partition, WrongRank(), backend="ring",
                device_family="M2 Ultra", mlx_version="0.test")

    def test_persisted_manifest_is_idempotent_and_replay_drift_fails_closed(self):
        plan = self._plan()
        manifest = self._manifest(plan)
        with TemporaryDirectory() as root:
            run_dir = Path(root)
            first = persist_distributed_manifest(run_dir, manifest)
            second = persist_distributed_manifest(run_dir, manifest)
            self.assertEqual(first, second)
            self.assertEqual(
                load_persisted_distributed_manifest(run_dir, plan.digest), manifest)
            drift = replace(manifest, partition_seed=manifest.partition_seed + 1)
            with self.assertRaises(Exception):
                persist_distributed_manifest(run_dir, drift)
            with self.assertRaises(Exception):
                load_persisted_distributed_manifest(run_dir, "G" * 64)

    def test_first_receipt_creation_fsyncs_new_directory_entries(self):
        manifest = self._manifest(self._plan())
        with TemporaryDirectory() as root, patch(
                "bilqis_mlx.runtime._atlas_resources.distributed_receipt."
                "_fsync_directory") as fsync_directory:
            persist_distributed_manifest(Path(root), manifest)
        fsynced = [call.args[0].name for call in fsync_directory.call_args_list]
        self.assertIn("receipts", fsynced)
        self.assertIn("c08-distributed", fsynced)

    def test_manifest_refuses_precision_not_owned_by_b11(self):
        plan = self._plan()
        with self.assertRaises(Exception):
            replace(self._manifest(plan), numeric_precision="bf16")

    def test_telemetry_reports_scaling_and_compares_retained_gain(self):
        plan = self._plan()
        manifest = self._manifest(plan)
        telemetry = DistributedStepTelemetry(
            manifest.digest, 4, 40, (1.0, 0.8), 0.2, 2.0, 1,
            (1024, 2048), 2, single_worker_reference_seconds=3.0)
        self.assertEqual(telemetry.examples_per_second, 2.0)
        self.assertEqual(telemetry.positions_per_second, 20.0)
        self.assertAlmostEqual(telemetry.scaling_efficiency, 0.75)
        source = "c" * 64
        evaluation = "d" * 64
        choices = (
            TopologyObservation(
                "single_fastest", -0.1, 60.0, source, evaluation,
                ("M3 Ultra",), (800.0,), (100.0,), (0.0,)),
            TopologyObservation(
                "synchronous_pair", 0.15, 50.0, source, evaluation,
                ("M3 Ultra", "M2 Ultra"), (800.0, 400.0),
                (100.0, 50.0), (10.0, 10.0)),
            TopologyObservation(
                "trainer_auxiliary", 0.2, 55.0, source, evaluation,
                ("M3 Ultra", "M2 Ultra"), (800.0, 400.0),
                (100.0, 50.0), (10.0, 10.0)),
        )
        self.assertIs(best_topology(choices), choices[2])
        with self.assertRaises(Exception):
            best_topology(choices[:2])
        self.assertIs(
            best_topology(
                (choices[0], choices[2]),
                (TopologyUnavailable("synchronous_pair", "no second host"),)),
            choices[2])
