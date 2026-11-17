"""Rank policy ancestry by retention and prior reward evidence."""
from __future__ import annotations
from ..teacher_strategy_population import (
    effective_policy_key, historical_policy_mean, BAMF_SUCCESSOR_SELECTION,
)

def _record_rank(record: dict) -> tuple[float, float, int]:
    trials = int(record.get("trials", 0))
    retained = int(record.get("retained", 0))
    reward_sum = float(record.get("reward_sum", 0.))
    return (retained / trials if trials else 0.,
            reward_sum / trials if trials else float("-inf"), trials)


def _birth_novelty(teacher: dict, policy_key: str) -> tuple[int, int]:
    policy = teacher.get("strategies", {}).get(policy_key)
    if policy is None:
        return (0, 0)
    birth = teacher.get("causal_experiment", {}).get(
        "strategy_births", {}).get(effective_policy_key(policy), {})
    if not isinstance(birth, dict):
        return (0, 0)
    return (
        int(birth.get("retained_novel_realized_action_count", 0)),
        int(birth.get("novel_realized_action_count", 0)),
    )


def _retained_parent_candidates(teacher: dict, capability: str,
                                curriculum_scope: str,
                                diagnostic_key: str | None):
    strategies = teacher.get("strategies", {})
    channel = teacher.get("causal_experiment", {})
    contexts = channel.get("contexts", {})
    grade = capability.partition(".")[0]
    levels = (
        ("CAPABILITY_DIAGNOSTIC_RETAINED", True, True),
        ("CAPABILITY_RETAINED", True, False),
        ("GRADE_DIAGNOSTIC_RETAINED", False, True),
        ("GRADE_RETAINED", False, False),
    )
    if teacher.get("selection_contract") == BAMF_SUCCESSOR_SELECTION:
        levels = tuple(level for level in levels if level[1])
    for basis, exact_capability, diagnostic_only in levels:
        candidates = []
        for context_key, scope in contexts.items():
            try:
                context_capability, _phase, context_scope = context_key.split("|", 2)
            except ValueError:
                continue
            if context_scope != curriculum_scope:
                continue
            if exact_capability:
                if context_capability != capability:
                    continue
            elif context_capability.partition(".")[0] != grade:
                continue
            for policy_key, record in scope.items():
                if policy_key not in strategies or not isinstance(record, dict):
                    continue
                evidence = record
                if diagnostic_only:
                    evidence = record.get("diagnostic_stats", {}).get(diagnostic_key)
                    if not isinstance(evidence, dict):
                        continue
                if int(evidence.get("retained", 0)) < 1:
                    continue
                candidates.append((
                    _record_rank(evidence), _birth_novelty(teacher, policy_key),
                    policy_key))
        if candidates:
            for _rank, _novelty, policy_key in sorted(candidates, reverse=True):
                yield policy_key, basis

    local = {} if teacher.get("selection_contract") == BAMF_SUCCESSOR_SELECTION else teacher.get("grade_stats", {}).get(grade, {})
    grade_candidates = [
        (historical_policy_mean(teacher, grade, key), key)
        for key, info in local.items()
        if key in strategies and isinstance(info, dict) and int(info.get("trials", 0)) > 0
    ]
    for _score, policy_key in sorted(grade_candidates, reverse=True):
        yield policy_key, "GRADE_REWARD_FALLBACK"
    global_candidates = [
        (float(info.get("reward_ema", 0.)), key)
        for key, info in teacher.get("global_stats", {}).items()
        if key in strategies and isinstance(info, dict) and int(info.get("trials", 0)) > 0
    ]
    for _score, policy_key in sorted(global_candidates, reverse=True):
        yield policy_key, "GLOBAL_REWARD_FALLBACK"
