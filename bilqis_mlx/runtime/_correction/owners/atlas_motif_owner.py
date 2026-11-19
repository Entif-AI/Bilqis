"""C09 correction ownership for B13-authenticated retained motif manifests."""
from __future__ import annotations

from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.semantics.cognitive_dependencies import (
    ArtifactKind, ArtifactNode, DependencyIndex, DependencyKind, DependencyRef,
)
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.runtime.atlas_revalidation_common import _invalid, owner_priority
from bilqis_mlx.runtime.atlas_revalidation_evidence import (
    CorrectionEvent, RevalidationFrontier,
)
from bilqis_mlx.runtime.atlas_revalidation_queue import (
    RevalidationProgress, RevalidationQueue,
)
from bilqis_mlx.runtime.atlas_revalidation_runtime import (
    advance_revalidation, apply_correction, next_revalidation_task,
    read_artifact, revalidate_node,
)
from bilqis_mlx.runtime.atlas_source_authority import SourceAuthorityRegistry


def _motif_node(cache, compiled: CompiledEncoderInput) -> tuple[ArtifactNode, tuple[str, ...]]:
    """Derive one retained-manifest node from authenticated B13 + A05 custody."""
    from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
        AcceptedExecutionCache, DistributedExecutionCache,
    )

    if (type(cache) not in (AcceptedExecutionCache, DistributedExecutionCache)
            or type(compiled) is not CompiledEncoderInput):
        _invalid("BAMF_C09_MOTIF_OWNER_INVALID")
    manifest = cache.motif_manifest
    if type(manifest) is not MotifManifest or manifest.digest != compiled.extents.motif_key_map_digest:
        _invalid("BAMF_C09_MOTIF_MANIFEST_DRIFT")
    packed_owner = compiled.packed_frame_artifact_owner
    frame_nodes = packed_owner.physical_nodes
    frame_ids = tuple(node.artifact_id for node in frame_nodes)
    dependencies = {
        *(node.reference for node in frame_nodes),
        *packed_owner.current_context_dependencies,
        DependencyRef(DependencyKind.RELEASE, "semantic-release:" + manifest.semantic_release),
        DependencyRef(DependencyKind.RELEASE, "generation:" + cache.generation_binding),
        DependencyRef(DependencyKind.SOURCE, "accepted-manifest:" + cache.accepted_manifest_sha256),
        DependencyRef(DependencyKind.SOURCE, "run:" + cache.run_id),
        DependencyRef(DependencyKind.TIME, "generation:" + str(cache.generation)),
    }
    impact, exigency = owner_priority(ArtifactKind.MOTIF)
    identity = (
        frame_ids if not packed_owner.origin_context_keys
        else ("multi-context", *frame_ids, *packed_owner.origin_context_keys)
    )
    return ArtifactNode(
        artifact_id="motif:" + manifest.digest + ":" + contract_digest(identity),
        kind=ArtifactKind.MOTIF,
        content_digest=manifest.digest,
        eligible=True,
        immediate_dependencies=tuple(sorted(dependencies)),
        impact=impact,
        exigency=exigency,
    ), frame_ids


