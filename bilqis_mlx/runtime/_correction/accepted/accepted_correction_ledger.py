"""Public accepted-generation C09 ledger API."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH, data_plane
from bilqis_mlx.runtime.capability_support_journal import event_from_record

from .accepted_correction_records import (
    ACCEPTED_EVENT_TYPES, CONTEXT_INVALIDATION_EVENT,
    CONTEXT_REVALIDATION_EVENT, CORRECTION_EVENT, DERIVED_CLAIM_EVENT,
    PROCESS_FAULT_EVENT, REMEDIATION_EVENT, REVALIDATION_EVENT, _canonical,
    correction_record, frontier_from_record, lineage_records_from_bytes,
    revalidation_record, validate_record,
)
from .accepted_context_records import (
    context_frontier_from_record, context_revalidation_record,
    context_invalidation_from_record, context_invalidation_record,
    context_temporal_identity_from_record,
)
from .accepted_correction_recovery import read_records_unlocked, recover_transaction
from .accepted_correction_storage import (
    HISTORY_COMMITMENT_SCHEMA, HISTORY_TRANSACTION_SCHEMA, commit_history,
    commit_history_and_clear, committed_history, history_state, ledger_lock,
    ledger_path, verify_committed_history, write_all, write_transaction,
)
from .atlas_revalidation_evidence import CorrectionEvent, RevalidationFrontier
from .atlas_source_authority import SourceAuthorityRegistry
from .atlas_revalidation_common import _invalid


def _manifest_lineage(run_dir: Path, manifest_sha256: str) -> tuple[str, ...]:
    """Return accepted bundle ancestry from genesis through the requested manifest."""
    root = Path(run_dir) / "bamf-bundles"
    current = manifest_sha256
    seen = set()
    lineage = []
    while current is not None:
        if (not isinstance(current, str) or len(current) != SHA256_HEX_LENGTH
                or any(char not in "0123456789abcdef" for char in current)
                or current in seen):
            _invalid("BAMF_C09_CORRECTION_LINEAGE_INVALID")
        seen.add(current)
        path = root / current / "manifest.json"
        if path.is_symlink() or not path.is_file():
            _invalid("BAMF_C09_CORRECTION_LINEAGE_INVALID")
        try:
            raw = path.read_bytes()
            record = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            _invalid("BAMF_C09_CORRECTION_LINEAGE_INVALID")
        if (hashlib.sha256(raw).hexdigest() != current
                or not isinstance(record, dict)
                or "parent_manifest_sha256" not in record):
            _invalid("BAMF_C09_CORRECTION_LINEAGE_INVALID")
        lineage.append(current)
        current = record["parent_manifest_sha256"]
    return tuple(reversed(lineage))


def read_records(run_dir: Path, manifest_sha256: str) -> tuple[dict, ...]:
    with ledger_lock(run_dir):
        lineage = _manifest_lineage(run_dir, manifest_sha256)
        for lineage_manifest in lineage:
            recover_transaction(run_dir, lineage_manifest)
        path = ledger_path(run_dir)
        if path.is_symlink() or (path.exists() and not path.is_file()):
            _invalid("BAMF_C09_CORRECTION_LEDGER_UNSAFE")
        if not path.exists():
            if any(committed_history(run_dir, item) is not None for item in lineage):
                _invalid("BAMF_C09_CORRECTION_LEDGER_MISSING")
            return ()
        try:
            raw = path.read_bytes()
        except OSError:
            _invalid("BAMF_C09_CORRECTION_LEDGER_INVALID")
        records = lineage_records_from_bytes(raw, lineage)
        for lineage_manifest in lineage:
            verify_committed_history(
                run_dir,
                lineage_manifest,
                tuple(item for item in records
                      if item["accepted_manifest_sha256"] == lineage_manifest),
            )
        return records


def accepted_correction_id(
    manifest_sha256: str, event: CorrectionEvent,
) -> str:
    return correction_record(manifest_sha256, event)["event_id"]


def accepted_corrections(
    run_dir: Path, manifest_sha256: str,
) -> tuple[tuple[str, CorrectionEvent], ...]:
    from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
        _accepted_correction_registry,
    )
    cache, registry = _accepted_correction_registry(run_dir)
    if cache.accepted_manifest_sha256 != manifest_sha256:
        _invalid("BAMF_C09_ACCEPTED_RUNTIME_STALE")
    records = read_records(run_dir, manifest_sha256)
    return _accepted_corrections_from_records(records, registry)


def _accepted_corrections_from_records(
    records: tuple[dict, ...], registry: SourceAuthorityRegistry,
) -> tuple[tuple[str, CorrectionEvent], ...]:
    """Verify already-read accepted correction records with bound C09 authority."""
    if not isinstance(registry, SourceAuthorityRegistry):
        _invalid("BAMF_C09_CORRECTION_AUTHORITY_REQUIRED")
    result = []
    for item in records:
        if item["event"] != CORRECTION_EVENT:
            continue
        event = event_from_record(item["correction"])
        registry.verify_correction(event)
        result.append((item["event_id"], event))
    return tuple(result)


def append_record(run_dir: Path, manifest_sha256: str, record: dict) -> None:
    run_dir = Path(run_dir)
    with ledger_lock(run_dir):
        recover_transaction(run_dir, manifest_sha256)
        prior = read_records_unlocked(run_dir, manifest_sha256)
        if (not ledger_path(run_dir).exists()
                and committed_history(run_dir, manifest_sha256) is not None):
            _invalid("BAMF_C09_CORRECTION_LEDGER_MISSING")
        verify_committed_history(run_dir, manifest_sha256, prior)
        if any(item["event_id"] == record.get("event_id") for item in prior):
            commit_history(run_dir, manifest_sha256, prior)
            return
        validate_record(record, manifest_sha256)
        path = ledger_path(run_dir)
        if path.is_symlink() or (path.exists() and not path.is_file()):
            _invalid("BAMF_C09_CORRECTION_LEDGER_UNSAFE")
        try:
            prior_raw = path.read_bytes() if path.exists() else b""
        except OSError:
            _invalid("BAMF_C09_CORRECTION_LEDGER_INVALID")
        target = (*prior, record)
        prior_state = history_state(prior)
        target_state = history_state(target)
        write_transaction(run_dir, manifest_sha256, {
            "schema_version": HISTORY_TRANSACTION_SCHEMA,
            "state": "PREPARED",
            "run_dir": str(run_dir.resolve()),
            "accepted_manifest_sha256": manifest_sha256,
            "record": record,
            "prior_file_size": len(prior_raw),
            "prior_file_sha256": hashlib.sha256(prior_raw).hexdigest(),
            "prior_event_ids": prior_state["event_ids"],
            "prior_records_sha256": prior_state["records_sha256"],
            "target_event_ids": target_state["event_ids"],
            "target_records_sha256": target_state["records_sha256"],
        })
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            write_all(descriptor, _canonical(record) + b"\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        data_plane().sync_event_ledger(run_dir)
        commit_history_and_clear(run_dir, manifest_sha256, target)


def append_current_record(
    run_dir: Path, manifest_sha256: str, record: dict,
) -> None:
    """Append only while ``manifest_sha256`` is still the accepted generation."""
    from bilqis_mlx.runtime.bamf_bundle.publication import _pointer_lock, _read_pointer

    run_dir = Path(run_dir)
    with _pointer_lock(run_dir):
        pointer = _read_pointer(run_dir / "bamf-state.json")
        if (pointer is None
                or pointer.get("manifest_sha256") != manifest_sha256):
            _invalid("BAMF_C09_ACCEPTED_RUNTIME_STALE")
        append_record(run_dir, manifest_sha256, record)


__all__ = (
    "CONTEXT_INVALIDATION_EVENT", "CONTEXT_REVALIDATION_EVENT",
    "CORRECTION_EVENT", "REVALIDATION_EVENT", "REMEDIATION_EVENT",
    "DERIVED_CLAIM_EVENT", "PROCESS_FAULT_EVENT", "accepted_correction_id",
    "accepted_corrections", "append_current_record", "append_record", "correction_record",
    "context_frontier_from_record", "context_revalidation_record",
    "context_invalidation_from_record", "context_invalidation_record",
    "context_temporal_identity_from_record",
    "frontier_from_record", "read_records", "revalidation_record",
)
