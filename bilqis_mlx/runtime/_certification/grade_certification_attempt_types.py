"""Attempt view and pointer identity for #1334 custody."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .grade_certification_contracts import (
    CertificationObligationScore, GradeCertificationPolicy, GradeCertificationRequest,
)
from .grade_certification_custody_common import POINTER_SCHEMA, _durable_json, _root

@dataclass(frozen=True)
class CertificationAttemptView:
    request: GradeCertificationRequest
    policy: GradeCertificationPolicy
    trigger_cohort_sha256: str
    trigger_scores: tuple[CertificationObligationScore, ...]
    committed_scores: tuple[CertificationObligationScore, ...]
    committed_cohort_sha256s: tuple[str, ...]
    next_cursor: int
    status: str
    blockers: tuple[CertificationObligationScore, ...] = ()
    receipt_sha256: str | None = None
    supersession_reason: str | None = None


def _attempt_dir(run_dir, request) -> Path:
    return _root(run_dir) / "attempts" / request.attempt_sha256


def _pointer_payload(request, *, status, next_cursor) -> dict:
    return {
        "schema": POINTER_SCHEMA,
        "family_sha256": request.family_sha256,
        "attempt_sha256": request.attempt_sha256,
        "request_sha256": request.request_sha256,
        "status": status,
        "next_cursor": next_cursor,
    }


def _write_pointer(run_dir, request, *, status, next_cursor) -> None:
    _durable_json(
        _root(run_dir) / "current.json",
        _pointer_payload(request, status=status, next_cursor=next_cursor),
        replace_existing=True)
