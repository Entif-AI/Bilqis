"""Historical acceptance adversaries for B13.5 feature authority."""
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import read_accepted_generation_feature_lineage
from bilqis_mlx.runtime.bamf_bundle import feature_authority
from bilqis_mlx.runtime.bamf_bundle.records import canonical
from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.feature_authority_lineage_support import (
    FeatureLineageCase,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.test_feature_authority import (
    feature_bound, source_features,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    accepted_state, candidate, parent_state, shape_patch,
)


class AcceptedFeatureHistoryTests(FeatureLineageCase):
    def test_successor_rejects_resigned_historical_parent_acceptance(self):
        root = source_features()
        first = self.publish_feature_genesis(root)
        retained = feature_bound(
            candidate(accepted_state(parent_state()), 1, first["manifest_sha256"]),
            root)
        self.publish(retained)

        parent_acceptance = (
            self.run / "bamf-acceptance" / f"{first['manifest_sha256']}.json")
        record = json.loads(parent_acceptance.read_text())
        record["policy_sha256"] = "0" * 64
        record["binding_sha256"] = hashlib.sha256(canonical({
            key: value for key, value in record.items()
            if key != "binding_sha256"
        })).hexdigest()
        parent_acceptance.write_text(json.dumps(record))

        with shape_patch(), self.source_replay(root), self.assertRaises(BilqisError):
            read_accepted_generation_feature_lineage(self.pointer)

    def test_long_accepted_history_has_no_python_recursion_ceiling(self):
        root = source_features()
        template = feature_bound(candidate(parent_state()), root)
        count = 1100
        manifests = [f"{index:064x}" for index in range(1, count + 1)]
        students = {}
        for generation, manifest in enumerate(manifests):
            students[manifest] = SimpleNamespace(
                run_id="long-history",
                generation=generation,
                parent_manifest_sha256=(
                    None if generation == 0 else manifests[generation - 1]),
                extents=SimpleNamespace(
                    factor_map_digest=root.digest,
                    active_semantic_digest=template.extents.active_semantic_digest),
                compiler_features=template.compiler_features,
                provenance=SimpleNamespace(release_digest=root.semantic_release),
            )

        def load_bundle(path, *, expected_manifest_sha256):
            self.assertEqual(path.name, expected_manifest_sha256)
            return students[expected_manifest_sha256]

        binding = object()
        with patch.object(
                feature_authority, "load_bamf_bundle", side_effect=load_bundle), patch.object(
                feature_authority, "accepted_binding_for_manifest",
                return_value=binding), patch.object(
                feature_authority, "parent_acceptance_anchor_from_manifest",
                return_value="a" * 64), patch.object(
                feature_authority, "_authenticate_feature_materialization",
                return_value=SimpleNamespace(features=root)):
            current, current_binding, predecessor = feature_authority._accepted_feature_chain(
                self.run, manifests[-1], students[manifests[-1]],
                expected_acceptance_sha256="b" * 64)

        self.assertIs(current, root)
        self.assertIs(current_binding, binding)
        self.assertIs(predecessor, root)
