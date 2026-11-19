"""Shared authenticated rejection ledger fixtures."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from bilqis_mlx.data_plane import DataPlane
from bilqis_mlx.runtime import checkpoint_outbox, checkpoints
from bilqis_mlx.runtime.bamf_bundle.records import canonical
class CountingPlane:
    def __init__(self, root):
        self.objects = {}
        self.gets = 0
        self.event_path = root / "events.sqlite3"
        self.events = DataPlane(self.event_path)
        self.tails = []

    def restart_events(self):
        self.events.close()
        self.events = DataPlane(self.event_path)

    def get_object(self, digest):
        self.gets += 1
        return self.objects[digest]

    def sync_event_ledger(self, run_dir):
        return self.events.sync_event_ledger(run_dir)

    def indexed_event_tail(self, run_dir, after_byte=0):
        result = self.events.indexed_event_tail(run_dir, after_byte)
        self.tails.append(result)
        return result

    def event_projection_state(self, run_dir, projection_key, schema_version):
        return self.events.event_projection_state(run_dir, projection_key, schema_version)

    def remember_event_projection(
            self, run_dir, projection_key, schema_version, ledger_identity,
            indexed_bytes, payload):
        return self.events.remember_event_projection(
            run_dir, projection_key, schema_version, ledger_identity,
            indexed_bytes, payload)


def _parent():
    return SimpleNamespace(retained_state=SimpleNamespace(optimizer_step=11))


def _cache(generation=2):
    return SimpleNamespace(
        generation=generation,
        accepted_manifest_sha256="f" * 64,
        run_id="run",
    )


def _rejection(
        plane, ordinal, *, capability="capability:beta", generation=2,
        journal_ordinal=None):
    evidence = {
        "schema": "bilqis.bamf.c16.3-rejection/v2",
        "rejection_attempt_ordinal": ordinal,
        **({"rejection_journal_ordinal": journal_ordinal}
           if journal_ordinal is not None else {}),
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


def _record(run_dir: Path, event):
    checkpoints._record(run_dir, event)
