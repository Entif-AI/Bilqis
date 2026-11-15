"""Incremental authenticated replay for current-generation rejection pressure."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime import checkpoint_outbox
from bilqis_mlx.runtime import priority_rejection_replay as rejection_replay
from bilqis_mlx.runtime.bamf_bundle.records import canonical


class CountingPlane:
    def __init__(self):
        self.objects = {}
        self.gets = 0

    def get_object(self, digest):
        self.gets += 1
        return self.objects[digest]


def _parent():
    return SimpleNamespace(retained_state=SimpleNamespace(optimizer_step=11))


def _cache(generation=2):
    return SimpleNamespace(
        generation=generation,
        accepted_manifest_sha256="f" * 64,
        run_id="run",
    )


def _rejection(plane, ordinal, *, capability="capability:beta", generation=2):
    evidence = {
        "schema": "bilqis.bamf.c16.3-rejection/v2",
        "rejection_attempt_ordinal": ordinal,
        "visit_id": f"visit:{capability}:{ordinal}",
        "capability": capability,
        "selected_option_id": capability,
        "selected_policy_key": "policy",
        "candidate_optimizer_step": 11 + ordinal,
        "retained_optimizer_step": 11,
        "retention_reason": "retention_gate",
    }
    authority = {
        "schema": "bilqis.mlx.bamf-rejection-authority/v1",
        "run_id": "run",
        "generation": generation,
        "student_manifest_sha256": "f" * 64,
        "optimizer_step": 11,
        "evidence": evidence,
    }
    authority_raw = canonical(authority)
    authority_sha256 = hashlib.sha256(authority_raw).hexdigest()
    event = checkpoint_outbox.with_delivery_outbox(
        {"run_id": "run", "generation": generation},
        ({
            "event": "BAMF_CANDIDATE_REJECTED",
            "generation": generation,
            "student_manifest_sha256": "f" * 64,
            "optimizer_step": 11,
            "evidence": evidence,
            "rejection_authority_sha256": authority_sha256,
        },),
    )["delivery_outbox"][0]
    receipt = {
        "schema": "bilqis.mlx.bamf-rejection-receipt/v1",
        "run_id": "run",
        "generation": generation,
        "student_manifest_sha256": "f" * 64,
        "event": event,
    }
    receipt_raw = canonical(receipt)
    receipt_sha256 = hashlib.sha256(receipt_raw).hexdigest()
    plane.objects[authority_sha256] = authority_raw
    plane.objects[receipt_sha256] = receipt_raw
    return event


def _append(journal: Path, event):
    with journal.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")


def test_rejection_projection_validates_only_newly_appended_events(monkeypatch, tmp_path):
    plane = CountingPlane()
    monkeypatch.setattr(rejection_replay, "data_plane", lambda: plane)
    journal = tmp_path / "events.jsonl"
    parent, cache = _parent(), _cache()

    for ordinal in range(1, 65):
        _append(journal, _rejection(plane, ordinal))
        rows = rejection_replay.current_rejections(tmp_path, parent, cache)
        assert len(rows) == ordinal

    assert plane.gets == 128


def test_cold_rebuild_matches_hot_projection(monkeypatch, tmp_path):
    plane = CountingPlane()
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


def test_authenticated_rejection_ordinals_fail_closed_when_reordered(monkeypatch, tmp_path):
    plane = CountingPlane()
    monkeypatch.setattr(rejection_replay, "data_plane", lambda: plane)
    journal = tmp_path / "events.jsonl"
    parent, cache = _parent(), _cache()
    second = _rejection(plane, 2)
    first = _rejection(plane, 1)
    _append(journal, second)
    _append(journal, first)

    with pytest.raises(BilqisError) as failure:
        rejection_replay.current_rejections(tmp_path, parent, cache)

    assert failure.value.context["reason"] == "BAMF_PRIORITY_REJECTION_ORDER_INVALID"


def test_generation_change_rebuilds_only_the_new_generation_projection(monkeypatch, tmp_path):
    plane = CountingPlane()
    monkeypatch.setattr(rejection_replay, "data_plane", lambda: plane)
    journal = tmp_path / "events.jsonl"
    parent = _parent()
    _append(journal, _rejection(plane, 1, generation=2))
    _append(journal, _rejection(plane, 2, generation=2))

    generation_two = rejection_replay.current_rejections(tmp_path, parent, _cache(2))
    assert [row[1] for row in generation_two] == [
        "visit:capability:beta:1",
        "visit:capability:beta:2",
    ]

    _append(journal, _rejection(plane, 1, generation=3))
    generation_three = rejection_replay.current_rejections(tmp_path, parent, _cache(3))

    assert [row[1] for row in generation_three] == ["visit:capability:beta:1"]


def test_hydrated_projection_fails_closed_if_verified_journal_prefix_is_rewritten(
        monkeypatch, tmp_path):
    plane = CountingPlane()
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