class MotifArtifactOwner:
    """Hold retained motif state before it can alter the next B11 hidden state."""

    def __init__(self, cache, compiled: CompiledEncoderInput):
        motif, frame_ids = _motif_node(cache, compiled)
        frame_nodes = compiled.packed_frame_artifact_owner.physical_nodes
        self._artifact_id = motif.artifact_id
        self._frame_ids = frame_ids
        self._index = DependencyIndex.build((*frame_nodes, motif))
        self._queue: RevalidationQueue | None = None

    @property
    def current_node(self) -> ArtifactNode:
        return self._index.node(self._artifact_id)

    @property
    def index(self) -> DependencyIndex:
        return self._index

    def _install_context_revalidation(
        self, index: DependencyIndex, transition,
    ) -> bool:
        if (not isinstance(index, DependencyIndex)
                or {node.artifact_id for node in index.nodes}
                != {node.artifact_id for node in self._index.nodes}):
            _invalid("BAMF_C09_CONTEXT_REVALIDATION_INDEX_DRIFT")
        self._index = index
        return True

    @property
    def queue(self) -> RevalidationQueue | None:
        return self._queue

    @property
    def source_dependencies(self) -> tuple[DependencyRef, ...]:
        return tuple(sorted({
            ref
            for artifact_id in self._frame_ids
            for ref in self._index.node(artifact_id).immediate_dependencies
            if ref.kind is DependencyKind.SOURCE
        }))

    def accepts_packed_owner(self, packed_owner) -> bool:
        """Whether cached custody matches the incoming immutable frame contract."""
        frame_nodes = packed_owner.physical_nodes
        if tuple(node.artifact_id for node in frame_nodes) != self._frame_ids:
            return False
        for expected in frame_nodes:
            current = self._index.node(expected.artifact_id)
            if current.content_digest != expected.content_digest:
                return False
            current_immutable = tuple(
                ref for ref in current.immediate_dependencies
                if ref.kind is not DependencyKind.TIME)
            expected_immutable = tuple(
                ref for ref in expected.immediate_dependencies
                if ref.kind is not DependencyKind.TIME)
            if current_immutable != expected_immutable:
                return False
        return True

    def require(self, cache, compiled: CompiledEncoderInput) -> ArtifactNode:
        expected, frame_ids = _motif_node(cache, compiled)
        if frame_ids != self._frame_ids or expected.artifact_id != self._artifact_id:
            _invalid("BAMF_C09_MOTIF_OWNER_MISMATCH")
        node = self.current_node
        if (node.content_digest != expected.content_digest
                or node.immediate_dependencies != expected.immediate_dependencies):
            _invalid("BAMF_C09_MOTIF_CONTENT_DRIFT")
        from bilqis_mlx.runtime.accepted_correction_runtime import require_pending_corrections
        for artifact_id in (*self._frame_ids, node.artifact_id):
            require_pending_corrections(self, artifact_id)
        # A direct source correction holds its actual A05 input before the
        # manifest lookup can influence hidden state. Downstream motif holding
        # is propagated only when the recomputed input changes.
        if self._queue is not None:
            for artifact_id in self._frame_ids:
                read_artifact(self._index, self._queue, artifact_id)
            return read_artifact(self._index, self._queue, node.artifact_id)
        if not node.eligible:
            _invalid("BAMF_C09_ARTIFACT_INELIGIBLE")
        return node

    def apply_correction(
        self, event: CorrectionEvent, authority_registry: SourceAuthorityRegistry,
    ) -> RevalidationQueue:
        from bilqis_mlx.runtime.accepted_correction_runtime import (
            require_bound_owner_registry,
        )
        authority_registry = require_bound_owner_registry(self, authority_registry)
        self._queue = apply_correction(event, self._index, authority_registry)
        return self._queue

    def advance(
        self, frontier: RevalidationFrontier,
        authority_registry: SourceAuthorityRegistry,
    ) -> RevalidationProgress:
        from bilqis_mlx.runtime.accepted_correction_runtime import (
            require_bound_owner_registry,
        )
        authority_registry = require_bound_owner_registry(self, authority_registry)
        if self._queue is None:
            _invalid("BAMF_C09_MOTIF_REVALIDATION_NOT_HELD")
        task = next_revalidation_task(self._index, self._queue)
        if task is None:
            _invalid("BAMF_C09_MOTIF_REVALIDATION_NOT_PENDING")
        transition = revalidate_node(
            self._index.node(task.artifact_id), frontier, authority_registry)
        progress = advance_revalidation(
            self._index, self._queue, transition, authority_registry)
        self._index = progress.index
        self._queue = progress.queue
        return progress


__all__ = ("MotifArtifactOwner",)
