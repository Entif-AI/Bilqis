"""B10.3 causal feedback, legal supervised loss, and neural fallback boundary."""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Mapping

import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled

from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.semantics.frame_schema import ConceptRef, RoleOccurrence
from .decisions import (
    DecodeState,
    DecisionOutput,
    allowed_values,
    commit_decisions,
    parent_outputs,
    start_decoding,
)
from .records import RoleCandidate, TypedHeadLogits, WIDTH, invalid, validate_hidden


FEEDBACK_PARAMETER = "readout.feedback"
FALLBACK_REASON = "BAMF_B10_NEURAL_OUTPUT_ILLEGAL"


class NeuralDecisionStatus(str, Enum):
    COMMITTED = "COMMITTED"
    FALLBACK_REQUIRED = "FALLBACK_REQUIRED"


@dataclass(frozen=True)
class NeuralDecisionResult:
    status: NeuralDecisionStatus
    state: DecodeState
    reason: str | None = None

    def __post_init__(self):
        if (type(self.status) is not NeuralDecisionStatus
                or type(self.state) is not DecodeState
                or (self.status is NeuralDecisionStatus.COMMITTED
                    and self.reason is not None)
                or (self.status is NeuralDecisionStatus.FALLBACK_REQUIRED
                    and self.reason != FALLBACK_REASON)):
            invalid()


def _canonical(value):
    if isinstance(value, Enum):
        return {"enum": type(value).__name__, "value": value.value}
    if is_dataclass(value):
        return {
            "type": type(value).__name__,
            "value": {key: _canonical(item) for key, item in asdict(value).items()},
        }
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in sorted(value.items())}
    if type(value) in (str, int, float, bool) or value is None:
        return value
    invalid()


def _structural_vector(value) -> mx.array:
    payload = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode("utf-8")
    raw = bytearray()
    block = 0
    while len(raw) < WIDTH:
        raw.extend(hashlib.sha256(
            payload + b"|" + str(block).encode("ascii")).digest())
        block += 1
    values = [(byte / 127.5 - 1.0) / math.sqrt(WIDTH) for byte in raw[:WIDTH]]
    return mx.array(values, dtype=mx.float32)


def _concept_vector(value: ConceptRef, snapshot, banks) -> mx.array:
    if snapshot is None or type(banks) is not tuple or not banks:
        invalid()
    try:
        entry = snapshot.abi_for_semantic(value.semantic_id)
    except (AttributeError, IndexError, TypeError):
        invalid()
    if (value.semantic_release != snapshot.release_sha256
            or entry.index != value.abi_index
            or entry.active is not True):
        invalid()
    bank_index, row = divmod(value.abi_index, ModelTopologySpecV2.semantic_bank_rows)
    if (tuple(bank.bank_index for bank in banks) != tuple(range(len(banks)))
            or any((bank.semantic_release, bank.active_semantic_digest) !=
                   (snapshot.release_sha256, snapshot.active_set_sha256)
                   for bank in banks)
            or bank_index >= len(banks)
            or banks[bank_index].bank_index != bank_index
            or row not in banks[bank_index].active_rows
            or banks[bank_index].semantic_release != value.semantic_release):
        invalid()
    return banks[bank_index].weights[row]


def encode_feedback_value(value, *, snapshot=None, banks=()) -> mx.array:
    """Encode a committed dependency without admitting target or descendant data."""
    return (_concept_vector(value, snapshot, banks)
            if type(value) is ConceptRef else _structural_vector(value))


def _canonical_legal_value(value, legal_values: tuple):
    exact = tuple(
        legal for legal in legal_values
        if type(value) is type(legal) and value == legal)
    if len(exact) == 1:
        return exact[0]
    if type(value) is str:
        enum_match = tuple(
            legal for legal in legal_values
            if isinstance(legal, Enum) and legal.value == value)
        if len(enum_match) == 1:
            return enum_match[0]
    return None


def _ancestor_ids(state: DecodeState, decision_id: str) -> frozenset[str]:
    lookup = {item.decision_id: item for item in state.plan.decisions}
    if decision_id not in lookup:
        invalid()
    pending = list(lookup[decision_id].depends_on)
    ancestors = set()
    while pending:
        current = pending.pop()
        if current in ancestors:
            continue
        ancestors.add(current)
        pending.extend(lookup[current].depends_on)
    return frozenset(ancestors)


