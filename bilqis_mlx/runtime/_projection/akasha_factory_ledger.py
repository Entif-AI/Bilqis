"""CT-052 deterministic Akasha FactoryRelease ledger rebuild and read-only queries."""
from __future__ import annotations

from dataclasses import dataclass

from .akasha_domains import (
    AkashaDomain,
    ProjectionIdentity,
    rebuild_projection_identity,
    require_current_projection,
    require_domain_operation,
)
from .akasha_factory_ledger_contracts import (
    FACTORY_LEDGER_SCHEMA,
    FactoryReleaseView,
    CurriculumCandidateView,
    FactoryLifecycleReceipt,
    CheckpointLineageView,
    _invalid,
)


@dataclass(frozen=True)
class FactoryLedgerProjection:
    releases: tuple[FactoryReleaseView, ...]
    candidates: tuple[CurriculumCandidateView, ...]
    lifecycle: tuple[FactoryLifecycleReceipt, ...]
    checkpoints: tuple[CheckpointLineageView, ...]
    identity: ProjectionIdentity
    schema_version: str = FACTORY_LEDGER_SCHEMA

    def __post_init__(self) -> None:
        if (self.schema_version != FACTORY_LEDGER_SCHEMA
                or self.releases != tuple(sorted(
                    self.releases, key=lambda item: item.factory_release_sha256))
                or self.candidates != tuple(sorted(
                    self.candidates, key=lambda item: item.candidate_sha256))
                or self.lifecycle != tuple(sorted(
                    self.lifecycle, key=lambda item: (item.ordinal, item.receipt_sha256)))
                or self.checkpoints != tuple(sorted(
                    self.checkpoints, key=lambda item: (item.run_id, item.checkpoint_sha256)))):
            _invalid("AKASHA_FACTORY_LEDGER_ORDER_INVALID")
        if (len({item.factory_release_sha256 for item in self.releases}) != len(self.releases)
                or len({item.candidate_sha256 for item in self.candidates}) != len(self.candidates)
                or len({item.receipt_sha256 for item in self.lifecycle}) != len(self.lifecycle)
                or len({item.ordinal for item in self.lifecycle}) != len(self.lifecycle)
                or len({item.checkpoint_sha256 for item in self.checkpoints}) != len(self.checkpoints)):
            _invalid("AKASHA_FACTORY_LEDGER_DUPLICATE")
        require_current_projection(self.identity, self.source_records())

    def source_records(self) -> tuple[dict, ...]:
        return _source_records(self.releases, self.candidates, self.lifecycle, self.checkpoints)


@dataclass(frozen=True)
class FactoryLedgerReadModel:
    projection: FactoryLedgerProjection

    def release(self, release_sha256: str) -> FactoryReleaseView | None:
        return next((item for item in self.projection.releases
                     if item.factory_release_sha256 == release_sha256), None)

    def dependencies(self, release_sha256: str) -> tuple[tuple[str, str], ...]:
        release = self.release(release_sha256)
        return release.dependency_edges if release is not None else ()

    def lifecycle_for(self, subject_sha256: str) -> tuple[FactoryLifecycleReceipt, ...]:
        return tuple(item for item in self.projection.lifecycle if subject_sha256 in (
            item.candidate_sha256, item.factory_release_sha256,
            item.predecessor_factory_release_sha256, item.successor_factory_release_sha256))

    def checkpoints_for(self, release_sha256: str) -> tuple[CheckpointLineageView, ...]:
        return tuple(item for item in self.projection.checkpoints
                     if item.factory_release_sha256 == release_sha256)

    def receipt_refs(self, subject_sha256: str) -> tuple[str, ...]:
        values = []
        release = self.release(subject_sha256)
        if release is not None:
            values.append(release.artifact_receipt_sha256)
        candidate = next((item for item in self.projection.candidates
                          if item.candidate_sha256 == subject_sha256), None)
        if candidate is not None:
            values.append(candidate.artifact_receipt_sha256)
        values.extend(item.receipt_sha256 for item in self.lifecycle_for(subject_sha256))
        values.extend(item.checkpoint_receipt_sha256
                      for item in self.checkpoints_for(subject_sha256))
        return tuple(sorted(set(values)))


