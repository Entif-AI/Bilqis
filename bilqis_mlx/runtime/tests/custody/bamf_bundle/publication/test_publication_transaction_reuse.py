"""Issue #1237: reuse authenticated B13 publication state within one transaction."""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
import bilqis_mlx.runtime.bamf_bundle.publication as publication
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    _reset_candidate_identity_metrics_for_tests, bind_candidate_identity,
    candidate_identity_metrics_snapshot,
)
from bilqis_mlx.runtime.bamf_bundle import publish_bamf_generation
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
    _reset_execution_cache_owner_for_tests,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, derive_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.tests.correction.capability_support_owner_support import (
    source_qualified_state,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    accepted_state, candidate, parent_state, publish_genesis,
    retention_decision, shape_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
    acceptance, publish_candidate,
)


class PublicationTransactionReuseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        _reset_execution_cache_owner_for_tests()
        self.environment.stop()
        self.temporary.cleanup()

    def _genesis(self):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_candidate(self.run, candidate(parent_state()))

    def _successor(self, parent, pointer):
        retained = accepted_state(
            parent.retained_state, parent.extents, parent.topology)
        return derive_successor_bundle(
            parent, retained,
            parent_manifest_sha256=pointer["manifest_sha256"],
            delivery_events=({"event": "FIXTURE_ACCEPTED"},))

    def _publish(self, bundle, parent, *, observer=None):
        return publish_bamf_generation(
            self.run, bundle,
            acceptance=acceptance(bundle, parent=parent.retained_state),
            reserve_gib=0., publication_observer=observer)

    def test_hot_publication_performs_no_additional_payload_load(self):
        pointer = self._genesis()
        _reset_execution_cache_owner_for_tests()
        original = mlx_checkpoint.load_bamf_state_payload
        metrics = []
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), patch.object(
                mlx_checkpoint, "load_bamf_state_payload", wraps=original) as payload:
            parent = load_accepted_generation(self.run)
            baseline = payload.call_count
            self._publish(self._successor(parent, pointer), parent, observer=metrics.append)
        self.assertEqual(payload.call_count - baseline, 0)
        self.assertEqual(metrics[0].parent_bundle_loads, 0)
        self.assertEqual(metrics[0].child_bundle_loads, 0)
        self.assertEqual(metrics[0].tensor_bytes_read, 0)
        self.assertGreater(metrics[0].write_bytes, 0)
        self.assertGreater(metrics[0].fsync_bytes, 0)

    def test_cold_publication_loads_parent_once_but_not_written_child(self):
        pointer = self._genesis()
        with shape_patch():
            parent = load_accepted_generation(self.run)
        bundle = self._successor(parent, pointer)
        _reset_execution_cache_owner_for_tests()
        original = mlx_checkpoint.load_bamf_state_payload
        metrics = []
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), patch.object(
                mlx_checkpoint, "load_bamf_state_payload", wraps=original) as payload:
            self._publish(bundle, parent, observer=metrics.append)
        self.assertEqual(payload.call_count, 1)
        self.assertEqual(metrics[0].parent_bundle_loads, 1)
        self.assertEqual(metrics[0].child_bundle_loads, 0)
        self.assertGreater(metrics[0].tensor_bytes_read, 0)

    def test_accept_and_publish_reuses_same_hot_parent_through_source_authority(self):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_genesis(self.run)
        _reset_execution_cache_owner_for_tests()
        original = mlx_checkpoint.load_bamf_state_payload
        metrics = []
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), patch.object(
                mlx_checkpoint, "load_bamf_state_payload", wraps=original) as payload:
            parent = load_accepted_generation(self.run)
            baseline = payload.call_count
            raw_parent, transaction, retained, _authority = source_qualified_state(
                parent.retained_state, extents=parent.extents,
                spec=parent.topology, steps=1)
            bind_candidate_identity(
                retained, parent.topology.digest, parent.extents.digest)
            bundle = derive_successor_bundle(
                parent, retained, parent_manifest_sha256=pointer["manifest_sha256"],
                delivery_events=({"event": "FIXTURE_ACCEPTED"},))
            _reset_candidate_identity_metrics_for_tests()
            accept_and_publish(
                self.run, bundle, retained,
                decision=retention_decision(parent=raw_parent, retained=retained),
                feature_sha256=bundle.extents.factor_map_digest,
                training_authorities=transaction.training_authorities,
                reserve_gib=0., publication_observer=metrics.append)
            identity_metrics = candidate_identity_metrics_snapshot()
        self.assertEqual(payload.call_count - baseline, 0)
        self.assertEqual(metrics[0].parent_bundle_loads, 0)
        self.assertEqual(metrics[0].child_bundle_loads, 0)
        self.assertEqual(metrics[0].tensor_bytes_read, 0)
        self.assertEqual(identity_metrics["candidate_identity_full_computations"], 0)
        self.assertEqual(identity_metrics["candidate_identity_numerical_bytes_hashed"], 0)
        self.assertGreater(identity_metrics["candidate_identity_require_calls"], 0)

    def test_cold_retry_rehydrates_parent_and_already_written_child(self):
        pointer = self._genesis()
        with shape_patch():
            parent = load_accepted_generation(self.run)
        bundle = self._successor(parent, pointer)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), patch.object(
                publication, "_atomic_pointer", side_effect=RuntimeError("crash")):
            with self.assertRaisesRegex(RuntimeError, "crash"):
                self._publish(bundle, parent)

        _reset_execution_cache_owner_for_tests()
        original = mlx_checkpoint.load_bamf_state_payload
        metrics = []
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), patch.object(
                mlx_checkpoint, "load_bamf_state_payload", wraps=original) as payload:
            published = self._publish(bundle, parent, observer=metrics.append)

        self.assertEqual(payload.call_count, 2)
        self.assertEqual(metrics[0].parent_bundle_loads, 1)
        self.assertEqual(metrics[0].child_bundle_loads, 1)
        self.assertGreater(metrics[0].tensor_bytes_read, 0)
        self.assertEqual(published["generation"], 1)

    def test_parent_witness_rejects_pointer_drift_before_commit(self):
        pointer = self._genesis()
        with shape_patch():
            parent = load_accepted_generation(self.run)
        bundle = self._successor(parent, pointer)
        original_save = publication._save_publication_bundle

        def save_then_drift(*args, **kwargs):
            manifest = original_save(*args, **kwargs)
            pointer_path = self.run / "bamf-state.json"
            drifted = json.loads(pointer_path.read_text())
            drifted["acceptance_sha256"] = "f" * 64
            pointer_path.write_text(json.dumps(drifted))
            return manifest

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), patch.object(
                publication, "_save_publication_bundle", side_effect=save_then_drift):
            with self.assertRaises(BilqisError) as caught:
                self._publish(bundle, parent)
        self.assertEqual(caught.exception.context["reason"], "B13_PUBLICATION_PARENT_STALE")


if __name__ == "__main__":
    unittest.main()
