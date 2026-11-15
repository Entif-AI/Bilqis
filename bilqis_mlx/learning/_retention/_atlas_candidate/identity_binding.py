"""Process-local full CandidateState identity binding for immutable custody."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from threading import RLock
from time import perf_counter
import weakref

from .common import invalid
from .identity import candidate_identity_digest
from .identity_guard import (
    binding_supported as candidate_identity_binding_supported,
    current_capability, guard_intact, numerical_witnesses, protect_state_storage,
    state_storage_protected,
)


_GROUPS = ("parameters", "m", "v", "update_counts")
_LOCK = RLock()
_STATUSES: dict[int, tuple[weakref.ReferenceType, str, str]] = {}
_BINDINGS: dict[int, tuple[weakref.ReferenceType, "CandidateIdentityBinding"]] = {}
_METRICS = {
    "candidate_identity_full_computations": 0,
    "candidate_identity_numerical_bytes_hashed": 0,
    "candidate_identity_binding_issues": 0,
    "candidate_identity_binding_reuses": 0,
    "candidate_identity_require_calls": 0,
    "candidate_identity_full_hash_wall_seconds": 0.0,
    "candidate_identity_require_wall_seconds": 0.0,
}


@dataclass(frozen=True)
class CandidateIdentityBinding:
    digest: str
    state_id: int
    state_ref: weakref.ReferenceType
    optimizer_ref: weakref.ReferenceType
    policy_ref: weakref.ReferenceType
    policy_digest: str
    allocation_ref: weakref.ReferenceType
    allocation_digest: str
    proof_witnesses: tuple[tuple[int, weakref.ReferenceType, str], ...]
    custody_witness: tuple | None
    numerical_witnesses: tuple
    topology_digest: str
    extents_digest: str
    optimizer_step: int
    identity_scheme: str
    schema_version: str
    guard_generation: int
    guard_token: object


def _cleanup_state(key, reference):
    with _LOCK:
        for registry in (_STATUSES, _BINDINGS):
            current = registry.get(key)
            if current is not None and current[0] is reference:
                registry.pop(key, None)


def _set_status(state, status, reason):
    key = id(state)
    reference = weakref.ref(state, lambda ref, key=key: _cleanup_state(key, ref))
    _STATUSES[key] = (reference, status, reason)


def protect_candidate_state(state) -> bool:
    if not protect_state_storage(state):
        mark_candidate_state_unbindable(state, "RUNTIME_UNSUPPORTED")
        return False
    with _LOCK:
        _set_status(state, "BINDABLE", "OWNER_PROTECTED")
    return True


def mark_candidate_state_unbindable(state, reason: str) -> None:
    with _LOCK:
        current = _BINDINGS.get(id(state))
        if current is not None and current[0]() is state:
            invalid()
        _set_status(state, "UNBINDABLE", reason)


def _policy_digest(policy) -> str:
    raw = json.dumps(policy.to_record(), sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _custody_witness(custody):
    if custody is None:
        return None
    return (custody.run_id, custody.generation, custody.manifest_sha256,
            custody.topology_digest, custody.extents_digest)


def _binding_for(state):
    current = _BINDINGS.get(id(state))
    return current[1] if current is not None and current[0]() is state else None


def bind_candidate_identity(state, topology_digest: str, extents_digest: str, *,
                            expected_digest: str | None = None):
    with _LOCK:
        existing = _binding_for(state)
    if existing is not None:
        binding = require_candidate_identity_binding(
            state, topology_digest, extents_digest, existing)
        if expected_digest is not None and binding.digest != expected_digest:
            invalid()
        with _LOCK:
            _METRICS["candidate_identity_binding_reuses"] += 1
        return binding
    if not protect_candidate_state(state):
        invalid()
    digest = candidate_identity_digest(state)
    if expected_digest is not None and digest != expected_digest:
        invalid()
    capability = current_capability()
    if capability is None:
        invalid()
    binding = CandidateIdentityBinding(
        digest=digest, state_id=id(state), state_ref=weakref.ref(state),
        optimizer_ref=weakref.ref(state.optimizer), policy_ref=weakref.ref(state.policy),
        policy_digest=_policy_digest(state.policy), allocation_ref=weakref.ref(state.allocations),
        allocation_digest=state.allocations.digest,
        proof_witnesses=tuple((id(p), weakref.ref(p), p.digest) for p in state.step_proofs),
        custody_witness=_custody_witness(state.custody),
        numerical_witnesses=numerical_witnesses(state), topology_digest=topology_digest,
        extents_digest=extents_digest, optimizer_step=state.optimizer_step,
        identity_scheme=state.identity_scheme, schema_version=state.schema_version,
        guard_generation=capability.generation, guard_token=capability.token)
    reference = weakref.ref(state, lambda ref, key=id(state): _cleanup_state(key, ref))
    with _LOCK:
        _BINDINGS[id(state)] = (reference, binding)
        _METRICS["candidate_identity_binding_issues"] += 1
    return binding


def require_candidate_identity_binding(state, topology_digest: str, extents_digest: str,
                                       binding=None):
    started = perf_counter()
    try:
        with _LOCK:
            _METRICS["candidate_identity_require_calls"] += 1
            binding = binding or _binding_for(state)
        capability = current_capability()
        if (binding is None or capability is None or not guard_intact(capability)
                or binding.guard_generation != capability.generation
                or binding.guard_token is not capability.token
                or binding.state_id != id(state) or binding.state_ref() is not state
                or binding.optimizer_ref() is not state.optimizer
                or binding.policy_ref() is not state.policy
                or binding.policy_digest != _policy_digest(state.policy)
                or binding.allocation_ref() is not state.allocations
                or binding.allocation_digest != state.allocations.digest
                or binding.custody_witness != _custody_witness(state.custody)
                or binding.topology_digest != topology_digest
                or binding.extents_digest != extents_digest
                or binding.optimizer_step != state.optimizer_step
                or binding.identity_scheme != state.identity_scheme
                or binding.schema_version != state.schema_version
                or not state_storage_protected(state)):
            invalid()
        proofs = tuple((id(p), p, p.digest) for p in state.step_proofs)
        if (len(proofs) != len(binding.proof_witnesses)
                or any(saved_id != current_id or saved_ref() is not current
                       or saved_digest != current_digest
                       for (saved_id, saved_ref, saved_digest),
                           (current_id, current, current_digest)
                       in zip(binding.proof_witnesses, proofs))):
            invalid()
        current = numerical_witnesses(state)
        if (len(current) != len(binding.numerical_witnesses)
                or any(saved[:3] != now[:3] or saved[3]() is not now[3]()
                       or saved[4] != now[4]
                       for saved, now in zip(binding.numerical_witnesses, current))):
            invalid()
        return binding
    finally:
        with _LOCK:
            _METRICS["candidate_identity_require_wall_seconds"] += perf_counter() - started


def candidate_identity_for_state(state, topology_digest: str, extents_digest: str,
                                 binding=None) -> str:
    if binding is not None:
        return require_candidate_identity_binding(
            state, topology_digest, extents_digest, binding).digest
    with _LOCK:
        existing = _binding_for(state)
        status = _STATUSES.get(id(state))
        status_value = (status[1] if status is not None and status[0]() is state
                        else "UNCLASSIFIED")
    if existing is not None:
        return require_candidate_identity_binding(
            state, topology_digest, extents_digest, existing).digest
    if status_value == "UNBINDABLE" or not candidate_identity_binding_supported():
        return candidate_identity_digest(state)
    invalid()


def candidate_identity_for_bound_state(state) -> str:
    """Reuse an exact live binding without making callers restate its B01 context."""
    with _LOCK:
        binding = _binding_for(state)
        status = _STATUSES.get(id(state))
        status_value = (status[1] if status is not None and status[0]() is state
                        else "UNCLASSIFIED")
    if binding is not None:
        return require_candidate_identity_binding(
            state, binding.topology_digest, binding.extents_digest, binding).digest
    if status_value == "UNBINDABLE" or not candidate_identity_binding_supported():
        return candidate_identity_digest(state)
    invalid()


def candidate_identity_for_canonical_consumer(state) -> str:
    """Reuse a live binding when present; otherwise perform the canonical proof."""
    with _LOCK:
        binding = _binding_for(state)
    if binding is not None:
        return require_candidate_identity_binding(
            state, binding.topology_digest, binding.extents_digest, binding).digest
    return candidate_identity_digest(state)


def candidate_identity_metrics_snapshot() -> dict:
    with _LOCK:
        return dict(_METRICS)


def candidate_identity_metrics_delta(before: dict) -> dict:
    after = candidate_identity_metrics_snapshot()
    return {key: after[key] - before.get(key, 0) for key in after}


def _record_full_identity_computation(state, elapsed_seconds: float) -> None:
    numerical_bytes = sum(
        int(value.nbytes) for group in _GROUPS
        for value in getattr(state.optimizer, group).values())
    with _LOCK:
        _METRICS["candidate_identity_full_computations"] += 1
        _METRICS["candidate_identity_numerical_bytes_hashed"] += numerical_bytes
        _METRICS["candidate_identity_full_hash_wall_seconds"] += elapsed_seconds


def _reset_candidate_identity_metrics_for_tests() -> None:
    with _LOCK:
        for key, value in _METRICS.items():
            _METRICS[key] = 0.0 if isinstance(value, float) else 0

