"""Accepted-custody runtime projection for bounded learning-health history."""
from __future__ import annotations

from bilqis_mlx.diagnostics.learning_health import (
    STATE_SCHEMA, project_learning_health, validate_learning_health_state,
)
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from .evidence_projection import complete_visit_evidence, selected_visit_evidence

_MAX_CAPABILITIES = 48


def _accepted_state(parent):
    state = getattr(parent, "learning_health_state", None)
    if state is not None:
        state = validate_learning_health_state(dict(state))
        return (
            dict(state["by_capability"]), state["coverage_state"],
            tuple(state.get("certified_surfaces", ())),
        )
    pristine = parent.generation == 0 and parent.retained_state.optimizer_step == 0
    return {}, "VALID" if pristine else "PARTIAL", ()


def accepted_learning_health_state(
        run_dir, parent, selection, candidate_evidence, decision, retained, capture, *,
        plasticity_escape=None):
    """Derive one bounded sidecar before publication so B13 authenticates it."""
    history, coverage, certified_surfaces = _accepted_state(parent)
    visit = complete_visit_evidence(
        run_dir, selected_visit_evidence(selection), candidate_evidence, decision)
    methodology = getattr(capture, "learning_methodology", None)
    visit["learning_methodology"] = (
        methodology() if callable(methodology) else ())
    visit["accepted_checkpoint_sha256"] = candidate_identity_digest(retained)
    visit["accepted_optimizer_step"] = retained.optimizer_step
    visit["history_seed_state"] = coverage
    health = project_learning_health(
        visit, accepted=True, previous=history.get(visit["capability_id"]),
        certified_surfaces=certified_surfaces)
    updated = dict(history)
    updated.pop(visit["capability_id"], None)
    updated[visit["capability_id"]] = health
    while len(updated) > _MAX_CAPABILITIES:
        updated.pop(next(iter(updated)))
    state = {
        "schema": STATE_SCHEMA,
        "coverage_state": (
            "PARTIAL" if coverage == "PARTIAL"
            or health.get("history_state") == "PARTIAL" else "VALID"),
        "by_capability": updated,
        "certified_surfaces": list(certified_surfaces),
    }
    previous_plasticity = None
    parent_state = getattr(parent, "learning_health_state", None)
    if isinstance(parent_state, dict) and isinstance(
            parent_state.get("plasticity_escape"), dict):
        from bilqis_mlx.runtime.plasticity_escape import PlasticityEscapeState
        previous_plasticity = PlasticityEscapeState.from_record(
            parent_state["plasticity_escape"])
    settled = previous_plasticity
    if plasticity_escape is not None:
        from bilqis_mlx.runtime.plasticity_escape import settle_accepted_escape
        settled = settle_accepted_escape(
            plasticity_escape, visit, certified_surfaces,
            accepted_optimizer_step=retained.optimizer_step)
    if settled is not None:
        state["plasticity_escape"] = settled.to_record()
    validate_learning_health_state(state)
    return state, health


def accepted_learning_health_from_parent(parent):
    """Read the authenticated aggregate for cold Mission Control fallback."""
    history, _, _ = _accepted_state(parent)
    return history


__all__ = (
    "accepted_learning_health_state",
    "accepted_learning_health_from_parent",
)
