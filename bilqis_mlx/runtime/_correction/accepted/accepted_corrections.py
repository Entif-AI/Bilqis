"""Accepted-generation C09 correction and revalidation ingress."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .accepted_correction_ledger import (
    accepted_correction_id, accepted_corrections, append_current_record,
    CONTEXT_INVALIDATION_EVENT, context_invalidation_record,
    context_revalidation_record, correction_record, read_records,
    revalidation_record,
)
from .accepted_stale_replay_ledger import (
    derived_claim_record, remediation_record,
)
from .accepted_correction_runtime import (
    _reset_accepted_correction_runtime_for_tests,
    deliver_accepted_context_invalidation,
    deliver_accepted_context_revalidation,
    deliver_accepted_correction,
    deliver_accepted_revalidation,
    register_accepted_target,
    register_accepted_support_target,
    register_compiled_batch, register_solve_context,
    replay_accepted_stale_evidence,
)
from .atlas_revalidation_common import _invalid
from .atlas_revalidation_evidence import CorrectionEvent, RevalidationFrontier
from .atlas_source_authority import SourceAuthorityRegistry
from .context_revalidation import (
    ContextRevalidatedArtifact, ContextRevalidationFrontier,
)
from .atlas_stale_replay import DerivedClaim, RemediationReceipt
from bilqis_mlx.semantics.cognitive_dependencies import (
    DependencyKind, DependencyRef,
)


@dataclass(frozen=True)
class AcceptedRuntimeHost:
    """Host-owned production ingress for one accepted run's C09 authority."""

    run_dir: Path
    _accepted_cache: object | None = field(
        default=None, init=False, repr=False, compare=False)
    _source_authority: object | None = field(
        default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.run_dir, Path):
            _invalid("BAMF_C09_ACCEPTED_RUNTIME_HOST_INVALID")
        from bilqis_mlx.runtime.bamf_bundle.admission import (
            bind_accepted_execution_cache,
        )
        from bilqis_mlx.runtime.atlas_source_authority import (
            _provision_source_authority_runtime,
        )

        cache = bind_accepted_execution_cache(self.run_dir)
        if not isinstance(cache._correction_registry, SourceAuthorityRegistry):
            _invalid("BAMF_C09_CORRECTION_AUTHORITY_REQUIRED")
        authority = _provision_source_authority_runtime(cache)
        object.__setattr__(self, "_accepted_cache", cache)
        object.__setattr__(self, "_source_authority", authority)

    def source_authority(self):
        """Return only the opaque source authority owned by this accepted host."""
        from bilqis_mlx.runtime.atlas_source_authority import (
            require_source_authority_runtime,
        )
        from bilqis_mlx.runtime.bamf_bundle.admission import (
            bind_accepted_execution_cache,
        )

        cache = bind_accepted_execution_cache(self.run_dir)
        return require_source_authority_runtime(self._source_authority, cache)

    def source_context(self, *, graph: dict | None = None, source_root: Path | None):
        """Mint context for the Factory release bound by accepted B13 custody."""
        self.source_authority()
        from bilqis_mlx.factory.live_answers import live_answer_registry
        from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
        from bilqis_mlx.runtime.source_execution import SourceExecutionContext
        from bilqis_mlx.source_adapters.school import live_source_registry

        student = load_accepted_generation(self.run_dir)
        from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_factory_release
        release = read_accepted_atlas_factory_release(self.run_dir)
        release_sha256 = release.release_sha256
        receipt = {
            "factory_release_sha256": release_sha256,
            "factory_release_file": f"factory-releases/{release_sha256}.json",
        }
        if graph is None:
            recorded = student.compiler_features.get("factory_semantic_catalog")
            graph_sha256 = student.compiler_features.get("factory_semantic_graph_sha256")
            catalog_sha256 = student.compiler_features.get("factory_semantic_catalog_sha256")
            if (not isinstance(recorded, dict)
                    or catalog_sha256 != release.semantic_catalog_sha256):
                _invalid("BAMF_ACCEPTED_SEMANTIC_CATALOG_REQUIRED")
            from copy import deepcopy
            from bilqis_mlx.runtime.state import _fingerprint
            graph = deepcopy(recorded)
            if _fingerprint(graph) != graph_sha256:
                _invalid("BAMF_ACCEPTED_SEMANTIC_CATALOG_DRIFT")
            try:
                release.verify_semantic_catalog(graph)
            except (TypeError, ValueError):
                _invalid("BAMF_ACCEPTED_SEMANTIC_CATALOG_DRIFT")
        return SourceExecutionContext.from_admitted_release(
            self.run_dir, receipt, graph=graph, source_root=source_root,
            source_registry=live_source_registry(),
            answer_registry=live_answer_registry(),
            accepted_runtime_host=self,
        )

    def record_correction(self, event: CorrectionEvent) -> str:
        return record_accepted_correction(self, event)

    def record_context_transition(self, previous, contexts, *caller_state):
        return record_accepted_context_transition(
            self, previous, contexts, *caller_state)

    def record_context_revalidation(
        self, frontier: ContextRevalidationFrontier,
    ) -> str:
        return record_accepted_context_revalidation(self, frontier)

    def record_revalidation(self, frontier: RevalidationFrontier) -> str:
        return record_accepted_revalidation(self, frontier)

    def record_remediation(self, remediation: RemediationReceipt) -> str:
        return record_accepted_remediation(self, remediation)

    def record_derived_claim(self, claim: DerivedClaim):
        return record_accepted_derived_claim(self, claim)


