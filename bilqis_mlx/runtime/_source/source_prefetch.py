"""Pure host-side lesson preparation for the three-lane human trainer.

Workers receive source/curriculum inputs only.  They never receive model
parameters, optimizers, run-state paths, checkpoint authority, or MLX handles.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import hashlib
import json
import multiprocessing
from pathlib import Path
import signal

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.fragile_replay import fresh_preservation_rows
from bilqis_mlx.profiles.retention import fragile_preservation_policy
from bilqis_mlx.factory.live_answers import live_answer_registry
from bilqis_mlx.source_adapters.school import live_source_registry
from bilqis_mlx.live_curriculum import draw_course_rows
from bilqis_mlx.factory.teaching import optional_teaching_rows
from .source_execution import SourceExecutionContext
from .source_packet_codec import (
    SourcePacketCodecError, SourcePacketForbiddenAuthority,
    freeze_payload, thaw_payload, validate_payload,
)
from . import state as _runtime_state


SCHEMA = "bilqis.mlx.source-prefetch/v1"
FORBIDDEN_AUTHORITY_KEYS = frozenset({
    "parameters", "params", "optimizer", "run_dir", "checkpoint",
    "student", "receipt", "teacher", "school_state",
    "model_state", "weights", "tensors", "gradient", "network_client",
})
FORBIDDEN_NESTED_AUTHORITY_KEYS = FORBIDDEN_AUTHORITY_KEYS - {"receipt"}
IMMUTABLE_PACKET_SCHEMA = "bilqis.mlx.source-prefetch-immutable/v2"
MAX_SOURCE_WORKERS = 2
SOURCE_WORKER_COUNTS = (1, MAX_SOURCE_WORKERS)
SHA256_HEX_LENGTH = hashlib.sha256().digest_size * 2


def _packet_invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.BAMF_RESOURCES.INVALID, reason=reason)


@dataclass(frozen=True)
class ImmutableSourcePacket:
    identity: str
    payload: tuple
    digest: str
    schema_version: str = IMMUTABLE_PACKET_SCHEMA

    def __post_init__(self):
        try:
            validate_payload(
                self.payload, forbidden_mapping_keys=FORBIDDEN_NESTED_AUTHORITY_KEYS)
            fields = dict(self.payload)
            if set(fields) != {"schema", "identity", "fresh", "prior", "preservation",
                               "retention_support", "teaching_enrichment_rows"}:
                _packet_invalid("SOURCE_PREFETCH_PACKET_SCHEMA_DRIFT")
            encoded = json.dumps(
                self.payload, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False).encode("utf-8")
            expected_digest = hashlib.sha256(encoded).hexdigest()
        except SourcePacketForbiddenAuthority:
            _packet_invalid("SOURCE_PREFETCH_FORBIDDEN_AUTHORITY")
        except (TypeError, ValueError):
            _packet_invalid("SOURCE_PREFETCH_IMMUTABLE_PACKET_INVALID")
        if (not isinstance(self.identity, str)
                or len(self.identity) != SHA256_HEX_LENGTH
                or any(c not in "0123456789abcdef" for c in self.identity)
                or not isinstance(self.payload, tuple)
                or not isinstance(self.digest, str)
                or len(self.digest) != SHA256_HEX_LENGTH
                or any(c not in "0123456789abcdef" for c in self.digest)
                or fields.get("identity") != self.identity
                or fields.get("schema") != SCHEMA
                or self.digest != expected_digest
                or self.schema_version != IMMUTABLE_PACKET_SCHEMA):
            _packet_invalid("SOURCE_PREFETCH_IMMUTABLE_PACKET_INVALID")


def freeze_source_packet(packet: dict) -> ImmutableSourcePacket:
    """Produce a picklable, recursively immutable CPU-only packet."""
    expected = {
        "schema", "identity", "fresh", "prior", "preservation",
        "retention_support", "teaching_enrichment_rows",
    }
    if (not isinstance(packet, dict) or set(packet) != expected
            or packet.get("schema") != SCHEMA):
        _packet_invalid("SOURCE_PREFETCH_PACKET_SCHEMA_DRIFT")
    try:
        payload = freeze_payload(
            packet, forbidden_mapping_keys=FORBIDDEN_NESTED_AUTHORITY_KEYS)
    except SourcePacketForbiddenAuthority:
        _packet_invalid("SOURCE_PREFETCH_FORBIDDEN_AUTHORITY")
    except SourcePacketCodecError:
        _packet_invalid("SOURCE_PREFETCH_UNFREEZABLE_VALUE")
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")
    return ImmutableSourcePacket(
        identity=packet["identity"], payload=payload,
        digest=hashlib.sha256(encoded).hexdigest())


def thaw_source_packet(packet: ImmutableSourcePacket) -> dict:
    """Restore the exact JSON-like source packet shape after worker transport."""
    if type(packet) is not ImmutableSourcePacket:
        _packet_invalid("SOURCE_PREFETCH_IMMUTABLE_PACKET_INVALID")
    return thaw_payload(packet.payload)


def prepare_immutable_step_sources(request: dict) -> ImmutableSourcePacket:
    """BAMF CPU worker entrypoint; legacy mutable packet stays isolated."""
    return freeze_source_packet(prepare_step_sources(request))


def source_prefetch_worker_initializer() -> None:
    """Keep Ctrl+C ownership in the human trainer parent process."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def source_prefetch_pool(workers: int) -> ProcessPoolExecutor:
    if type(workers) is not int or workers not in SOURCE_WORKER_COUNTS:
        _packet_invalid("SOURCE_PREFETCH_WORKER_COUNT_INVALID")
    return ProcessPoolExecutor(
        max_workers=workers,
        mp_context=multiprocessing.get_context("spawn"),
        initializer=source_prefetch_worker_initializer,
    )


