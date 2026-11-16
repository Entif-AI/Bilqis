"""Accepted-run C09 replay, concurrency, and cold-restart custody."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.tests.test_frame_encoder import FrameEncoderTests
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost, _reset_accepted_correction_runtime_for_tests,
    record_accepted_correction, record_accepted_revalidation,
)
from bilqis_mlx.runtime.accepted_correction_ledger import correction_record
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _reset_execution_cache_owner_for_tests
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache,
    derive_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import bind_motif_artifact_owner
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, next_accepted_step, parent_state, publish_candidate, shape_patch,
    provision_source_authority_registry, with_source_authority_registry,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import (
    AUTHORITY, _event, _result, _sign_event,
)


class AcceptedCorrectionReplayTests(unittest.TestCase):
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

    def publish(self, source):
        provision_source_authority_registry(self.run, AUTHORITY)
        source = with_source_authority_registry(source, AUTHORITY)
        with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_candidate(self.run, source)
            return pointer

    def _motif_fixture(self):
        self.publish(candidate(parent_state()))
        with shape_patch(AUTHORITY):
            cache = bind_accepted_execution_cache(self.run)
        fixture = FrameEncoderTests()
        fixture.setUp()
        compiled, _vectors, _ast = fixture.compiled_inputs()
        compiled = replace(
            compiled,
            extents=replace(
                compiled.extents,
                motif_key_map_digest=cache.motif_manifest.digest,
            ),
        )
        with shape_patch(AUTHORITY):
            owner = bind_motif_artifact_owner(cache, compiled)
        return cache, compiled, owner

    def test_unresolved_correction_survives_unrelated_successor_and_cold_restart(self):
        cache, compiled, owner = self._motif_fixture()
        correction = _event(owner.source_dependencies[0])
        with shape_patch(AUTHORITY):
            AcceptedRuntimeHost(self.run).record_correction(correction)
        with self.assertRaises(BilqisError) as held:
            owner.require(cache, compiled)
        self.assertEqual(held.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")

        with shape_patch(AUTHORITY):
            parent = load_accepted_generation(self.run)
        retained = next_accepted_step(parent.retained_state, parent.extents)
        successor = derive_successor_bundle(
            parent,
            retained,
            parent_manifest_sha256=cache.accepted_manifest_sha256,
            delivery_events=({"event": "FIXTURE_SUCCESSOR"},),
        )
        self.publish(successor)
        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()

        with shape_patch(AUTHORITY):
            cold_cache = bind_accepted_execution_cache(self.run)
        cold_compiled = replace(
            compiled,
            extents=replace(
                compiled.extents,
                motif_key_map_digest=cold_cache.motif_manifest.digest,
            ),
        )
        with shape_patch(AUTHORITY), self.assertRaises(BilqisError) as cold_held:
            bind_motif_artifact_owner(cold_cache, cold_compiled)
        self.assertEqual(
            cold_held.exception.context["reason"],
            "BAMF_C09_ARTIFACT_HELD",
        )

    def test_live_reader_observes_correction_committed_by_another_process(self):
        cache, compiled, owner = self._motif_fixture()
        with shape_patch(AUTHORITY):
            self.assertIs(
                bind_accepted_execution_cache(self.run),
                cache,
            )
        correction = _event(owner.source_dependencies[0])
        record = correction_record(cache.accepted_manifest_sha256, correction)
        script = (
            "import json, pathlib, sys; "
            "from bilqis_mlx.runtime.accepted_correction_ledger import append_record; "
            "append_record(pathlib.Path(sys.argv[1]), sys.argv[2], json.loads(sys.argv[3]))"
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(self.run),
                cache.accepted_manifest_sha256,
                json.dumps(record, sort_keys=True),
            ],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout={completed.stdout!r} stderr={completed.stderr!r}",
        )

        with self.assertRaises(BilqisError) as held:
            owner.require(cache, compiled)
        self.assertEqual(held.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")

    def test_concurrent_accepted_corrections_remain_staged_until_each_revalidates(self):
        cache, compiled, owner = self._motif_fixture()
        first = _event(owner.source_dependencies[0])
        second = _sign_event(replace(
            first, event_id="correction:synthetic:2",
            source_receipt_sha256="e" * 64, new_evidence_sha256="d" * 64))
        with shape_patch(AUTHORITY):
            AcceptedRuntimeHost(self.run).record_correction(first)
            AcceptedRuntimeHost(self.run).record_correction(second)
        self.assertEqual(owner.queue.event.event_id, first.event_id)
        with self.assertRaises(BilqisError):
            owner.require(cache, compiled)
        first_node = owner.index.node(owner.queue.held_artifact_ids[0])
        with shape_patch(AUTHORITY):
            AcceptedRuntimeHost(self.run).record_revalidation(_result(
                    first_node, digest=first_node.content_digest, correction=first))
        self.assertEqual(owner.queue.event.event_id, second.event_id)
        second_node = owner.index.node(owner.queue.held_artifact_ids[0])
        with shape_patch(AUTHORITY):
            AcceptedRuntimeHost(self.run).record_revalidation(_result(
                    second_node, digest=second_node.content_digest, correction=second))
        self.assertEqual(owner.queue.held_artifact_ids, ())
        self.assertIs(owner.require(cache, compiled), owner.current_node)
