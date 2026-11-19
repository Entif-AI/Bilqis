"""Typed R13 weakness context and B13 rejection-evidence contracts."""
from __future__ import annotations

import hashlib
import json

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory._model.weakness import WeaknessClassId


EVIDENCE_SCHEMA = "bilqis.bamf.structural-weakness/v1"
CONTEXT_SCHEMA = "bilqis.bamf.structural-weakness-context/v1"
LEDGER_SCHEMA = "bilqis.bamf.structural-weakness-ledger/v1"
SHA256_LENGTH = 64


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode()).hexdigest()


def issue_weakness_context(selection) -> dict:
    """Project current lawful WHAT/source/grade policy into weakness identity."""
    from bilqis_mlx.runtime.accepted_priority_visit_contracts import (
        _require_issued,
    )

    _require_issued(selection)
    frontier = getattr(selection, "_lawful_frontier", None)
    metadata = selection.metadata
    how = metadata.get("how_context") if isinstance(metadata, dict) else None
    capability = getattr(getattr(selection, "visit", None), "identity", None)
    capability = getattr(capability, "capability_id", None)
    if (frontier is None or not isinstance(how, dict)
            or not isinstance(capability, str) or not capability
            or capability != getattr(getattr(selection, "offer", None),
                                     "capability_id", None)
            or capability not in set(getattr(frontier, "ready_capability_ids", ()))):
        _invalid("BAMF_WEAKNESS_CONTEXT_INVALID")
    required_hashes = (
        "grade_definition_sha256", "source_binding_sha256",
        "factory_release_sha256", "rubric_sha256",
    )
    if any(not isinstance(how.get(key), str) or len(how[key]) != SHA256_LENGTH
           for key in required_hashes) or any(
               not isinstance(how.get(key), str) or not how[key]
               for key in ("grade", "curriculum_scope")):
        _invalid("BAMF_WEAKNESS_CONTEXT_INVALID")
    record = {
        "schema": CONTEXT_SCHEMA,
        "capability_id": capability,
        "grade_id": how["grade"],
        "curriculum_scope": how["curriculum_scope"],
        "grade_definition_sha256": how["grade_definition_sha256"],
        "source_binding_sha256": how["source_binding_sha256"],
        "factory_release_sha256": how["factory_release_sha256"],
        "rubric_sha256": how["rubric_sha256"],
        "active_grade_activation_sha256": frontier.active_grade_activation_sha256,
        "active_grade_definition_sha256": frontier.active_grade_definition_sha256,
        "policy_epoch": frontier.policy_epoch,
        "rights_epoch": frontier.rights_epoch,
        "correction_generation": frontier.correction_generation,
        "source_authority_registry_sha256":
            frontier.source_authority_registry_sha256,
    }
    record["context_sha256"] = _digest(record)
    return record


def _validate_context(record: dict) -> dict:
    if not isinstance(record, dict) or set(record) != {
        "schema", "capability_id", "grade_id", "curriculum_scope",
        "grade_definition_sha256", "source_binding_sha256",
        "factory_release_sha256", "rubric_sha256",
        "active_grade_activation_sha256", "active_grade_definition_sha256",
        "policy_epoch", "rights_epoch", "correction_generation",
        "source_authority_registry_sha256", "context_sha256",
    } or record.get("schema") != CONTEXT_SCHEMA:
        _invalid("BAMF_WEAKNESS_CONTEXT_INVALID")
    if record["context_sha256"] != _digest({
            key: value for key, value in record.items()
            if key != "context_sha256"}):
        _invalid("BAMF_WEAKNESS_CONTEXT_DRIFT")
    return record


def validate_weakness_evidence(record: dict) -> dict:
    if not isinstance(record, dict) or set(record) != {
        "schema", "state", "freshness", "capability_id", "weakness_class",
        "context", "candidate_evidence_sha256", "outcome_sha256",
        "retention_reason", "weakness_evidence_sha256",
    } or record.get("schema") != EVIDENCE_SCHEMA:
        _invalid("BAMF_WEAKNESS_EVIDENCE_INVALID")
    if (record.get("state") != "UNRESOLVED"
            or record.get("freshness") != "FRESH_EQUIVALENT_REQUIRED"):
        _invalid("BAMF_WEAKNESS_EVIDENCE_INVALID")
    context = _validate_context(record["context"])
    try:
        weakness = WeaknessClassId.from_record(record["weakness_class"])
    except (TypeError, ValueError) as exc:
        _invalid("BAMF_WEAKNESS_CLASS_INVALID")
        raise AssertionError from exc
    if (weakness.capability_id != record.get("capability_id")
            or context["capability_id"] != record.get("capability_id")
            or record["weakness_evidence_sha256"] != _digest({
                key: value for key, value in record.items()
                if key != "weakness_evidence_sha256"})):
        _invalid("BAMF_WEAKNESS_EVIDENCE_DRIFT")
    return record


def validate_rejection_weaknesses(
        evidence: dict, rejection_receipt_sha256: str | None = None,
) -> tuple[dict, ...]:
    records = evidence.get("structural_weaknesses", ())
    if not isinstance(records, (tuple, list)):
        _invalid("BAMF_WEAKNESS_EVIDENCE_INVALID")
    candidate = evidence.get("candidate_evidence")
    candidate_sha = (
        candidate.get("object", {}).get("sha256")
        if isinstance(candidate, dict) else None)
    outcome = evidence.get("how_outcome")
    outcome_sha = outcome.get("outcome_sha256") if isinstance(outcome, dict) else None
    result = []
    for record in records:
        validate_weakness_evidence(record)
        if (record["capability_id"] != evidence.get("capability")
                or record["retention_reason"] != evidence.get("retention_reason")
                or record["candidate_evidence_sha256"] != candidate_sha
                or record["outcome_sha256"] != outcome_sha):
            _invalid("BAMF_WEAKNESS_REJECTION_BINDING_DRIFT")
        result.append({
            "weakness": record,
            "candidate_evidence": candidate,
            **({"rejection_receipt_sha256": rejection_receipt_sha256}
               if rejection_receipt_sha256 is not None else {}),
        })
    return tuple(result)


__all__ = (
    "CONTEXT_SCHEMA", "EVIDENCE_SCHEMA", "LEDGER_SCHEMA", "SHA256_LENGTH",
    "_digest", "_invalid", "issue_weakness_context",
    "validate_rejection_weaknesses", "validate_weakness_evidence",
)
