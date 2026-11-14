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


_SEEN_ATTR = "_cp07_native_event_ids"
_SERVICE_LOCKS = weakref.WeakKeyDictionary()
_SERVICE_LOCKS_GUARD = threading.Lock()


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
    records.extend(rejected_records)
    events.extend(rejected_events)
    return NativeProjectionMaterial(tuple(records), tuple(events), tuple(manifests))


def native_query_catalog(run_dir: Path) -> MissionControlQueryCatalog:
    """Build the current CP03 catalog directly from authenticated BAMF custody."""
    root = Path(run_dir).expanduser().resolve()
    pointer = root / "bamf-state.json"
    if not pointer.exists() and not pointer.is_symlink():
        return MissionControlQueryCatalog.unavailable()
    material = materialize_native_projection(root, include_live_rejections=True)
    return MissionControlQueryCatalog(material.records)


def publish_native_events(service, *, seen_event_ids: set[str] | None = None):
    """Publish authenticated BAMF deltas exactly once per caller-owned frontier."""
    seen = set() if seen_event_ids is None else seen_event_ids
    material = materialize_native_projection(
        service.run_dir, include_live_rejections=True)
    published = []
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
            seen = getattr(service, _SEEN_ATTR, None)
            if seen is None:
                material = materialize_native_projection(
                    service.run_dir, include_live_rejections=True)
                setattr(service, _SEEN_ATTR, {
                    event_id for _family, _record, event_id in material.events})
                return ()
            _material, published = publish_native_events(service, seen_event_ids=seen)
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
    "materialize_native_projection", "native_query_catalog", "publish_native_events",
    "refresh_native_events",
)
