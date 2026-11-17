"""Durable #1333 recovery-boundary handoff receipts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.state import _durable_json

from .active_grade_cadence_contracts import (
    ActiveGradeCadencePhase,
    CADENCE_POLICY_EPOCH,
    _is_issued_cadence_state,
)


SCHEMA = "bilqis.bamf.active-grade-cadence-boundary/v1"


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _canonical(value) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False)


def _digest(value) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _root(run_dir: Path) -> Path:
    root = Path(run_dir) / "active-grade-cadence-boundaries"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_BOUNDARY_CUSTODY_UNSAFE")
    return root


def _persist_boundary(run_dir: Path, state) -> dict:
    if (not _is_issued_cadence_state(state)
            or state.phase is not ActiveGradeCadencePhase.BOUNDARY):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_BOUNDARY_AUTHORITY_INVALID")
    body = {
        "schema": SCHEMA,
        "run_id": state.run_id,
        "active_grade_activation_sha256": state.active_grade_activation_sha256,
        "active_grade_definition_sha256": state.active_grade_definition_sha256,
        "policy_epoch": state.policy_epoch,
        "cadence_epoch": state.cadence_epoch,
        "member_census_sha256": state.member_census_sha256,
        "deficit_evidence_sha256": state.deficit_evidence_sha256,
        "phase_sha256": state.phase_sha256,
        "recovery_attempt_counts": [list(item) for item in state.recovery_attempt_counts],
    }
    receipt = {**body, "boundary_sha256": _digest(body)}
    root = _root(run_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{state.cadence_epoch:08d}-{receipt['boundary_sha256']}.json"
    if not path.exists():
        _durable_json(path, receipt)
    return receipt


def _latest_boundary(run_dir: Path, frontier, member_census_sha256) -> dict | None:
    root = _root(run_dir)
    if not root.exists():
        return None
    candidates = []
    for path in root.iterdir():
        if path.is_symlink() or not path.is_file() or path.suffix != ".json":
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_BOUNDARY_CUSTODY_UNSAFE")
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_BOUNDARY_INVALID")
        body = dict(record)
        claimed = body.pop("boundary_sha256", None)
        if (claimed != _digest(body) or record.get("schema") != SCHEMA
                or path.name != f"{record.get('cadence_epoch', -1):08d}-{claimed}.json"):
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_BOUNDARY_INVALID")
        if (record.get("run_id") == frontier.run_id
                and record.get("active_grade_activation_sha256")
                == frontier.active_grade_activation_sha256
                and record.get("active_grade_definition_sha256")
                == frontier.active_grade_definition_sha256
                and record.get("policy_epoch") == CADENCE_POLICY_EPOCH
                and record.get("member_census_sha256") == member_census_sha256):
            candidates.append(record)
    if not candidates:
        return None
    return max(candidates, key=lambda item: item["cadence_epoch"])


__all__ = ()
