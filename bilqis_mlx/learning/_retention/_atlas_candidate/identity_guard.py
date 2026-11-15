"""MLX storage guard for process-local immutable CandidateState custody."""
from __future__ import annotations

from dataclasses import dataclass, field
import copy
from threading import RLock
import weakref

import mlx.core as mx
import numpy as np


_GROUPS = ("parameters", "m", "v", "update_counts")
_MUTATION_SLOTS = (
    "__setitem__", "__iadd__", "__iand__", "__ifloordiv__", "__ilshift__",
    "__imatmul__", "__imod__", "__imul__", "__ior__", "__ipow__",
    "__irshift__", "__isub__", "__itruediv__", "__ixor__",
)
_EXPORT_SLOTS = ("__buffer__", "__dlpack__", "__getstate__", "__reduce_ex__",
                 "__setstate__")
_STATE_TUPLE_WIDTH = 2
_REDUCER_STATE_INDEX = 2
_LOCK = RLock()
_ARRAY_TYPE = type(mx.array([0], dtype=mx.int32))


@dataclass
class _GuardOwnerState:
    originals: dict[str, object] = field(default_factory=dict)
    guards: dict[str, object] = field(default_factory=dict)
    protected_spans: dict[tuple[int, int], int] = field(default_factory=dict)
    protections: dict[
        int, tuple[weakref.ReferenceType, tuple[tuple[int, int], ...]]
    ] = field(default_factory=dict)


class _GuardViolation(RuntimeError):
    pass


_OWNER = _GuardOwnerState()
_CAPABILITY = None
_UNSUPPORTED = False
_POISONED = False
_GENERATION = 0
_TOKEN = object()


@dataclass(frozen=True)
class GuardCapability:
    generation: int
    token: object
    guarded_type: type
    slots: tuple[tuple[str, object, object], ...]


def _numpy_span(view: np.ndarray) -> tuple[int, int] | None:
    if view.size == 0:
        return None
    pointer = int(view.__array_interface__["data"][0])
    strides = view.strides
    if strides is None:
        strides = tuple(
            int(view.itemsize * np.prod(view.shape[index + 1:], dtype=np.int64))
            for index in range(view.ndim))
    low = high = 0
    for dimension, stride in zip(view.shape, strides):
        extent = (int(dimension) - 1) * int(stride)
        low += min(0, extent)
        high += max(0, extent)
    return pointer + low, pointer + high + int(view.itemsize)


def storage_span(array) -> tuple[int, int] | None:
    state = _OWNER.originals["__getstate__"](array)
    if (type(state) is not tuple or len(state) != _STATE_TUPLE_WIDTH
            or not isinstance(state[0], np.ndarray)):
        raise _GuardViolation()
    return _numpy_span(state[0])


def _overlaps(array) -> bool:
    try:
        current = storage_span(array)
    except Exception:
        return True
    if current is None:
        return False
    lo, hi = current
    with _LOCK:
        return any(lo < other_hi and other_lo < hi
                   for (other_lo, other_hi), count in _OWNER.protected_spans.items()
                   if count > 0)


def _guard_mutation(name, original):
    def guarded(self, *args, **kwargs):
        if _overlaps(self):
            raise _GuardViolation()
        return original(self, *args, **kwargs)
    return guarded


def _guarded_state(self):
    state = _OWNER.originals["__getstate__"](self)
    if not _overlaps(self):
        return state
    return np.array(state[0], copy=True), state[1]


def _build_guard(name, original):
    if name in _MUTATION_SLOTS or name == "__setstate__":
        return _guard_mutation(name, original)
    if name == "__buffer__":
        def guarded(self, flags):
            view = original(self, flags)
            return view.toreadonly() if _overlaps(self) else view
        return guarded
    if name == "__array__":
        def guarded(self, *args, **kwargs):
            view = original(self, *args, **kwargs)
            if _overlaps(self):
                view.flags.writeable = False
            return view
        return guarded
    if name == "__dlpack__":
        def guarded(self, *args, **kwargs):
            if _overlaps(self):
                raise _GuardViolation()
            return original(self, *args, **kwargs)
        return guarded
    if name == "__getstate__":
        return _guarded_state
    if name == "__reduce_ex__":
        def guarded(self, protocol):
            value = original(self, protocol)
            if not _overlaps(self):
                return value
            items = list(value)
            if len(items) <= _REDUCER_STATE_INDEX:
                raise _GuardViolation()
            items[_REDUCER_STATE_INDEX] = _guarded_state(self)
            return tuple(items)
        return guarded
    raise _GuardViolation()


def _add_span(value):
    if value is not None:
        _OWNER.protected_spans[value] = _OWNER.protected_spans.get(value, 0) + 1


def _remove_span(value):
    if value is None:
        return
    count = _OWNER.protected_spans.get(value, 0)
    if count <= 1:
        _OWNER.protected_spans.pop(value, None)
    else:
        _OWNER.protected_spans[value] = count - 1