def _teacher_ancestor_state(
        state: DecodeState, decision_id: str,
        teacher_targets: Mapping[str, object]) -> DecodeState:
    ancestors = _ancestor_ids(state, decision_id)
    prefix = start_decoding(state.plan)
    replayed = set()
    for output in state.committed:
        if output.decision_id not in ancestors:
            continue
        value = teacher_targets.get(output.decision_id, output.value)
        canonical = _canonical_legal_value(
            value, allowed_values(prefix, output.decision_id))
        if canonical is None:
            invalid()
        prefix = commit_decisions(
            prefix, (DecisionOutput(output.decision_id, canonical),))
        replayed.add(output.decision_id)
    if replayed != ancestors:
        invalid()
    return prefix


def _parent_values(
        state: DecodeState, decision_id: str,
        teacher_targets: Mapping[str, object] | None):
    inferred = parent_outputs(state, decision_id)
    if teacher_targets is None:
        return inferred
    if not isinstance(teacher_targets, Mapping):
        invalid()
    decision = next(
        (item for item in state.plan.decisions if item.decision_id == decision_id),
        None)
    if decision is None or any(parent not in teacher_targets for parent in decision.depends_on):
        invalid()
    # Deliberately index only declared parents. Current/descendant targets are loss-only.
    forced = []
    for parent in decision.depends_on:
        target = teacher_targets[parent]
        parent_state = _teacher_ancestor_state(state, parent, teacher_targets)
        canonical = _canonical_legal_value(
            target, allowed_values(parent_state, parent))
        if canonical is None:
            invalid()
        forced.append(canonical)
    return tuple(forced)


def decision_hidden(
        anchor: mx.array, state: DecodeState, decision_id: str,
        parameters: Mapping[str, mx.array], *,
        teacher_targets: Mapping[str, object] | None = None,
        snapshot=None, banks=()) -> mx.array:
    """Apply mean parent feedback; training can see only declared prior targets."""
    validate_hidden(anchor)
    if type(state) is not DecodeState or not isinstance(parameters, Mapping):
        invalid()
    weight = parameters.get(FEEDBACK_PARAMETER)
    if (not isinstance(weight, mx.array) or weight.shape != (WIDTH, WIDTH)
            or weight.dtype != mx.float32
            or (host_tensor_validation_enabled()
                and not bool(mx.all(mx.isfinite(weight))))):
        invalid()
    values = _parent_values(state, decision_id, teacher_targets)
    feedback = (mx.zeros((WIDTH,), dtype=mx.float32) if not values else
                mx.mean(mx.stack(tuple(
                    encode_feedback_value(value, snapshot=snapshot, banks=banks)
                    for value in values)), axis=0))
    combined = anchor + weight @ feedback
    return combined * mx.rsqrt(
        mx.mean(combined * combined, axis=-1, keepdims=True)
        + ModelTopologySpecV2.rms_norm_epsilon)


def _candidate_key(value):
    if isinstance(value, Enum):
        return value.value
    if type(value) in (str, ConceptRef, RoleOccurrence, RoleCandidate):
        return value
    invalid()


def typed_decision_loss(
        head: TypedHeadLogits, target,
        *, legal_values: tuple, supplied: bool = True) -> mx.array:
    """Cross entropy over legal candidates only; absent auxiliary labels contribute 0."""
    if (type(head) is not TypedHeadLogits or type(legal_values) is not tuple
            or not legal_values or type(supplied) is not bool):
        invalid()
    if not supplied:
        if target is not None:
            invalid()
        return mx.array(0.0, dtype=mx.float32)
    target_key = _candidate_key(target)
    legal_keys = tuple(_candidate_key(value) for value in legal_values)
    if len(set(legal_keys)) != len(legal_keys) or target_key not in legal_keys:
        invalid()
    candidates = tuple(_candidate_key(value) for value in head.candidates)
    legal = mx.array([candidate in legal_keys for candidate in candidates], dtype=mx.bool_)
    if target_key not in candidates or not any(
            candidate in legal_keys for candidate in candidates):
        invalid()
    target_index = candidates.index(target_key)
    masked = mx.where(legal, head.logits, -mx.inf)
    shifted = masked - mx.max(masked, axis=-1, keepdims=True)
    return mx.mean(mx.logsumexp(shifted, axis=-1) - shifted[..., target_index])


def commit_neural_decision(
        state: DecodeState, decision_id: str, value) -> NeuralDecisionResult:
    """Turn an illegal neural choice into an explicit solver fallback request."""
    legal_values = allowed_values(state, decision_id)
    canonical = _canonical_legal_value(value, legal_values)
    if canonical is None:
        return NeuralDecisionResult(
            NeuralDecisionStatus.FALLBACK_REQUIRED, state, FALLBACK_REASON)
    advanced = commit_decisions(
        state, (DecisionOutput(decision_id, canonical),))
    return NeuralDecisionResult(NeuralDecisionStatus.COMMITTED, advanced)
