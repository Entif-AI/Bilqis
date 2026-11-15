"""Real-A01 B07 allocation crosses C05/B13 publication and cold custody."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning._engram.tests.test_atlas_engram_source import (
    REAL_RELEASE, SourceQualifiedMotifTests,
)
from bilqis_mlx.learning._retention.tests.motif_allocation_support import (
    CandidateMotifAllocationFixture, MOTIF,
)
from bilqis_mlx.learning.atlas_engram import MotifBudget
from bilqis_mlx.learning.atlas_candidate import resolve_candidate
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, derive_motif_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle.motif.source_continuation import (
    continue_source_qualified_motifs_from_bundle,
    seal_source_qualified_motifs_from_bundle,
    stage_source_qualified_motif_allocation,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle import helpers
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    genesis_feature_source_patch, issue_feature_authority, source_features,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import publish_genesis
from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
    host_source_authority_patch,
)
from bilqis_mlx.semantics.context_eligibility import SourceFrontier
from .support import accepted_c05_decision


@unittest.skipUnless(os.environ.get("BILQIS_ATLAS_REAL_ARTIFACT"),
                     "real repo-pinned A01 artifact required")
class MotifAllocationPublicationTests(unittest.TestCase):
    def _assert_continuation_mutation_rejected(self, run_dir, transaction, continuation):
        original_manifest = continuation.parent_manifest_sha256
        object.__setattr__(continuation, "parent_manifest_sha256", "f" * 64)
        with self.assertRaises(BilqisError):
            stage_source_qualified_motif_allocation(run_dir, transaction, continuation)
        object.__setattr__(continuation, "parent_manifest_sha256", original_manifest)

        original_extents = continuation.parent_extents_sha256
        object.__setattr__(continuation, "parent_extents_sha256", "f" * 64)
        with self.assertRaises(BilqisError):
            stage_source_qualified_motif_allocation(run_dir, transaction, continuation)
        object.__setattr__(continuation, "parent_extents_sha256", original_extents)

        approved = continuation.approved
        original_context = approved.approved_context_digest
        object.__setattr__(approved, "approved_context_digest", "f" * 64)
        with self.assertRaises(BilqisError):
            stage_source_qualified_motif_allocation(run_dir, transaction, continuation)
        object.__setattr__(approved, "approved_context_digest", original_context)

    def _assert_transition_mutation_rejected(self, run_dir, staged, parent,
                                             successor, retained, decision):
        original_pages = staged.motif_transition.added_pages
        object.__setattr__(staged.motif_transition, "added_pages", 1)
        with self.assertRaises(BilqisError):
            resolve_candidate(staged, accepted=True)
        object.__setattr__(staged.motif_transition, "added_pages", original_pages)

        original_generation_pages = successor.transition.added_pages
        object.__setattr__(successor.transition, "added_pages", 1)
        with self.assertRaises(BilqisError):
            accept_and_publish(
                run_dir, successor, retained, decision=decision,
                feature_sha256=successor.extents.factor_map_digest,
                reserve_gib=0., training_authorities=None)
        object.__setattr__(successor.transition, "added_pages", original_generation_pages)

    def test_v6_publication_cold_load_preserves_motif_allocation_and_optimizer(self):
        fixture = CandidateMotifAllocationFixture()
        fixture.setUp()
        source = SourceQualifiedMotifTests(
            "test_real_source_replay_qualifies_pinned_schema_and_owner_grants")
        (selection, source_root, graph, adapter, row, task, policy,
         seed, each, profile) = source._case()
        features = source_features(release=REAL_RELEASE)
        with TemporaryDirectory() as directory:
            run_dir = Path(directory)
            with (genesis_feature_source_patch(features),
                  host_source_authority_patch(),
                  patch.dict(os.environ, {
                    "BILQIS_DATA_PLANE": str(run_dir / "plane.sqlite3")}),
                  patch.object(helpers, "DECLARED", fixture.declared),
                  fixture._shape_patches()):
                feature_authority = issue_feature_authority(features)
                genesis = publish_genesis(
                    run_dir, foundation_features=feature_authority)
                parent = load_accepted_generation(run_dir)
                fixture.parent = parent.retained_state
                fixture.extents = parent.extents
                transaction = fixture._step()
                continuation, _frontier = seal_source_qualified_motifs_from_bundle(
                    adapter, row, selection,
                    retained_bundle_root=(run_dir / "bamf-bundles"
                                          / genesis["manifest_sha256"]),
                    expected_manifest_sha256=genesis["manifest_sha256"],
                    source_root=source_root, graph=graph, task_scope=task,
                    source_frontier=SourceFrontier(1, 1, ()), policy=policy,
                    source_seed=seed, source_each=each, budget=MotifBudget(64),
                    source_profile_parameters=profile)
                self._assert_continuation_mutation_rejected(
                    run_dir, transaction, continuation)
                staged = stage_source_qualified_motif_allocation(
                    run_dir, transaction, continuation)
                retained = resolve_candidate(staged, accepted=True)
                successor = derive_motif_successor_bundle(
                    parent, staged, retained_state=retained,
                    parent_manifest_sha256=genesis["manifest_sha256"],
                    delivery_events=({
                        "event": "BAMF_GENERATION_ACCEPTED",
                        "optimizer_step": retained.optimizer_step,
                    },))
                self.assertIs(successor.retained_state, retained)
                decision = accepted_c05_decision(
                    run_dir, staged, parent, successor, retained)
                self._assert_transition_mutation_rejected(
                    run_dir, staged, parent, successor, retained, decision)
                published = accept_and_publish(
                    run_dir, successor, retained, decision=decision,
                    feature_sha256=successor.extents.factor_map_digest,
                    reserve_gib=0., training_authorities=None)
                cold = load_accepted_generation(run_dir)
                continued, _frontier = continue_source_qualified_motifs_from_bundle(
                    adapter, row, selection,
                    retained_bundle_root=(run_dir / "bamf-bundles"
                                          / published["manifest_sha256"]),
                    expected_manifest_sha256=published["manifest_sha256"],
                    source_root=source_root, graph=graph, task_scope=task,
                    source_frontier=SourceFrontier(1, 1, ()), policy=policy,
                    source_seed=seed, source_each=each, budget=MotifBudget(64),
                    source_profile_parameters=profile)

        self.assertEqual(cold.generation, 1)
        self.assertEqual(cold.transition["kind"], "MOTIF_ALLOCATION")
        self.assertEqual(cold.extents, successor.extents)
        self.assertEqual(cold.retained_state.allocations, retained.allocations)
        self.assertEqual(published["manifest_sha256"],
                         cold.retained_state.custody.manifest_sha256)
        for tree in ("parameters", "m", "v", "update_counts"):
            np.testing.assert_array_equal(
                np.asarray(getattr(cold.retained_state.optimizer, tree)[MOTIF]),
                np.asarray(getattr(retained.optimizer, tree)[MOTIF]))
        self.assertEqual(continued.candidate.view.plan.allocated, ())
        self.assertEqual(continued.candidate.proposed.manifest.slots,
                         retained.allocations.manifest.slots)
        prior_uses = dict(retained.allocations.observed_uses)
        next_uses = dict(continued.candidate.proposed.observed_uses)
        self.assertEqual(set(next_uses), set(prior_uses))
        self.assertTrue(all(next_uses[key] > value
                            for key, value in prior_uses.items()))


if __name__ == "__main__":
    unittest.main()
