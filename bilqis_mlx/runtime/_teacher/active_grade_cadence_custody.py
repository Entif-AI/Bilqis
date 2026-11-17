"""Crash-idempotent run custody for #1333 active-grade cadence projections."""
from __future__ import annotations

import json
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.state import _durable_json

from .active_grade_cadence_contracts import (
    ActiveGradeCadenceState,
    CADENCE_POINTER_SCHEMA,
    cadence_state_from_record,
)


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _root(run_dir: Path) -> Path:
    root = Path(run_dir) / "active-grade-cadence"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_CUSTODY_UNSAFE")
    return root


def _states_root(run_dir: Path) -> Path:
    states = _root(run_dir) / "states"
    if states.is_symlink() or (states.exists() and not states.is_dir()):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_CUSTODY_UNSAFE")
    return states


def _json(path: Path, reason: str) -> dict:
    if path.is_symlink() or not path.is_file():
        _invalid(reason)
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        _invalid(reason)
    canonical = json.dumps(
        value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if not isinstance(value, dict) or raw != canonical:
        _invalid(reason)
    return value


def _write_pointer(run_dir: Path, cadence_sha256: str) -> None:
    _durable_json(
        _root(run_dir) / "current.json",
        {"schema": CADENCE_POINTER_SCHEMA, "cadence_sha256": cadence_sha256},
        replace_existing=True,
    )


def persist_cadence_state(run_dir: Path, state: ActiveGradeCadenceState) -> None:
    states = _states_root(run_dir)
    states.mkdir(parents=True, exist_ok=True)
    path = states / f"{state.cadence_sha256}.json"
    record = state.to_record()
    if path.exists():
        if _json(path, "BAMF_ACTIVE_GRADE_CADENCE_STATE_COLLISION") != record:
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_STATE_COLLISION")
    else:
        _durable_json(path, record)
    _write_pointer(run_dir, state.cadence_sha256)


def _state_chain_tip(run_dir: Path) -> ActiveGradeCadenceState | None:
    states_root = _states_root(run_dir)
    if not states_root.exists():
        return None
    entries = tuple(states_root.iterdir())
    if any(item.is_symlink() or not item.is_file() or item.suffix != ".json"
           for item in entries):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_CUSTODY_UNSAFE")
    if not entries:
        return None
    states = {}
    predecessors = set()
    for path in entries:
        state = cadence_state_from_record(_json(
            path, "BAMF_ACTIVE_GRADE_CADENCE_RECORD_INVALID"))
        if path.stem != state.cadence_sha256 or state.cadence_sha256 in states:
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_RECORD_INVALID")
        states[state.cadence_sha256] = state
        if state.predecessor_sha256 is not None:
            predecessors.add(state.predecessor_sha256)
    if not predecessors <= set(states):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_CHAIN_DRIFT")
    tips = set(states) - predecessors
    if len(tips) != 1:
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_CHAIN_FORK")
    tip = states[tips.pop()]
    visited = set()
    cursor = tip
    while cursor.predecessor_sha256 is not None:
        if cursor.cadence_sha256 in visited:
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_CHAIN_DRIFT")
        visited.add(cursor.cadence_sha256)
        predecessor = states[cursor.predecessor_sha256]
        if predecessor.revision + 1 != cursor.revision:
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_CHAIN_DRIFT")
        cursor = predecessor
    if cursor.revision != 0 or len(visited) + 1 != len(states):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_CHAIN_DRIFT")
    return tip


def read_current_cadence(run_dir: Path) -> ActiveGradeCadenceState | None:
    """Read the unique chain tip and heal a missing/stale current pointer."""
    root = _root(run_dir)
    tip = _state_chain_tip(run_dir)
    pointer = root / "current.json"
    if tip is None:
        if pointer.exists() or pointer.is_symlink():
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_POINTER_INVALID")
        return None
    pointed = None
    if pointer.exists() or pointer.is_symlink():
        record = _json(pointer, "BAMF_ACTIVE_GRADE_CADENCE_POINTER_INVALID")
        if (set(record) != {"schema", "cadence_sha256"}
                or record.get("schema") != CADENCE_POINTER_SCHEMA):
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_POINTER_INVALID")
        pointed = record["cadence_sha256"]
        if not (_states_root(run_dir) / f"{pointed}.json").is_file():
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_POINTER_DRIFT")
    if pointed != tip.cadence_sha256:
        _write_pointer(run_dir, tip.cadence_sha256)
    return tip


__all__ = ("persist_cadence_state", "read_current_cadence")
