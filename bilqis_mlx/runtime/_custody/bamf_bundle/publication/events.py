"""B13 publication-side outbox and rejection evidence helpers."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.data_plane import DataPlaneError, data_plane

from ..records import CompleteStudent, canonical, invalid, sha
from .storage import _live_bundle_manifest, _pointer_lock, _read_pointer


def _validated_c03_rejection_evidence(student: CompleteStudent, pointer: dict,
                                      evidence: dict) -> dict:
    """Bind supported rejection evidence to an actually issued C03 visit."""
    if evidence.get("schema") != "bilqis.bamf.c16.3-rejection/v2":
        return dict(evidence)
    from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
    from bilqis_mlx.learning.teacher_visit_identity import (
        TeacherVisitIdentity, require_teacher_visit_receipt,
    )

    state = student.teacher_state
    identity = TeacherVisitIdentity.from_record(evidence.get("teacher_visit"))
    if (evidence.get("visit_id") != identity.visit_id
            or evidence.get("capability") != identity.capability_id
            or evidence.get("selected_policy_key") != identity.policy_key
            or identity.run_identity_sha256 != student.run_identity.digest
            or identity.run_seed != student.run_identity.run_seed
            or identity.generation != student.generation
            or identity.accepted_manifest_sha256 != pointer["manifest_sha256"]
            or identity.student_sha256 != candidate_identity_digest(student.retained_state)
            or identity.selection_seed != state.get("next_seed")
            or identity.cursor != state.get("cursor")
            or ("c03_lineage" in state
                and (identity.teacher_identity != state.get("teacher_identity")
                     or identity.teacher_epoch != state.get("teacher_epoch")))):
        invalid("BAMF_REJECTION_VISIT_DRIFT")
    require_teacher_visit_receipt(identity)
    return {**evidence, "teacher_visit": identity.to_record()}


def reconcile_bamf_outbox(
        run_dir: Path, student: CompleteStudent, *, publish_missing=True) -> bool:
    """Reconcile while the caller holds the generation pointer writer lock."""
    from bilqis_mlx.runtime import checkpoints
    return checkpoints._reconcile_delivery_outbox(
        Path(run_dir), {"run_id": student.run_id, "generation": student.generation,
                        "delivery_outbox": list(student.outbox)},
        publish_missing=publish_missing)


def record_bamf_rejection(run_dir: Path, student: CompleteStudent, evidence: dict) -> str:
    """Publish idempotent failure evidence without minting or mutating a generation."""
    if type(student) is not CompleteStudent or not isinstance(evidence, dict) or not evidence:
        invalid("BAMF_REJECTION_EVIDENCE_INVALID")
    from bilqis_mlx.runtime import checkpoint_outbox, checkpoints
    run_dir = Path(run_dir)
    pointer_path = run_dir / "bamf-state.json"
    with _pointer_lock(run_dir):
        pointer = _read_pointer(pointer_path)
        if (pointer is None or pointer["run_id"] != student.run_id
                or pointer["generation"] != student.generation):
            invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
        manifest = _live_bundle_manifest(run_dir, pointer)
        optimizer_step = manifest.get("optimizer", {}).get("step") if isinstance(manifest, dict) else None
        if type(optimizer_step) is not int or optimizer_step != manifest.get("tensors", {}).get("optimizer_step"):
            invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
        evidence = _validated_c03_rejection_evidence(student, pointer, evidence)
        authority = {
            "schema": "bilqis.mlx.bamf-rejection-authority/v1",
            "run_id": student.run_id,
            "generation": student.generation,
            "student_manifest_sha256": pointer["manifest_sha256"],
            "optimizer_step": optimizer_step,
            "evidence": dict(evidence),
        }
        authority_raw = canonical(authority)
        authority_sha256 = sha(authority_raw)
        data_plane().put_object(authority_sha256, authority_raw)
        event = {
            "event": "BAMF_CANDIDATE_REJECTED",
            "generation": pointer["generation"],
            "student_manifest_sha256": pointer["manifest_sha256"],
            "optimizer_step": optimizer_step,
            "evidence": dict(evidence),
            "rejection_authority_sha256": authority_sha256,
        }
        record = {"run_id": pointer["run_id"], "generation": pointer["generation"]}
        outbox = checkpoint_outbox.with_delivery_outbox(record, (event,))["delivery_outbox"]
        receipt = {
            "schema": "bilqis.mlx.bamf-rejection-receipt/v1",
            "run_id": student.run_id, "generation": student.generation,
            "student_manifest_sha256": pointer["manifest_sha256"], "event": outbox[0],
        }
        raw = canonical(receipt)
        digest = sha(raw)
        data_plane().put_object(digest, raw)
        checkpoints._reconcile_delivery_outbox(
            run_dir, {**record, "delivery_outbox": outbox})
        return digest
