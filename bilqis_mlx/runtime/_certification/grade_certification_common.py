"""Shared primitives for #1334 certification contracts."""
from __future__ import annotations

import hashlib
import json

from bilqis_mlx.errors import ErrorBus, SCHOOL

SHA256_HEX_LENGTH = hashlib.sha256().digest_size * 2

def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha(value) -> bool:
    return (
        type(value) is str and len(value) == SHA256_HEX_LENGTH
        and all(char in "0123456789abcdef" for char in value)
    )


def _threshold(value) -> bool:
    return (
        type(value) is tuple and len(value) == 2
        and all(type(item) is int for item in value)
        and value[1] > 0 and 0 <= value[0] <= value[1]
    )
