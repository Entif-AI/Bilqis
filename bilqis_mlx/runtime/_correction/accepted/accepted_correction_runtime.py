"""Process-owned accepted C09 runtimes and production registration gates."""
from __future__ import annotations

from contextvars import ContextVar
from pathlib import Path
from threading import RLock
import weakref

from .accepted_correction_dispatch import AcceptedCorrectionRuntime
from .atlas_revalidation_common import _invalid


_REGISTRAR_ISSUER = object()


class _AcceptedTargetRegistrar:
    """Opaque process-live target registrar bound to one accepted C09 runtime."""

    __slots__ = ("_runtime", "_issuance")

    def __init__(self, *args, **kwargs):
        _invalid("BAMF_C09_ACCEPTED_RUNTIME_REQUIRED")

    def register(self, kind: str, owner, *, seen_event_ids: tuple[str, ...] = ()) -> None:
        if (getattr(self, "_issuance", None) is not _REGISTRAR_ISSUER
                or type(seen_event_ids) is not tuple
                or any(not isinstance(event_id, str) or not event_id
                       for event_id in seen_event_ids)):
            _invalid("BAMF_C09_ACCEPTED_TARGET_IDENTITY_CONFLICT")
        from bilqis_mlx.runtime._atlas_owner_ingress import _route
        self._runtime.register(kind, owner, _route, seen_event_ids)


def _make_owner_custody(entries):
    active_owner = ContextVar("bamf_c09_active_accepted_owner", default=None)
    superseded_owners = weakref.WeakSet()

    def authorize_owner(owner, action):
        token = active_owner.set(owner)
        try:
            return action()
        finally:
            active_owner.reset(token)

    def retire_owner(owner) -> None:
        superseded_owners.add(owner)

    def owner_is_superseded(owner) -> bool:
        return owner in superseded_owners

    def require_bound_registry(owner, registry):
        from .atlas_source_authority import SourceAuthorityRegistry

        if not isinstance(registry, SourceAuthorityRegistry):
            _invalid("BAMF_C09_CORRECTION_AUTHORITY_REQUIRED")
        matched = [
            retained.registry
            for retained in entries.values()
            for target in retained.targets.values()
            if target.owner is owner
        ]
        if not matched:
            return registry
        bound = matched[0]
        if (active_owner.get() is not owner
                or registry is not bound
                or any(candidate is not bound for candidate in matched)):
            _invalid("BAMF_C09_CALLER_SELECTED_AUTHORITY_FORBIDDEN")
        return bound

    def target_for_owner(owner):
        matched = [
            target
            for retained in entries.values()
            for target in retained.targets.values()
            if target.owner is owner
        ]
        if not matched:
            return None
        target = matched[0]
        if any(candidate is not target for candidate in matched):
            _invalid("BAMF_C09_ACCEPTED_TARGET_IDENTITY_CONFLICT")
        return target

    return (
        authorize_owner, retire_owner, owner_is_superseded,
        require_bound_registry, target_for_owner,
    )


def _retain_runtime(entries, lock, run_dir, manifest_sha256, registry,
                    require_owned, authorize_owner, retire_owner):
    key = (str(Path(run_dir).resolve()), manifest_sha256)
    with lock:
        current = entries.get(key)
        if current is None:
            current = AcceptedCorrectionRuntime(
                Path(run_dir), manifest_sha256, registry,
                require_owned, authorize_owner, retire_owner)
            entries[key] = current
        elif current.registry != registry:
            _invalid("BAMF_C09_CORRECTION_AUTHORITY_DRIFT")
        return current


