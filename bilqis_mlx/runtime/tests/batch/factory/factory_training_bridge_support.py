"""Shared A01-backed setup for Factory-to-B11 integration tests."""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bilqis_mlx.data_plane import close_data_planes
from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.learning.source_atoms.tests.backbone_test_support import (
    SourceBackboneTestBase,
)
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.bamf_bundle import (
    authenticate_bamf_candidate_feature_context,
    issue_initial_foundation_feature_authority,
    prepare_initial_generation,
)
from bilqis_mlx.runtime.bamf_bundle.genesis.foundation import (
    initial_foundation_sidecars,
)
from bilqis_mlx.runtime.bamf_bundle.genesis.preparation_authority import (
    _factory_generation_provenance,
)
from bilqis_mlx.runtime.factory_training_bridge import prepare_factory_training_batch
from bilqis_mlx.runtime.model_topology_v2 import (
    b01_generation_authority, b01_generation_extents,
)
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import visit_provenance
from bilqis_mlx.runtime.tests.capability.factory.retention.factory_retention_live_support import (
    HP, genesis_bundle, live_factory_context,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    issue_factory_authority,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
    host_source_authority_patch,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY
from bilqis_mlx.semantics.atlas.feature_io import persist_feature_manifest


class FactoryTrainingBridgeFixture(SourceBackboneTestBase):
    def setUp(self):
        artifact = os.environ.get("BILQIS_A01_ATLAS_BUNDLE")
        if not artifact or not Path(artifact).is_dir():
            self.skipTest("BILQIS_A01_ATLAS_BUNDLE fixture is not mounted")
        self.artifact = Path(artifact)
        self.data_plane_root = TemporaryDirectory()
        self.addCleanup(self.data_plane_root.cleanup)
        self.enterContext(patch.dict(
            os.environ,
            {"BILQIS_DATA_PLANE": str(Path(self.data_plane_root.name) / "plane.sqlite3")},
        ))
        self.addCleanup(close_data_planes)
        super().setUp()
        self.enterContext(host_source_authority_patch(AUTHORITY))
        self.root = Path.cwd()
        self.context, _ = live_factory_context(
            self.root, (self.root / "vendor/legacy-v16").resolve())
        self.candidate, _ = genesis_bundle(
            self, self.snapshot, self.schema, self.artifact)
        authenticated = authenticate_bamf_candidate_feature_context(
            self.candidate, str(self.artifact))
        self.feature_root = TemporaryDirectory()
        self.addCleanup(self.feature_root.cleanup)
        self.feature_receipt = persist_feature_manifest(
            authenticated.features, self.feature_root.name)
        self.generation = execution_generation_digest(
            self.candidate.retained_state.optimizer.parameters,
            spec=self.candidate.topology, extents=self.candidate.extents)
        self.feature_context = authenticated

    def prepare(self, capability, seed, each):
        rows = tuple(self.context.draw_rows(
            seed=seed, capability=capability, each=each))
        execution = self.context.release.execution_plan.capability_map[capability]
        delivery = describe_delivered_teaching(
            self.context.release, capability,
            execution.teaching_option_ids[0], rows)
        return rows, prepare_factory_training_batch(
            self.context, self.candidate, str(self.artifact),
            self.feature_receipt.path, rows, self.generation,
            capability=capability, delivery=delivery, requested_count=each + 2,
            source_seed=seed, source_each=each,
            optimizer_step_seed=7,
            visit_provenance=visit_provenance(capability),
            teacher_strategy={"policy": "c02-parent-integration"})

    def b11_snapshot(self, compiled):
        """Return the exact process-local snapshot that issued this B11 row."""
        authority = compiled.source_execution_authority
        self.assertIsNotNone(authority)
        return authority.snapshot

    def production_genesis(self, *, run_seed=37100):
        """Build current B13 generation zero from this live Factory/A01 authority."""
        origin = Checkpoint(
            "7" * 64, "bundles/factory-training-origin", 0, True)
        factory = issue_factory_authority(
            self.context.release, self.context.graph, origin)
        features = issue_initial_foundation_feature_authority(
            self.source.selection)
        semantic, compiler, *_ = initial_foundation_sidecars(
            self.context.release, factory.admission, self.context.graph,
            run_seed=run_seed, feature_authority=features)
        motif = MotifManifest(features.features.semantic_release)
        extents = b01_generation_extents(
            semantic_abi=semantic, compiler_features=compiler,
            motif_page_count=1, motif_key_map_digest=motif.digest)
        return prepare_initial_generation(
            run_id="factory-training-live", run_seed=run_seed,
            graph=self.context.graph, factory_authority=factory,
            model_authority=b01_generation_authority(extents),
            optimizer_hyperparameters=HP,
            provenance=_factory_generation_provenance(
                self.context.release, features),
            foundation_features=features,
            delivery_events=({
                "event": "FACTORY_TRAINING_GENESIS", "optimizer_step": 0},),
        )

    def accepted_source_context(self, run_dir: Path):
        return AcceptedRuntimeHost(run_dir).source_context(
            graph=self.context.graph, source_root=self.context.source_root)


__all__ = ("FactoryTrainingBridgeFixture",)