def _source_records(releases, candidates, lifecycle, checkpoints) -> tuple[dict, ...]:
    records = (
        *(("factory_release", item.to_record()) for item in releases),
        *(("curriculum_candidate", item.to_record()) for item in candidates),
        *(("lifecycle_receipt", item.to_record()) for item in lifecycle),
        *(("checkpoint_lineage", item.to_record()) for item in checkpoints),
    )
    return tuple({"record_type": kind, **record} for kind, record in records)


def rebuild_factory_ledger(
    releases: tuple[FactoryReleaseView, ...],
    candidates: tuple[CurriculumCandidateView, ...],
    lifecycle: tuple[FactoryLifecycleReceipt, ...],
    checkpoints: tuple[CheckpointLineageView, ...],
    *, authority_owner: str = "factory-release-authority",
) -> FactoryLedgerProjection:
    require_domain_operation(
        AkashaDomain.FACTORY_RELEASE_LEDGER, authority_owner, "rebuild")
    releases = tuple(sorted(releases, key=lambda item: item.factory_release_sha256))
    candidates = tuple(sorted(candidates, key=lambda item: item.candidate_sha256))
    lifecycle = tuple(sorted(lifecycle, key=lambda item: (item.ordinal, item.receipt_sha256)))
    checkpoints = tuple(sorted(checkpoints, key=lambda item: (item.run_id, item.checkpoint_sha256)))
    release_map = {item.factory_release_sha256: item for item in releases}
    candidate_map = {item.candidate_sha256: item for item in candidates}
    if len(release_map) != len(releases) or len(candidate_map) != len(candidates):
        _invalid("AKASHA_FACTORY_LEDGER_DUPLICATE")
    for event in lifecycle:
        if event.candidate_sha256 is not None:
            candidate = candidate_map.get(event.candidate_sha256)
            if candidate is None or candidate.semantic_release_sha256 != event.semantic_release_sha256:
                _invalid("AKASHA_FACTORY_CANDIDATE_EVIDENCE_MISMATCH")
        if event.factory_release_sha256 is not None:
            release = release_map.get(event.factory_release_sha256)
            if release is None or release.semantic_release_sha256 != event.semantic_release_sha256:
                _invalid("AKASHA_FACTORY_RELEASE_EVIDENCE_MISMATCH")
        for related in (event.predecessor_factory_release_sha256,
                        event.successor_factory_release_sha256):
            if related is not None and related not in release_map:
                _invalid("AKASHA_FACTORY_RELEASE_LINEAGE_MISSING")
    for checkpoint in checkpoints:
        release = release_map.get(checkpoint.factory_release_sha256)
        if (release is None
                or release.semantic_release_sha256 != checkpoint.semantic_release_sha256):
            _invalid("AKASHA_FACTORY_CHECKPOINT_RELEASE_MISMATCH")
    records = _source_records(releases, candidates, lifecycle, checkpoints)
    identity = rebuild_projection_identity(AkashaDomain.FACTORY_RELEASE_LEDGER, records)
    return FactoryLedgerProjection(releases, candidates, lifecycle, checkpoints, identity)


def require_current_factory_ledger(
    projection: FactoryLedgerProjection,
    releases: tuple[FactoryReleaseView, ...],
    candidates: tuple[CurriculumCandidateView, ...],
    lifecycle: tuple[FactoryLifecycleReceipt, ...],
    checkpoints: tuple[CheckpointLineageView, ...],
) -> FactoryLedgerProjection:
    if not isinstance(projection, FactoryLedgerProjection):
        _invalid("AKASHA_FACTORY_LEDGER_REQUIRED")
    records = _source_records(
        tuple(sorted(releases, key=lambda item: item.factory_release_sha256)),
        tuple(sorted(candidates, key=lambda item: item.candidate_sha256)),
        tuple(sorted(lifecycle, key=lambda item: (item.ordinal, item.receipt_sha256))),
        tuple(sorted(checkpoints, key=lambda item: (item.run_id, item.checkpoint_sha256))),
    )
    require_current_projection(projection.identity, records)
    return projection


from .akasha_factory_ledger_contracts import (  # noqa: E402
    FactoryLifecycleState,
    TopologyKnowledge,
    TopologyView,
)

__all__ = (
    "FACTORY_LEDGER_SCHEMA", "FactoryLifecycleState", "TopologyKnowledge",
    "FactoryReleaseView", "CurriculumCandidateView", "FactoryLifecycleReceipt",
    "TopologyView", "CheckpointLineageView", "FactoryLedgerProjection",
    "FactoryLedgerReadModel", "rebuild_factory_ledger", "require_current_factory_ledger",
)