def _host_run_dir(host: AcceptedRuntimeHost) -> Path:
    if type(host) is not AcceptedRuntimeHost:
        _invalid("BAMF_C09_ACCEPTED_RUNTIME_HOST_REQUIRED")
    host.source_authority()
    return host.run_dir


def record_accepted_correction(
    host: AcceptedRuntimeHost, event: CorrectionEvent,
) -> str:
    """Persist and synchronously deliver one signed correction to live owners."""
    from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
        _accepted_correction_registry,
    )

    if not isinstance(event, CorrectionEvent):
        _invalid("BAMF_C09_CORRECTION_EVENT_REQUIRED")
    run_dir = _host_run_dir(host)
    cache, registry = _accepted_correction_registry(run_dir)
    registry.verify_correction(event)
    record = correction_record(cache.accepted_manifest_sha256, event)
    append_current_record(run_dir, cache.accepted_manifest_sha256, record)
    deliver_accepted_correction(
        run_dir, cache.accepted_manifest_sha256, record["event_id"], event)
    return record["event_id"]


def record_accepted_context_transition(
    host: AcceptedRuntimeHost, previous, contexts, *caller_state,
):
    """Persist only source-authorized A13 invalidations without correction authority."""
    from bilqis_mlx.runtime.bamf_bundle.admission import bind_accepted_execution_cache
    from bilqis_mlx.factory.skos_curriculum.source_context import (
        SourceLessonContexts, source_lesson_expiry_task,
    )
    from bilqis_mlx.factory.skos_curriculum.source_context_policy import (
        source_context_temporal_identity,
    )
    from bilqis_mlx.semantics.context_eligibility import transition_context
    from bilqis_mlx.semantics.context_eligibility import SourceFrontier

    if (caller_state or type(contexts) is not SourceLessonContexts
            or contexts.transition_authority is None):
        _invalid("BAMF_C09_CONTEXT_TRANSITION_AUTHORITY_REQUIRED")
    contexts.__post_init__()
    authority = contexts.transition_authority
    source_frontier = SourceFrontier(
        authority.frontier.rights_epoch,
        authority.frontier.correction_generation,
        contexts.grants,
    )
    task_scope = source_lesson_expiry_task(
        contexts, authority.task, source_frontier, authority.policy)
    frames = (contexts.positive.envelope, contexts.contrast.envelope)

    run_dir = _host_run_dir(host)
    cache = bind_accepted_execution_cache(run_dir)
    temporal = source_context_temporal_identity(authority)
    transition = transition_context(
        previous, frames, task_scope, source_frontier, authority.policy,
        temporal_identity={
            "source_time": temporal["source_time"],
            "effective_time": temporal["effective_time"],
            "observed_at": temporal["observed_at"],
            "recorded_at": temporal["recorded_at"],
            "temporal_authority_sha256":
                temporal["authority_registry_sha256"],
        },
    )
    if not transition.invalidations:
        return transition
    for event in transition.invalidations:
        record = context_invalidation_record(
            cache.accepted_manifest_sha256, event, authority)
        append_current_record(run_dir, cache.accepted_manifest_sha256, record)
        deliver_accepted_context_invalidation(
            run_dir, cache.accepted_manifest_sha256, record["event_id"], event)
    return transition


