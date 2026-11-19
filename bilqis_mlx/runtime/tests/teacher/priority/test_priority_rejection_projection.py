"""Incremental authenticated replay for current-generation rejection pressure."""
from __future__ import annotations

import importlib
import json
import os

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime import priority_rejection_replay as rejection_replay
from bilqis_mlx.runtime.tests.teacher.priority.rejection_projection_support import (
    CountingPlane, _parent, _cache, _rejection, _append, _record,
)


def test_rejection_projection_validates_only_newly_appended_events(monkeypatch, tmp_path):
    plane = CountingPlane(tmp_path)
    monkeypatch.setattr(rejection_replay, "data_plane", lambda: plane)
    journal = tmp_path / "events.jsonl"
    parent, cache = _parent(), _cache()

    for ordinal in range(1, 65):
        _record(tmp_path, _rejection(plane, ordinal, journal_ordinal=ordinal))
        rows = rejection_replay.current_rejections(tmp_path, parent, cache)
        assert len(rows) == ordinal

    assert plane.gets == 128


def test_cold_rebuild_matches_hot_projection(monkeypatch, tmp_path):
    plane = CountingPlane(tmp_path)
    monkeypatch.setattr(rejection_replay, "data_plane", lambda: plane)
    journal = tmp_path / "events.jsonl"
    parent, cache = _parent(), _cache()
    for ordinal in range(1, 5):
        _append(journal, _rejection(plane, ordinal))

    hot = rejection_replay.current_rejections(tmp_path, parent, cache)
    cold_module = importlib.reload(rejection_replay)
    monkeypatch.setattr(cold_module, "data_plane", lambda: plane)
    cold = cold_module.current_rejections(tmp_path, parent, cache)

    assert cold == hot


def test_cold_restart_reuses_persisted_projection_and_scans_only_new_tail(
        monkeypatch, tmp_path):
    plane = CountingPlane(tmp_path)
    monkeypatch.setattr(rejection_replay, "data_plane", lambda: plane)
    parent, cache = _parent(), _cache()
    for ordinal in range(1, 17):
        _record(tmp_path, _rejection(plane, ordinal, journal_ordinal=ordinal))

    hot = rejection_replay.current_rejections(tmp_path, parent, cache)
    assert len(hot) == 16
    first_frontier = plane.tails[-1]["indexed_bytes"]
    gets_after_hot = plane.gets

    plane.restart_events()
    cold_module = importlib.reload(rejection_replay)
    monkeypatch.setattr(cold_module, "data_plane", lambda: plane)
    cold = cold_module.current_rejections(tmp_path, parent, cache)

    assert cold == hot
    assert plane.tails[-1]["scanned_bytes"] == 0
    assert plane.tails[-1]["event_count"] == 0
    assert plane.gets == gets_after_hot

    next_event = _rejection(plane, 1, capability="Z.FUTURE", journal_ordinal=17)
    _record(tmp_path, next_event)
    new_bytes = (tmp_path / "events.jsonl").stat().st_size - first_frontier
    plane.restart_events()
    cold_module = importlib.reload(cold_module)
    monkeypatch.setattr(cold_module, "data_plane", lambda: plane)
    resumed = cold_module.current_rejections(tmp_path, parent, cache)

    assert len(resumed) == 17
    assert resumed[-1][0] == "Z.FUTURE"
    assert plane.tails[-1]["scanned_bytes"] == new_bytes
    assert plane.tails[-1]["event_count"] == 1
    assert plane.gets == gets_after_hot + 2


def test_cold_resume_legacy_cross_capability_prefix_preserves_pressure_without_fake_recency(
        monkeypatch, tmp_path):
    plane = CountingPlane(tmp_path)
    journal = tmp_path / "events.jsonl"
    parent, cache = _parent(), _cache()
    _append(journal, _rejection(
        plane, 1, capability="capability:alpha"))
    _append(journal, _rejection(
        plane, 1, capability="capability:beta"))

    cold_module = importlib.reload(rejection_replay)
    monkeypatch.setattr(cold_module, "data_plane", lambda: plane)

    rows = cold_module.current_rejections(tmp_path, parent, cache)

    assert tuple(row[0] for row in rows) == (
        "capability:alpha", "capability:beta")
    assert cold_module.rejection_pressure(
        tmp_path, parent, cache, "capability:alpha") == ({"retention_gate": 1}, 1)
    assert cold_module.rejection_pressure(
        tmp_path, parent, cache, "capability:beta") == ({"retention_gate": 1}, 1)
    assert cold_module.rejection_recency(tmp_path, parent, cache) == (2, {})
    assert cold_module.ordered_rejections(tmp_path, parent, cache) == ()
    assert cold_module.rejection_attempt_ordinals(
        tmp_path, parent, cache, "capability:beta") == (3, 2)

    _record(tmp_path, _rejection(
        plane, 2, capability="capability:beta", journal_ordinal=3))
    rows = cold_module.current_rejections(tmp_path, parent, cache)

    assert len(rows) == 3
    assert cold_module.rejection_pressure(
        tmp_path, parent, cache, "capability:beta") == ({"retention_gate": 2}, 2)
    assert cold_module.rejection_recency(
        tmp_path, parent, cache) == (3, {"capability:beta": 3})
    assert cold_module.ordered_rejections(tmp_path, parent, cache) == (
        rows[-1],)
    assert cold_module.rejection_attempt_ordinals(
        tmp_path, parent, cache, "capability:beta") == (4, 3)


