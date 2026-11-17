"""Shared filesystem primitives for #1334 certification custody."""
from __future__ import annotations

import json
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.state import _durable_json
from .grade_certification_contracts import CertificationObligationScore

ATTEMPT_SCHEMA = "bilqis.bamf.grade-certification-attempt-state/v1"
RESULT_SCHEMA = "bilqis.bamf.grade-certification-obligation-result/v1"
TERMINAL_SCHEMA = "bilqis.bamf.grade-certification-terminal/v1"
POINTER_SCHEMA = "bilqis.bamf.grade-certification-pointer/v1"

def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _root(run_dir: Path) -> Path:
    root = Path(run_dir) / "grade-certification"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        _invalid("BAMF_GRADE_CERTIFICATION_CUSTODY_UNSAFE")
    return root


def _read(path: Path, reason: str) -> dict:
    if path.is_symlink() or not path.is_file():
        _invalid(reason)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _invalid(reason)
    if not isinstance(value, dict):
        _invalid(reason)
    return value


def _immutable(path: Path, payload: dict, reason: str) -> None:
    if path.exists() or path.is_symlink():
        if _read(path, reason) != payload:
            _invalid(reason)
        return
    _durable_json(path, payload)
    if _read(path, reason) != payload:
        _invalid(reason)


def _score_records(scores) -> list[dict]:
    return [item.to_record() for item in scores]


def _scores_from_records(records) -> tuple[CertificationObligationScore, ...]:
    try:
        return tuple(CertificationObligationScore(**item) for item in records)
    except (TypeError, KeyError):
        _invalid("BAMF_GRADE_CERTIFICATION_SCORE_CUSTODY_INVALID")
