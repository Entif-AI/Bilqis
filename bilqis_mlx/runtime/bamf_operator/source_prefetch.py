"""CPU-only source preparation for the persistent BAMF operator."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.teaching import optional_teaching_rows
from bilqis_mlx.runtime.source_execution import source_content_digest
from bilqis_mlx.runtime.source_prefetch import (
    FORBIDDEN_AUTHORITY_KEYS,
    ImmutableSourcePacket,
    SCHEMA,
    SOURCE_WORKER_COUNTS,
    freeze_source_packet,
    thaw_source_packet,
)
from bilqis_mlx.semantics.domains import contract_digest
from .rehearsal import materialize_rehearsal_rows


REQUEST_SCHEMA = "bilqis.bamf.native-source-prefetch-request/v1"
SERIAL_SOURCE_WORKERS = 0
NATIVE_SOURCE_WORKER_COUNTS = (SERIAL_SOURCE_WORKERS, *SOURCE_WORKER_COUNTS)


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_RESOURCES.INVALID, reason=reason)


def _fingerprint(value) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def priority_source_request(
        selection, source_context, parent, ordinal: int, *,
        enrichment_rows=None, rehearsal_plan=None, rehearsal=None) -> dict:
    """Bind one pure worker request to the exact accepted candidate step."""
    offer = selection.offer
    if type(ordinal) is not int or ordinal < 1:
        _invalid("BAMF_SOURCE_PREFETCH_STEP_INVALID")
    if enrichment_rows is None:
        source_registry = getattr(source_context, "source_registry", None)
        graph = getattr(source_context, "graph", None)
        if source_registry is None or graph is None:
            enrichment_rows = ()
        else:
            enrichment_rows = optional_teaching_rows(
                getattr(source_context, "source_root", None), graph,
                source_context.release, source_registry,
                capability=offer.capability_id, seed=offer.source_seed, enabled=True)
    enrichment_rows = tuple(enrichment_rows)
    if rehearsal is None and rehearsal_plan is not None:
        rehearsal = materialize_rehearsal_rows(source_context, rehearsal_plan, ordinal)
    prior_rows = () if rehearsal is None else rehearsal.prior
    preservation_rows = () if rehearsal is None else rehearsal.preservation
    retention_support_rows = () if rehearsal is None else rehearsal.retention_support
    role_rows = {
        "prior": tuple(prior_rows),
        "preservation": tuple(preservation_rows),
        "retention_support": tuple(retention_support_rows),
    }
    rehearsal_bindings = () if rehearsal is None else rehearsal.bindings
    rehearsal_sha256 = contract_digest({
        "rows": role_rows, "bindings": rehearsal_bindings})
    rehearsal_plan_sha256 = None if rehearsal_plan is None else rehearsal_plan.identity
    content_binding = {
        "release_sha256": offer.release_sha256,
        "capability": offer.capability_id,
        "source_seed": offer.source_seed,
        "source_each": offer.source_each,
        "source_family_id": offer.source_family_id,
        "source_binding_digest": offer.source_binding_digest,
        "source_content_sha256": offer.source_authority.content_sha256,
        "teaching_enrichment_sha256": contract_digest(enrichment_rows),
        "rehearsal_plan_sha256": rehearsal_plan_sha256,
        "rehearsal_rows_sha256": rehearsal_sha256,
    }
    content_identity = _fingerprint(content_binding)
    binding = {
        "schema": REQUEST_SCHEMA,
        "accepted_manifest_sha256": offer.accepted_manifest_sha256,
        "generation_binding": offer.generation_binding,
        **content_binding,
        "content_identity": content_identity,
        "visit_id": selection.visit.identity.visit_id,
        "candidate_step": ordinal,
        "parent_optimizer_step": parent.retained_state.optimizer_step,
    }
    return {
        **binding,
        "identity": _fingerprint(binding),
        "executable_release": source_context.release,
        "source_rows": offer.rows(),
        "prior_rows": list(prior_rows),
        "preservation_rows": list(preservation_rows),
        "retention_support_rows": list(retention_support_rows),
        "rehearsal_bindings": list(rehearsal_bindings),
        "teaching_enrichment_rows": list(enrichment_rows),
    }


def prepare_priority_source_packet(request: dict) -> ImmutableSourcePacket:
    """Transport one already-authorized source batch without executing its provider."""
    required = {
        "schema", "identity", "accepted_manifest_sha256", "generation_binding",
        "release_sha256", "capability", "source_seed", "source_each",
        "source_family_id", "source_binding_digest", "source_content_sha256",
        "teaching_enrichment_sha256", "rehearsal_plan_sha256",
        "rehearsal_rows_sha256", "content_identity", "visit_id",
        "candidate_step", "parent_optimizer_step", "executable_release",
        "source_rows", "prior_rows", "preservation_rows",
        "retention_support_rows", "rehearsal_bindings", "teaching_enrichment_rows",
    }
    if (not isinstance(request, dict) or set(request) != required
            or FORBIDDEN_AUTHORITY_KEYS & set(request)
            or request.get("schema") != REQUEST_SCHEMA):
        _invalid("BAMF_SOURCE_PREFETCH_REQUEST_INVALID")
    binding = {key: request[key] for key in (
        "schema", "accepted_manifest_sha256", "generation_binding", "release_sha256",
        "capability", "source_seed", "source_each", "source_family_id",
        "source_binding_digest", "source_content_sha256", "content_identity",
        "teaching_enrichment_sha256", "rehearsal_plan_sha256",
        "rehearsal_rows_sha256", "visit_id", "candidate_step", "parent_optimizer_step",
    )}
    if request["identity"] != _fingerprint(binding):
        _invalid("BAMF_SOURCE_PREFETCH_IDENTITY_INVALID")
    content_binding = {key: request[key] for key in (
        "release_sha256", "capability", "source_seed", "source_each",
        "source_family_id", "source_binding_digest", "source_content_sha256",
        "teaching_enrichment_sha256", "rehearsal_plan_sha256",
        "rehearsal_rows_sha256",
    )}
    if request["content_identity"] != _fingerprint(content_binding):
        _invalid("BAMF_SOURCE_PREFETCH_CONTENT_IDENTITY_INVALID")
    release = request["executable_release"]
    if (release.release_sha256 != request["release_sha256"]
            or contract_digest(release.source_bindings.by_capability[
                request["capability"]]) != request["source_binding_digest"]):
        _invalid("BAMF_SOURCE_PREFETCH_RELEASE_DRIFT")
    rows = tuple(request["source_rows"])
    if (len(rows) != request["source_each"]
            or any(type(row) is not dict for row in rows)
            or source_content_digest(rows) != request["source_content_sha256"]):
        _invalid("BAMF_SOURCE_PREFETCH_SOURCE_DRIFT")
    enrichment = tuple(request["teaching_enrichment_rows"])
    if (any(type(row) is not dict for row in enrichment)
            or contract_digest(enrichment) != request["teaching_enrichment_sha256"]):
        _invalid("BAMF_SOURCE_PREFETCH_ENRICHMENT_DRIFT")
    prior = tuple(request["prior_rows"])
    preservation = tuple(request["preservation_rows"])
    retention_support = tuple(request["retention_support_rows"])
    rehearsal_bindings = tuple(request["rehearsal_bindings"])
    role_rows = {
        "prior": prior,
        "preservation": preservation,
        "retention_support": retention_support,
    }
    if (any(type(row) is not dict for row in (*prior, *preservation, *retention_support))
            or any(type(item) is not dict for item in rehearsal_bindings)
            or contract_digest({"rows": role_rows, "bindings": rehearsal_bindings})
            != request["rehearsal_rows_sha256"]):
        _invalid("BAMF_SOURCE_PREFETCH_REHEARSAL_DRIFT")
    return freeze_source_packet({
        "schema": SCHEMA,
        "identity": request["identity"],
        "fresh": list(rows),
        "prior": list(prior),
        "preservation": list(preservation),
        "retention_support": list(retention_support),
        "teaching_enrichment_rows": list(enrichment),
    })


@dataclass
class SourcePrefetchMetrics:
    submitted_steps: int = 0
    prepared_steps: int = 0
    serial_steps: int = 0
    wait_seconds: float = 0.0
    overlap_seconds: float = 0.0


@dataclass(frozen=True)
class CandidateLessonRows:
    direct: tuple
    prior: tuple = ()
    preservation: tuple = ()
    retention_support: tuple = ()
    enrichment: tuple = ()
    rehearsal_bindings: tuple = ()
    rehearsal_authorities: tuple = ()

    @property
    def delivered(self) -> tuple:
        return (
            *self.direct, *self.prior, *self.preservation,
            *self.retention_support, *self.enrichment)

    @property
    def rehearsal_by_id(self) -> dict[str, str]:
        return {
            **{row["id"]: "prior" for row in self.prior},
            **{row["id"]: "preservation" for row in self.preservation},
            **{row["id"]: "retention_support" for row in self.retention_support},
        }

    @property
    def rehearsal_bindings_by_id(self) -> dict[str, dict]:
        return {item["row_id"]: item for item in self.rehearsal_bindings}

    @property
    def rehearsal_authorities_by_id(self) -> dict[str, object]:
        return dict(self.rehearsal_authorities)


class CandidateSourceLane:
    """Schedule exact future source packets without owning neural state."""

    def __init__(self, selection, source_context, parent, horizon: int, *,
                 rehearsal_plan=None,
                 workers: int, executor, metrics: SourcePrefetchMetrics):
        if (type(workers) is not int or workers not in NATIVE_SOURCE_WORKER_COUNTS
                or (workers == SERIAL_SOURCE_WORKERS) != (executor is None)):
            _invalid("BAMF_SOURCE_PREFETCH_WORKER_CONFIGURATION_INVALID")
        self.selection = selection
        self.source_context = source_context
        self.parent = parent
        self.horizon = horizon
        self.workers = workers
        self.executor = executor
        self.metrics = metrics
        self.rehearsal_plan = rehearsal_plan
        self.pending = {}
        self.rehearsal_custody = {}
        source_registry = getattr(source_context, "source_registry", None)
        graph = getattr(source_context, "graph", None)
        self.enrichment_rows = (
            () if source_registry is None or graph is None else
            optional_teaching_rows(
                getattr(source_context, "source_root", None), graph,
                source_context.release, source_registry,
                capability=selection.offer.capability_id,
                seed=selection.offer.source_seed, enabled=True))
        if workers:
            for ordinal in range(1, min(workers, horizon) + 1):
                self._submit(ordinal)

    def _request(self, ordinal):
        rehearsal = (
            None if self.rehearsal_plan is None else
            materialize_rehearsal_rows(
                self.source_context, self.rehearsal_plan, ordinal))
        self.rehearsal_custody[ordinal] = (
            () if rehearsal is None else rehearsal.authorities)
        return priority_source_request(
            self.selection, self.source_context, self.parent, ordinal,
            enrichment_rows=self.enrichment_rows,
            rehearsal_plan=self.rehearsal_plan, rehearsal=rehearsal)

    def _submit(self, ordinal):
        request = self._request(ordinal)
        self.pending[ordinal] = (
            request, time.monotonic(),
            self.executor.submit(prepare_priority_source_packet, request))
        self.metrics.submitted_steps += 1

    def lesson(self, ordinal: int) -> CandidateLessonRows:
        if self.workers:
            request, submitted_at, future = self.pending.pop(ordinal)
            wait_started = time.monotonic()
            packet = future.result()
            self.metrics.wait_seconds += time.monotonic() - wait_started
            self.metrics.overlap_seconds += max(0.0, wait_started - submitted_at)
            next_ordinal = ordinal + self.workers
            if next_ordinal <= self.horizon:
                self._submit(next_ordinal)
            self.metrics.prepared_steps += 1
        else:
            request = self._request(ordinal)
            wait_started = time.monotonic()
            packet = prepare_priority_source_packet(request)
            self.metrics.wait_seconds += time.monotonic() - wait_started
            self.metrics.serial_steps += 1
        if (type(packet) is not ImmutableSourcePacket
                or packet.identity != request["identity"]):
            _invalid("BAMF_SOURCE_PREFETCH_PACKET_IDENTITY_DRIFT")
        payload = thaw_source_packet(packet)
        if (not isinstance(payload, dict) or payload.get("schema") != SCHEMA
                or payload.get("identity") != request["identity"]
                or not isinstance(payload.get("prior"), list)
                or not isinstance(payload.get("preservation"), list)
                or not isinstance(payload.get("retention_support"), list)):
            _invalid("BAMF_SOURCE_PREFETCH_PACKET_INVALID")
        rows = payload.get("fresh")
        enrichment = payload.get("teaching_enrichment_rows")
        if not isinstance(rows, list) or len(rows) != self.selection.offer.source_each:
            _invalid("BAMF_SOURCE_PREFETCH_PACKET_INVALID")
        if (not isinstance(enrichment, list)
                or any(type(row) is not dict for row in enrichment)):
            _invalid("BAMF_SOURCE_PREFETCH_PACKET_INVALID")
        return CandidateLessonRows(
            tuple(rows), tuple(payload["prior"]), tuple(payload["preservation"]),
            tuple(payload["retention_support"]), tuple(enrichment),
            tuple(request.get("rehearsal_bindings", ())),
            tuple(self.rehearsal_custody.pop(ordinal, ())))

    def rows(self, ordinal: int):
        return self.lesson(ordinal).direct
