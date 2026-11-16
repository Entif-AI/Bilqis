"""B13.6 generation-zero custody is distinct from C05 retention acceptance."""
from __future__ import annotations

from dataclasses import asdict, replace
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import mlx.core as mx

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
import bilqis_mlx.runtime.bamf_bundle.feature_authority as feature_authority
from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
    accepted_binding_for_manifest,
)
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import (
    InitialGenerationBinding, PreparedInitialGeneration,
    issue_initial_factory_foundation_authority,
    load_bamf_generation, load_bamf_generation_authority,
    prepare_initial_generation, publish_bamf_generation, publish_initial_generation,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    HP, acceptance, candidate, genesis_preparation,
    parent_state, shape_patch,
)
from bilqis_mlx.state_dag import persist, read_current


class GenerationZeroAuthorityTests(unittest.TestCase):
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

    def publish_genesis(self, *, run_seed=73):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            prepared = genesis_preparation(run_seed=run_seed)
            pointer = publish_initial_generation(
                self.run, prepared, reserve_gib=0.)
        return prepared, pointer

    def test_genesis_persists_run_seed_and_zero_foundation_optimizer(self):
        prepared, pointer = self.publish_genesis(run_seed=73)
        with shape_patch():
            student = load_bamf_generation(self.run / "bamf-state.json")

        self.assertEqual(student.generation, 0)
        self.assertEqual(student.run_identity.run_seed, 73)
        self.assertEqual(student.run_identity.digest,
                         prepared.candidate.run_identity.digest)
        self.assertEqual(student.retained_state.optimizer_step, 0)
        self.assertEqual(student.retained_state.policy.mode, "FOUNDATION")
        self.assertEqual(student.parent_manifest_sha256, None)
        self.assertEqual(pointer["acceptance_sha256"], prepared.binding.digest)
        for tree in (student.retained_state.optimizer.m,
                     student.retained_state.optimizer.v,
                     student.retained_state.optimizer.update_counts):
            for value in tree.values():
                self.assertFalse(bool(mx.any(value)))

    def test_generation_zero_authenticates_through_shared_accepted_authority_loader(self):
        prepared, pointer = self.publish_genesis(run_seed=74)
        with shape_patch():
            student, manifest = load_bamf_generation_authority(
                self.run / "bamf-state.json")
        self.assertEqual(manifest, pointer["manifest_sha256"])
        self.assertEqual(student.run_identity.digest,
                         prepared.candidate.run_identity.digest)
        self.assertEqual(student.run_identity.run_seed, 74)

    def test_generation_zero_refuses_c05_candidate_acceptance(self):
        legacy = candidate(parent_state())
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            with self.assertRaises(BilqisError) as failure:
                publish_bamf_generation(
                    self.run, legacy, acceptance=acceptance(legacy), reserve_gib=0.)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_BOOTSTRAP_REQUIRED")

    def test_generation_zero_feature_authority_refuses_legacy_c05_binding(self):
        legacy = candidate(parent_state())
        binding = acceptance(legacy)
        manifest_sha = "f" * 64
        acceptance_dir = self.run / "bamf-acceptance"
        acceptance_dir.mkdir(parents=True)
        (acceptance_dir / f"{manifest_sha}.json").write_text(
            json.dumps(binding.to_record()))
        pointer = {
            "schema": "bilqis.mlx.bamf-generation-pointer/v2",
            "manifest_sha256": manifest_sha,
            "acceptance_sha256": binding.digest,
        }
        with self.assertRaises(BilqisError) as failure:
            accepted_binding_for_manifest(
                self.run, manifest_sha, legacy,
                expected_acceptance_sha256=binding.digest)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_GENERATION_ACCEPTANCE_INVALID")

    def test_source_admission_drift_rejects_before_any_run_write(self):
        from bilqis_mlx.runtime.model_topology_v2 import (
            b01_generation_authority,
        )
        with shape_patch():
            prepared = genesis_preparation(run_seed=73)
        admission = replace(prepared.admission, student_sha256="8" * 64)
        with shape_patch(), self.assertRaises(BilqisError) as failure:
            prepare_initial_generation(
                run_id="fixture-run", run_seed=73,
                factory_authority=prepared.factory_authority,
                origin_checkpoint=prepared.origin_checkpoint,
                release=prepared.release, admission=admission,
                graph=prepared.graph,
                model_authority=b01_generation_authority(prepared.candidate.extents),
                optimizer_hyperparameters=HP,
                provenance=prepared.candidate.provenance,
                foundation_features=prepared.foundation_features)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_SOURCE_AUTHORITY_DRIFT")
        self.assertFalse(self.run.exists())

    def test_factory_foundation_accepts_current_descendant_of_admitted_baseline(self):
        with shape_patch():
            prepared = genesis_preparation(run_seed=74)
        source = Path(prepared.factory_authority.source_run_dir)
        current = read_current(source)
        descendant = replace(
            prepared.origin_checkpoint,
            sha256="8" * 64,
            optimizer_step=prepared.origin_checkpoint.optimizer_step + 1,
        )
        persist(source, {
            **current,
            "generation": current["generation"] + 1,
            "school": {
                **current["school"],
                "current_student": asdict(descendant),
            },
        })

        authority = issue_initial_factory_foundation_authority(source, prepared.graph)

        self.assertEqual(authority.admission, prepared.admission)
        self.assertEqual(authority.origin_checkpoint, descendant)

    def test_corrupt_run_identity_sidecar_rejects_cold_read(self):
        _, pointer = self.publish_genesis(run_seed=79)
        bundle = self.run / "bamf-bundles" / pointer["manifest_sha256"]
        identity = bundle / "run-identity.json"
        record = json.loads(identity.read_text())
        record["run_seed"] = 80
        identity.write_text(json.dumps(record, sort_keys=True))
        with shape_patch(), self.assertRaises(BilqisError):
            load_bamf_generation(self.run / "bamf-state.json")

    def test_persisted_bootstrap_record_never_regains_live_authority(self):
        prepared = None
        with shape_patch():
            prepared = genesis_preparation(run_seed=91)
        parsed = InitialGenerationBinding.from_record(prepared.binding.to_record())
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            with self.assertRaises(BilqisError):
                publish_initial_generation(
                    self.run,
                    PreparedInitialGeneration(
                        prepared.candidate, parsed, prepared.factory_authority,
                        prepared.graph, prepared.foundation_features),
                    reserve_gib=0.)

    def test_exact_retry_converges_and_conflicting_seed_cannot_replace_genesis(self):
        prepared, first = self.publish_genesis(run_seed=101)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            second = publish_initial_generation(
                self.run, prepared, reserve_gib=0.)
            foreign = genesis_preparation(run_seed=102)
            with self.assertRaises(BilqisError):
                publish_initial_generation(self.run, foreign, reserve_gib=0.)
        self.assertEqual(first, second)
        self.assertEqual(
            json.loads((self.run / "bamf-state.json").read_text()), first)

    def _advance_factory_source(self, prepared):
        source = Path(prepared.factory_authority.source_run_dir)
        current = read_current(source)
        advanced = dict(current)
        advanced["generation"] = current["generation"] + 1
        school = dict(current["school"])
        checkpoint = dict(school["current_student"])
        checkpoint.update(
            optimizer_step=checkpoint["optimizer_step"] + 1,
            sha256="8" * 64, filename="bundles/advanced")
        school["current_student"] = checkpoint
        advanced["school"] = school
        persist(source, advanced)

    def test_exact_retry_converges_after_upstream_factory_advances(self):
        prepared, first = self.publish_genesis(run_seed=109)
        self._advance_factory_source(prepared)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            second = publish_initial_generation(
                self.run, prepared, reserve_gib=0.)
        self.assertEqual(second, first)
        self.assertEqual(
            json.loads((self.run / "bamf-state.json").read_text()), first)

    def test_unpublished_stale_preparation_still_requires_current_factory_authority(self):
        with shape_patch():
            prepared = genesis_preparation(run_seed=113)
        self._advance_factory_source(prepared)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), \
                self.assertRaises(BilqisError) as failure:
            publish_initial_generation(self.run, prepared, reserve_gib=0.)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_FACTORY_AUTHORITY_DRIFT")
        self.assertFalse((self.run / "bamf-state.json").exists())

    def test_bootstrap_binding_cannot_authorize_successor_publication(self):
        prepared, first = self.publish_genesis(run_seed=117)
        successor = replace(
            prepared.candidate, generation=1,
            parent_manifest_sha256=first["manifest_sha256"],
            transition={
                "schema": "bilqis.mlx.bamf-generation-transition/v1",
                "kind": "RETAINED_CANDIDATE",
                "invalidate_derived_caches": False,
            })
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            with self.assertRaises(BilqisError) as failure:
                publish_bamf_generation(
                    self.run, successor, acceptance=prepared.binding,
                    reserve_gib=0.)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_GENERATION_ACCEPTANCE_REQUIRED")


if __name__ == "__main__":
    unittest.main()
