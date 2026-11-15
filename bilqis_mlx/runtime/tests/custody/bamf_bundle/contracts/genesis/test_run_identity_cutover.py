"""B13 run identity cannot be minted across an identity-less historical cutover."""
from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import (
    load_bamf_generation, load_bamf_generation_authority,
    publish_bamf_generation,
)
from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
    accepted_binding_for_manifest,
)
from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle, save_bamf_bundle
from bilqis_mlx.runtime.bamf_bundle.admission import accept_and_publish
from bilqis_mlx.runtime.bamf_bundle.records import BAMF_POINTER_SCHEMA, canonical
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    acceptance, accepted_state, candidate, genesis_preparation,
    next_accepted_step, parent_state, publish_candidate,
    retention_decision, shape_patch,
)


class RunIdentityCutoverTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def _install_identityless_v2_parent(self):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            first = publish_candidate(self.run, candidate(parent_state()))
            published_parent = load_bamf_generation(self.run / "bamf-state.json")
        generation_one = candidate(
            accepted_state(
                published_parent.retained_state, published_parent.extents),
            1, first["manifest_sha256"])
        stage = self.run / "legacy-v2-stage"
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest = save_bamf_bundle(generation_one, stage)
        target = self.run / "bamf-bundles" / manifest["manifest_sha256"]
        stage.rename(target)
        accepted_one = acceptance(
            generation_one, parent=published_parent.retained_state)
        acceptance_dir = self.run / "bamf-acceptance"
        acceptance_dir.mkdir(exist_ok=True)
        (acceptance_dir / f"{manifest['manifest_sha256']}.json").write_bytes(
            canonical(accepted_one.to_record()))
        pointer = {
            "schema": BAMF_POINTER_SCHEMA,
            "run_id": generation_one.run_id,
            "generation": generation_one.generation,
            "parent_manifest_sha256": generation_one.parent_manifest_sha256,
            "bundle": f"bamf-bundles/{manifest['manifest_sha256']}",
            "manifest_sha256": manifest["manifest_sha256"],
            "acceptance_sha256": accepted_one.digest,
        }
        (self.run / "bamf-state.json").write_bytes(canonical(pointer))
        with shape_patch():
            loaded = load_bamf_generation(self.run / "bamf-state.json")
        self.assertIsNone(loaded.run_identity)
        return loaded, manifest["manifest_sha256"], accepted_one

    def _successor(self, parent, parent_manifest, *, run_identity):
        retained = next_accepted_step(parent.retained_state, parent.extents)
        return replace(
            candidate(retained, 2, parent_manifest),
            implementation_sha256=parent.implementation_sha256,
            topology=parent.topology,
            extents=parent.extents,
            provenance=parent.provenance,
            semantic_abi=dict(parent.semantic_abi),
            compiler_features=dict(parent.compiler_features),
            correction_frontier=dict(parent.correction_frontier),
            teacher_state=dict(parent.teacher_state),
            evaluation_contract=dict(parent.evaluation_contract),
            run_identity=run_identity,
        )

    def _binding(self, parent, successor):
        return acceptance(successor, parent=parent.retained_state)

    def test_identityless_historical_parent_rejects_caller_minted_run_identity(self):
        parent, parent_manifest, _parent_acceptance = self._install_identityless_v2_parent()
        with shape_patch():
            forged_identity = genesis_preparation(run_seed=1017).candidate.run_identity
        successor = self._successor(
            parent, parent_manifest, run_identity=forged_identity)
        binding = self._binding(parent, successor)
        before = json.loads((self.run / "bamf-state.json").read_text())

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), \
                self.assertRaises(BilqisError):
            publish_bamf_generation(
                self.run, successor, acceptance=binding, reserve_gib=0.)

        self.assertEqual(
            json.loads((self.run / "bamf-state.json").read_text()), before)

    def test_identityless_historical_parent_continues_without_minting_identity(self):
        parent, parent_manifest, _parent_acceptance = self._install_identityless_v2_parent()
        successor = self._successor(parent, parent_manifest, run_identity=None)
        binding = self._binding(parent, successor)

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_bamf_generation(
                self.run, successor, acceptance=binding, reserve_gib=0.)
            loaded, manifest = load_bamf_generation_authority(
                self.run / "bamf-state.json")

        self.assertEqual(pointer["generation"], 2)
        self.assertEqual(manifest, pointer["manifest_sha256"])
        self.assertIsNone(loaded.run_identity)

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            retried = publish_bamf_generation(
                self.run, successor, acceptance=binding, reserve_gib=0.)
        self.assertEqual(retried, pointer)

    def test_identityless_historical_successor_ordinary_retry_converges(self):
        parent, parent_manifest, _parent_acceptance = self._install_identityless_v2_parent()
        successor = self._successor(parent, parent_manifest, run_identity=None)
        decision = retention_decision(
            parent=parent.retained_state, retained=successor.retained_state)

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            first = accept_and_publish(
                self.run, successor, successor.retained_state,
                decision=decision,
                feature_sha256=successor.extents.factor_map_digest,
                reserve_gib=0.)
            retried = accept_and_publish(
                self.run, successor, successor.retained_state,
                decision=decision,
                feature_sha256=successor.extents.factor_map_digest,
                reserve_gib=0.)

        self.assertEqual(retried, first)
        with shape_patch():
            loaded = load_bamf_generation(self.run / "bamf-state.json")
        self.assertIsNone(loaded.run_identity)

    def test_identityless_historical_successor_retry_rejects_identity_introduction(self):
        parent, parent_manifest, _parent_acceptance = self._install_identityless_v2_parent()
        successor = self._successor(parent, parent_manifest, run_identity=None)
        binding = self._binding(parent, successor)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_bamf_generation(
                self.run, successor, acceptance=binding, reserve_gib=0.)
            forged_identity = genesis_preparation(run_seed=1023).candidate.run_identity
        forged_retry = replace(successor, run_identity=forged_identity)

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), \
                self.assertRaises(BilqisError):
            publish_bamf_generation(
                self.run, forged_retry, acceptance=binding, reserve_gib=0.)

    def test_forged_current_successor_is_not_authoritative_on_readback(self):
        parent, parent_manifest, parent_acceptance = self._install_identityless_v2_parent()
        with shape_patch():
            forged_identity = genesis_preparation(run_seed=1021).candidate.run_identity
        successor = self._successor(
            parent, parent_manifest, run_identity=forged_identity)
        binding = self._binding(parent, successor)
        stage = self.run / "forged-v3-stage"
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest = save_bamf_bundle(
                successor, stage, reserve_gib=0.,
                parent_acceptance_sha256=parent_acceptance.digest)
        target = self.run / "bamf-bundles" / manifest["manifest_sha256"]
        stage.rename(target)
        (self.run / "bamf-acceptance" / f"{manifest['manifest_sha256']}.json").write_bytes(
            canonical(binding.to_record()))
        pointer = {
            "schema": BAMF_POINTER_SCHEMA,
            "run_id": successor.run_id,
            "generation": successor.generation,
            "parent_manifest_sha256": successor.parent_manifest_sha256,
            "bundle": f"bamf-bundles/{manifest['manifest_sha256']}",
            "manifest_sha256": manifest["manifest_sha256"],
            "acceptance_sha256": binding.digest,
        }
        (self.run / "bamf-state.json").write_bytes(canonical(pointer))

        with shape_patch(), self.assertRaises(BilqisError):
            load_bamf_generation_authority(self.run / "bamf-state.json")
        with shape_patch():
            student = load_bamf_bundle(
                target, expected_manifest_sha256=manifest["manifest_sha256"])
        with self.assertRaises(BilqisError):
            accepted_binding_for_manifest(
                self.run, manifest["manifest_sha256"], student,
                expected_acceptance_sha256=binding.digest)


if __name__ == "__main__":
    unittest.main()
