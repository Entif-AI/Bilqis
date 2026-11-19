"""Facade joining authenticated BAMF custody to CP04 and CP06."""
from __future__ import annotations

from pathlib import Path
import threading
import weakref

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.mission_control import MissionControlQueryCatalog

from .native_contracts import AuthenticatedGeneration, NativeProjectionMaterial
from .native_custody import accepted_pointer, authenticated_history
from .native_mapping import accepted_records
from .native_rejections import rejection_material
from .native_contracts import run_ref
from .observed import observed_records, publish_observed_events
from bilqis_mlx.mission_control.contracts.trainer import TrainerObservation


_SEEN_ATTR = "_cp07_native_event_ids"
_SOURCE_TOKEN_ATTR = "_cp07_native_source_token"
_RUN_REFS_ATTR = "_cp07_native_run_refs"
_ACCEPTED_HEALTH_ATTR = "_cp07_native_accepted_health"
_SERVICE_LOCKS = weakref.WeakKeyDictionary()
_SERVICE_LOCKS_GUARD = threading.Lock()



def _source_token(run_dir: Path):
    """Cheap change detector for mutable CP07 observation inputs."""
    root = Path(run_dir)
    token = []
    for name in ("bamf-state.json", "events.jsonl", "trainer-observed.json"):
        path = root / name
        try:
            stat = path.stat()
            token.append((name, stat.st_ino, stat.st_size, stat.st_mtime_ns))
        except FileNotFoundError:
            token.append((name, None, None, None))
    return tuple(token)


def _run_refs(records):
    """Recover one stable RunRef per accepted generation from projected records."""
    refs = {}
    for record in records:
        run = record.meta.run
        if run is not None:
            refs[(run.run_id, run.generation_manifest_sha256)] = run
    return tuple(sorted(refs.values(), key=lambda item: (item.run_id, item.generation)))


def _accepted_learning_health(history):
    values = {}
    for generation in history:
        state = generation.learning_health_state
        by_capability = state.get("by_capability") if isinstance(state, dict) else None
        if isinstance(by_capability, dict):
            values[generation.manifest_sha256] = dict(by_capability)
    return values

def _service_lock(service):
    with _SERVICE_LOCKS_GUARD:
        lock = _SERVICE_LOCKS.get(service)
        if lock is None:
            lock = threading.Lock()
            _SERVICE_LOCKS[service] = lock
        return lock


def materialize_native_projection(
        run_dir: Path, *, include_live_rejections: bool = False) -> NativeProjectionMaterial:
    """Materialize portable accepted history; optionally add live rejection facts."""
    history = authenticated_history(run_dir)
    records, events, manifests = [], [], []
    parent = None
    for generation in history:
        generated, emitted = accepted_records(generation, parent)
        records.extend(generated)
        events.extend(emitted)
        manifests.append(generation.manifest_sha256)
        parent = generation
    rejected_records, rejected_events = (
        rejection_material(Path(run_dir), history)
        if include_live_rejections else ((), ()))
    after = accepted_pointer(Path(run_dir))
    if (not history
            or after["manifest_sha256"] != history[-1].manifest_sha256
            or after["acceptance_sha256"] != history[-1].acceptance_sha256):
        from .native_contracts import invalid
        invalid("CONTROL_PLANE_NATIVE_HISTORY_POINTER_CHANGED")
    accepted_health = _accepted_learning_health(history)
    if include_live_rejections:
        records.extend(observed_records(
            run_dir, tuple(run_ref(item) for item in history),
            accepted_health_by_manifest=accepted_health))
    records.extend(rejected_records)
    events.extend(rejected_events)
    return NativeProjectionMaterial(
        tuple(records), tuple(events), tuple(manifests), accepted_health)


def native_query_catalog(run_dir: Path) -> MissionControlQueryCatalog:
    """Build the current CP03 catalog directly from authenticated BAMF custody."""
    root = Path(run_dir).expanduser().resolve()
    pointer = root / "bamf-state.json"
    if not pointer.exists() and not pointer.is_symlink():
        return MissionControlQueryCatalog.unavailable()
    try:
        material = materialize_native_projection(root, include_live_rejections=True)
    except BilqisError as error:
        if error.context.get("reason") in {
            "BAMF_GENERATION_POINTER_CHANGED_DURING_READ",
            "CONTROL_PLANE_NATIVE_HISTORY_POINTER_CHANGED",
        }:
            return MissionControlQueryCatalog.unavailable()
        raise
    return MissionControlQueryCatalog(material.records)