def test_authenticated_rejection_ordinals_fail_closed_when_reordered(monkeypatch, tmp_path):
    plane = CountingPlane(tmp_path)
    monkeypatch.setattr(rejection_replay, "data_plane", lambda: plane)
    journal = tmp_path / "events.jsonl"
    parent, cache = _parent(), _cache()
    second = _rejection(plane, 2, journal_ordinal=2)
    first = _rejection(plane, 1, journal_ordinal=1)
    _append(journal, second)
    _append(journal, first)

    with pytest.raises(BilqisError) as failure:
        rejection_replay.current_rejections(tmp_path, parent, cache)

    assert failure.value.context["reason"] == "BAMF_PRIORITY_REJECTION_ORDER_INVALID"


def test_cross_capability_authenticated_global_order_is_global(monkeypatch, tmp_path):
    plane = CountingPlane(tmp_path)
    monkeypatch.setattr(rejection_replay, "data_plane", lambda: plane)
    journal = tmp_path / "events.jsonl"
    parent, cache = _parent(), _cache()
    first = _rejection(plane, 1, capability="capability:alpha",
        journal_ordinal=1)
    second = _rejection(plane, 1, capability="capability:beta",
        journal_ordinal=2)
    _append(journal, second)
    _append(journal, first)

    with pytest.raises(BilqisError) as failure:
        rejection_replay.current_rejections(tmp_path, parent, cache)

    assert failure.value.context["reason"] == "BAMF_PRIORITY_REJECTION_ORDER_INVALID"


def test_generation_change_rebuilds_only_the_new_generation_projection(monkeypatch, tmp_path):
    plane = CountingPlane(tmp_path)
    monkeypatch.setattr(rejection_replay, "data_plane", lambda: plane)
    journal = tmp_path / "events.jsonl"
    parent = _parent()
    _record(tmp_path, _rejection(plane, 1, generation=2, journal_ordinal=1))
    _record(tmp_path, _rejection(plane, 2, generation=2, journal_ordinal=2))

    generation_two = rejection_replay.current_rejections(tmp_path, parent, _cache(2))
    assert [row[1] for row in generation_two] == [
        "visit:capability:beta:1",
        "visit:capability:beta:2",
    ]

    _record(tmp_path, _rejection(plane, 1, generation=3, journal_ordinal=1))
    generation_three = rejection_replay.current_rejections(tmp_path, parent, _cache(3))

    assert [row[1] for row in generation_three] == ["visit:capability:beta:1"]


def test_hydrated_projection_fails_closed_if_verified_journal_prefix_is_rewritten(
        monkeypatch, tmp_path):
    plane = CountingPlane(tmp_path)
    monkeypatch.setattr(rejection_replay, "data_plane", lambda: plane)
    journal = tmp_path / "events.jsonl"
    parent, cache = _parent(), _cache()
    first = _rejection(plane, 1)
    second = _rejection(plane, 2)
    _append(journal, first)
    _append(journal, second)
    assert len(rejection_replay.current_rejections(tmp_path, parent, cache)) == 2

    before = journal.stat().st_mtime_ns
    journal.write_text(
        "".join(
            json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
            for event in (second, first)
        ),
        encoding="utf-8",
    )
    os.utime(journal, ns=(journal.stat().st_atime_ns, before + 1_000_000_000))

    with pytest.raises(BilqisError) as failure:
        rejection_replay.current_rejections(tmp_path, parent, cache)

    assert failure.value.context["reason"] == "BAMF_PRIORITY_REJECTION_JOURNAL_INVALID"


def test_hydrated_projection_rejects_old_prefix_rewrite_followed_by_append(
        monkeypatch, tmp_path):
    plane = CountingPlane(tmp_path)
    monkeypatch.setattr(rejection_replay, "data_plane", lambda: plane)
    journal = tmp_path / "events.jsonl"
    parent, cache = _parent(), _cache()
    events = [
        _rejection(plane, ordinal, journal_ordinal=ordinal)
        for ordinal in range(1, 6)
    ]
    for event in events[:4]:
        _append(journal, event)
    assert len(rejection_replay.current_rejections(tmp_path, parent, cache)) == 4

    lines = journal.read_text(encoding="utf-8").splitlines()
    forged = json.loads(lines[0])
    forged["evidence"]["retention_reason"] = "retention_gato"
    lines[0] = json.dumps(forged, sort_keys=True, separators=(",", ":"))
    journal.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _record(tmp_path, events[4])

    with pytest.raises(BilqisError) as failure:
        rejection_replay.current_rejections(tmp_path, parent, cache)

    assert failure.value.context["reason"] == "BAMF_PRIORITY_REJECTION_JOURNAL_INVALID"