def _make_runtime_core():
    """Own accepted runtimes, verifier roots, and mutation leases privately."""
    entries = {}
    lock = RLock()
    (
        authorize_owner, retire_owner, owner_is_superseded,
        require_bound_registry, target_for_owner,
    ) = _make_owner_custody(entries)

    def require_owned(retained) -> None:
        if not any(candidate is retained for candidate in entries.values()):
            _invalid("BAMF_C09_ACCEPTED_RUNTIME_REQUIRED")

    def retained(run_dir: Path, manifest_sha256: str) -> AcceptedCorrectionRuntime:
        from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
            _accepted_correction_registry,
        )

        cache, registry = _accepted_correction_registry(run_dir)
        if cache.accepted_manifest_sha256 != manifest_sha256:
            _invalid("BAMF_C09_ACCEPTED_RUNTIME_STALE")
        return _retain_runtime(
            entries, lock, run_dir, manifest_sha256, registry,
            require_owned, authorize_owner, retire_owner)

    def retained_authenticated(run_dir: Path, manifest_sha256: str, registry) -> AcceptedCorrectionRuntime:
        """Reuse verifier material already authenticated by the accepted host."""
        from .atlas_source_authority import SourceAuthorityRegistry

        if (not isinstance(registry, SourceAuthorityRegistry)
                or not isinstance(manifest_sha256, str) or not manifest_sha256):
            _invalid("BAMF_C09_CORRECTION_AUTHORITY_REQUIRED")
        return _retain_runtime(
            entries, lock, run_dir, manifest_sha256, registry,
            require_owned, authorize_owner, retire_owner)

    def refresh(owner) -> None:
        target = target_for_owner(owner)
        if target is None:
            return
        current = next((
            candidate for candidate in entries.values()
            if any(item is target for item in candidate.targets.values())
        ), None)
        if current is not None:
            current.refresh_target(target)

    def register(run_dir: Path, manifest_sha256: str, kind: str, owner, *,
                 seen_event_ids: tuple[str, ...] = ()) -> None:
        if type(seen_event_ids) is not tuple or any(
                not isinstance(event_id, str) or not event_id
                for event_id in seen_event_ids):
            _invalid("BAMF_C09_ACCEPTED_TARGET_IDENTITY_CONFLICT")
        from bilqis_mlx.runtime._atlas_owner_ingress import _route

        retained(run_dir, manifest_sha256).register(
            kind, owner, _route, seen_event_ids)

    def register_support(run_dir: Path, manifest_sha256: str, owner, hold, node, *,
                         seen_event_ids: tuple[str, ...] = ()) -> None:
        if type(seen_event_ids) is not tuple or any(
                not isinstance(event_id, str) or not event_id
                for event_id in seen_event_ids):
            _invalid("BAMF_C09_ACCEPTED_TARGET_IDENTITY_CONFLICT")
        from bilqis_mlx.runtime._atlas_owner_ingress import _route
        from .capability_support_requalification import _rehydrate_support_hold

        retained(run_dir, manifest_sha256).register(
            "CAPABILITY_SUPPORT", owner, _route, seen_event_ids,
            prepare=lambda registry: _rehydrate_support_hold(
                owner, hold, node, registry),
        )

    def reset_for_tests() -> None:
        with lock:
            for retained_runtime in entries.values():
                for target in retained_runtime.targets.values():
                    retire_owner(target.owner)
            entries.clear()

    return (
        require_bound_registry, refresh, register, register_support, retained,
        retained_authenticated,
        reset_for_tests, target_for_owner, owner_is_superseded,
    )


def _require_persisted(
    run_dir: Path, manifest_sha256: str, event_id: str, event_kind: str, expected,
) -> None:
    from bilqis_mlx.runtime.capability_support_journal import event_from_record
    from .accepted_correction_ledger import (
        CONTEXT_INVALIDATION_EVENT, CONTEXT_REVALIDATION_EVENT,
        CORRECTION_EVENT, REVALIDATION_EVENT,
        context_frontier_from_record, context_invalidation_from_record,
        frontier_from_record, read_records,
    )

    record = next((
        item for item in read_records(run_dir, manifest_sha256)
        if item["event_id"] == event_id and item["event"] == event_kind
    ), None)
    if record is None:
        _invalid("BAMF_C09_ACCEPTED_EVENT_NOT_DURABLE")
    readers = {
        CORRECTION_EVENT: lambda item: event_from_record(item["correction"]),
        REVALIDATION_EVENT: frontier_from_record,
        CONTEXT_INVALIDATION_EVENT: context_invalidation_from_record,
        CONTEXT_REVALIDATION_EVENT: context_frontier_from_record,
    }
    reader = readers.get(event_kind)
    if reader is None or reader(record) != expected:
        _invalid("BAMF_C09_ACCEPTED_EVENT_NOT_DURABLE")


def _make_delivery_api(retained):
    def deliver_correction(run_dir, manifest_sha256, event_id, event) -> None:
        from .accepted_correction_ledger import CORRECTION_EVENT
        _require_persisted(run_dir, manifest_sha256, event_id, CORRECTION_EVENT, event)
        retained(run_dir, manifest_sha256).deliver(event_id, event)

    def deliver_revalidation(run_dir, manifest_sha256, event_id, frontier) -> None:
        from .accepted_correction_ledger import REVALIDATION_EVENT
        _require_persisted(
            run_dir, manifest_sha256, event_id, REVALIDATION_EVENT, frontier)
        retained(run_dir, manifest_sha256).deliver_revalidation(event_id, frontier)

    def deliver_context_invalidation(run_dir, manifest_sha256, event_id, event) -> None:
        from .accepted_correction_ledger import CONTEXT_INVALIDATION_EVENT
        _require_persisted(
            run_dir, manifest_sha256, event_id, CONTEXT_INVALIDATION_EVENT, event)
        retained(run_dir, manifest_sha256).deliver_context_invalidation(event_id, event)

    def deliver_context_revalidation(run_dir, manifest_sha256, event_id, frontier) -> None:
        from .accepted_correction_ledger import CONTEXT_REVALIDATION_EVENT
        _require_persisted(
            run_dir, manifest_sha256, event_id, CONTEXT_REVALIDATION_EVENT, frontier)
        retained(run_dir, manifest_sha256).deliver_context_revalidation(event_id, frontier)

    def replay_stale(run_dir, manifest_sha256):
        from .accepted_stale_replay_runtime import replay_stale_evidence
        return replay_stale_evidence(retained(run_dir, manifest_sha256))

    return (
        deliver_correction, deliver_revalidation,
        deliver_context_invalidation, deliver_context_revalidation, replay_stale,
    )


