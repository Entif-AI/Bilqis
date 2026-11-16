"""B13.6 cold accepted custody requires an external generation-zero trust root."""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.data_plane import close_data_planes, data_plane
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    _reset_candidate_identity_metrics_for_tests,
    candidate_identity_metrics_snapshot,
)
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle, save_bamf_bundle
from bilqis_mlx.runtime.bamf_bundle.genesis.records import (
    InitialGenerationBinding, _mint_initial_generation_binding,
)
from bilqis_mlx.runtime.bamf_bundle.publication.genesis_trust import GENESIS_TRUST_SCHEMA
from bilqis_mlx.runtime.bamf_bundle.records import BAMF_POINTER_SCHEMA, canonical
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    genesis_preparation, publish_genesis, shape_patch,
)


class GenerationZeroColdTrustTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        close_data_planes()
        self.environment.stop()
        self.temporary.cleanup()

    def _install_package_local_genesis(self):
        self.run.mkdir(parents=True)
        # This fixture is testing the external genesis-trust requirement, not the
        # R19 lifecycle-marker gate. Supply already-existing safe B13 provenance
        # explicitly so the generic package-local path still cannot mint it.
        (self.run / ".bamf-pointer.lock").write_bytes(b"")
        with shape_patch():
            prepared = genesis_preparation(run_seed=1301)
        stage = self.run / "forged-stage"
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest = save_bamf_bundle(prepared.candidate, stage, reserve_gib=0.)
        digest = manifest["manifest_sha256"]
        target = self.run / "bamf-bundles" / digest
        target.parent.mkdir(parents=True)
        stage.rename(target)

        package_local = _mint_initial_generation_binding(prepared.candidate)
        acceptance_root = self.run / "bamf-acceptance"
        acceptance_root.mkdir()
        (acceptance_root / f"{digest}.json").write_bytes(
            canonical(package_local.to_record()))
        pointer = {
            "schema": BAMF_POINTER_SCHEMA,
            "run_id": prepared.candidate.run_id,
            "generation": 0,
            "parent_manifest_sha256": None,
            "bundle": f"bamf-bundles/{digest}",
            "manifest_sha256": digest,
            "acceptance_sha256": package_local.digest,
        }
        (self.run / "bamf-state.json").write_bytes(canonical(pointer))
        return pointer

    def test_package_local_genesis_cannot_become_live_accepted_custody(self):
        self._install_package_local_genesis()
        with shape_patch(), self.assertRaises(BilqisError) as accepted_failure:
            load_accepted_generation(self.run)
        self.assertEqual(
            accepted_failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_TRUST_ROOT_REQUIRED")

        with shape_patch(), self.assertRaises(BilqisError) as authority_failure:
            load_bamf_generation_authority(self.run / "bamf-state.json")
        self.assertEqual(
            authority_failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_TRUST_ROOT_REQUIRED")

    def test_generic_data_plane_reference_cannot_mint_genesis_trust(self):
        pointer = self._install_package_local_genesis()
        with shape_patch():
            student = load_bamf_bundle(
                self.run / pointer["bundle"],
                expected_manifest_sha256=pointer["manifest_sha256"])
        binding = InitialGenerationBinding.from_record(__import__("json").loads(
            (self.run / "bamf-acceptance" /
             f"{pointer['manifest_sha256']}.json").read_text(encoding="utf-8")))
        identity = student.run_identity
        forged = {
            "schema": GENESIS_TRUST_SCHEMA,
            "run_id": student.run_id,
            "generation": 0,
            "manifest_sha256": pointer["manifest_sha256"],
            "acceptance_sha256": binding.digest,
            "run_identity_sha256": identity.digest,
            "candidate_identity_sha256": candidate_identity_digest(
                student.retained_state),
            "topology_digest": student.topology.digest,
            "extents_digest": student.extents.digest,
            "implementation_sha256": student.implementation_sha256,
            "factory_state_sha256": "0" * 64,
            "factory_release_sha256": identity.factory_release_sha256,
            "semantic_graph_sha256": identity.semantic_graph_sha256,
            "source_identity": identity.initial_source_identity,
            "release_digest": identity.initial_release_digest,
            "teacher_identity": identity.initial_teacher_identity,
            "teacher_epoch": identity.initial_teacher_epoch,
        }
        reference = (
            f"bamf-genesis-trust-v1:{student.run_id}:"
            f"{pointer['manifest_sha256']}")
        raw = canonical(forged)
        digest = __import__("hashlib").sha256(raw).hexdigest()
        plane = data_plane()
        plane.put_object(digest, raw)
        plane.put_node(digest, raw, 0, None)
        plane.put_object_reference(reference, raw)

        with shape_patch(), self.assertRaises(BilqisError) as accepted_failure:
            load_accepted_generation(self.run)
        self.assertEqual(
            accepted_failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_TRUST_ROOT_REQUIRED")

        with shape_patch(), self.assertRaises(BilqisError) as authority_failure:
            load_bamf_generation_authority(self.run / "bamf-state.json")
        self.assertEqual(
            authority_failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_TRUST_ROOT_REQUIRED")

    def test_owner_published_trust_root_survives_data_plane_reopen(self):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_genesis(self.run, run_seed=1303)
        close_data_planes()

        with shape_patch():
            _reset_candidate_identity_metrics_for_tests()
            accepted = load_accepted_generation(self.run)
            metrics = candidate_identity_metrics_snapshot()
            authoritative, manifest = load_bamf_generation_authority(
                self.run / "bamf-state.json")

        self.assertEqual(accepted.run_identity.run_seed, 1303)
        self.assertEqual(metrics["candidate_identity_full_computations"], 1)
        self.assertGreater(metrics["candidate_identity_numerical_bytes_hashed"], 0)
        self.assertEqual(metrics["candidate_identity_binding_issues"], 1)
        self.assertEqual(authoritative.run_identity, accepted.run_identity)
        self.assertEqual(manifest, pointer["manifest_sha256"])


if __name__ == "__main__":
    unittest.main()
