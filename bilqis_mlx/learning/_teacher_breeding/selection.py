"""Selection and filtering of effective teacher policies."""
from __future__ import annotations
from ..teacher_strategy_population import (
    active_effective_strategy_keys, checkpoint_active_effective_strategy_keys,
    effective_policy_key, effective_strategy_inventory, BAMF_SUCCESSOR_SELECTION,
)
from .mutation import mint_bespoke_effective_strategy

UNPROVEN_BESPOKE_PER_CAPABILITY = 8

def _numeric_scope_family(scope: str) -> str | None:
    """Return the stable release family for a numeric-scope revision."""
    if not isinstance(scope, str):
        return None
    family, separator, leaf = scope.rpartition("/")
    return family if separator and family and leaf.isdigit() else None


def portable_retained_challenger(teacher: dict, *, capability: str, phase: str,
                                 curriculum_scope: str):
    """Retry one proven same-capability policy after a numeric scope revision.

    Prior-scope reward remains prior-scope evidence. This helper uses retention
    only to prioritize one fresh trial in the new scope; it never copies the old
    contextual record forward.
    """
    family = _numeric_scope_family(curriculum_scope)
    if family is None:
        return None
    channel = teacher.get("causal_experiment", {})
    strategies = teacher.get("strategies", {})
    inventory = effective_strategy_inventory(teacher)
    live = set(channel.get("live_effective_strategies", inventory))
    current = channel.get("contexts", {}).get(
        capability + "|" + phase + "|" + curriculum_scope, {})
    tried = {
        effective_policy_key(strategies[key])
        for key in current if key in strategies
    }
    candidates = {}
    for context_key, records in channel.get("contexts", {}).items():
        try:
            context_capability, _context_phase, context_scope = context_key.split("|", 2)
        except ValueError:
            continue
        if (context_capability != capability or context_scope == curriculum_scope or
                _numeric_scope_family(context_scope) != family or
                not isinstance(records, dict)):
            continue
        for policy_key, record in records.items():
            policy = strategies.get(policy_key)
            if policy is None or not isinstance(record, dict):
                continue
            retained = int(record.get("retained", 0))
            trials = int(record.get("trials", 0))
            if retained < 1 or trials < retained:
                continue
            effective = effective_policy_key(policy)
            if effective not in live or effective in tried:
                continue
            target = candidates.setdefault(effective, {
                "retained": 0, "trials": 0, "reward_sum": 0.,
                "members": [], "source_scopes": set(),
            })
            target["retained"] += retained
            target["trials"] += trials
            target["reward_sum"] += float(record.get("reward_sum", 0.))
            target["members"].append(policy_key)
            target["source_scopes"].add(context_scope)
    if not candidates:
        return None

    def rank(item):
        effective, record = item
        return (
            record["retained"] / record["trials"], record["retained"],
            record["reward_sum"] / record["trials"], record["trials"], effective,
        )

    effective, record = max(candidates.items(), key=rank)
    member = max(
        record["members"],
        key=lambda key: (
            int(teacher.get("global_stats", {}).get(key, {}).get("trials", 0)), key))
    return member, strategies[member], {
        "portable_effective_policy_key": effective,
        "portable_prior_retained": record["retained"],
        "portable_prior_trials": record["trials"],
        "portable_source_scopes": sorted(record["source_scopes"]),
    }


def pressure_challenger(engine, teacher: dict, rng, *, capability: str, phase: str,
                        curriculum_scope: str, diagnostic_key: str | None,
                        total_capabilities: int):
    portable = portable_retained_challenger(
        teacher, capability=capability, phase=phase,
        curriculum_scope=curriculum_scope)
    if portable is not None:
        return (*portable[:2], "PORTABLE_RETAINED_CHALLENGER", portable[2])
    novel = mint_bespoke_effective_strategy(
        engine, teacher, rng, capability=capability,
        curriculum_scope=curriculum_scope, diagnostic_key=diagnostic_key,
        total_capabilities=total_capabilities)
    return ((*novel[:2], "FRESH_MUTATED_CHALLENGER", novel[2])
            if novel is not None else None)