def _source_execution_context(request: dict) -> SourceExecutionContext | None:
    release = request.get("executable_release")
    if release is None:
        return None
    return SourceExecutionContext(
        release=release,
        graph=request["graph"],
        source_root=Path(request["source_root"]),
        source_registry=live_source_registry(),
        answer_registry=live_answer_registry(),
    )


def _source_rows(request, *, seed: int, capability: str, each: int,
                 source_context: SourceExecutionContext | None = None):
    """Only pure, previously admitted source contracts enter worker processes."""
    root = Path(request["source_root"])
    release = request.get("executable_release")
    if release is not None:
        context = source_context or _source_execution_context(request)
        return context.draw_rows(seed=seed, capability=capability, each=each)
    return draw_course_rows(
        root, request["graph"], request["course"],
        seed=seed, capability=capability, each=each)


def _fragile_rows(request: dict, *,
                  source_context: SourceExecutionContext | None = None) -> tuple[dict, ...]:
    fixed = tuple(request["fragile_fixed_rows"])
    requested = tuple(request["fragile_requested"])
    if not fixed or not requested:
        return ()
    policy = fragile_preservation_policy()
    def seed_for(name, attempt):
        seeds = tuple(request["fragile_seeds"].get(name, ()))
        if len(seeds) != 3:
            raise ValueError("SOURCE_PREFETCH_FRAGILE_SEEDS_INVALID")
        return seeds[attempt]
    return fresh_preservation_rows(
        fixed, capabilities=requested, rotation=request["fragile_rotation"],
        batch_size=request["batch_size"], retention_policy=policy, seed_for=seed_for,
        draw_rows=lambda **kwargs: _source_rows(
            request, source_context=source_context, **kwargs))


def _teaching_enrichment_rows(request: dict):
    if request.get("executable_release") is not None:
        return optional_teaching_rows(Path(request["source_root"]), request["graph"],
            request["executable_release"], live_source_registry(), capability=request["capability"],
            seed=request["teaching_seed"], enabled=request["teaching_enrichment_enabled"])
    return live_source_registry().optional_teaching_rows(
        request["course"], capability=request["capability"],
        source_root=Path(request["source_root"]), graph=request["graph"],
        seed=request["teaching_seed"], enabled=request["teaching_enrichment_enabled"])


def _retention_support_rows(request: dict, *,
                            source_context: SourceExecutionContext | None = None):
    capability = request["retention_support_capability"]
    if capability is None:
        return ()
    from bilqis_mlx.runtime.candidate_evidence import (
        _select_fresh_retention_support_rows,
    )
    rows = _source_rows(
        request, seed=request["retention_support_seed"],
        capability=capability, each=max(request["batch_size"], 6),
        source_context=source_context)
    return _select_fresh_retention_support_rows(
        rows, rotation=request["retention_support_rotation"])


def prepare_step_sources(request: dict) -> dict:
    """Prepare one optimizer step without access to neural or writable run state."""
    if not isinstance(request, dict) or FORBIDDEN_AUTHORITY_KEYS & set(request):
        raise ValueError("SOURCE_PREFETCH_FORBIDDEN_AUTHORITY")
    required = {
        "identity", "source_root", "graph", "course", "capability",
        "batch_size", "fresh_seed", "prior_capability",
        "prior_seed", "fragile_fixed_rows", "fragile_requested", "fragile_seeds",
        "fragile_rotation", "retention_support_capability",
        "retention_support_seed", "retention_support_rotation",
        "teaching_seed", "teaching_enrichment_enabled",
    }
    if set(request) not in (required, required | {"executable_release"}):
        raise ValueError("SOURCE_PREFETCH_REQUEST_SCHEMA_DRIFT")
    identity = request["identity"]
    if (not isinstance(identity, str) or len(identity) != 64 or
            any(char not in "0123456789abcdef" for char in identity)):
        raise ValueError("SOURCE_PREFETCH_IDENTITY_INVALID")
    batch_size = request["batch_size"]
    source_root = Path(request["source_root"])
    source_context = _source_execution_context(request)
    if source_context is not None:
        source_context.require_capabilities(tuple(
            capability for capability in (
                request["capability"], request["prior_capability"],
                *request["fragile_requested"], request["retention_support_capability"])
            if capability is not None))
    fresh = _source_rows(
        request, seed=request["fresh_seed"],
        capability=request["capability"], each=max(32, batch_size),
        source_context=source_context)
    prior = []
    if request["prior_capability"] is not None:
        prior = _source_rows(
            request, seed=request["prior_seed"],
            capability=request["prior_capability"], each=max(batch_size, 6),
            source_context=source_context)
    preservation = _fragile_rows(request, source_context=source_context)
    retention_support = _retention_support_rows(request, source_context=source_context)
    enrichment = _teaching_enrichment_rows(request)
    return {
        "schema": SCHEMA,
        "identity": identity,
        "fresh": list(fresh),
        "prior": list(prior),
        "preservation": list(preservation),
        "retention_support": list(retention_support),
        "teaching_enrichment_rows": list(enrichment),
    }


