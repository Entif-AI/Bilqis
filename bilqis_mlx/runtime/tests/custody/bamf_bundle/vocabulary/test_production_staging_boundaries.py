"""Source identity and R06 reset boundaries for A02 production staging."""
from dataclasses import replace
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.capability_championship_state import (
    championship_epoch_identity, compact_championship_state,
)
from bilqis_mlx.runtime.bamf_bundle import (
    load_bamf_generation, stage_vocabulary_extension_from_source_id,
)
from bilqis_mlx.runtime.bamf_bundle.atlas_admission import (
    _issue_atlas_admission_binding, require_atlas_admission_binding,
)
import bilqis_mlx.runtime.bamf_bundle.vocabulary.admission as vocabulary_admission
from bilqis_mlx.runtime.tests.custody.bamf_bundle.vocabulary.production_staging_support import (
    A02ProductionStagingSupport,
)
from bilqis_mlx.semantics.tests.atlas.projection.helpers import (
    _fixture_bundle, _rewrite_bundle,
)


class A02ProductionStagingBoundaryTests(A02ProductionStagingSupport):
    def test_new_semantic_staging_archives_and_clears_championship_epoch(self):
        current_snapshot, _features, _optimizer = self._publish_source_parent()
        with self._source_patches(current_snapshot):
            accepted = vocabulary_admission._accepted_vocabulary_parent(
                self.run, "/artifact")
            parent, parent_manifest, parent_receipt, features, predecessor, prior = accepted
            identity = championship_epoch_identity(
                factory_release_sha256="1" * 64,
                semantic_catalog_sha256="2" * 64,
                curriculum_sha256="3" * 64,
                capability_groups=(("future:capability", "future:group"),),
                fixed_cohort_sha256="4" * 64, rubric_sha256="5" * 64,
                scope_sha256="6" * 64, source_sha256="7" * 64,
                policy_sha256="8" * 64, topology_sha256=parent.topology.digest,
                extents_sha256=parent.extents.digest, semantic_abi=parent.semantic_abi)
            state = compact_championship_state({
                "active_roles": {},
                "settled_matchups": {
                    "future:capability|" + "9" * 64 + "|" + "a" * 64: {
                        "capability": "future:capability", "winner_sha256": "9" * 64,
                    },
                },
            }, identity)
            parent = replace(parent, championship_state=state)
            accepted = (
                parent, parent_manifest, parent_receipt, features, predecessor, prior)
            staged = vocabulary_admission._stage_vocabulary_extension_from_accepted(
                self.run, Path("/source"), ("urn:concept:8192",), accepted)
        championship = staged.candidate.championship_state
        self.assertEqual(championship["active_roles"], {})
        self.assertEqual(championship["settled_matchups"], {})
        self.assertEqual(len(championship["epoch_history"]), 1)
        self.assertEqual(
            championship["epoch_history"][0]["source_manifest_sha256"],
            parent_manifest)
        binding = _issue_atlas_admission_binding(
            staged.candidate, parent,
            lease_sha256="b" * 64, source_approval_sha256="c" * 64,
            proposal_sha256="d" * 64, factory_release_sha256="e" * 64,
            staging_receipt_sha256=staged.receipt.digest,
            parent_feature_receipt_sha256=parent_receipt.digest)
        self.assertIs(require_atlas_admission_binding(staged.candidate, binding), binding)

    def test_stages_from_content_id_through_real_source_bundle_verifier(self):
        bundle = self._real_source_bundle()
        current_snapshot, _features, _optimizer = self._publish_source_parent(
            source_bundle_id=bundle.name)
        attacker_root = self.root / "attacker-source"
        attacker_root.mkdir()
        attacker, *_ = _fixture_bundle(attacker_root)
        attacker = _rewrite_bundle(
            attacker, "canonical.nt",
            (attacker / "canonical.nt").read_bytes()
            + b'<urn:attacker> <http://www.w3.org/2004/02/skos/core#definition> "other"@en .\n')
        shutil.copytree(attacker, bundle.parent / attacker.name)
        with patch.dict(
                os.environ, {"BILQIS_A01_SOURCE_BUNDLE_ROOT": str(bundle.parent)},
                clear=False), self._source_patches(current_snapshot, patch_bundle=False):
            with patch(
                    "bilqis_mlx.runtime.bamf_bundle.vocabulary.admission.shutil.disk_usage",
                    return_value=SimpleNamespace(free=0)):
                with self.assertRaises(BilqisError) as failure:
                    stage_vocabulary_extension_from_source_id(
                        self.run, "/artifact", attacker.name, ("urn:concept:8192",))
            self.assertEqual(
                failure.exception.context["reason"],
                "BAMF_A02_SOURCE_BUNDLE_ID_MISMATCH")
            with patch(
                    "bilqis_mlx.runtime.bamf_bundle.vocabulary.admission.shutil.disk_usage",
                    return_value=SimpleNamespace(free=1 << 50)):
                staged = stage_vocabulary_extension_from_source_id(
                    self.run, "/artifact", current_snapshot.source_bundle_id,
                    ("urn:concept:8192",))
        self.assertEqual(staged.receipt.status, "STAGED_NOT_ADMITTED")
        self.assertNotIn(str(bundle.parent), repr((staged.receipt.to_record(), staged.candidate.outbox)))
        self.assertEqual(
            load_bamf_generation(self.pointer, publish_missing_outbox=False).generation, 0)


class A02ContentIdentityBoundaryTests(A02ProductionStagingSupport):
    def test_wrong_content_id_is_rejected_before_staging_entry(self):
        requested = "7" * 64
        accepted = "8" * 64
        prior = SimpleNamespace(source_selection=SimpleNamespace(source_bundle_id=accepted))
        accepted_parent = (object(), "1" * 64, object(), object(), None, prior)
        with (
            patch(
                "bilqis_mlx.runtime.bamf_bundle.vocabulary.admission."
                "resolve_atlas_source_bundle", return_value=Path("/host") / requested),
            patch(
                "bilqis_mlx.runtime.bamf_bundle.vocabulary.admission."
                "_accepted_vocabulary_parent", return_value=accepted_parent),
            patch(
                "bilqis_mlx.runtime.bamf_bundle.vocabulary.admission."
                "stage_vocabulary_extension",
                side_effect=AssertionError("wrong source ID reached staging")),
        ):
            with self.assertRaises(BilqisError) as failure:
                stage_vocabulary_extension_from_source_id(
                    Path("/run"), "/artifact", requested, ("urn:concept:8192",))
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_A02_SOURCE_BUNDLE_ID_MISMATCH")
