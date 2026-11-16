"""Read-only #1318 projection over already-issued BAMF visit evidence."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from bilqis_mlx.errors.authority import authority_label
from bilqis_mlx.runtime.teacher_observation_capture import read_sidecar

VISIT_EVIDENCE_SCHEMA = "bilqis.bamf.visit-evidence/v1"
GENERATED_GRADE_EVIDENCE_SCHEMA = "bilqis.bamf.generated-grade-evidence/v1"
UNKNOWN = "UNKNOWN"
NOT_MEASURED = "NOT_MEASURED"


def unknown_generated_grade_evidence(grade_id=None):
    """Represent missing producer evidence explicitly; never infer grade rationale."""
    return {
        "schema": GENERATED_GRADE_EVIDENCE_SCHEMA,
        "state": UNKNOWN,
        "grade_id": grade_id,
        "proposal_id": None,
        "definition_id": None,
        "definition_version": None,
        "predecessor_definition_id": None,
        "learner_evidence_epoch": None,
        "factory_release_sha256": None,
        "policy_epoch": None,
        "a08_provenance": [],
        "a09_provenance": [],
        "selected_semantic_ids": [],
        "members": [],
        "developmental_slope_state": UNKNOWN,
        "synthesis_dimensions": [],
        "representative_coverage": None,
        "downstream_unlocks": None,
        "constituent_rationale": None,
        "required_bridges": [],
        "deferred_candidates": [],
        "holds": [],
        "predecessor_certification_receipt": None,
    }


def _selected_frontier_capability(selection):
    frontier = getattr(selection, "_lawful_frontier", None)
    capability = getattr(getattr(selection, "offer", None), "capability_id", None)
    for item in getattr(frontier, "capabilities", ()):
        if getattr(item, "capability_id", None) == capability:
            return item
    return None


def selected_visit_evidence(selection):
    """Project C03/C06-issued selection facts without re-ranking or re-deciding."""
    identity = getattr(getattr(selection, "visit", None), "identity", None)
    frontier = getattr(selection, "_lawful_frontier", None)
    item = _selected_frontier_capability(selection)
    ranking = getattr(selection, "ranking_evidence", None) or {}
    grade_id = getattr(selection, "lesson_grade", None)
    return {
        "schema": VISIT_EVIDENCE_SCHEMA,
        "state": "PARTIAL",
        "grade_id": grade_id,
        "grade_definition_id": None,
        "grade_definition_version": None,
        "capability_id": getattr(getattr(selection, "offer", None), "capability_id", None),
        "semantic_ids": list(getattr(item, "semantic_ids", ())),
        "prerequisites": list(getattr(item, "prerequisites", ())),
        "semantic_prerequisites": list(getattr(item, "semantic_prerequisites", ())),
        "constituents": list(getattr(item, "constituents", ())),
        "lawful_frontier_sha256": getattr(frontier, "frontier_sha256", None),
        "a09_snapshot_sha256": getattr(frontier, "a09_snapshot_sha256", None),
        "a09_closure_sha256": getattr(frontier, "a09_closure_sha256", None),
        "ranking": deepcopy(ranking),
        "teacher_visit_id": getattr(identity, "visit_id", None),
        "teacher_policy_key": getattr(identity, "policy_key", None),
        "selected_option_id": getattr(selection, "option_id", None),
        "lesson_roles": {},
        "target": {"state": NOT_MEASURED},
        "affected_scope_state": UNKNOWN,
        "affected": [],
        "protected_scope_state": UNKNOWN,
        "protected": [],
        "retention_economics_state": UNKNOWN,
        "retention_policy_sha256": None,
        "threshold_refs": [],
        "budget_refs": [],
        "probe_each": None,
        "baseline_coverage": None,
        "decision": None,
        "blocking_capability": None,
        "blocking_scope": None,
        "reason": None,
        "human_reason": None,
        "candidate_evidence_sha256": None,
        "candidate_evidence_file": None,
    }


def merge_retention_scorecard(visit, scorecard):
    result = deepcopy(visit)
    if not isinstance(scorecard, dict) or scorecard.get("schema") != "bilqis.bamf.retention-scorecard/v1":
        return result
    result["target"] = deepcopy(scorecard.get("target", {"state": NOT_MEASURED}))
    result["protected"] = deepcopy(scorecard.get("protected", []))
    result["protected_scope_state"] = "PARTIAL"
    result["retention_economics_state"] = "PARTIAL"
    result["retention_policy_sha256"] = scorecard.get("policy_sha256")
    result["evidence_stage"] = scorecard.get("evidence_stage")
    result["learning_signals"] = deepcopy(scorecard.get("learning_signals", ()))
    result["learning_target"] = deepcopy(scorecard.get("learning_target"))
    for field in ("fixed_cohort_sha256", "rubric_sha256", "source_sha256"):
        result[field] = scorecard.get(field)
    result["probe_each"] = scorecard.get("probe_each")
    result["baseline_coverage"] = deepcopy(scorecard.get("baseline_coverage"))
    return result


def _role_counts(payload):
    counts = {}
    for step in payload.get("steps", ()):
        for position in step.get("positions", ()):
            for role in position.get("roles", ()):
                counts[role] = counts.get(role, 0) + 1
        mentors = step.get("mentors")
        if isinstance(mentors, (list, tuple)):
            counts["mentors"] = counts.get("mentors", 0) + len(mentors)
        elif mentors:
            counts["mentors"] = counts.get("mentors", 0) + 1
    return dict(sorted(counts.items()))


def apply_candidate_evidence(run_dir: Path, visit, reference):
    """Hydrate only content-addressed candidate evidence for live or cold replay."""
    result = deepcopy(visit)
    if not isinstance(reference, dict) or not isinstance(reference.get("object"), dict):
        return result
    payload = read_sidecar(run_dir, reference["object"])
    result["candidate_evidence_sha256"] = reference["object"].get("sha256")
    result["candidate_evidence_file"] = reference["object"].get("file")
    result["lesson_roles"] = _role_counts(payload)
    proposal = payload.get("proposal", {})
    for target, source in (
        ("teacher_visit_id", "visit_id"),
        ("teacher_policy_key", "selected_policy_key"),
        ("selected_option_id", "selected_option"),
        ("capability_id", "capability"),
    ):
        if result.get(target) is None:
            result[target] = proposal.get(source)
    outcome = payload.get("outcome", {})
    decision = outcome.get("decision") if isinstance(outcome, dict) else None
    if isinstance(decision, dict):
        result["decision"] = decision.get("decision")
        result["reason"] = decision.get("reason")
        result["blocking_capability"] = decision.get("blocking_capability")
        result["blocking_scope"] = decision.get("blocking_scope")
        result["human_reason"] = authority_label(
            result["reason"], blocking_capability=result["blocking_capability"],
            blocking_scope=result["blocking_scope"])
        if result.get("retention_policy_sha256") is None:
            result["retention_policy_sha256"] = decision.get("policy_sha256")
        if result.get("baseline_coverage") is None:
            result["baseline_coverage"] = deepcopy(decision.get("baseline_coverage"))
    result["state"] = "COMPLETE"
    return result


def complete_visit_evidence(run_dir, visit, reference, decision):
    result = apply_candidate_evidence(Path(run_dir), visit, reference)
    if decision is not None:
        result["decision"] = getattr(decision, "decision", None)
        result["reason"] = getattr(decision, "reason", None)
        result["blocking_capability"] = getattr(decision, "blocking_capability", None)
        result["blocking_scope"] = getattr(decision, "blocking_scope", None)
        result["human_reason"] = authority_label(
            result["reason"], blocking_capability=result["blocking_capability"],
            blocking_scope=result["blocking_scope"])
    result["state"] = "COMPLETE"
    return result


__all__ = (
    "GENERATED_GRADE_EVIDENCE_SCHEMA", "NOT_MEASURED", "UNKNOWN",
    "VISIT_EVIDENCE_SCHEMA", "apply_candidate_evidence", "complete_visit_evidence",
    "merge_retention_scorecard", "selected_visit_evidence",
    "unknown_generated_grade_evidence",
)
