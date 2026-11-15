"""B13-authenticated rejection replay for C03.4 priority recency."""
import hashlib
import json
from pathlib import Path

from bilqis_mlx.data_plane import data_plane
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime import checkpoint_outbox
from bilqis_mlx.runtime.bamf_bundle.records import canonical


SHA256_HEX_LENGTH = 64
_REJECTION_JOURNAL_INVALID = "BAMF_PRIORITY_REJECTION_JOURNAL_INVALID"


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def current_rejections(run_dir, parent, cache):
    """Replay only B13 rejection receipts bound to the exact accepted parent."""
    journal = Path(run_dir) / "events.jsonl"
    if not journal.exists():
        return ()
    if journal.is_symlink() or not journal.is_file():
        _invalid(_REJECTION_JOURNAL_INVALID)
    rows, seen = [], set()
    for raw in journal.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            _invalid(_REJECTION_JOURNAL_INVALID)
        if not isinstance(event, dict) or event.get("event") != "BAMF_CANDIDATE_REJECTED":
            continue
        if event.get("generation") != cache.generation:
            continue
        if (event.get("student_manifest_sha256") != cache.accepted_manifest_sha256
                or event.get("optimizer_step") != parent.retained_state.optimizer_step):
            _invalid("BAMF_PRIORITY_REJECTION_IDENTITY_DRIFT")
        lineage = {"run_id": cache.run_id, "generation": cache.generation}
        if not checkpoint_outbox.ordinary_outbox_lineage(lineage, [event]):
            _invalid("BAMF_PRIORITY_REJECTION_OUTBOX_INVALID")
        evidence = event.get("evidence")
        if not isinstance(evidence, dict) or evidence.get("schema") != "bilqis.bamf.c16.3-rejection/v2":
            continue
        authority_sha256 = event.get("rejection_authority_sha256")
        if (not isinstance(authority_sha256, str)
                or len(authority_sha256) != SHA256_HEX_LENGTH
                or any(char not in "0123456789abcdef" for char in authority_sha256)):
            _invalid("BAMF_PRIORITY_REJECTION_AUTHORITY_INVALID")
        authority = {
            "schema": "bilqis.mlx.bamf-rejection-authority/v1",
            "run_id": cache.run_id,
            "generation": cache.generation,
            "student_manifest_sha256": cache.accepted_manifest_sha256,
            "optimizer_step": parent.retained_state.optimizer_step,
            "evidence": evidence,
        }
        try:
            authority_raw = data_plane().get_object(authority_sha256)
        except ValueError:
            _invalid("BAMF_PRIORITY_REJECTION_AUTHORITY_INVALID")
        if authority_raw != canonical(authority):
            _invalid("BAMF_PRIORITY_REJECTION_AUTHORITY_DRIFT")
        receipt = {
            "schema": "bilqis.mlx.bamf-rejection-receipt/v1",
            "run_id": cache.run_id,
            "generation": cache.generation,
            "student_manifest_sha256": cache.accepted_manifest_sha256,
            "event": event,
        }
        receipt_raw = canonical(receipt)
        receipt_sha256 = hashlib.sha256(receipt_raw).hexdigest()
        try:
            stored_receipt = data_plane().get_object(receipt_sha256)
        except ValueError:
            _invalid("BAMF_PRIORITY_REJECTION_RECEIPT_INVALID")
        if stored_receipt != receipt_raw:
            _invalid("BAMF_PRIORITY_REJECTION_RECEIPT_DRIFT")
        selected = evidence.get("capability")
        visit_id = evidence.get("visit_id")
        candidate_step = evidence.get("candidate_optimizer_step")
        retained_step = evidence.get("retained_optimizer_step")
        reason = evidence.get("retention_reason")
        if (not isinstance(selected, str) or not selected
                or not isinstance(visit_id, str) or not visit_id
                or type(candidate_step) is not int
                or candidate_step <= parent.retained_state.optimizer_step
                or retained_step != parent.retained_state.optimizer_step
                or not isinstance(reason, str) or not reason):
            _invalid("BAMF_PRIORITY_REJECTION_EVIDENCE_INVALID")
        if receipt_sha256 in seen:
            continue
        seen.add(receipt_sha256)
        rows.append((selected, visit_id, reason, receipt_sha256))
    return tuple(rows)


def candidate_step_horizon(run_dir, parent, cache, capability, configured_steps):
    """Project authenticated C16.3 rejection pressure into the teacher horizon rule.

    Rejections do not mutate the accepted teacher state.  The accepted-generation
    journal is therefore the authoritative pressure source for the current
    speculative lineage.  Feed only that bounded projection into the existing
    candidate-step policy rather than inventing a second shortening cadence.
    """
    from bilqis_mlx.learning.learning_experiment import candidate_step_budget

    reasons = {}
    consecutive_interference = 0
    for selected, _visit_id, reason, _receipt in current_rejections(
            run_dir, parent, cache):
        if selected != capability:
            continue
        reasons[reason] = reasons.get(reason, 0) + 1
        consecutive_interference = (
            0 if reason == "NO_MEASURABLE_TARGET_GAIN"
            else consecutive_interference + 1)
    projected_teacher = {
        "causal_experiment": {
            "capability_stagnation": {
                capability + "|": {
                    "current_rejection_reasons": reasons,
                    "consecutive_interference_rejections": consecutive_interference,
                },
            },
        },
    }
    return candidate_step_budget(configured_steps, projected_teacher, capability)


__all__ = ("candidate_step_horizon", "current_rejections")
