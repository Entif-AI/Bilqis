"""C07-authorized parameter extensions publish through ordinary B13 custody."""
from contextlib import ExitStack
from dataclasses import replace
import numpy as np

from bilqis_mlx.runtime.bamf_bundle import (
    load_bamf_generation, load_bamf_generation_authority,
    publish_atlas_admission_generation,
    read_accepted_generation_feature_receipt,
)
from bilqis_mlx.runtime.bamf_bundle.codec import save_bamf_bundle
from bilqis_mlx.runtime.bamf_bundle.admission import derive_successor_bundle
from bilqis_mlx.runtime.bamf_bundle import source_authority_custody as custody
from bilqis_mlx.runtime.bamf_bundle.records import BAMF_POINTER_SCHEMA, canonical
from bilqis_mlx.runtime.bamf_bundle.atlas_admission import (
    _issue_atlas_admission_binding,
)
from bilqis_mlx.runtime.atlas_source_authority import SourceAuthorityRegistry
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    acceptance, accepted_state, candidate, provision_source_authority_registry,
)
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.tests.core.test_atlas_export_clearance import REGISTRY
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    frozen_snapshot as genesis_frozen_snapshot,
    source_features as genesis_source_features,
)

from ._generation_acceptance_support import *


class AtlasAdmissionPublicationTests(GenerationAcceptanceFixture, unittest.TestCase):
    def atlas_context(self):
        features = genesis_source_features()
        stack = ExitStack()
        stack.enter_context(shape_patch())
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_bundle.feature_authority.build_feature_manifest",
            return_value=features))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_bundle.feature_authority."
            "resolve_atlas_artifact_selection",
            side_effect=lambda identity: AtlasArtifactSelection(
                "/fixture/atlas", identity.bundle_id,
                identity.release_sha256, identity.source_bundle_id)))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_bundle.feature_authority.load_pinned_atlas_snapshot",
            side_effect=genesis_frozen_snapshot))
        stack.enter_context(patch.object(mlx_checkpoint, "assert_headroom"))
        return stack

    @staticmethod
    def atlas_binding(source, parent):
        return _issue_atlas_admission_binding(
            source, parent,
            lease_sha256="9" * 64,
            source_approval_sha256="8" * 64,
            proposal_sha256="7" * 64,
            factory_release_sha256="6" * 64,
            staging_receipt_sha256="5" * 64,
            parent_feature_receipt_sha256="4" * 64,
        )

    def extension(self):
        parent = self.parent()
        source = candidate(
            parent.retained_state, 1, self._parent_pointer["manifest_sha256"])
        active = "8" * 64
        return parent, replace(
            source,
            run_identity=parent.run_identity,
            implementation_sha256=parent.implementation_sha256,
            topology=parent.topology,
            extents=replace(parent.extents, active_semantic_digest=active),
            provenance=parent.provenance,
            semantic_abi={**parent.semantic_abi, "active_set_sha256": active},
            compiler_features=dict(parent.compiler_features),
            correction_frontier=dict(parent.correction_frontier),
            teacher_state=dict(parent.teacher_state),
            evaluation_contract=dict(parent.evaluation_contract),
            transition={
                "schema": "bilqis.mlx.bamf-generation-transition/v1",
                "kind": "PARAMETER_EXTENSION",
                "invalidate_derived_caches": True,
            },
        )

    def install_historical_unanchored_parent(self):
        parent = self.parent()
        retained = accepted_state(parent.retained_state, parent.extents)
        historical = derive_successor_bundle(
            parent, retained,
            parent_manifest_sha256=self._parent_pointer["manifest_sha256"],
            delivery_events=({"event": "FIXTURE_HISTORICAL_PARENT"},),
        )
        frontier = dict(historical.correction_frontier)
        frontier.pop("source_authority_registry_origin", None)
        frontier.pop("source_authority_registry", None)
        frontier.pop("source_authority_registry_sha256", None)
        historical = replace(historical, correction_frontier=frontier)
        stage = self.run / "historical-unanchored-stage"
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest = save_bamf_bundle(historical, stage, reserve_gib=0.0)
        target = self.run / "bamf-bundles" / manifest["manifest_sha256"]
        stage.rename(target)
        accepted = acceptance(historical, parent=parent.retained_state)
        acceptance_dir = self.run / "bamf-acceptance"
        acceptance_dir.mkdir(exist_ok=True)
        (acceptance_dir / f"{manifest['manifest_sha256']}.json").write_bytes(
            canonical(accepted.to_record()))
        pointer = {
            "schema": BAMF_POINTER_SCHEMA,
            "run_id": historical.run_id,
            "generation": historical.generation,
            "parent_manifest_sha256": historical.parent_manifest_sha256,
            "bundle": f"bamf-bundles/{manifest['manifest_sha256']}",
            "manifest_sha256": manifest["manifest_sha256"],
            "acceptance_sha256": accepted.digest,
        }
        (self.run / "bamf-state.json").write_bytes(canonical(pointer))
        with shape_patch():
            return load_bamf_generation(self.run / "bamf-state.json"), pointer

    @staticmethod
    def extension_from(parent, parent_pointer):
        retained = parent.retained_state
        active = "8" * 64
        source = derive_successor_bundle(
            parent, retained,
            parent_manifest_sha256=parent_pointer["manifest_sha256"],
            delivery_events=({"event": "FIXTURE_ATLAS_EXTENSION"},),
        )
        return replace(
            source,
            extents=replace(parent.extents, active_semantic_digest=active),
            semantic_abi={**parent.semantic_abi, "active_set_sha256": active},
            transition={
                "schema": "bilqis.mlx.bamf-generation-transition/v1",
                "kind": "PARAMETER_EXTENSION",
                "invalidate_derived_caches": True,
            },
        )

    def test_retention_acceptance_cannot_publish_vocabulary_extension(self):
        _parent, source = self.extension()
        with self.assertRaises(BilqisError) as failure:
            self.publish(source, acceptance=self.binding(source))
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_ATLAS_ADMISSION_EXECUTOR_REQUIRED")
        self.assertEqual(
            json.loads((self.run / "bamf-state.json").read_text()),
            self._parent_pointer)

    def test_c07_binding_publishes_and_cold_replays_exact_generation(self):
        parent, source = self.extension()
        with self.atlas_context():
            binding = self.atlas_binding(source, parent)
            pointer = publish_atlas_admission_generation(
                self.run, source, admission=binding, reserve_gib=0.)
            loaded, manifest = load_bamf_generation_authority(
                self.run / "bamf-state.json")
            receipt = read_accepted_generation_feature_receipt(
                self.run / "bamf-state.json")

        self.assertEqual(pointer["generation"], 1)
        self.assertEqual(manifest, pointer["manifest_sha256"])
        self.assertEqual(loaded.extents, source.extents)
        self.assertEqual(
            set(loaded.retained_state.optimizer.update_counts),
            set(source.retained_state.optimizer.update_counts))
        for name, expected in source.retained_state.optimizer.update_counts.items():
            np.testing.assert_array_equal(
                np.asarray(loaded.retained_state.optimizer.update_counts[name]),
                np.asarray(expected))
        self.assertEqual(receipt.generation_manifest_sha256, manifest)
        self.assertEqual(receipt.acceptance_sha256, binding.digest)
        self.assertEqual(receipt.active_set_sha256,
                         source.extents.active_semantic_digest)

    def test_host_root_drift_rejects_direct_atlas_before_pointer_change(self):
        parent, source = self.extension()
        before = json.loads((self.run / "bamf-state.json").read_text())
        drift = SourceAuthorityRegistry((replace(
            REGISTRY.keys[0], owner_id="source:atlas-drift"),))
        with self.atlas_context():
            binding = self.atlas_binding(source, parent)
            with patch.object(
                    custody, "read_host_system_source_authority_registry",
                    return_value=drift), self.assertRaises(BilqisError) as failure:
                publish_atlas_admission_generation(
                    self.run, source, admission=binding, reserve_gib=0.)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_MISMATCH")
        self.assertEqual(
            json.loads((self.run / "bamf-state.json").read_text()), before)

    def test_already_pointed_atlas_retry_revalidates_host_root(self):
        parent, source = self.extension()
        with self.atlas_context():
            binding = self.atlas_binding(source, parent)
            first = publish_atlas_admission_generation(
                self.run, source, admission=binding, reserve_gib=0.)
        drift = SourceAuthorityRegistry((replace(
            REGISTRY.keys[0], owner_id="source:atlas-retry-drift"),))
        with self.atlas_context(), patch.object(
                custody, "read_host_system_source_authority_registry",
                return_value=drift), self.assertRaises(BilqisError) as failure:
            publish_atlas_admission_generation(
                self.run, source, admission=binding, reserve_gib=0.)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_MISMATCH")
        self.assertEqual(
            json.loads((self.run / "bamf-state.json").read_text()), first)
        with self.atlas_context():
            retried = publish_atlas_admission_generation(
                self.run, source, admission=binding, reserve_gib=0.)
        self.assertEqual(retried, first)

    def test_atlas_cannot_establish_historical_run_local_anchor(self):
        parent, parent_pointer = self.install_historical_unanchored_parent()
        source = self.extension_from(parent, parent_pointer)
        provision_source_authority_registry(self.run, REGISTRY)
        source = replace(source, correction_frontier={
            **source.correction_frontier,
            "source_authority_registry": REGISTRY.to_record(),
            "source_authority_registry_sha256": REGISTRY.digest,
        })
        before = json.loads((self.run / "bamf-state.json").read_text())
        with self.atlas_context():
            binding = self.atlas_binding(source, parent)
            with self.assertRaises(BilqisError) as failure:
                publish_atlas_admission_generation(
                    self.run, source, admission=binding, reserve_gib=0.)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_C09_SOURCE_AUTHORITY_BINDING_INVALID")
        self.assertEqual(
            json.loads((self.run / "bamf-state.json").read_text()), before)


if __name__ == "__main__":
    unittest.main()
