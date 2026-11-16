"""Accepted-run C09 correction and temporal-invalidation custody."""
from dataclasses import replace
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.tests.test_frame_encoder import FrameEncoderTests
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost, _reset_accepted_correction_runtime_for_tests, record_accepted_revalidation,
    register_accepted_target,
)
from bilqis_mlx.runtime.accepted_correction_runtime import require_pending_corrections
from bilqis_mlx.runtime.accepted_correction_ledger import read_records
from bilqis_mlx.runtime.atlas_artifact_owner import PackedFrameArtifactOwner
from bilqis_mlx.runtime._atlas_owner_ingress import _route
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _reset_execution_cache_owner_for_tests
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import bind_motif_artifact_owner
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, provision_source_authority_registry,
    publish_candidate, shape_patch, with_source_authority_registry,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import (
    AUTHORITY, _event, _result,
)
from bilqis_mlx.semantics.cognitive_dependencies import (
    ArtifactKind, ArtifactNode, DependencyIndex, DependencyKind, DependencyRef,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.correction_runtime.temporal_support import (
    source_owned_temporal_case,
)


class AcceptedCorrectionRuntimeTests(unittest.TestCase):
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

    def test_signed_revalidation_replays_after_correction_and_clears_cold_hold(self):
        _cache, compiled, owner = self._motif_fixture()
        correction = _event(owner.source_dependencies[0])
        with shape_patch(AUTHORITY):
            host = AcceptedRuntimeHost(self.run)
            host.record_correction(correction)
        held = owner.index.node(owner.queue.held_artifact_ids[0])
        with shape_patch(AUTHORITY):
            host.record_revalidation(_result(
                held, digest=held.content_digest, correction=correction))
        self.assertEqual(owner.queue.held_artifact_ids, ())
        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        with shape_patch(AUTHORITY):
            cold_cache = bind_accepted_execution_cache(self.run)
            cold_owner = bind_motif_artifact_owner(cold_cache, compiled)
        self.assertEqual(cold_owner.queue.held_artifact_ids, ())
        self.assertIs(cold_owner.require(cold_cache, compiled), cold_owner.current_node)

    def test_a13_context_invalidation_is_durable_without_becoming_a_correction(self):
        case = source_owned_temporal_case()
        owner = case.owner()

        self.publish(candidate(parent_state()))
        with shape_patch(AUTHORITY):
            cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256,
                "PACKED_FRAME", owner
            )
            self.assertTrue(owner.require_row(case.row))
            host = AcceptedRuntimeHost(self.run)
            transition = host.record_context_transition(
                case.previous, case.contexts)
        self.assertEqual(len(transition.invalidations), 1)
        self.assertEqual(
            transition.invalidations[0].old_context_digest,
            case.previous.digest,
        )
        records = read_records(self.run, cache.accepted_manifest_sha256)
        self.assertEqual(records[-1]["event"], "BAMF_C09_CONTEXT_INVALIDATION")
        self.assertNotIn("correction", records[-1])
        self.assertEqual(
            records[-1]["context_invalidation"]["context_event_id"],
            transition.invalidations[0].event_id,
        )
        with self.assertRaises(BilqisError) as held:
            owner.require_row(case.row)
        self.assertEqual(held.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")

        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        cold_owner = case.owner()
        with shape_patch(AUTHORITY):
            cold_cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cold_cache.accepted_manifest_sha256,
                "PACKED_FRAME", cold_owner
            )
        with self.assertRaises(BilqisError) as cold_held:
            cold_owner.require_row(case.row)
        self.assertEqual(cold_held.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")

    def test_caller_selected_expiry_cannot_enter_accepted_context_invalidation(self):
        case = source_owned_temporal_case()
        owner = case.owner()

        self.publish(candidate(parent_state()))
        with shape_patch(AUTHORITY):
            cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256,
                "PACKED_FRAME", owner
            )
            host = AcceptedRuntimeHost(self.run)
            forged_task = replace(
                case.task,
                effective_time=case.contexts.transition_authority.effective_until,
            )
            before = read_records(self.run, cache.accepted_manifest_sha256)
            with self.assertRaises(BilqisError) as rejected:
                host.record_context_transition(
                    case.previous, case.frames, forged_task,
                    case.frontier, case.policy,
                )
        self.assertEqual(
            rejected.exception.context["reason"],
            "BAMF_C09_CONTEXT_TRANSITION_AUTHORITY_REQUIRED",
        )
        self.assertEqual(
            read_records(self.run, cache.accepted_manifest_sha256),
            before,
        )

    def test_context_invalidation_holds_direct_time_dependent_not_unchanged_descendant(self):
        case = source_owned_temporal_case()
        direct = ArtifactNode(
            "frame:context-direct", ArtifactKind.PACKED_FRAME, "a" * 64, True,
            (DependencyRef(
                DependencyKind.TIME,
                "time:asof:context:" + case.previous.digest),),
            impact=3, exigency=3,
        )
        descendant = ArtifactNode(
            "motif:context-descendant", ArtifactKind.MOTIF, "b" * 64, True,
            (direct.reference,), impact=2, exigency=2,
        )

        class Owner:
            def __init__(self):
                self.index = DependencyIndex.build((direct, descendant))

        owner = Owner()
        self.publish(candidate(parent_state()))
        with shape_patch(AUTHORITY):
            cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256, "TEST_CONTEXT", owner
            )
            AcceptedRuntimeHost(self.run).record_context_transition(
                case.previous, case.contexts)

        with self.assertRaises(BilqisError) as held:
            require_pending_corrections(owner, direct.artifact_id)
        self.assertEqual(held.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")
        self.assertIsNone(require_pending_corrections(owner, descendant.artifact_id))

    def test_caller_cannot_detach_accepted_correction_custody_from_registered_owner(self):
        case = source_owned_temporal_case()
        direct = ArtifactNode(
            "frame:tamper-direct", ArtifactKind.PACKED_FRAME, "c" * 64, True,
            (DependencyRef(
                DependencyKind.TIME,
                "time:asof:context:" + case.previous.digest),),
            impact=3, exigency=3,
        )

        class Owner:
            def __init__(self):
                self.index = DependencyIndex.build((direct,))

        owner = Owner()
        self.publish(candidate(parent_state()))
        with shape_patch(AUTHORITY):
            cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256, "TEST_TAMPER", owner
            )
            AcceptedRuntimeHost(self.run).record_context_transition(
                case.previous, case.contexts)

        owner._accepted_correction_target = None
        with self.assertRaises(BilqisError) as held:
            require_pending_corrections(owner, direct.artifact_id)
        self.assertEqual(
            held.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")

    def test_caller_cannot_select_accepted_correction_dispatch(self):
        case = source_owned_temporal_case()
        owner = case.owner()
        self.publish(candidate(parent_state()))
        with shape_patch(AUTHORITY):
            cache = bind_accepted_execution_cache(self.run)
        with self.assertRaises(TypeError):
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256, "PACKED_FRAME", owner,
                lambda current, event, source_authority: current,
            )

    def test_runtime_reset_retires_live_accepted_owner(self):
        case = source_owned_temporal_case()
        direct = ArtifactNode(
            "frame:reset-owner", ArtifactKind.PACKED_FRAME, "e" * 64, True,
            (DependencyRef(
                DependencyKind.TIME,
                "time:asof:context:" + case.previous.digest),),
            impact=3, exigency=3,
        )

        class Owner:
            def __init__(self):
                self.index = DependencyIndex.build((direct,))

        owner = Owner()
        self.publish(candidate(parent_state()))
        with shape_patch(AUTHORITY):
            cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256, "TEST_RESET", owner
            )
            AcceptedRuntimeHost(self.run).record_context_transition(
                case.previous, case.contexts)

        _reset_accepted_correction_runtime_for_tests()
        with self.assertRaises(BilqisError) as rejected:
            require_pending_corrections(owner, direct.artifact_id)
        self.assertEqual(
            rejected.exception.context["reason"],
            "BAMF_C09_ARTIFACT_OWNER_SUPERSEDED",
        )

    def test_caller_cannot_revive_superseded_accepted_owner(self):
        case = source_owned_temporal_case()
        direct = ArtifactNode(
            "frame:superseded-owner", ArtifactKind.PACKED_FRAME, "d" * 64, True,
            (DependencyRef(
                DependencyKind.TIME,
                "time:asof:context:" + case.previous.digest),),
            impact=3, exigency=3,
        )

        class Owner:
            def __init__(self, ledger):
                self.index = DependencyIndex.build((direct,))
                self.ledger = ledger

        old_owner = Owner(("old",))
        replacement = Owner(("replacement",))
        self.publish(candidate(parent_state()))
        with shape_patch(AUTHORITY):
            cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256,
                "TEST_SUPERSEDED", old_owner,
            )
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256,
                "TEST_SUPERSEDED", replacement,
            )

        old_owner._accepted_owner_superseded = False
        with self.assertRaises(BilqisError) as rejected:
            require_pending_corrections(old_owner, direct.artifact_id)
        self.assertEqual(
            rejected.exception.context["reason"],
            "BAMF_C09_ARTIFACT_OWNER_SUPERSEDED",
        )
