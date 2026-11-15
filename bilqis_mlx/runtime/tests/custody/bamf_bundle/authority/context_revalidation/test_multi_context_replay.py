"""Accepted C09 multi-context packed-frame and motif replay coverage."""
from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.tests.test_frame_encoder import FrameEncoderTests
from bilqis_mlx.runtime.accepted_correction_ledger import (
    append_record, context_invalidation_record,
)
from bilqis_mlx.runtime.accepted_correction_runtime import (
    deliver_accepted_context_invalidation,
)
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost, ContextRevalidationFrontier,
    _reset_accepted_correction_runtime_for_tests, register_accepted_target,
)
from bilqis_mlx.runtime.atlas_artifact_owner import PackedFrameArtifactOwner
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
    _reset_execution_cache_owner_for_tests,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    bind_motif_artifact_owner,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.correction_runtime.temporal_support import (
    source_owned_temporal_case,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.test_accepted_context_revalidation import (
    _signed_context_result,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.test_accepted_context_revalidation_ordering import (
    _event,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, provision_source_authority_registry,
    publish_candidate, shape_patch, with_source_authority_registry,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY
from bilqis_mlx.semantics.cognitive_dependencies import (
    DependencyKind, DependencyRef,
)
from bilqis_mlx.semantics.frame_compiler import CompiledFrameRows, _prefix_digest


class AcceptedMultiContextReplayTests(unittest.TestCase):
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

    def _publish(self):
        provision_source_authority_registry(self.run, AUTHORITY)
        source = with_source_authority_registry(candidate(parent_state()), AUTHORITY)
        with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_candidate(self.run, source)
            return bind_accepted_execution_cache(self.run)

    def _persist_invalidation(self, cache, event):
        with shape_patch(AUTHORITY):
            record = context_invalidation_record(
                cache.accepted_manifest_sha256, event)
            append_record(self.run, cache.accepted_manifest_sha256, record)
            deliver_accepted_context_invalidation(
                self.run, cache.accepted_manifest_sha256,
                record["event_id"], event)
        return record["event_id"]

    @staticmethod
    def _two_context_rows(case, second_digest):
        first = case.row
        second = replace(
            first,
            context_digest=second_digest,
            cache_key=_prefix_digest(
                first.source_instance_id, first.semantic_release,
                first.visible_end, first.schema_map, second_digest,
                first.positions, first.scope, first.policy_version),
        )
        mask = (True,) * len(first.positions)
        return CompiledFrameRows(
            (first, second), (first.positions, second.positions), (mask, mask))

    @staticmethod
    def _compiled_with_owner(cache, owner):
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
        object.__setattr__(compiled, "packed_frame_artifact_owner", owner)
        return compiled

    def _bind_origin_sets(self, case, rows, owner, cache):
        compiled = self._compiled_with_owner(cache, owner)
        with shape_patch(AUTHORITY):
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256, "PACKED_FRAME", owner)
            motif = bind_motif_artifact_owner(cache, compiled)
            host = AcceptedRuntimeHost(self.run)
        alternate_owner = PackedFrameArtifactOwner(
            self._two_context_rows(case, "c" * 64))
        alternate_compiled = self._compiled_with_owner(cache, alternate_owner)
        with shape_patch(AUTHORITY):
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256,
                "PACKED_FRAME", alternate_owner)
            alternate_motif = bind_motif_artifact_owner(
                cache, alternate_compiled)
            self.assertIs(motif, bind_motif_artifact_owner(cache, compiled))
            self.assertIs(
                alternate_motif,
                bind_motif_artifact_owner(cache, alternate_compiled),
            )
        self.assertNotEqual(
            alternate_motif.current_node.artifact_id,
            motif.current_node.artifact_id)
        return compiled, motif, host

    def _revalidate_primary(self, case, rows, owner, cache, compiled, motif, host):
        new_digest = "e" * 64
        invalidation = _event(case, case.previous.digest, new_digest)
        receipt = self._persist_invalidation(cache, invalidation)
        view = owner.index.node(
            owner.physical_nodes[0].artifact_id
            + ":context:" + case.previous.digest)
        old_time = DependencyRef(
            DependencyKind.TIME, "time:asof:context:" + case.previous.digest)
        new_time = DependencyRef(
            DependencyKind.TIME, "time:asof:context:" + new_digest)
        with self.assertRaises(BilqisError):
            owner.require_row(case.row)
        self.assertTrue(owner.require_row(rows.rows[1]))
        with self.assertRaises(BilqisError):
            motif.require(cache, compiled)
        view_result = _signed_context_result(
            view, invalidation=invalidation, accepted_event_id=receipt,
            dependencies=tuple(sorted(
                (set(view.immediate_dependencies) - {old_time}) | {new_time})))
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(
                ContextRevalidationFrontier((view_result,)))
        motif_result = _signed_context_result(
            motif.current_node, invalidation=invalidation,
            accepted_event_id=receipt,
            dependencies=tuple(sorted(
                (set(motif.current_node.immediate_dependencies) - {old_time})
                | {new_time})))
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(
                ContextRevalidationFrontier((motif_result,)))
            self.assertIs(motif, bind_motif_artifact_owner(cache, compiled))
        self.assertIn(new_time, motif.current_node.immediate_dependencies)
        self.assertNotIn(old_time, motif.current_node.immediate_dependencies)
        self.assertIs(motif.require(cache, compiled), motif.current_node)
        return new_time

    def _cold_reconstruct(self, rows, cache, packed_identity, motif_identity,
                          origin_keys, new_time, case):
        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        cold_owner = PackedFrameArtifactOwner(rows)
        with shape_patch(AUTHORITY):
            cold_cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cold_cache.accepted_manifest_sha256,
                "PACKED_FRAME", cold_owner)
            cold_compiled = self._compiled_with_owner(cold_cache, cold_owner)
            cold_motif = bind_motif_artifact_owner(cold_cache, cold_compiled)
        self.assertEqual(cold_owner.cache_identity, packed_identity)
        self.assertEqual(cold_owner.origin_context_keys, origin_keys)
        self.assertEqual(cold_motif.current_node.artifact_id, motif_identity)
        self.assertIn(new_time, cold_owner.current_context_dependencies)
        self.assertTrue(cold_owner.require_row(case.row))
        self.assertTrue(cold_owner.require_row(rows.rows[1]))
        self.assertIs(
            cold_motif.require(cold_cache, cold_compiled),
            cold_motif.current_node,
        )

    def test_multi_context_revalidation_and_cold_replay_keep_stable_identity(self):
        case = source_owned_temporal_case()
        rows = self._two_context_rows(case, "d" * 64)
        owner = PackedFrameArtifactOwner(rows)
        cache = self._publish()
        compiled, motif, host = self._bind_origin_sets(
            case, rows, owner, cache)
        packed_identity = owner.cache_identity
        motif_identity = motif.current_node.artifact_id
        origin_keys = owner.origin_context_keys
        new_time = self._revalidate_primary(
            case, rows, owner, cache, compiled, motif, host)
        self.assertEqual(owner.cache_identity, packed_identity)
        self.assertEqual(owner.origin_context_keys, origin_keys)
        self.assertEqual(motif.current_node.artifact_id, motif_identity)
        self.assertTrue(owner.require_row(case.row))
        self.assertTrue(owner.require_row(rows.rows[1]))
        self._cold_reconstruct(
            rows, cache, packed_identity, motif_identity,
            origin_keys, new_time, case)


if __name__ == "__main__":
    unittest.main()
