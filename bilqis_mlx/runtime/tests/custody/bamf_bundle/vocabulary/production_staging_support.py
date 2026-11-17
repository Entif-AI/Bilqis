"""Shared fixture support for full-topology A02 staging witnesses."""
from contextlib import ExitStack
from dataclasses import replace
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.runtime.bamf_bundle import (
    issue_initial_foundation_feature_authority,
    load_bamf_generation,
    publish_initial_generation,
)
from bilqis_mlx.runtime.bamf_bundle.genesis import foundation as genesis_foundation
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import genesis_preparation
from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
    host_source_authority_patch,
)
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.atlas_features import FeatureSchema, build_feature_manifest
from bilqis_mlx.semantics.tests.atlas.vocabulary_fixtures import _allocation_fixture
from bilqis_mlx.semantics.tests.atlas.projection.helpers import (
    _fixture_bundle, _rewrite_bundle,
)


@unittest.skipUnless(os.environ.get("BILQIS_BAMF_FULL_WITNESS"),
                     "full v2 production-staging witness is explicitly gated")
class A02ProductionStagingSupport(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.pointer = self.run / "bamf-state.json"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()
        self.host_authority = host_source_authority_patch()
        self.host_authority.__enter__()

    def tearDown(self):
        self.host_authority.__exit__(None, None, None)
        self.environment.stop()
        self.temporary.cleanup()

    def _publish_source_parent(self, *, source_bundle_id=None):
        current_base, _ = _allocation_fixture(highest=8192)
        current_snapshot = replace(
            current_base, bundle_id="4" * 64, release_sha256="5" * 64,
            source_bundle_id=source_bundle_id or "6" * 64, prior_abi_sha256=None)
        current_features = build_feature_manifest(current_snapshot, FeatureSchema((), ()))
        selection = AtlasArtifactSelection(
            "/artifact", current_snapshot.bundle_id, current_snapshot.release_sha256,
            current_snapshot.source_bundle_id)
        current_schema = FeatureSchema((), ())
        foundation_replay = patch.multiple(
            genesis_foundation,
            _source_owned_feature_schema=lambda _selection: (current_snapshot, current_schema),
            build_feature_manifest=lambda _snapshot, _schema: current_features,
        )
        with foundation_replay:
            authority = issue_initial_foundation_feature_authority(selection)
            prepared = genesis_preparation(
                run_id="a02-production-fixture", foundation_features=authority)
            with patch.object(mlx_checkpoint, "assert_headroom"):
                publish_initial_generation(self.run, prepared, reserve_gib=0.)
        parent = load_bamf_generation(self.pointer, publish_missing_outbox=False)
        self.assertEqual(parent.generation, 0)
        return current_snapshot, current_features, parent.retained_state.optimizer

    def _source_patches(self, current_snapshot, *, patch_bundle=True):
        source_nt = (
            '<urn:concept:8192> <http://www.w3.org/2004/02/skos/core#definition> '
            '"semantic role 8192"@en .\n').encode("utf-8")
        stack = ExitStack()
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_bundle.feature_authority."
            "resolve_atlas_artifact_selection",
            side_effect=lambda identity: AtlasArtifactSelection(
                "/artifact", identity.bundle_id, identity.release_sha256,
                identity.source_bundle_id)))
        for target in (
                "bilqis_mlx.runtime.bamf_bundle.feature_authority.load_pinned_atlas_snapshot",
                "bilqis_mlx.runtime.bamf_bundle.vocabulary.admission.load_pinned_atlas_snapshot",
                "bilqis_mlx.semantics.atlas.vocabulary_planning.load_pinned_atlas_snapshot",
                "bilqis_mlx.semantics.atlas.vocabulary_resources.load_pinned_atlas_snapshot"):
            stack.enter_context(patch(target, return_value=current_snapshot))
        if patch_bundle:
            stack.enter_context(patch(
                "bilqis_mlx.semantics.atlas.vocabulary_resources._verify_bundle",
                return_value=(current_snapshot.source_bundle_id, {"canonical.nt": source_nt})))
        return stack

    def _real_source_bundle(self):
        source_root = self.root / "source-bundles"
        source_root.mkdir()
        bundle, *_ = _fixture_bundle(source_root)
        canonical = (bundle / "canonical.nt").read_bytes() + (
            b'<urn:concept:8192> <http://www.w3.org/2004/02/skos/core#definition> '
            b'"semantic role 8192"@en .\n')
        return _rewrite_bundle(bundle, "canonical.nt", canonical)
