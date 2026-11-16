"""Current-generation binding for accepted C09 capability support."""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.runtime.atlas_capability_support_owner import (
    load_capability_support_owner,
)
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, derive_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.tests.correction.capability_support_owner_support import (
    TARGET, source_qualified_state,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    publish_genesis, provision_source_authority_registry,
    retention_decision, shape_patch, with_source_authority_registry,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY


class CapabilitySupportGenerationTests(unittest.TestCase):
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

    def test_retained_update_binds_support_to_current_execution_generation(self):
        with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_genesis(
                self.run, source_authority_registry=AUTHORITY)
            accepted_parent = load_accepted_generation(self.run)
            parent = accepted_parent.retained_state
            parent_generation = execution_generation_digest(
                parent.optimizer.parameters,
                spec=accepted_parent.topology,
                extents=accepted_parent.extents,
            )
            parent, transaction, retained, authority = source_qualified_state(
                parent,
                generation_binding=parent_generation,
                extents=accepted_parent.extents,
                spec=accepted_parent.topology,
            )
            bundle = derive_successor_bundle(
                accepted_parent,
                retained,
                parent_manifest_sha256=pointer["manifest_sha256"],
                delivery_events=({"event": "FIXTURE_CAPABILITY_SUPPORT"},),
            )
            provision_source_authority_registry(self.run, AUTHORITY)
            bundle = with_source_authority_registry(bundle, AUTHORITY)
            decision = retention_decision(parent=parent, retained=retained)
            accept_and_publish(
                self.run, bundle, retained, decision=decision,
                feature_sha256=bundle.extents.factor_map_digest,
                training_authorities=transaction.training_authorities,
            )
            accepted = load_accepted_generation(self.run)
            current_generation = execution_generation_digest(
                accepted.retained_state.optimizer.parameters,
                spec=accepted.topology,
                extents=accepted.extents,
            )
        self.assertEqual(authority.generation_binding, parent_generation)
        self.assertNotEqual(current_generation, parent_generation)
        with shape_patch(AUTHORITY):
            owner = load_capability_support_owner(self.run, TARGET)
        self.assertEqual(owner.require(TARGET, current_generation), owner.support)


if __name__ == "__main__":
    unittest.main()