def visit_source_request(step_index, policy, old_capabilities, school, retention_support_capabilities, receipt, cap, fragile_requested, boolean_association_bridge, executable_release, course_digest, graph_digest, step_before, course, graph, source_root, batch_size, fragile_fixed_rows):
    """Construct the existing worker packet without model or teacher authority."""
    selected, retention_support_capability, fresh_seed, prior_seed, fragile_seeds = (
        _visit_source_seeds(step_index, policy, old_capabilities, school,
            retention_support_capabilities, receipt, cap, fragile_requested))
    teaching_seed = _runtime_state._seed(
        receipt, capability="TEACHING_ENRICHMENT:" + cap,
        step=step_index + 1)
    retention_support_seed = _runtime_state._seed(
        receipt,
        capability=(
            "RETENTION_SUPPORT:" + retention_support_capability
            if retention_support_capability is not None
            else "RETENTION_SUPPORT:NONE"),
        step=step_index + 1)
    identity = _runtime_state._fingerprint({
        "schema": SCHEMA,
        "factory_release_sha256": executable_release.release_sha256,
        "run_id": receipt["run_id"],
        "generation": receipt["generation"],
        "source_manifest_sha256": receipt.get("source_manifest_sha256"),
        "course_digest": course_digest,
        "factory_release_sha256": executable_release.release_sha256,
        "graph_digest": graph_digest,
        "durable_parent_sha256": school.current_student.sha256,
        "parent_optimizer_step": step_before,
        "capability": cap,
        "visit_step": step_index + 1,
        "policy": policy,
        "prior_capability": selected,
        "batch_size": batch_size,
        "fresh_seed": fresh_seed,
        "prior_seed": prior_seed,
        "fragile_seeds": fragile_seeds,
        "retention_support_capability": retention_support_capability,
        "retention_support_seed": retention_support_seed,
        "retention_support_rotation": school.visits + step_index,
        "teaching_seed": teaching_seed,
        "teaching_enrichment_enabled": boolean_association_bridge,
    })
    return {
        "identity": identity,
        "source_root": str(Path(source_root).resolve()),
        "graph": graph,
        "course": course,
        "executable_release": executable_release,
        "capability": cap,
        "batch_size": batch_size,
        "fresh_seed": fresh_seed,
        "prior_capability": selected,
        "prior_seed": prior_seed,
        "fragile_fixed_rows": tuple(fragile_fixed_rows),
        "fragile_requested": fragile_requested,
        "fragile_seeds": fragile_seeds,
        "fragile_rotation": step_index * 4,
        "retention_support_capability": retention_support_capability,
        "retention_support_seed": retention_support_seed,
        "retention_support_rotation": school.visits + step_index,
        "teaching_seed": teaching_seed,
        "teaching_enrichment_enabled": boolean_association_bridge,
    }


def _visit_source_seeds(step_index, policy, old_capabilities, school, retention_support_capabilities, receipt, cap, fragile_requested):
    selected = None
    if int(policy.get("old", 0)) > 0 and old_capabilities:
        selected = old_capabilities[(school.visits + step_index) % len(old_capabilities)]
    retention_support_capability = (
        retention_support_capabilities[
            step_index % len(retention_support_capabilities)]
        if retention_support_capabilities else None)
    fresh_seed = _runtime_state._seed(receipt, capability=cap, step=step_index + 1)
    prior_seed = (_runtime_state._seed(
        receipt, capability="EXPERIMENT_OLD:" + selected, step=step_index)
        if selected is not None else None)
    fragile_seeds = {
        name: tuple(_runtime_state._seed(
            receipt, capability=f"FRAGILE_PRESERVE:{name}:{attempt}",
            step=step_index + 1) for attempt in range(3))
        for name in fragile_requested
    }
    return selected, retention_support_capability, fresh_seed, prior_seed, fragile_seeds
