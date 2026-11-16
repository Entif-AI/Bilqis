"""H3 lineage regression for accepted capability-support correction ancestry."""
from __future__ import annotations

from dataclasses import replace
import os
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost,
    _reset_accepted_correction_runtime_for_tests, accepted_correction_id, record_accepted_correction,
)
from bilqis_mlx.runtime.accepted_correction_ledger import read_records
from bilqis_mlx.runtime.atlas_capability_support_owner import (
    load_capability_support_owner,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, derive_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.capability_support_journal import journal_path, read_journal
from bilqis_mlx.runtime.tests.correction.capability_support_owner_support import (
    SOURCE_ROW, TARGET, source_qualified_state,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    provision_source_authority_registry, publish_genesis, retention_decision,
    shape_patch, with_source_authority_registry,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import (
    AUTHORITY, _event, _ref, _sign_event,
)
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind


class CapabilitySupportLineageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = self.temporary.name
        from pathlib import Path
        self.run = Path(self.root) / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(Path(self.root) / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def publish_support(self):
        with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_genesis(
                self.run, source_authority_registry=AUTHORITY)
            accepted_parent = load_accepted_generation(self.run)
            parent, transaction, retained, authority = source_qualified_state(
                accepted_parent.retained_state,
                extents=accepted_parent.extents,
                spec=accepted_parent.topology,
            )
            provision_source_authority_registry(self.run, AUTHORITY)
            bundle = derive_successor_bundle(
                accepted_parent,
                retained,
                parent_manifest_sha256=pointer["manifest_sha256"],
                delivery_events=({"event": "FIXTURE_CAPABILITY_SUPPORT"},),
            )
            bundle = with_source_authority_registry(bundle, AUTHORITY)
            decision = retention_decision(parent=parent, retained=retained)
            published = accept_and_publish(
                self.run, bundle, retained, decision=decision,
                feature_sha256=bundle.extents.factor_map_digest,
                training_authorities=transaction.training_authorities)
        return published, authority

    def load_support(self, authority_registry=None):
        with shape_patch(AUTHORITY):
            if authority_registry is not None:
                from bilqis_mlx.runtime.bamf_bundle.admission import bind_accepted_execution_cache
                cache = bind_accepted_execution_cache(self.run)
                self.assertEqual(cache._correction_registry, authority_registry)
            return load_capability_support_owner(self.run, TARGET)

    def test_cold_rehydrated_correction_remains_branch_ancestor_for_supersession(self):
        published, _authority = self.publish_support()
        live = self.load_support(AUTHORITY)
        first = _event(_ref(DependencyKind.SOURCE, SOURCE_ROW))
        with shape_patch(AUTHORITY):
            accepted_id = AcceptedRuntimeHost(self.run).record_correction(first)
        self.assertEqual(live.queue.event.event_id, first.event_id)
        manifest = published["manifest_sha256"]
        hold_path = journal_path(self.run, manifest, TARGET)
        hold = read_journal(
            hold_path, capability_id=TARGET, manifest_sha256=manifest,
            artifact_id="capability-support:" + TARGET)
        self.assertEqual(hold["state"], "HELD")
        self.assertEqual(accepted_correction_id(manifest, first), accepted_id)
        self.assertEqual(
            tuple(item["event_id"] for item in read_records(self.run, manifest)),
            (accepted_id,),
        )

        _reset_accepted_correction_runtime_for_tests()
        reloaded = self.load_support(AUTHORITY)
        self.assertEqual(reloaded.queue.event.event_id, first.event_id)

        second = _sign_event(replace(
            first,
            event_id="correction:capability-support:2",
            source_receipt_sha256="e" * 64,
            new_evidence_sha256="d" * 64,
            supersedes_event_ids=(first.event_id,),
        ))
        with shape_patch(AUTHORITY):
            AcceptedRuntimeHost(self.run).record_correction(second)
        self.assertIsNotNone(reloaded.queue)
        self.assertEqual(reloaded.queue.event.event_id, second.event_id)
        records = read_records(self.run, manifest)
        self.assertEqual(len(records), 2)


if __name__ == "__main__":
    unittest.main()
