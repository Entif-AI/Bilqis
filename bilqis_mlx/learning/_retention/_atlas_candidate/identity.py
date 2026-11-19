"""Versioned, streaming numerical candidate identity; no mutable-state cache."""
from __future__ import annotations

import hashlib
import json
from time import perf_counter


from bilqis_mlx.errors import ErrorBus, SCHOOL

LEGACY_IDENTITY_SCHEME = "bilqis.mlx.candidate-identity/hex-json-v1"
RAW_IDENTITY_SCHEME = "bilqis.mlx.candidate-identity/raw-v2"
IDENTITY_SCHEMES = (LEGACY_IDENTITY_SCHEME, RAW_IDENTITY_SCHEME)
_GROUPS = ("parameters", "m", "v", "update_counts")
_CHUNK_BYTES = 64 * 1024
_UINT64_LIMIT = 1 << 64


def _invalid():
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


def require_identity_scheme(scheme):
    if scheme not in IDENTITY_SCHEMES:
        _invalid()
    return scheme


def _u64(number):
    if type(number) is not int or not 0 <= number < _UINT64_LIMIT:
        _invalid()
    return number.to_bytes(8, "big")


def _text(digest, value):
    if type(value) is not str:
        _invalid()
    encoded = value.encode("utf-8")
    digest.update(_u64(len(encoded)))
    digest.update(encoded)


def _bytes(array):
    import numpy as np
    # MLX's NumPy bridge may share storage; consume it immediately, never cache it.
    contiguous = array if array.flags.c_contiguous else np.ascontiguousarray(array)
    return memoryview(contiguous).cast("B") if array.nbytes else b""


def optimizer_snapshot_digest(optimizer, optimizer_step):
    """Stream the exact model, native AdamW moments and update counts."""
    import numpy as np
    digest = hashlib.sha256(RAW_IDENTITY_SCHEME.encode("ascii") + b"\0")
    digest.update(_u64(optimizer_step))
    for group in _GROUPS:
        values = getattr(optimizer, group)
        _text(digest, group)
        digest.update(_u64(len(values)))
        for name in sorted(values):
            array = np.asarray(values[name])
            if array.dtype.kind not in "biufc" or array.dtype.fields or array.dtype.subdtype:
                _invalid()
            _text(digest, name)
            _text(digest, array.dtype.str)
            digest.update(_u64(array.ndim))
            for dimension in array.shape:
                digest.update(_u64(dimension))
            digest.update(_u64(array.nbytes))
            digest.update(_bytes(array))
    return digest.hexdigest()


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def _legacy_digest(state):
    """Reproduce the historical canonical stream without full-tree materialization."""
    import numpy as np
    digest = hashlib.sha256(b'{"optimizer_step":' + _json(state.optimizer_step)
                            + b',"state":{')
    for group_index, group in enumerate(sorted(_GROUPS)):
        digest.update((b"," if group_index else b"") + _json(group) + b":{")
        for index, (name, value) in enumerate(sorted(getattr(state.optimizer, group).items())):
            digest.update((b"," if index else b"") + _json(name) + b':"')
            raw = _bytes(np.asarray(value))
            for offset in range(0, len(raw), _CHUNK_BYTES):
                digest.update(raw[offset:offset + _CHUNK_BYTES].hex().encode("ascii"))
            digest.update(b'"')
        digest.update(b"}")
    digest.update(b"}}\n")
    return digest.hexdigest()


def candidate_identity_digest(state) -> str:
    """Bind exact numerical content under the state's custody-selected scheme.

    New states use raw-v2. Only historical bundle loading selects legacy-v1 on
    an absent manifest field; an unknown explicit scheme is never a fallback.
    """
    scheme = require_identity_scheme(state.identity_scheme)
    started = perf_counter()
    result = (optimizer_snapshot_digest(state.optimizer, state.optimizer_step)
              if scheme == RAW_IDENTITY_SCHEME else _legacy_digest(state))
    elapsed = perf_counter() - started
    try:
        from .identity_binding import _record_full_identity_computation
    except ImportError:
        pass
    else:
        _record_full_identity_computation(state, elapsed)
    return result
