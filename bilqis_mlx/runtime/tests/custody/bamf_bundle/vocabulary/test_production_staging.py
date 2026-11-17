"""Full-topology A02 staging through accepted B13 custody."""
from dataclasses import replace
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import mlx.core as mx
import numpy as np

from bilqis_mlx.errors import BilqisError
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.learning.atlas_plasticity import IdentityRowAge
from bilqis_mlx.learning.frame_embeddings import semantic_bank_views
from bilqis_mlx.runtime.atlas_model_contracts import bind_candidate_active_semantic_rows
from bilqis_mlx.runtime.bamf_bundle import (
    authenticate_bamf_candidate_feature_context,
    authenticate_bamf_generation_feature_context,
    issue_initial_foundation_feature_authority,
    load_bamf_generation,
    publish_bamf_generation, publish_initial_generation, stage_vocabulary_extension,
    stage_vocabulary_extension_from_source_id,
)
from bilqis_mlx.runtime.model_topology_v2 import (
    expected_bamf_shapes, initialize_bamf_row,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    acceptance, genesis_preparation,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.vocabulary.production_staging_support import (
    A02ProductionStagingSupport,
)
from bilqis_mlx.semantics.atlas.vocabulary_factors import prepare_identity_factors


class A02ProductionStagingTests(A02ProductionStagingSupport):

    def _accept(self, bundle, *, parent_state=None):
        return publish_bamf_generation(
            self.run, bundle,
            acceptance=acceptance(bundle, parent=parent_state), reserve_gib=0.)

    def _assert_staged_bank_extension(
        self, current_snapshot, current_features, optimizer, parent, staged,
        authenticated, active_rows,
    ):
        self.assertEqual(
            load_bamf_generation(self.pointer, publish_missing_outbox=False).generation, 0)
        self.assertEqual(staged.receipt.generation, 1)
        self.assertEqual(staged.receipt.semantic_bank_count, 2)
        self.assertEqual(staged.receipt.status, "STAGED_NOT_ADMITTED")
        self.assertFalse(current_snapshot.abi(8192).active)
        self.assertEqual(active_rows.active_indices, (0, 8192))
        self.assertEqual(
            active_rows.active_semantic_digest, staged.receipt.active_set_sha256)
        banks = semantic_bank_views(
            staged.candidate.retained_state.optimizer.parameters,
            staged.candidate.extents,
            authenticated.features.semantic_release,
            active_rows.active_indices,
        )
        self.assertEqual(tuple(bank.active_rows for bank in banks), ((0,), (0,)))
        self.assertIs(
            banks[1].weights,
            staged.candidate.retained_state.optimizer.parameters["identity.bank.1"])
        self.assertNotEqual(parent.run_identity.run_seed, parent.topology.default_run_seed)
        feature_names = (
            "features.type", "features.project_type",
            "features.project_graph", "features.gates",
        )
        _, factors = prepare_identity_factors(
            current_snapshot, current_features, ("urn:concept:8192",),
            {name: parent.retained_state.optimizer.parameters[name]
             for name in feature_names},
            extents=parent.extents,
        )
        specs = {
            item.name: item for item in expected_bamf_shapes(
                parent.topology, staged.candidate.extents)
        }
        expected_row = initialize_bamf_row(
            specs["identity.bank.1"], run_seed=parent.run_identity.run_seed,
            row_id="urn:concept:8192", factor=factors[0][1],
        )
        np.testing.assert_array_equal(
            np.asarray(staged.candidate.retained_state.optimizer.parameters[
                "identity.bank.1"][0]),
            expected_row,
        )
        np.testing.assert_array_equal(
            np.asarray(staged.candidate.retained_state.optimizer.parameters["identity.bank.0"]),
            np.asarray(optimizer.parameters["identity.bank.0"]))
        self.assertTrue(bool(mx.all(
            staged.candidate.retained_state.optimizer.update_counts["identity.bank.1"] == 0)))
        self.assertIn(
            IdentityRowAge(1, 0, 0), staged.candidate.retained_state.policy.row_ages)
        with self.assertRaises(BilqisError) as failure:
            publish_bamf_generation(
                self.run, staged.candidate,
                acceptance=acceptance(
                    staged.candidate, parent=parent.retained_state),
                reserve_gib=0.)
        self.assertEqual(
            failure.exception.context["reason"], "BAMF_ATLAS_ADMISSION_EXECUTOR_REQUIRED")

    def test_stages_bank_extension_without_granting_admission(self):
        current_snapshot, current_features, optimizer = self._publish_source_parent()
        parent = load_bamf_generation(self.pointer, publish_missing_outbox=False)
        with self._source_patches(current_snapshot):
            parent_authenticated = authenticate_bamf_generation_feature_context(
                parent, "/artifact", self.pointer)
            parent_active_rows = bind_candidate_active_semantic_rows(
                parent, parent_authenticated)
            self.assertEqual(parent_active_rows.active_indices, (0,))
            forged_schema = {
                **parent.compiler_features["feature_schema"],
                "role_ids": ["urn:role:forged"],
            }
            forged_parent = replace(
                parent,
                compiler_features={
                    **parent.compiler_features,
                    "feature_schema": forged_schema,
                },
            )
            with self.assertRaises(BilqisError) as forged_failure:
                authenticate_bamf_generation_feature_context(
                    forged_parent, "/artifact", self.pointer)
            self.assertEqual(
                forged_failure.exception.context["reason"],
                "BAMF_GENERATION_POINTER_DRIFT")
            with self.assertRaises(BilqisError):
                stage_vocabulary_extension(
                    self.run, "/artifact", Path("/source"),
                    ("urn:concept:not-present",))
            staged = stage_vocabulary_extension(
                self.run, "/artifact", Path("/source"), ("urn:concept:8192",))
            authenticated = authenticate_bamf_candidate_feature_context(
                staged.candidate, "/artifact")
            active_rows = bind_candidate_active_semantic_rows(
                staged.candidate, authenticated)
        self._assert_staged_bank_extension(
            current_snapshot, current_features, optimizer, parent, staged,
            authenticated, active_rows)

if __name__ == "__main__":
    unittest.main()
