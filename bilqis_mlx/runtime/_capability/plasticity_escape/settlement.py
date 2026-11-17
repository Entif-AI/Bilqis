"""Accepted-only debt settlement and plasticity deactivation."""
from ..capability_evaluation import _invalid
from .records import (
    CertifiedSurfaceDebt,
    CertifiedSurfaceId,
    PlasticityEscapeState,
)


def _visit_scores(visit):
    scores = {}
    if not isinstance(visit, dict):
        return scores
    target = visit.get("learning_target") or visit.get("target")
    capability = visit.get("capability_id")
    if isinstance(target, dict) and isinstance(capability, str):
        after, total = target.get("after"), target.get("total")
        if type(after) is int and type(total) is int and total > 0:
            scores[capability] = (after, total)
    for item in visit.get("protected", ()):
        if not isinstance(item, dict):
            continue
        cap, after, total = (
            item.get("capability_id"), item.get("after"), item.get("total"))
        if (isinstance(cap, str) and cap
                and type(after) is int and type(total) is int and total > 0):
            scores[cap] = (after, total)
    return scores


def settle_accepted_escape(
        state: PlasticityEscapeState | None, visit, certified_surfaces,
        *, accepted_optimizer_step):
    """Settle debt only after publication-authorized acceptance and deactivate."""
    if state is None:
        return None
    if (not isinstance(certified_surfaces, (tuple, list))
            or type(accepted_optimizer_step) is not int
            or accepted_optimizer_step < 0):
        _invalid("BAMF_PLASTICITY_ACCEPTED_SETTLEMENT_INVALID")
    scores = _visit_scores(visit)
    debt = {item.surface: item for item in state.debt}
    seen = set()
    for surface in certified_surfaces:
        identity = CertifiedSurfaceId.from_certified_surface(surface)
        if identity is None:
            continue
        score = scores.get(identity.capability_id)
        measured = (surface.get("after"), surface.get("total"))
        if (score is None or type(measured[0]) is not int
                or type(measured[1]) is not int or measured[1] <= 0
                or score[1] != measured[1]):
            continue
        comparable = (
            surface.get("rubric_sha256") == visit.get("rubric_sha256")
            and surface.get("source_sha256") == visit.get("source_sha256")
            and surface.get("fixed_cohort_sha256") == visit.get("fixed_cohort_sha256")
            and surface.get("retention_policy_sha256")
            == visit.get("retention_policy_sha256"))
        if not comparable:
            continue
        seen.add(identity)
        amount = max(0, measured[0] - score[0])
        if amount:
            debt[identity] = CertifiedSurfaceDebt(
                identity, amount, measured[0], measured[1])
        else:
            debt.pop(identity, None)

    protected = {
        item.get("capability_id"): item
        for item in (visit.get("protected", ()) if isinstance(visit, dict) else ())
        if isinstance(item, dict)}
    for identity, existing in tuple(debt.items()):
        if identity in seen:
            continue
        item = protected.get(identity.capability_id)
        delta = item.get("delta") if isinstance(item, dict) else None
        if type(delta) is int:
            amount = max(0, existing.amount - delta)
            if amount:
                debt[identity] = CertifiedSurfaceDebt(
                    identity, amount, existing.certified_correct, existing.total)
            else:
                debt.pop(identity, None)

    ordered = tuple(item for _identity, item in sorted(
        debt.items(), key=lambda pair: (pair[0].surface_id, pair[0].capability_id)))
    return PlasticityEscapeState(
        policy_epoch_sha256=state.policy_epoch_sha256,
        target_capability_id=state.target_capability_id,
        active=False,
        activation_reasons=state.activation_reasons,
        attempts_since_retained=0,
        school_attempts_since_retained=0,
        debt=ordered,
        unqualified_debt_capability_ids=state.unqualified_debt_capability_ids,
        last_repair_opportunity=(
            accepted_optimizer_step if ordered else state.last_repair_opportunity),
        deactivated=state.active or state.deactivated)