def native_query_source(run_dir: Path):
    """Reuse accepted CP03 custody while refreshing live observation independently."""
    root = Path(run_dir).expanduser().resolve()
    lock = threading.Lock()
    cached_token = None
    cached_catalog = None
    cached_base_records = ()
    cached_run_refs = ()
    cached_accepted_health = {}

    def source():
        nonlocal cached_token, cached_catalog, cached_base_records, cached_run_refs
        nonlocal cached_accepted_health
        with lock:
            before = _source_token(root)
            if cached_catalog is not None and cached_token == before:
                return cached_catalog
            observation_only = (
                cached_catalog is not None and cached_token is not None
                and cached_token[:2] == before[:2]
                and cached_run_refs
            )
            if observation_only:
                observed = observed_records(
                    root, cached_run_refs,
                    accepted_health_by_manifest=cached_accepted_health)
                catalog = MissionControlQueryCatalog((*cached_base_records, *observed))
                base_records = cached_base_records
                run_refs = cached_run_refs
            else:
                pointer = root / "bamf-state.json"
                if not pointer.exists() and not pointer.is_symlink():
                    return MissionControlQueryCatalog.unavailable()
                try:
                    material = materialize_native_projection(
                        root, include_live_rejections=True)
                except BilqisError as error:
                    if error.context.get("reason") in {
                        "BAMF_GENERATION_POINTER_CHANGED_DURING_READ",
                        "CONTROL_PLANE_NATIVE_HISTORY_POINTER_CHANGED",
                    }:
                        return MissionControlQueryCatalog.unavailable()
                    raise
                base_records = tuple(
                    record for record in material.records
                    if not isinstance(record, TrainerObservation))
                observed = tuple(
                    record for record in material.records
                    if isinstance(record, TrainerObservation))
                run_refs = _run_refs(base_records)
                accepted_health = material.accepted_learning_health_by_manifest or {}
                catalog = MissionControlQueryCatalog((*base_records, *observed))
            after = _source_token(root)
            if after == before:
                cached_token = after
                cached_catalog = catalog
                cached_base_records = base_records
                cached_run_refs = run_refs
                cached_accepted_health = (
                    accepted_health if not observation_only
                    else cached_accepted_health)
            return catalog

    return source


def publish_native_events(service, *, seen_event_ids: set[str] | None = None):
    """Publish authenticated BAMF deltas exactly once per caller-owned frontier."""
    seen = set() if seen_event_ids is None else seen_event_ids
    material = materialize_native_projection(
        service.run_dir, include_live_rejections=True)
    published = list(publish_observed_events(service, tuple(
        record for record in material.records if isinstance(record, TrainerObservation))))
    resource_pending = False
    for family, record, event_id in material.events:
        if event_id in seen:
            continue
        emitted = service.publish_event(family, record, event_id=event_id)
        if emitted is not None:
            published.append(emitted)
        elif family.value == "resource.health.sample":
            resource_pending = True
        seen.add(event_id)
    if resource_pending:
        emitted = service.flush_event_telemetry()
        if emitted is not None:
            published.append(emitted)
    return material, tuple(published)


def refresh_native_events(service):
    """Refresh one service's delivery frontier without making CP04 authoritative."""
    pointer = service.run_dir / "bamf-state.json"
    if not pointer.exists() and not pointer.is_symlink():
        return ()
    with _service_lock(service):
        try:
            before = _source_token(service.run_dir)
            previous = getattr(service, _SOURCE_TOKEN_ATTR, None)
            if previous == before:
                return ()
            run_refs = getattr(service, _RUN_REFS_ATTR, ())
            accepted_health = getattr(service, _ACCEPTED_HEALTH_ATTR, {})
            observation_only = (
                previous is not None and previous[:2] == before[:2]
                and run_refs
            )
            seen = getattr(service, _SEEN_ATTR, None)
            material = None
            if observation_only:
                published = publish_observed_events(
                    service, observed_records(
                        service.run_dir, run_refs,
                        accepted_health_by_manifest=accepted_health))
            elif seen is None:
                material = materialize_native_projection(
                    service.run_dir, include_live_rejections=True)
                setattr(service, _SEEN_ATTR, {
                    event_id for _family, _record, event_id in material.events})
                published = publish_observed_events(service, tuple(
                    record for record in material.records
                    if isinstance(record, TrainerObservation)))
            else:
                _material, published = publish_native_events(service, seen_event_ids=seen)
                material = _material
            after = _source_token(service.run_dir)
            if after == before:
                setattr(service, _SOURCE_TOKEN_ATTR, after)
                if material is not None:
                    setattr(service, _RUN_REFS_ATTR, _run_refs(material.records))
                    setattr(
                        service, _ACCEPTED_HEALTH_ATTR,
                        material.accepted_learning_health_by_manifest or {})
            return published
        except BilqisError as error:
            if error.context.get("reason") in {
                "BAMF_GENERATION_POINTER_CHANGED_DURING_READ",
                "CONTROL_PLANE_NATIVE_HISTORY_POINTER_CHANGED",
            }:
                return ()
            raise


__all__ = (
    "AuthenticatedGeneration", "NativeProjectionMaterial", "authenticated_history",
    "materialize_native_projection", "native_query_catalog", "native_query_source",
    "publish_native_events", "refresh_native_events",
)
