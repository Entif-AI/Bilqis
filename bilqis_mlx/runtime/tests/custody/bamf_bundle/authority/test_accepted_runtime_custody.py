"""Accepted-generation runtime custody and C09 replay witnesses."""
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
    record_accepted_correction,
)
from bilqis_mlx.runtime.accepted_correction_ledger import (
    append_record, correction_record, read_records,
)
from bilqis_mlx.runtime.atlas_revalidation import (
    SourceAuthorityKey, SourceAuthorityRegistry, SourceAuthorityScope,
)
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle import source_authority_custody as custody
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _reset_execution_cache_owner_for_tests
from bilqis_mlx.runtime.bamf_bundle.admission import (
    admit_candidate_step, bind_accepted_execution_cache,
    derive_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    AcceptedExecutionCache, CandidateExecutionCache,
    bind_candidate_execution_cache, bind_motif_artifact_owner,
    require_accepted_execution_cache, require_candidate_execution_cache,
)
from bilqis_mlx.learning.atlas_candidate import begin_candidate
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, next_accepted_step, parent_state, publish_candidate,
    shape_patch as _shape_patch,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import (
    AUTHORITY, _event, _sign_event,
)


def shape_patch():
    stack = _shape_patch()
    stack.enter_context(patch.object(
        custody, "read_host_system_source_authority_registry",
        return_value=AUTHORITY))
    return stack


class AcceptedRuntimeCustodyTests(unittest.TestCase):
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

    def publish(self, source, registry=None):
        if registry is not None:
            self.assertEqual(
                registry, AUTHORITY,
                "this suite binds its synthetic signer as the HOST registry")
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_candidate(self.run, source)

    def test_only_accepted_b13_custody_mints_live_execution_cache(self):
        self.publish(candidate(parent_state()))
        with shape_patch():
            cache = bind_accepted_execution_cache(self.run)
            rebound = bind_accepted_execution_cache(self.run)
            self.assertIs(require_accepted_execution_cache(cache), cache)
            self.assertIs(rebound, cache)
        self.assertEqual(cache.run_id, "fixture-run")
        with shape_patch():
            accepted = load_accepted_generation(self.run)
        self.assertEqual(
            cache.motif_manifest.digest,
            accepted.retained_state.allocations.manifest.digest,
        )
        with self.assertRaises(BilqisError):
            AcceptedExecutionCache()

    def test_candidate_execution_cache_is_bound_to_current_parent_and_transaction(self):
        self.publish(candidate(parent_state()))
        with shape_patch():
            accepted = load_accepted_generation(self.run)
            cache = bind_accepted_execution_cache(self.run)
            transaction = begin_candidate(accepted.retained_state)
            speculative = bind_candidate_execution_cache(
                cache, accepted, transaction,
                spec=accepted.topology, extents=accepted.extents)
            self.assertIs(require_candidate_execution_cache(speculative), speculative)
        self.assertEqual(speculative.run_id, accepted.run_id)
        self.assertEqual(speculative.generation, accepted.generation)
        self.assertEqual(
            speculative.accepted_manifest_sha256, cache.accepted_manifest_sha256)
        self.assertEqual(speculative.generation_binding, cache.generation_binding)
        with self.assertRaises(BilqisError):
            CandidateExecutionCache()

        foreign_parent = replace(accepted, retained_state=parent_state())
        with shape_patch(), self.assertRaises(BilqisError):
            bind_candidate_execution_cache(
                cache, foreign_parent, transaction,
                spec=accepted.topology, extents=accepted.extents)

    def _motif_fixture(self):
        self.publish(candidate(parent_state()), AUTHORITY)
        with shape_patch():
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
        with shape_patch():
            owner = bind_motif_artifact_owner(cache, compiled)
        return cache, compiled, owner

    def test_signed_accepted_correction_replays_into_motif_owner_after_cold_restart(self):
        cache, compiled, owner = self._motif_fixture()
        correction = _event(owner.source_dependencies[0])
        with shape_patch():
            AcceptedRuntimeHost(self.run).record_correction(correction)
        self.assertTrue(owner.queue.held_artifact_ids)
        with self.assertRaises(BilqisError):
            owner.require(cache, compiled)

        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        with shape_patch():
            cold_cache = bind_accepted_execution_cache(self.run)
            with self.assertRaises(BilqisError):
                bind_motif_artifact_owner(cold_cache, compiled)
            with self.assertRaises(BilqisError):
                bind_motif_artifact_owner(cold_cache, compiled)

    def test_stale_accepted_host_cannot_roll_forward_correction_into_successor(self):
        cache, _compiled, owner = self._motif_fixture()
        with shape_patch():
            host = AcceptedRuntimeHost(self.run)
        correction = _event(owner.source_dependencies[0])
        successor = candidate(
            next_accepted_step(parent_state()), generation=1,
            parent=cache.accepted_manifest_sha256,
        )
        self.publish(successor, AUTHORITY)
        with shape_patch(), self.assertRaises(BilqisError):
            host.record_correction(correction)

    def test_exact_retained_registry_cannot_bypass_accepted_ledger_ingress(self):
        _cache, _compiled, owner = self._motif_fixture()
        correction = _event(owner.source_dependencies[0])
        from bilqis_mlx.runtime import accepted_corrections
        leaked_owner = getattr(accepted_corrections, "_RUNTIME_OWNER", None)
        if leaked_owner is None:
            return
        retained = next(iter(leaked_owner.entries.values()))
        with shape_patch(), self.assertRaises(BilqisError):
            owner.apply_correction(correction, retained.registry)

    def test_missing_local_correction_ledger_fails_closed_after_history_exists(self):
        _cache, compiled, owner = self._motif_fixture()
        correction = _event(owner.source_dependencies[0])
        with shape_patch():
            AcceptedRuntimeHost(self.run).record_correction(correction)
        (self.run / "events.jsonl").unlink()
        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        with shape_patch():
            cold_cache = bind_accepted_execution_cache(self.run)
            with self.assertRaises(BilqisError) as caught:
                bind_motif_artifact_owner(cold_cache, compiled)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C09_CORRECTION_LEDGER_MISSING",
        )

    def test_truncated_local_correction_ledger_fails_closed_against_committed_history(self):
        _cache, compiled, owner = self._motif_fixture()
        first = _event(owner.source_dependencies[0])
        second = _sign_event(replace(
            first,
            event_id="correction:synthetic:history-2",
            source_receipt_sha256="e" * 64,
            new_evidence_sha256="d" * 64,
        ))
        with shape_patch():
            AcceptedRuntimeHost(self.run).record_correction(first)
            AcceptedRuntimeHost(self.run).record_correction(second)
        ledger = self.run / "events.jsonl"
        lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
        ledger.write_text("".join(lines[:-1]), encoding="utf-8")
        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        with shape_patch():
            cold_cache = bind_accepted_execution_cache(self.run)
            with self.assertRaises(BilqisError) as caught:
                bind_motif_artifact_owner(cold_cache, compiled)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C09_CORRECTION_HISTORY_COMMITMENT_DRIFT",
        )

if __name__ == "__main__":
    unittest.main()
