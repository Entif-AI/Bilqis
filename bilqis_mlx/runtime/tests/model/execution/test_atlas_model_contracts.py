"""B11 model-contract custody regressions that require no pinned A01 bundle."""
from pathlib import Path
import hashlib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import mlx.core as mx
from lib.ithkuil.src.skos.publication import json_bytes

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.source_atoms import SourceAtomRow
from bilqis_mlx.learning.tests.test_frame_encoder import FrameEncoderTests
from bilqis_mlx.runtime.atlas_model_contracts import (
    BamfActiveSemanticRows, BamfCompiledBatch,
)
from bilqis_mlx.runtime.atlas_model_participation import _active_banks
from bilqis_mlx.runtime.atlas_model_training import (
    _require_finite_tensor_tree,
)
from bilqis_mlx.runtime.model_topology_v2 import GenerationExtents
from bilqis_mlx.runtime.tests.model.execution.active_semantic_rows_support import active_semantic_rows
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.atlas_features import FeatureSchema
from bilqis_mlx.semantics.tests.atlas.vocabulary_fixtures import _allocation_fixture


class BamfCompiledBatchOwnerTests(unittest.TestCase):
    def test_explicit_host_boundary_rejects_nonfinite_tensor_tree(self):
        _require_finite_tensor_tree(
            {"a": mx.ones((2,), dtype=mx.float32)}, "B11_PARAMETER_NONFINITE")
        with self.assertRaises(BilqisError):
            _require_finite_tensor_tree(
                {"a": mx.array([1.0, float("nan")], dtype=mx.float32)},
                "B11_PARAMETER_NONFINITE")

    def test_extracted_contracts_preserve_public_type_identity(self):
        self.assertEqual(
            BamfActiveSemanticRows.__module__,
            "bilqis_mlx.runtime.atlas_model_contracts",
        )
        self.assertEqual(
            BamfCompiledBatch.__module__,
            "bilqis_mlx.runtime.atlas_model_contracts",
        )

    def test_generation_active_rows_supersede_immutable_source_active_flags(self):
        snapshot, _prior = _allocation_fixture(highest=8192)
        self.assertFalse(snapshot.abi(8192).active)
        indices = (0, 8192)
        active_digest = hashlib.sha256(json_bytes(list(indices))).hexdigest()
        extents = GenerationExtents(2, 1, active_digest, "b" * 64, "c" * 64)
        first = mx.zeros((8192, 768), dtype=mx.float32)
        second = mx.ones((8192, 768), dtype=mx.float32)
        batch = SimpleNamespace(
            sources=(SimpleNamespace(selection=AtlasArtifactSelection(
                "/fixture", snapshot.bundle_id, snapshot.release_sha256,
                snapshot.source_bundle_id)),),
            compiled=SimpleNamespace(
                features=SimpleNamespace(semantic_release=snapshot.release_sha256),
                extents=extents,
            ),
            active_semantic_rows=SimpleNamespace(active_indices=indices),
        )
        plan = SimpleNamespace(snapshot=snapshot)
        with patch(
                "bilqis_mlx.runtime.atlas_model_participation.load_pinned_atlas_snapshot",
                side_effect=AssertionError("B11 Atlas reload"), create=True):
            banks = _active_banks(
                {"identity.bank.0": first, "identity.bank.1": second}, batch, plan)
        self.assertEqual(tuple(bank.active_rows for bank in banks), ((0,), (0,)))
        self.assertIs(banks[0].weights, first)
        self.assertIs(banks[1].weights, second)

    def test_revalidation_preserves_existing_atlas_feature_owner(self):
        fixture = FrameEncoderTests()
        fixture.setUp()
        compiled, _vectors, _ast = fixture.compiled_inputs()
        source = SourceAtomRow(
            AtlasArtifactSelection(
                "/fixture", "1" * 64, compiled.features.semantic_release,
                "2" * 64),
            {"id": "fixture:model-contract"}, {}, Path("."), 1, 1)
        batch = BamfCompiledBatch(
            compiled, (source,), FeatureSchema((), ()),
            active_semantic_rows(compiled, (11, 12)))
        owner = batch.atlas_feature_artifact_owner

        batch.__post_init__()

        self.assertIs(batch.atlas_feature_artifact_owner, owner)
        self.assertEqual(
            owner.require(compiled.features), owner.current_node)


if __name__ == "__main__":
    unittest.main()
