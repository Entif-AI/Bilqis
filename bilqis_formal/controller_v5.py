"""Measured, finite-budget, standalone-only atomic Boolean training controller.

DEV and taught-domain coverage can steer blocks and repair; the SEALED
held-out gate is not evaluated until the stage is finished. No learner
judgment task, previous dialogue input, native Kev, or e7 source mutation.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
import random

import torch
from torch.nn import functional as F

from bilqis_ref.model import state_hash
from .curriculum_v5 import STAGES, DEPENDENCIES, family, literal_coverage_rows, split
from .dialogue_v3 import STUDENT_LABELS
from .pilot_v3 import score
from .student_v3 import inputs_for, predict, typed_logits

VERSION = "bilqis.formal.controller/v0.5.0"


@dataclass(frozen=True)
class Budget:
    block: int = 64
    baseline: int = 320
    adaptive_cap: int = 1280
    repair_cap: int = 256
    patience: int = 3
    stable_checks: int = 2

    def validate(self):
        if (self.block < 1 or self.baseline < self.block or
                self.baseline % self.block != 0 or
                self.adaptive_cap < self.baseline or
                self.adaptive_cap % self.block != 0 or
                self.repair_cap < self.block or
                self.repair_cap % self.block != 0 or
                self.patience < 2 or self.stable_checks < 2):
            raise ValueError("INVALID_V05_BUDGET")
        return True


BUDGET = Budget()
ARMS = ("fixed320", "fixed1280", "adaptive")
SEEDS = (463, 467, 479)  # predeclared match across both arms, not seed selection


def accuracy(model, rows):
    return score(predict(model, rows, mode="none"))


def by_gold(predictions):
    return {
        gold: {
            "correct": sum(p["prediction"] == gold for p in predictions
                           if p["gold"] == gold),
            "n": sum(p["gold"] == gold for p in predictions),
        } for gold in ("ATOM.FALSE", "ATOM.TRUE")
    }


def negative_log_likelihood(predictions):
    if not predictions:
        raise ValueError("MISSING_FORMATIVE_PREDICTIONS")
    return sum(-math.log(max(1e-12, min(1., p["prob_gold"])))
               for p in predictions) / len(predictions)


def trained_literal_score(model, stage):
    rows = literal_coverage_rows(stage)
    return accuracy(model, rows) if rows else {"correct": 0, "n": 0}


def prior_formative(model, accepted):
    result = {}
    for previous in accepted:
        previous_dev = predict(model, split(previous)["dev"], mode="none")
        literal_rows = literal_coverage_rows(previous)
        literal_predictions = (predict(model, literal_rows, mode="none")
                               if literal_rows else [])
        result[previous] = {
            "dev": score(previous_dev),
            "literal_coverage": (score(literal_predictions)
                                 if literal_predictions else {"correct": 0, "n": 0}),
            "dev_items": {p["id"]: p["prediction"] == p["gold"]
                          for p in previous_dev},
            "literal_items": {p["id"]: p["prediction"] == p["gold"]
                              for p in literal_predictions},
        }
    return result


def declined_prior(retention, baseline):
    """A previously admitted skill must not deteriorate from its entry level.

    Admission uses a small SEALED exam. It does not guarantee the distinct
    DEV questions were 100% correct before teaching the next skill.
    """
    losses = []
    for stage in STAGES:
        if stage not in retention:
            continue
        current, start = retention[stage], baseline[stage]
        lower_total = any(
            current[part]["correct"] < start[part]["correct"]
            for part in ("dev", "literal_coverage"))
        lost_item = any(
            start.get(part, {}).get(key, False) and not value
            for part in ("dev_items", "literal_items")
            for key, value in current.get(part, {}).items())
        if lower_total or lost_item:
            losses.append(stage)
    return losses


def inspect_progress(model, stage, accepted, baseline=None):
    """No sealed identities here: only DEV and closed-domain teaching rows."""
    now = split(stage)["dev"]
    dev_prediction = predict(model, now, mode="none")
    dev = score(dev_prediction)
    literal = trained_literal_score(model, stage)
    retention = prior_formative(model, accepted)
    baseline = retention if baseline is None else baseline
    lost = declined_prior(retention, baseline)
    healthy = not lost
    total = dev["n"] + literal["n"] + sum(
        p[key]["n"] for p in retention.values()
        for key in ("dev", "literal_coverage"))
    correct = dev["correct"] + literal["correct"] + sum(
        p[key]["correct"] for p in retention.values()
        for key in ("dev", "literal_coverage"))
    return {
        "dev": dev, "literal_coverage_taught_domain": literal,
        "retention": retention, "retention_healthy": healthy,
        "retention_baseline": baseline, "declined_prior": lost,
        "combined_correct": correct, "combined_n": total,
        "dev_nll": negative_log_likelihood(dev_prediction),
        "dev_by_gold": by_gold(dev_prediction),
        "dev_prediction": dev_prediction,
    }


def dev_summary(observed):
    """Small public-safe summary; entire prediction records remain in local epoch."""
    return {key: observed[key] for key in (
        "dev", "literal_coverage_taught_domain", "retention",
        "retention_baseline", "declined_prior", "retention_healthy",
        "dev_by_gold",
        "combined_correct", "combined_n", "dev_nll")}


def weakest_retained(observed):
    if "declined_prior" in observed:
        return observed["declined_prior"][0] if observed["declined_prior"] else None
    for stage in STAGES:
        recorded = observed["retention"].get(stage)
        if recorded and any(
                p["n"] and p["correct"] != p["n"] for p in recorded.values()):
            return stage
    return None


def formative_mastered(observed):
    return (observed["dev"]["n"] > 0 and
            observed["dev"]["correct"] == observed["dev"]["n"] and
            (not observed["literal_coverage_taught_domain"]["n"] or
             observed["literal_coverage_taught_domain"]["correct"] ==
             observed["literal_coverage_taught_domain"]["n"]) and
            observed["retention_healthy"])


def decide_after_block(*, arm, updates, observed, previous_observations,
                       repair_updates, budget=BUDGET):
    """Pure predeclared next action. Never takes final-gate score as an input."""
    budget.validate()
    if arm not in ARMS or updates % budget.block:
        raise ValueError("BAD_CONTROLLER_STATE")
    if arm in ("fixed320", "fixed1280"):
        ceiling = budget.baseline if arm == "fixed320" else budget.adaptive_cap
        return "FINISH_FIXED" if updates >= ceiling else "CONTINUE_CURRENT"
    if not observed["retention_healthy"]:
        return ("REPAIR_PRIOR" if repair_updates < budget.repair_cap
                and updates < budget.adaptive_cap else "ROLLBACK_EXHAUSTED")
    if updates >= budget.adaptive_cap:
        return "FINISH_CAP"
    if updates < budget.baseline:
        return "CONTINUE_CURRENT"
    all_obs = (*previous_observations, observed)
    if len(all_obs) >= budget.stable_checks and all(
            formative_mastered(x) for x in all_obs[-budget.stable_checks:]):
        return "FINISH_STABLE"
    if len(all_obs) >= budget.patience + 1:
        recent = all_obs[-(budget.patience + 1):]
        # Worsening or flat accuracy is not a plateau while held-out DEV
        # confidence is meaningfully increasing at equal accuracy.
        if all(
                recent[i]["combined_correct"] < recent[i-1]["combined_correct"] or
                (recent[i]["combined_correct"] == recent[i-1]["combined_correct"]
                 and recent[i]["dev_nll"] >= recent[i-1]["dev_nll"] - 1e-4)
               for i in range(1, len(recent))):
            return "FINISH_PLATEAU"
    return "CONTINUE_CURRENT"


def training_priorities(model, stage, observed, *, adaptive):
    if not adaptive:
        return {}
    records = split(stage)["train"]
    outcomes = predict(model, records, mode="none")
    counts = Counter()
    for row, prediction in zip(records, outcomes):
        if prediction["prediction"] != row["gold"]:
            counts[family(row)] += 1
    for p in observed["dev_prediction"]:
        if p["prediction"] != p["gold"]:
            counts[family({"stage": stage, "input": p["input"]})] += 1
    return {name: min(4, 1 + n) for name, n in counts.items()}


def sample_balanced(rng, rows, n, priorities):
    by_gold = {}
    for row in rows:
        by_gold.setdefault(row["gold"], []).append(row)
    if set(by_gold) != {"ATOM.FALSE", "ATOM.TRUE"} or n % 2:
        raise ValueError("MISSING_BALANCED_TRUTH_FAMILY")
    selected = []
    for gold in sorted(by_gold):
        available = by_gold[gold]
        buckets = {
            name: [row for row in available if family(row) == name]
            for name in sorted({family(row) for row in available})
        }
        families = sorted(buckets)
        if n // 2 < len(families):
            raise ValueError("INSUFFICIENT_FAMILY_FLOORS")
        for name in families:
            selected.append(rng.choice(buckets[name]))
        rest = n // 2 - len(families)
        # Weight concept families, not individual rows, so a larger family
        # does not silently receive more samples at the same declared priority.
        chosen = rng.choices(
            families, weights=[priorities.get(name, 1) for name in families], k=rest)
        selected.extend(rng.choice(buckets[name]) for name in chosen)
    rng.shuffle(selected)
    return selected


def training_batches(*, stage, rehearsal, seed, block_number,
                     repair=None, priorities=None, budget=BUDGET):
    rng = random.Random(seed * 997 + STAGES.index(stage) * 13007 + block_number * 107)
    current = split(stage)["train"]
    earlier = [r for old in rehearsal for r in split(old)["train"]]
    focused = split(repair)["train"] if repair else current
    companion = current if repair else earlier
    for _ in range(budget.block):
        primary = sample_balanced(rng, focused, 24 if companion else 32,
                                  priorities or {})
        secondary = (sample_balanced(rng, companion, 8, {}) if companion else [])
        combined = primary + secondary
        rng.shuffle(combined)
        yield combined


def sample_ledger(*, stage, rehearsal, seed, block_number, repair=None,
                  priorities=None, budget=BUDGET):
    """Reconstruct exact training-row custody without executing a gradient."""
    digest = hashlib.sha256()
    families = Counter()
    examples = 0
    for records in training_batches(
            stage=stage, rehearsal=rehearsal, seed=seed,
            block_number=block_number, repair=repair,
            priorities=priorities, budget=budget):
        for row in records:
            digest.update(row["id"].encode())
            families[family(row)] += 1
            examples += 1
    return {
        "sample_sha256": digest.hexdigest(),
        "families": dict(sorted(families.items())),
        "examples": examples,
    }


def optimizer_digest(state):
    """Canonical optimizer state, including AdamW moments and parameter groups."""
    digest = hashlib.sha256()
    digest.update(json.dumps(state["param_groups"], sort_keys=True,
                             separators=(",", ":")).encode())
    for parameter in sorted(state["state"]):
        digest.update(str(parameter).encode() + b"\0")
        for name, value in sorted(state["state"][parameter].items()):
            digest.update(name.encode() + b"\0")
            if isinstance(value, torch.Tensor):
                t = value.detach().cpu().contiguous()
                digest.update(str((str(t.dtype), tuple(t.shape))).encode())
                digest.update(t.numpy().tobytes())
            else:
                digest.update(repr(value).encode())
            digest.update(b"\0")
    return digest.hexdigest()


def train_block(model, optimizer, *, stage, accepted, rehearsal, seed,
                block_number, repair=None, priorities=None, budget=BUDGET):
    """Exactly budget.block real optimizer updates and an inspectable sample hash."""
    if repair and repair not in accepted:
        raise ValueError("REPAIR_UNLEARNED_COMPETENCY")
    digest = hashlib.sha256()
    losses, right, left, examples = [], 0, 0, 0
    used_families = Counter()
    for batch_rows in training_batches(
            stage=stage, rehearsal=rehearsal, seed=seed,
            block_number=block_number, repair=repair,
            priorities=priorities, budget=budget):
        for row in batch_rows:
            digest.update(row["id"].encode())
            used_families[family(row)] += 1
        (ids, lengths), sequences = inputs_for(model, batch_rows, mode="none")
        if any(not seq or len(seq) > model.cfg.context for seq in sequences):
            raise ValueError("STANDALONE_PROMPT_OVERFLOW")
        model.train()
        optimizer.zero_grad(set_to_none=True)
        logits = typed_logits(model(ids, lengths), batch_rows)
        targets = torch.tensor([STUDENT_LABELS.index(row["gold"]) for row in batch_rows])
        correct = int((logits.argmax(-1) == targets).sum().item())
        right += correct
        left += len(batch_rows) - correct
        loss = F.cross_entropy(logits, targets)
        if not bool(torch.isfinite(loss)):
            raise ValueError("NONFINITE_ADAPTIVE_LOSS")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        losses.append(float(loss.detach()))
        examples += len(batch_rows)
    return {
        "step_count": budget.block,
        "examples": examples,
        "correct_pre_update": right,
        "incorrect_pre_update": left,
        "loss_mean": sum(losses) / len(losses),
        "loss_last": losses[-1],
        "sample_sha256": digest.hexdigest(),
        "families": dict(sorted(used_families.items())),
        "primary_stage": repair or stage,
        "secondary_mode": "current" if repair else "rehearsal",
        "context_exposures": 0,
    }


def optimizer_steps(optimizer):
    return {int(x["step"]) for x in optimizer.state.values() if "step" in x}


def run_stage(model, optimizer, *, stage, accepted, monitored=None,
              rehearsal=None, seed, arm,
              budget=BUDGET, trace=None):
    """A single stage, sealed gate consulted only when the teaching decision ends."""
    if stage not in STAGES or arm not in ARMS or any(
            dep not in accepted for dep in DEPENDENCIES[stage]):
        raise ValueError("BAD_STAGE_ADMISSION")
    budget.validate()
    start_hash = state_hash(model)
    start_model, start_opt = deepcopy(model.state_dict()), deepcopy(optimizer.state_dict())
    start_rng = torch.get_rng_state().clone()
    # The final sealed exam may admit a skill to the prerequisite DAG, but
    # it must not select adaptive repair targets in an independent sibling.
    # Repair monitors only earlier DEV-mastered, actually taught skills.
    prior = list(accepted if monitored is None else monitored)
    if any(name not in STAGES[:STAGES.index(stage)] for name in prior):
        raise ValueError("INVALID_MONITORED_STAGE_SET")
    retention_at_entry = prior_formative(model, prior)
    earlier_lessons = list(prior if rehearsal is None else rehearsal)
    if any(name not in STAGES[:STAGES.index(stage)] for name in earlier_lessons):
        raise ValueError("INVALID_EARLIER_LESSON_SET")
    blocks, observations = [], []
    total_updates = repair_updates = 0
    mode = "current"
    repair_target = None
    priorities = {}
    ceiling = budget.baseline if arm == "fixed320" else budget.adaptive_cap
    while total_updates < ceiling:
        block_record = train_block(
            model, optimizer, stage=stage, accepted=prior,
            rehearsal=earlier_lessons, seed=seed,
            block_number=len(blocks), repair=repair_target if mode == "repair" else None,
            priorities=priorities if mode == "current" else {},
            budget=budget)
        total_updates += budget.block
        if mode == "repair":
            repair_updates += budget.block
        observed = inspect_progress(model, stage, prior, baseline=retention_at_entry)
        decision = decide_after_block(
            arm=arm, updates=total_updates, observed=observed,
            previous_observations=observations, repair_updates=repair_updates,
            budget=budget)
        block_record.update({
            "block": len(blocks) + 1, "mode": mode,
            "updates_total": total_updates, "repair_updates": repair_updates,
            "start_priorities": dict(priorities) if mode == "current" else {},
            "development": dev_summary(observed), "decision": decision,
        })
        blocks.append(block_record)
        observations.append(observed)
        if trace:
            trace(block_record)
        if decision == "ROLLBACK_EXHAUSTED":
            model.load_state_dict(start_model)
            optimizer.load_state_dict(start_opt)
            torch.set_rng_state(start_rng)
            return {
                "stage": stage, "arm": arm, "decision": decision,
                "attempted_updates": total_updates, "committed_updates": 0,
                "repair_updates": repair_updates, "rolled_back": True,
                "state_before": start_hash, "state_after": state_hash(model),
                "blocks": blocks, "last_dev": dev_summary(observed),
                "monitored_at_entry": prior,
                "prior_retention_at_entry": retention_at_entry,
                "sealed_gate": None, "sealed_retention": None,
                "promoted": False,
            }
        if decision.startswith("FINISH_"):
            break
        if decision == "REPAIR_PRIOR":
            mode = "repair"
            repair_target = weakest_retained(observed)
            if repair_target is None:
                raise ValueError("REPAIR_TARGET_NOT_FAILED")
        else:
            mode = "current"
            repair_target = None
            priorities = training_priorities(model, stage, observed,
                                             adaptive=arm == "adaptive")
    # Final sealed exam is executed once per stage, never in the block loop
    # and never as input to sampling/extra updates/remediation.
    sealed_predictions = predict(model, split(stage)["gate"], mode="none")
    sealed = score(sealed_predictions)
    sealed_by_gold = by_gold(sealed_predictions)
    frozen_retention = {old: accuracy(model, split(old)["gate"]) for old in accepted}
    taught_domain = trained_literal_score(model, stage)
    old_taught_coverage = {
        old: trained_literal_score(model, old) for old in accepted}
    promoted = (sealed["n"] and sealed["correct"] == sealed["n"] and
                taught_domain["correct"] == taught_domain["n"] and
                all(s["correct"] == s["n"] for s in frozen_retention.values()) and
                all(s["correct"] == s["n"] for s in old_taught_coverage.values()))
    return {
        "stage": stage, "arm": arm, "decision": decision,
        "attempted_updates": total_updates, "committed_updates": total_updates,
        "repair_updates": repair_updates, "rolled_back": False,
        "state_before": start_hash, "state_after": state_hash(model),
        "blocks": blocks, "last_dev": dev_summary(observations[-1]),
        "monitored_at_entry": prior,
        "prior_retention_at_entry": retention_at_entry,
        "sealed_gate": sealed, "sealed_retention": frozen_retention,
        "sealed_by_gold": sealed_by_gold,
        "taught_domain": taught_domain, "old_taught_coverage": old_taught_coverage,
        "promoted": bool(promoted),
    }