def _self_test() -> None:
    root = mx.arange(12, dtype=mx.float32).reshape((3, 4))
    root_span = storage_span(root)
    _add_span(root_span)
    try:
        aliases = (
            root, root[:, 1:3], root[::-1], root[:, ::2], root.T,
            root.reshape((2, 6)), root[0, 0], mx.stop_gradient(root),
        )
        for alias in aliases:
            if storage_span(alias) is None or not _overlaps(alias):
                raise _GuardViolation()
            if not memoryview(alias).readonly or np.asarray(alias).flags.writeable:
                raise _GuardViolation()
            try:
                alias[0] = 0
            except Exception:
                pass
            else:
                raise _GuardViolation()
            try:
                alias.__dlpack__()
            except Exception:
                pass
            else:
                raise _GuardViolation()
            if hasattr(alias, "__array__"):
                exported = alias.__array__()
                if exported.flags.writeable:
                    raise _GuardViolation()
            try:
                alias.__setstate__(_OWNER.originals["__getstate__"](alias))
            except Exception:
                pass
            else:
                raise _GuardViolation()
        for name in _MUTATION_SLOTS:
            if name == "__setitem__":
                continue
            try:
                getattr(root, name)(1)
            except Exception:
                pass
            else:
                raise _GuardViolation()
        for candidate in (copy.copy(root), copy.deepcopy(root)):
            if _overlaps(candidate) and np.asarray(candidate).flags.writeable:
                raise _GuardViolation()
        if storage_span(root) == _numpy_span(_guarded_state(root)[0]):
            raise _GuardViolation()
    finally:
        _remove_span(root_span)
    ordinary = mx.array([1.0, 2.0], dtype=mx.float32)
    ordinary[0] = 9.0
    if (float(ordinary[0]) != 9.0 or memoryview(ordinary).readonly
            or not np.asarray(ordinary).flags.writeable):
        raise _GuardViolation()
    ordinary.__dlpack__()
    if hasattr(ordinary, "__array__") and not ordinary.__array__().flags.writeable:
        raise _GuardViolation()


def guard_intact(capability) -> bool:
    global _POISONED
    if _POISONED:
        return False
    intact = (capability is not None and capability.guarded_type is _ARRAY_TYPE
              and all(getattr(_ARRAY_TYPE, name, None) is guard
                      for name, _original, guard in capability.slots))
    if not intact and _OWNER.protections:
        _POISONED = True
    return intact


def binding_supported() -> bool:
    global _CAPABILITY, _UNSUPPORTED, _GENERATION
    with _LOCK:
        if _CAPABILITY is not None:
            return guard_intact(_CAPABILITY)
        if _UNSUPPORTED or _POISONED:
            return False
        names = list(_MUTATION_SLOTS + _EXPORT_SLOTS)
        if hasattr(_ARRAY_TYPE, "__array__"):
            names.append("__array__")
        changed = []
        try:
            for name in names:
                original = getattr(_ARRAY_TYPE, name)
                _OWNER.originals.setdefault(name, original)
                guard = _build_guard(name, _OWNER.originals[name])
                setattr(_ARRAY_TYPE, name, guard)
                _OWNER.guards[name] = guard
                changed.append(name)
            _self_test()
        except Exception:
            for name in reversed(changed):
                setattr(_ARRAY_TYPE, name, _OWNER.originals[name])
            _UNSUPPORTED = True
            return False
        _GENERATION += 1
        _CAPABILITY = GuardCapability(
            _GENERATION, _TOKEN, _ARRAY_TYPE,
            tuple((name, _OWNER.originals[name], _OWNER.guards[name]) for name in names))
        return True


def current_capability() -> GuardCapability | None:
    with _LOCK:
        return _CAPABILITY if _CAPABILITY is not None and guard_intact(_CAPABILITY) else None


def numerical_witnesses(state):
    result = []
    for group in _GROUPS:
        for name in sorted(getattr(state.optimizer, group)):
            value = getattr(state.optimizer, group)[name]
            result.append((group, name, id(value), weakref.ref(value), storage_span(value)))
    return tuple(result)


def _release_protection(key, reference):
    with _LOCK:
        current = _OWNER.protections.get(key)
        if current is not None and current[0] is reference:
            for span in current[1]:
                _remove_span(span)
            _OWNER.protections.pop(key, None)


def protect_state_storage(state) -> bool:
    if not binding_supported():
        return False
    key = id(state)
    with _LOCK:
        current = _OWNER.protections.get(key)
        if current is not None and current[0]() is state:
            return True
        spans = tuple(item[4] for item in numerical_witnesses(state)
                      if item[4] is not None)
        for span in spans:
            _add_span(span)
        reference = weakref.ref(
            state, lambda ref, key=key: _release_protection(key, ref))
        _OWNER.protections[key] = (reference, spans)
    return True


def state_storage_protected(state) -> bool:
    with _LOCK:
        current = _OWNER.protections.get(id(state))
        return bool(current is not None and current[0]() is state)