def selection_population(teacher: dict, *, grade: str, capability: str,
                         curriculum_scope: str, scope: dict, channel: dict,
                         context_key: str, student_checkpoint_sha256: str | None,
                         total_capabilities: int | None):
    active, inventory = active_effective_strategy_keys(
        teacher, grade, scope, total_capabilities=total_capabilities)
    active = filter_active_effective(
        teacher, grade=grade, capability=capability,
        curriculum_scope=curriculum_scope, active_effective=active,
        inventory=inventory)
    active, retired = checkpoint_active_effective_strategy_keys(
        teacher, grade, scope, channel, context_key, active, inventory,
        student_checkpoint_sha256)
    return active, inventory, retired


def selection_metadata(teacher: dict, *, channel: dict, inventory: dict,
                       active_effective, checkpoint_retired,
                       total_capabilities: int | None,
                       diagnostic_context_consumed: bool,
                       diagnostic_context_key: str | None,
                       selection_reason: str, selection_policy: str,
                       selection_detail: dict | None = None) -> dict:
    live = channel.get("live_effective_strategies")
    live_count = len(live) if isinstance(live, list) else len(inventory)
    result = {
        "diagnostic_context_consumed": diagnostic_context_consumed,
        "diagnostic_context_key": diagnostic_context_key,
        "selection_reason": selection_reason, "selection_policy": selection_policy,
        "active_effective_strategy_count": len(active_effective),
        "dormant_effective_strategy_count": live_count - len(active_effective),
        "live_effective_strategy_count": live_count,
        "retired_effective_strategy_count": len(channel.get("retired_effective_strategies", ())),
        "strategy_archive_count": len(teacher.get("strategies", {})),
        "realized_action_ecology_count": len(
            channel.get("realized_action_ecology", {})),
        "checkpoint_retired_effective_strategy_count": len(checkpoint_retired),
    }
    if total_capabilities is not None:
        from ..teacher_population_control import population_limits
        limits = population_limits(total_capabilities)
        result.update(strategy_population_capacity=limits.max_effective,
                      active_effective_strategy_capacity=limits.active_effective)
    if selection_detail:
        result.update(selection_detail)
    return result


def filter_active_effective(teacher: dict, *, grade: str, capability: str,
                            curriculum_scope: str, active_effective,
                            inventory):
    """Keep newborn bespoke policies local until retention proves them."""
    births = teacher.get("causal_experiment", {}).get("strategy_births", {})
    local_unproven = sorted(
        ((int(birth.get("birth_event", 0)), key)
         for key, birth in births.items()
         if isinstance(birth, dict) and not birth.get("proven_retained") and
         birth.get("origin_capability") == capability and
         birth.get("curriculum_scope") == curriculum_scope),
        reverse=True)
    current_unproven = {key for _, key in local_unproven[:UNPROVEN_BESPOKE_PER_CAPABILITY]}

    def allowed(key):
        birth = births.get(key)
        if not isinstance(birth, dict):
            return True
        if birth.get("proven_retained"):
            if teacher.get("selection_contract") == BAMF_SUCCESSOR_SELECTION:
                return birth.get("curriculum_scope") == curriculum_scope
            return birth.get("origin_grade") == grade
        if birth.get("curriculum_scope") != curriculum_scope:
            return False
        return (birth.get("origin_capability") == capability and
                key in current_unproven)

    live = set(teacher.get("causal_experiment", {}).get(
        "live_effective_strategies", inventory))
    eligible = [key for key in active_effective if key in live and allowed(key)]
    for key in sorted(live):
        if len(eligible) >= len(active_effective):
            break
        if key in inventory and key not in eligible and allowed(key):
            eligible.append(key)
    if not eligible:
        def recovery_rank(key):
            birth = births.get(key)
            if isinstance(birth, dict) and birth.get("proven_retained"):
                return (0, key)
            return (1 if not isinstance(birth, dict) else 2, key)

        archived = sorted(
            (key for key in inventory if key not in live and allowed(key)),
            key=recovery_rank)
        eligible.extend(archived[:max(1, len(active_effective))])
    return tuple(eligible)
