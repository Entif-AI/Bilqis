"""Generate and register effective teacher-policy mutations."""
from __future__ import annotations
import hashlib
import json
import math
from ..teacher_strategy_population import effective_policy_key, effective_strategy_inventory
from .ancestry import _retained_parent_candidates

_INEFFECTIVE_MUTATION_FIELDS = frozenset({"preview"})
_ADAPTIVE_NUMERIC_FIELDS = ("old", "lr", "distill")
_ADAPTIVE_OLD_RESOLUTION = 1
_ADAPTIVE_LR_RESOLUTION = 0.000001
_ADAPTIVE_DISTILL_RESOLUTION = 0.01

def _one_knob_children(base: dict, knobs: dict, rng):
    fields = [field for field in knobs if field not in _INEFFECTIVE_MUTATION_FIELDS]
    rng.shuffle(fields)
    for field in fields:
        values = [value for value in knobs[field] if value != base.get(field)]
        rng.shuffle(values)
        for value in values:
            child = dict(base)
            child[field] = value
            yield field, child


def _quantized_midpoint(field: str, left: float, right: float):
    if field == "lr":
        value = math.sqrt(left * right)
    else:
        value = (left + right) / 2
    resolution = (_ADAPTIVE_OLD_RESOLUTION if field == "old" else
                  _ADAPTIVE_LR_RESOLUTION if field == "lr" else
                  _ADAPTIVE_DISTILL_RESOLUTION)
    value = round(value / resolution) * resolution
    if field == "old":
        return int(round(value))
    decimals = 6 if field == "lr" else 2
    return round(value, decimals)


def _adaptive_numeric_children(base: dict, strategies: dict,
                               knobs: dict, rng):
    """Bisect one local numeric gap without leaving the historical envelope."""
    fields = [field for field in _ADAPTIVE_NUMERIC_FIELDS
              if field in knobs and field in base]
    rng.shuffle(fields)
    for field in fields:
        allowed = tuple(knobs[field])
        if not allowed or any(not isinstance(value, (int, float)) for value in allowed):
            continue
        lower_bound = float(min(allowed))
        upper_bound = float(max(allowed))
        base_value = float(base[field])
        observed = sorted({
            float(policy[field]) for policy in strategies.values()
            if isinstance(policy, dict) and isinstance(policy.get(field), (int, float))
            and lower_bound <= float(policy[field]) <= upper_bound
        })
        neighbors = []
        lower = [value for value in observed if value < base_value]
        upper = [value for value in observed if value > base_value]
        if lower:
            neighbors.append(max(lower))
        if upper:
            neighbors.append(min(upper))
        rng.shuffle(neighbors)
        for neighbor in neighbors:
            value = _quantized_midpoint(field, base_value, neighbor)
            numeric = float(value)
            if (numeric <= lower_bound or numeric >= upper_bound or
                    numeric == base_value or numeric == neighbor or
                    numeric in observed):
                continue
            child = dict(base)
            child[field] = value
            yield field, child


def _register_child(teacher: dict, child: dict, *, effective: str,
                    parent_key: str, parent: dict, basis: str,
                    field: str, capability: str, curriculum_scope: str,
                    total_capabilities: int, mutation_mode: str):
    strategies = teacher["strategies"]
    identity = hashlib.sha256(
        json.dumps(child, sort_keys=True).encode()).hexdigest()[:12]
    if identity in strategies:
        return None
    strategies[identity] = child
    teacher.setdefault("global_stats", {})[identity] = {
        "trials": 0, "reward_sum": 0.0, "reward_ema": 0.0, "latest": None,
    }
    teacher["mutations"] = int(teacher.get("mutations", 0)) + 1
    channel = teacher.setdefault("causal_experiment", {})
    channel.setdefault("strategy_births", {})[effective] = {
        "origin_capability": capability,
        "origin_grade": capability.partition(".")[0],
        "curriculum_scope": curriculum_scope,
        "parent_policy_key": parent_key,
        "parent_effective_policy_key": effective_policy_key(parent),
        "parent_basis": basis,
        "changed_fields": [field],
        "mutation_mode": mutation_mode,
        "birth_event": int(channel.get("events", 0)) + 1,
        "proven_retained": False,
    }
    from ..teacher_population_control import rebalance_live_population
    rebalance_live_population(teacher, total_capabilities=total_capabilities)
    return identity, child, {
        "mutation_parent_policy_key": parent_key,
        "mutation_parent_basis": basis,
        "mutation_changed_fields": [field],
        "mutation_mode": mutation_mode,
    }


def mint_bespoke_effective_strategy(engine, teacher: dict, rng, *,
                                    capability: str, curriculum_scope: str,
                                    diagnostic_key: str | None = None,
                                    total_capabilities: int = 1):
    """Breed one novel effective policy from retained capability/grade ancestry."""
    strategies = teacher.get("strategies", {})
    knobs = getattr(engine, "KNOBS", None)
    if not knobs:
        return None
    existing = set(effective_strategy_inventory(teacher))
    max_context = int(getattr(engine, "MAX_TEACHER_CONTEXT_ITEMS", 24))
    seen_parents = set()
    parents = []
    for parent_key, basis in _retained_parent_candidates(
            teacher, capability, curriculum_scope, diagnostic_key):
        if parent_key in seen_parents:
            continue
        seen_parents.add(parent_key)
        parent = strategies[parent_key]
        if any(field not in parent for field in knobs):
            continue
        parents.append((parent_key, basis, parent))
    for mutation_mode, children in (
            ("LEGACY_GRID", lambda parent: _one_knob_children(parent, knobs, rng)),
            ("ADAPTIVE_LOCAL_REFINEMENT",
             lambda parent: _adaptive_numeric_children(parent, strategies, knobs, rng))):
        for parent_key, basis, parent in parents:
            for field, child in children(parent):
                if child["old"] + child["preview"] > max_context:
                    continue
                effective = effective_policy_key(child)
                if effective in existing:
                    continue
                registered = _register_child(
                    teacher, child, effective=effective, parent_key=parent_key,
                    parent=parent, basis=basis, field=field,
                    capability=capability, curriculum_scope=curriculum_scope,
                    total_capabilities=total_capabilities,
                    mutation_mode=mutation_mode)
                if registered is not None:
                    return registered
    return None
