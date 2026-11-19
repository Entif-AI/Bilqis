"""Durable, cold-readable receipts for normal BAMF operator stops."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime import checkpoints
from bilqis_mlx.runtime import disk as runtime_disk


RUN_STOP_SCHEMA = "bilqis.bamf.run-stop/v1"
RUN_STOP_EVENT = "BAMF_RUN_STOPPED"
RUN_STOP_RECEIPT_INVALID = "BAMF_RUN_STOP_RECEIPT_INVALID"


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.BAMF_OPERATOR.INVALID, reason=reason)


def _canonical(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checkpoint_identity(student) -> str:
    from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
    return candidate_identity_digest(student.retained_state)


def _accepted_pointer(run_dir: Path) -> dict:
    from bilqis_mlx.runtime.bamf_bundle.publication.pointer_storage import _read_pointer
    from bilqis_mlx.runtime.bamf_bundle.publication.storage import _pointer_read_lock
    pointer_path = Path(run_dir) / "bamf-state.json"
    with _pointer_read_lock(pointer_path.parent):
        pointer = _read_pointer(pointer_path)
    if not isinstance(pointer, dict):
        _invalid("BAMF_RUN_STOP_ACCEPTED_POINTER_MISSING")
    return pointer


def _resume_state(status: str) -> tuple[bool, str]:
    if status in {"ACTION_REQUIRED", "ADMISSION_LEASE_REQUIRED"}:
        return False, "ACTION_REQUIRED"
    if status == "DISK_RESERVE_REACHED":
        return False, "RESUME_AFTER_RESOURCE_RECOVERY"
    if status == "RESOURCE_HOLD":
        return True, "RESUME_AFTER_RESOURCE_RECOVERY"
    if status in {"PRIORITY_HOLD", "ADMISSION_HOLD", "FIXED_POINT"}:
        return True, "RESUME_WHEN_WORK_AVAILABLE"
    return True, "RESUME_ALLOWED"


def stop_resource_witness(run_dir: Path, reserve_gib: float) -> dict:
    """Capture the configured reserve against current free disk without mutating state."""
    return runtime_disk.headroom_snapshot(
        Path(run_dir), required_bytes=0, reserve_gib=reserve_gib)


def record_normal_stop_receipt(
        run_dir: Path, student, *, status: str, minutes: int, max_visits: int,
        steps_per_visit: int, reserve_gib: float, source_prefetch_workers: int,
        visits: int, accepted: int, rejected: int, elapsed_seconds: float,
        admission_status: str | None, admission_advances: int,
        resource_witness: dict) -> str | None:
    """Append a normal-stop receipt without minting or replacing a generation."""
    run_dir = Path(run_dir)
    # Unit routing tests use lightweight stand-ins. Production custody always has
    # a run ID; only authoritative accepted students are eligible to mint receipts.
    if not isinstance(getattr(student, "run_id", None), str):
        return None
    pointer = _accepted_pointer(run_dir)
    manifest_sha256 = pointer.get("manifest_sha256")
    if (pointer.get("run_id") != student.run_id
            or pointer.get("generation") != student.generation
            or not isinstance(manifest_sha256, str)
            or len(manifest_sha256) != SHA256_HEX_LENGTH):
        _invalid("BAMF_RUN_STOP_ACCEPTED_STATE_DRIFT")
    if (not isinstance(status, str) or not status
            or not isinstance(resource_witness, dict)
            or type(resource_witness.get("sufficient")) is not bool):
        _invalid(RUN_STOP_RECEIPT_INVALID)
    safe_resume, disposition = _resume_state(status)
    body = {
        "schema": RUN_STOP_SCHEMA,
        "policy_version": "ADR-015/R01",
        "run_id": student.run_id,
        "accepted_manifest_sha256": manifest_sha256,
        "accepted_generation": student.generation,
        "checkpoint_identity_sha256": _checkpoint_identity(student),
        "optimizer_step": student.retained_state.optimizer_step,
        "stop_reason": status,
        "configured": {
            "minutes": minutes,
            "max_visits": max_visits,
            "steps_per_visit": steps_per_visit,
            "reserve_gib": reserve_gib,
            "source_prefetch_workers": source_prefetch_workers,
        },
        "elapsed_seconds": elapsed_seconds,
        "visits": visits,
        "accepted_visits": accepted,
        "rejected_visits": rejected,
        "admission_status": admission_status,
        "admission_advances": admission_advances,
        "resource_witness": dict(resource_witness),
        "safe_resume_available": safe_resume,
        "resume_disposition": disposition,
        "normal_stop": True,
    }
    digest = sha256(_canonical(body).encode()).hexdigest()
    receipt = {**body, "receipt_sha256": digest}
    checkpoints._record(run_dir, {
        "event": RUN_STOP_EVENT,
        "generation": student.generation,
        "accepted_manifest_sha256": manifest_sha256,
        "optimizer_step": student.retained_state.optimizer_step,
        "stop_reason": status,
        "visits_this_command": visits,
        "safe_resume_available": safe_resume,
        "resume_disposition": disposition,
        "receipt_sha256": digest,
        "run_stop_receipt": receipt,
    })
    return digest


def read_latest_run_stop_receipt(run_dir: Path) -> dict | None:
    """Return the latest valid durable normal-stop receipt for cold resume/status."""
    path = Path(run_dir) / "events.jsonl"
    if not path.is_file():
        return None
    for raw in reversed(path.read_text(encoding="utf-8").splitlines()):
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if event.get("event") != RUN_STOP_EVENT:
            continue
        receipt = event.get("run_stop_receipt")
        if not isinstance(receipt, dict) or receipt.get("schema") != RUN_STOP_SCHEMA:
            _invalid(RUN_STOP_RECEIPT_INVALID)
        expected = receipt.get("receipt_sha256")
        body = {key: value for key, value in receipt.items()
                if key != "receipt_sha256"}
        if (not isinstance(expected, str)
                or sha256(_canonical(body).encode()).hexdigest() != expected
                or event.get("receipt_sha256") != expected):
            _invalid("BAMF_RUN_STOP_RECEIPT_DRIFT")
        return receipt
    return None


__all__ = (
    "RUN_STOP_EVENT", "RUN_STOP_SCHEMA", "read_latest_run_stop_receipt",
    "record_normal_stop_receipt", "stop_resource_witness",
)
