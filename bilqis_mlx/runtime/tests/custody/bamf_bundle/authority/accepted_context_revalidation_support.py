"""Shared accepted-context fixture for C09 revalidation tests."""
from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost, ContextRevalidatedArtifact, _reset_accepted_correction_runtime_for_tests,
    register_accepted_target,
)
from bilqis_mlx.runtime.accepted_correction_ledger import (
    append_record, context_invalidation_record,
)
from bilqis_mlx.runtime.accepted_correction_runtime import (
    deliver_accepted_context_invalidation,
)
from bilqis_mlx.runtime._atlas_owner_ingress import _route
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, provision_source_authority_registry,
    publish_candidate, shape_patch, with_source_authority_registry,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.correction_runtime.temporal_support import (
    source_owned_temporal_case,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import (
    AUTHORITY, _SOURCE_OWNER, _TEST_PRIVATE,
)
from bilqis_mlx.semantics.cognitive_dependencies import (
    ArtifactKind, ArtifactNode, DependencyIndex, DependencyKind, DependencyRef,
)
from bilqis_mlx.semantics.context_eligibility import C09ContextInvalidation


def signed_context_result(
    node: ArtifactNode, *, invalidation, accepted_event_id: str,
    dependencies: tuple[DependencyRef, ...] | None = None,
    digest: str | None = None, eligible: bool | None = None,
) -> ContextRevalidatedArtifact:
    result = ContextRevalidatedArtifact(
        artifact_id=node.artifact_id,
        immediate_dependencies=(
            node.immediate_dependencies if dependencies is None else dependencies),
        content_digest=node.content_digest if digest is None else digest,
        eligible=node.eligible if eligible is None else eligible,
        source_receipt_sha256="c" * 64,
        context_event_id=invalidation.event_id,
        context_invalidation_receipt_sha256=accepted_event_id,
        source_owner=_SOURCE_OWNER,
        source_signature_hex="0" * 128,
    )
    return replace(
        result,
        source_signature_hex=_TEST_PRIVATE.sign(result.signing_bytes()).hex(),
    )


class ContextOwner:
    def __init__(self, nodes: tuple[ArtifactNode, ...]):
        self._index = DependencyIndex.build(nodes)

    @property
    def index(self) -> DependencyIndex:
        return self._index

    def _install_context_revalidation(self, index: DependencyIndex, transition) -> None:
        self._index = index


class AcceptedContextFixture(unittest.TestCase):
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

    def publish(self):
        provision_source_authority_registry(self.run, AUTHORITY)
        source = with_source_authority_registry(candidate(parent_state()), AUTHORITY)
        with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_candidate(self.run, source)
            return bind_accepted_execution_cache(self.run)

    def registered_owner(self):
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
        owner = ContextOwner((direct, descendant))
        cache = self.publish()
        with shape_patch(AUTHORITY):
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256, "TEST_CONTEXT", owner
            )
            host = AcceptedRuntimeHost(self.run)
        invalidation = C09ContextInvalidation(
            old_context_digest=case.previous.digest,
            new_context_digest="e" * 64,
            reason_codes=("BAMF_CONTEXT_APPROVED_VIEW_CHANGED",),
            principal_id=case.task.principal_id,
            tenant_id=case.task.tenant_id,
            scope=case.task.scope,
            semantic_release=case.task.semantic_release,
            policy_epoch=case.policy.policy_epoch,
            rights_epoch=case.frontier.rights_epoch,
            correction_generation=case.frontier.correction_generation,
            causal_prefix_end=case.task.causal_prefix_end,
            invalidated_handles=tuple(sorted({
                handle
                for frame in case.previous.eligible.frames
                for handle in (frame.frame_handle, *frame.member_handles)
            })),
        )
        with shape_patch(AUTHORITY):
            record = context_invalidation_record(
                cache.accepted_manifest_sha256, invalidation)
            append_record(self.run, cache.accepted_manifest_sha256, record)
            deliver_accepted_context_invalidation(
                self.run, cache.accepted_manifest_sha256,
                record["event_id"], invalidation)
        return case, owner, host, invalidation, record["event_id"]
