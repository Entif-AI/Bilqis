"""C08 distributed execution receipts remain verifiable on cold evidence readback."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from bilqis_mlx.runtime.atlas_resources import (
    DistributedRank, DistributedStepManifest, persist_distributed_manifest,
)
from bilqis_mlx.runtime.bamf_operator.session_parts.distributed_receipt_validation import (
    validate_distributed_step_receipts,
)


class DistributedReceiptValidationTests(unittest.TestCase):
    def test_exact_receipt_validates_and_topology_drift_fails_closed(self):
        manifest = DistributedStepManifest(
            retained_generation=3, retained_manifest_sha256="a" * 64,
            curriculum_release="b" * 64, source_release="c" * 64,
            logical_batch_digest="d" * 64, partition_seed=7, world_size=2,
            workers=(DistributedRank(0, "rank-0", "Apple M3 Ultra"),
                     DistributedRank(1, "rank-1", "Apple M2 Ultra")),
            mlx_version="0.31.1", backend="ring", numeric_precision="fp32")
        proposal = {
            "generation": 3, "accepted_manifest_sha256": "a" * 64,
            "factory_release_sha256": "b" * 64,
        }
        cost = {
            "c08_distributed_manifest_digest": manifest.digest,
            "c08_distributed_logical_batch_digest": manifest.logical_batch_digest,
            "c08_distributed_source_release": manifest.source_release,
            "c08_distributed_curriculum_release": manifest.curriculum_release,
            "c08_distributed_world_size": 2,
            "c08_distributed_backend": "ring",
            "c08_distributed_device_families":
                ["Apple M3 Ultra", "Apple M2 Ultra"],
            "c08_distributed_mlx_version": "0.31.1",
            "c08_distributed_numeric_precision": "fp32",
            "c08_distributed_reduction_policy": "fp32_weighted_mean",
        }
        steps = [{"controls": {"realized_cost": cost}}]
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            persist_distributed_manifest(root, manifest)
            validate_distributed_step_receipts(root, proposal, steps)
            drift = {"controls": {"realized_cost": {
                **cost, "c08_distributed_backend": "nccl"}}}
            with self.assertRaises(Exception):
                validate_distributed_step_receipts(root, proposal, [drift])

    def test_single_host_step_without_distributed_fields_is_noop(self):
        validate_distributed_step_receipts(
            Path("."), {}, [{"controls": {"realized_cost": {"wall_seconds": 1.0}}}])