def record_accepted_revalidation(
    host: AcceptedRuntimeHost, frontier: RevalidationFrontier,
) -> str:
    """Persist signed source recomputation evidence and advance live holds."""
    from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
        _accepted_correction_registry,
    )

    if not isinstance(frontier, RevalidationFrontier) or not frontier.results:
        _invalid("BAMF_C09_REVALIDATION_FRONTIER_REQUIRED")
    run_dir = _host_run_dir(host)
    cache, registry = _accepted_correction_registry(run_dir)
    for result in frontier.results:
        registry.verify_revalidation(result)
    corrections = {
        event.event_id: event
        for _event_id, event in accepted_corrections(
            run_dir, cache.accepted_manifest_sha256)
    }
    for result in frontier.results:
        correction = corrections.get(result.correction_event_id)
        if (correction is None
                or correction.source_receipt_sha256
                != result.correction_receipt_sha256):
            _invalid("BAMF_C09_REVALIDATION_CORRECTION_MISSING")
    record = revalidation_record(cache.accepted_manifest_sha256, frontier)
    append_current_record(run_dir, cache.accepted_manifest_sha256, record)
    deliver_accepted_revalidation(
        run_dir, cache.accepted_manifest_sha256, record["event_id"], frontier)
    return record["event_id"]


def record_accepted_context_revalidation(
    host: AcceptedRuntimeHost, frontier: ContextRevalidationFrontier,
) -> str:
    """Persist source-signed context recomputation without inventing a correction."""
    from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
        _accepted_correction_registry,
    )

    if (not isinstance(frontier, ContextRevalidationFrontier)
            or not frontier.results):
        _invalid("BAMF_C09_CONTEXT_REVALIDATION_FRONTIER_REQUIRED")
    run_dir = _host_run_dir(host)
    cache, registry = _accepted_correction_registry(run_dir)
    records = read_records(run_dir, cache.accepted_manifest_sha256)
    invalidations = {
        item["context_invalidation"]["context_event_id"]: item
        for item in records
        if item["event"] == CONTEXT_INVALIDATION_EVENT
    }
    for result in frontier.results:
        invalidation = invalidations.get(result.context_event_id)
        if (invalidation is None
                or invalidation["event_id"]
                != result.context_invalidation_receipt_sha256):
            _invalid("BAMF_C09_CONTEXT_REVALIDATION_INVALIDATION_MISSING")
        registry.verify_detached(
            result.source_owner,
            DependencyRef(DependencyKind.ARTIFACT, result.artifact_id),
            result.source_signature_hex,
            result.signing_bytes(),
        )
    record = context_revalidation_record(
        cache.accepted_manifest_sha256, frontier)
    append_current_record(run_dir, cache.accepted_manifest_sha256, record)
    deliver_accepted_context_revalidation(
        run_dir, cache.accepted_manifest_sha256, record["event_id"], frontier)
    return record["event_id"]


def record_accepted_remediation(
    host: AcceptedRuntimeHost, remediation: RemediationReceipt,
) -> str:
    """Persist one claimed repair outcome against an accepted signed correction."""
    from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
        _accepted_correction_registry,
    )

    if not isinstance(remediation, RemediationReceipt):
        _invalid("BAMF_C09_REMEDIATION_RECEIPT_INVALID")
    run_dir = _host_run_dir(host)
    cache, registry = _accepted_correction_registry(run_dir)
    corrections = {
        event.event_id: event
        for _event_id, event in accepted_corrections(
            run_dir, cache.accepted_manifest_sha256)
    }
    correction = corrections.get(remediation.correction_event_id)
    if (correction is None
            or correction.source_receipt_sha256
            != remediation.correction_receipt_sha256):
        _invalid("BAMF_C09_REMEDIATION_CORRECTION_MISSING")
    record = remediation_record(cache.accepted_manifest_sha256, remediation)
    append_current_record(run_dir, cache.accepted_manifest_sha256, record)
    replay_accepted_stale_evidence(run_dir, cache.accepted_manifest_sha256)
    return record["event_id"]


def record_accepted_derived_claim(
    host: AcceptedRuntimeHost, claim: DerivedClaim,
) -> tuple[str, tuple[object, ...]]:
    """Persist later evidence and classify any proven post-remediation stale replay."""
    from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
        _accepted_correction_registry,
    )

    if not isinstance(claim, DerivedClaim):
        _invalid("BAMF_C09_DERIVED_CLAIM_INVALID")
    run_dir = _host_run_dir(host)
    cache, registry = _accepted_correction_registry(run_dir)
    record = derived_claim_record(cache.accepted_manifest_sha256, claim)
    append_current_record(run_dir, cache.accepted_manifest_sha256, record)
    results = replay_accepted_stale_evidence(
        run_dir, cache.accepted_manifest_sha256)
    return record["event_id"], results


__all__ = (
    "AcceptedRuntimeHost", "_reset_accepted_correction_runtime_for_tests",
    "accepted_correction_id",
    "accepted_corrections", "ContextRevalidatedArtifact",
    "ContextRevalidationFrontier",
    "register_accepted_target",
    "register_compiled_batch", "register_solve_context",
    "register_accepted_support_target",
)