def _make_runtime_boundary():
    """Compose public closures without exposing the retained runtime getter."""
    (
        require_bound_registry, refresh, register, register_support, retained,
        retained_authenticated, reset,
        target_for_owner, owner_is_superseded,
    ) = _make_runtime_core()

    def bind_registrar(host, cache):
        """Bind registration to the exact host/cache pair authenticated by planning."""
        from .accepted_corrections import AcceptedRuntimeHost

        if (type(host) is not AcceptedRuntimeHost
                or host._accepted_cache is not cache
                or cache is None
                or getattr(cache, "_run_dir", None) is None
                or Path(cache._run_dir).resolve() != host.run_dir.resolve()
                or getattr(cache, "_correction_registry", None) is None):
            _invalid("BAMF_C09_ACCEPTED_RUNTIME_REQUIRED")
        retained_runtime = retained_authenticated(
            host.run_dir, cache.accepted_manifest_sha256,
            cache._correction_registry)
        registrar = object.__new__(_AcceptedTargetRegistrar)
        registrar._runtime = retained_runtime
        registrar._issuance = _REGISTRAR_ISSUER
        return registrar

    def require_pending(owner, artifact_id: str) -> None:
        """Fail closed when accepted correction state blocks this physical owner."""
        if owner_is_superseded(owner):
            _invalid("BAMF_C09_ARTIFACT_OWNER_SUPERSEDED")
        refresh(owner)
        target = target_for_owner(owner)
        if target is None:
            return
        if artifact_id in target.context_holds:
            _invalid("BAMF_C09_ARTIFACT_HELD")
        if artifact_id in target.process_fault_holds:
            _invalid("BAMF_C09_PROPAGATION_REPAIR_FAILED")
        node = owner.index.node(artifact_id)
        for event in target.pending:
            if event.dependency in node.immediate_dependencies:
                _invalid("BAMF_C09_ARTIFACT_HELD")

    return (
        require_bound_registry, refresh, register, register_support,
        *_make_delivery_api(retained), reset, require_pending, bind_registrar,
    )


(
    require_bound_owner_registry,
    refresh_owner_corrections,
    register_accepted_target,
    register_accepted_support_target,
    deliver_accepted_correction,
    deliver_accepted_revalidation,
    deliver_accepted_context_invalidation,
    deliver_accepted_context_revalidation,
    replay_accepted_stale_evidence,
    _reset_accepted_correction_runtime_for_tests,
    require_pending_corrections,
    _bind_accepted_target_registrar,
) = _make_runtime_boundary()


def register_compiled_batch(run_dir: Path, batch) -> None:
    from bilqis_mlx.runtime.bamf_bundle.admission import bind_accepted_execution_cache

    cache = bind_accepted_execution_cache(run_dir)
    owners = (
        ("ATLAS_FEATURE", batch.atlas_feature_artifact_owner),
        ("PACKED_FRAME", batch.compiled.packed_frame_artifact_owner),
    )
    for kind, owner in owners:
        register_accepted_target(
            run_dir, cache.accepted_manifest_sha256, kind, owner,
        )


def register_solve_context(run_dir: Path, context) -> None:
    from bilqis_mlx.runtime.bamf_bundle.admission import bind_accepted_execution_cache

    cache = bind_accepted_execution_cache(run_dir)
    owner = context.operator_composition_artifact_owner
    register_accepted_target(
        run_dir, cache.accepted_manifest_sha256, "OPERATOR_COMPOSITION", owner)


__all__ = (
    "deliver_accepted_context_invalidation",
    "deliver_accepted_context_revalidation",
    "deliver_accepted_correction", "deliver_accepted_revalidation",
    "register_accepted_target", "refresh_owner_corrections",
    "register_accepted_support_target",
    "register_compiled_batch", "register_solve_context",
    "replay_accepted_stale_evidence", "require_bound_owner_registry",
    "require_pending_corrections",
)
