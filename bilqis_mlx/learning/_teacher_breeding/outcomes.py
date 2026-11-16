"""Track policy usage, retention and realized-action novelty."""
from __future__ import annotations

def mark_bespoke_retained(channel: dict, effective_key: str, *,
                          capability: str, curriculum_scope: str) -> None:
    birth = channel.get("strategy_births", {}).get(effective_key)
    if not isinstance(birth, dict):
        return
    if (birth.get("origin_capability") == capability and
            birth.get("curriculum_scope") == curriculum_scope):
        birth["proven_retained"] = True


def record_policy_outcome_side_effects(channel: dict, effective_key: str, *,
                                       capability: str, curriculum_scope: str,
                                       retained: bool,
                                       realized_action_key: str | None = None) -> None:
    from ..teacher_population_control import record_strategy_usage
    record_strategy_usage(channel, effective_key)
    if realized_action_key is not None:
        ecology = channel.setdefault("realized_action_ecology", {})
        novel = realized_action_key not in ecology
        record = ecology.setdefault(realized_action_key, {
            "trials": 0, "retained": 0,
            "first_event": int(channel.get("events", 0)) + 1,
            "last_event": int(channel.get("events", 0)) + 1,
            "effective_policy_keys": [],
        })
        record["trials"] += 1
        record["retained"] += int(retained)
        record["last_event"] = int(channel.get("events", 0)) + 1
        if effective_key not in record["effective_policy_keys"]:
            record["effective_policy_keys"].append(effective_key)
            record["effective_policy_keys"].sort()
        birth = channel.get("strategy_births", {}).get(effective_key)
        if isinstance(birth, dict):
            actions = birth.setdefault("realized_action_keys", [])
            if realized_action_key not in actions:
                actions.append(realized_action_key)
            if novel:
                birth["novel_realized_action_count"] = int(
                    birth.get("novel_realized_action_count", 0)) + 1
                if retained:
                    birth["retained_novel_realized_action_count"] = int(
                        birth.get("retained_novel_realized_action_count", 0)) + 1
    if retained:
        mark_bespoke_retained(
            channel, effective_key, capability=capability,
            curriculum_scope=curriculum_scope)
