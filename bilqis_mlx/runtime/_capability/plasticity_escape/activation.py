"""Policy-driven derivation of exceptional plasticity activation."""
from fractions import Fraction

from ..capability_evaluation import _invalid, _sha
from .records import (
    CertifiedSurfaceDebt,
    CertifiedSurfaceId,
    FRONTIER_STARVATION_ATTEMPTS,
    ORDINARY_STARVATION_ATTEMPTS,
    PlasticityActivationReason,
    PlasticityEscapeState,
    SCHOOL_DROUGHT_ATTEMPTS,
)


def _latest_score(health):
    if not isinstance(health, dict) or not isinstance(health.get("latest"), dict):
        return None
    latest = health["latest"]
    correct, total = latest.get("correct"), latest.get("total")
    if (type(correct) is not int or type(total) is not int or total <= 0
            or not 0 <= correct <= total):
        return None
    return correct, total, Fraction(correct, total)


def _debt_context(health_state, previous):
    debt = {item.surface: item for item in previous.debt} if previous else {}
    unqualified = set(previous.unqualified_debt_capability_ids if previous else ())
    for surface in health_state.get("certified_surfaces", ()):
        identity = CertifiedSurfaceId.from_certified_surface(surface)
        if identity is None:
            capability = surface.get("capability_id") if isinstance(surface, dict) else None
            if isinstance(capability, str) and capability:
                unqualified.add(capability)
            continue
        correct, total = surface.get("after"), surface.get("total")
        if (type(correct) is int and type(total) is int and total > 0
                and 0 <= correct <= total and identity not in debt):
            debt[identity] = CertifiedSurfaceDebt(identity, 0, correct, total)
    return (
        tuple(sorted(debt.values(),
                     key=lambda item: (item.surface.surface_id, item.surface.capability_id))),
        tuple(sorted(unqualified)),
    )


def derive_plasticity_escape_state(
        teacher_state, learning_health_state, *, target_capability_id,
        target_group_id, frontier_group_id, phase, curriculum_scope,
        policy_epoch_sha256):
    """Derive strict escape from accepted/replayed failure and measured health."""
    if (not isinstance(target_capability_id, str) or not target_capability_id
            or not isinstance(target_group_id, str) or not target_group_id
            or not isinstance(frontier_group_id, str) or not frontier_group_id
            or not isinstance(phase, str) or not phase
            or not isinstance(curriculum_scope, str) or not curriculum_scope
            or not _sha(policy_epoch_sha256)):
        _invalid("BAMF_PLASTICITY_ACTIVATION_INPUT_INVALID")
    teacher = teacher_state if isinstance(teacher_state, dict) else {}
    channel = teacher.get("causal_experiment")
    channel = channel if isinstance(channel, dict) else {}
    stagnation = channel.get("capability_stagnation")
    stagnation = stagnation if isinstance(stagnation, dict) else {}
    record = stagnation.get(target_capability_id + "|" + curriculum_scope)
    record = record if isinstance(record, dict) else {}
    attempts = record.get("attempts_since_retained", 0)
    school_attempts = channel.get("school_attempts_since_retained", 0)
    attempts = attempts if type(attempts) is int and attempts >= 0 else 0
    school_attempts = (
        school_attempts if type(school_attempts) is int and school_attempts >= 0 else 0)

    health_state = learning_health_state if isinstance(learning_health_state, dict) else {}
    by_capability = health_state.get("by_capability")
    by_capability = by_capability if isinstance(by_capability, dict) else {}
    current = _latest_score(by_capability.get(target_capability_id))
    valid = tuple(score for score in map(_latest_score, by_capability.values())
                  if score is not None)
    mean = (sum((score[2] for score in valid), Fraction()) / len(valid)
            if valid else None)
    threshold = (FRONTIER_STARVATION_ATTEMPTS
                 if target_group_id == frontier_group_id
                 else ORDINARY_STARVATION_ATTEMPTS)
    local = attempts >= threshold
    drought = bool(
        school_attempts >= SCHOOL_DROUGHT_ATTEMPTS
        and current is not None and mean is not None and current[2] < mean)
    training_phase = phase in {"MAIN", "RECOVERY_1", "RECOVERY_2"}
    reasons = []
    if training_phase and current is not None and local:
        reasons.append(PlasticityActivationReason.LOCAL_STARVATION)
    if training_phase and current is not None and drought:
        reasons.append(PlasticityActivationReason.SCHOOL_RETENTION_DROUGHT_BELOW_MEAN)

    prior = health_state.get("plasticity_escape")
    previous = PlasticityEscapeState.from_record(prior) if isinstance(prior, dict) else None
    debt, unqualified = _debt_context(health_state, previous)
    active = bool(reasons)
    return PlasticityEscapeState(
        policy_epoch_sha256=policy_epoch_sha256,
        target_capability_id=target_capability_id,
        active=active,
        activation_reasons=tuple(reasons),
        attempts_since_retained=attempts,
        school_attempts_since_retained=school_attempts,
        debt=debt,
        unqualified_debt_capability_ids=unqualified,
        last_repair_opportunity=(
            previous.last_repair_opportunity if previous is not None else None),
        deactivated=bool(previous is not None and previous.active and not active))
