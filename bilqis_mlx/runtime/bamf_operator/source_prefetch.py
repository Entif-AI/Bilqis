"""CPU-only source preparation for the persistent BAMF operator."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import time

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.runtime.source_prefetch import (
    FORBIDDEN_AUTHORITY_KEYS,
    ImmutableSourcePacket,
    SCHEMA,
    SOURCE_WORKER_COUNTS,
    freeze_source_packet,
    thaw_source_packet,
)
from bilqis_mlx.source_adapters.school import live_source_registry
from bilqis_mlx.factory.live_answers import live_answer_registry
from bilqis_mlx.semantics.domains import contract_digest


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


def priority_source_request(selection, source_context, parent, ordinal: int) -> dict:
    """Bind one pure worker request to the exact accepted candidate step."""
    offer = selection.offer
    if type(ordinal) is not int or ordinal < 1:
        _invalid("BAMF_SOURCE_PREFETCH_STEP_INVALID")
    binding = {
        "schema": REQUEST_SCHEMA,
        "accepted_manifest_sha256": offer.accepted_manifest_sha256,
        "generation_binding": offer.generation_binding,
        "release_sha256": offer.release_sha256,
        "capability": offer.capability_id,
        "source_seed": offer.source_seed,
        "source_each": offer.source_each,
        "source_family_id": offer.source_family_id,
        "source_binding_digest": offer.source_binding_digest,
        "visit_id": selection.visit.identity.visit_id,
        "candidate_step": ordinal,
        "parent_optimizer_step": parent.retained_state.optimizer_step,
    }
    return {
        **binding,
        "identity": _fingerprint(binding),
        "source_root": (
            None if source_context.source_root is None
            else str(source_context.source_root)),
        "graph": source_context.graph,
        "executable_release": source_context.release,
    }


def prepare_priority_source_packet(request: dict) -> ImmutableSourcePacket:
    """Redraw an issued source offer in a spawned, neural-inert worker."""
    required = {
        "schema", "identity", "accepted_manifest_sha256", "generation_binding",
        "release_sha256", "capability", "source_seed", "source_each",
        "source_family_id", "source_binding_digest", "visit_id",
        "candidate_step", "parent_optimizer_step", "source_root", "graph",
        "executable_release",
    }
    if (not isinstance(request, dict) or set(request) != required
            or FORBIDDEN_AUTHORITY_KEYS & set(request)
            or request.get("schema") != REQUEST_SCHEMA):
        _invalid("BAMF_SOURCE_PREFETCH_REQUEST_INVALID")
    binding = {key: request[key] for key in (
        "schema", "accepted_manifest_sha256", "generation_binding",
        "release_sha256", "capability", "source_seed", "source_each",
        "source_family_id", "source_binding_digest", "visit_id",
        "candidate_step", "parent_optimizer_step",
    )}
    if request["identity"] != _fingerprint(binding):
        _invalid("BAMF_SOURCE_PREFETCH_IDENTITY_INVALID")
    release = request["executable_release"]
    if (release.release_sha256 != request["release_sha256"]
            or contract_digest(release.source_bindings.by_capability[
                request["capability"]]) != request["source_binding_digest"]):
        _invalid("BAMF_SOURCE_PREFETCH_RELEASE_DRIFT")
    context = SourceExecutionContext(
        release=release,
        graph=request["graph"],
        source_root=(
            None if request["source_root"] is None
            else Path(request["source_root"])),
        source_registry=live_source_registry(),
        answer_registry=live_answer_registry(),
    )
    context.require_capabilities((request["capability"],))
    rows = context.draw_rows(
        seed=request["source_seed"], capability=request["capability"],
        each=request["source_each"])
    authority = context.bind_rows(
        rows, seed=request["source_seed"], capability=request["capability"],
        each=request["source_each"])
    if (authority.source_family_id != request["source_family_id"]
            or authority.release_sha256 != request["release_sha256"]):
        _invalid("BAMF_SOURCE_PREFETCH_SOURCE_DRIFT")
    return freeze_source_packet({
        "schema": SCHEMA,
        "identity": request["identity"],
        "fresh": list(rows),
        "prior": [],
        "preservation": [],
        "retention_support": [],
        "teaching_enrichment_rows": [],
    })


@dataclass
class SourcePrefetchMetrics:
    submitted_steps: int = 0
    prepared_steps: int = 0
    serial_steps: int = 0
    wait_seconds: float = 0.0
    overlap_seconds: float = 0.0


class CandidateSourceLane:
    """Schedule exact future source packets without owning neural state."""

    def __init__(self, selection, source_context, parent, horizon: int, *,
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
        self.pending = {}
        if workers:
            for ordinal in range(1, min(workers, horizon) + 1):
                self._submit(ordinal)

    def _request(self, ordinal):
        return priority_source_request(
            self.selection, self.source_context, self.parent, ordinal)

    def _submit(self, ordinal):
        request = self._request(ordinal)
        self.pending[ordinal] = (
            request, time.monotonic(),
            self.executor.submit(prepare_priority_source_packet, request))
        self.metrics.submitted_steps += 1

    def rows(self, ordinal: int):
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
                or payload.get("prior") != []
                or payload.get("preservation") != []
                or payload.get("retention_support") != []
                or payload.get("teaching_enrichment_rows") != []):
            _invalid("BAMF_SOURCE_PREFETCH_PACKET_INVALID")
        rows = payload.get("fresh")
        if not isinstance(rows, list) or len(rows) != self.selection.offer.source_each:
            _invalid("BAMF_SOURCE_PREFETCH_PACKET_INVALID")
        return tuple(rows)
