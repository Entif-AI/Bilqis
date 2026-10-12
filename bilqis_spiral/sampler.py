"""12/4/8/8 spiral lessons with oracle-bound generation and DEV-only adaptation."""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
import random

from bilqis_logic.kernel import digest
from bilqis_micro import data as old_data
from bilqis_micro import kernel as old_kernel
from bilqis_development import data as new_data
from bilqis_development import kernel as newer

MIX = {"current": 12, "fresh_prior": 4, "cross_stage": 8, "weak_reinforcement": 8}
WEAK_OLD_FLOOR = 2
WEAK_NEW_FLOOR = 2
WEAK_FAMILY_CEILING = 3
CROSS_STAGE_EACH = 4
MAX_TOKENS = 96


def family_key(stage, family):
    if stage == 0:
        return "Boolean"
    if stage == 4:
        return "evidence_state"
    return family.removeprefix("helper:").split(":")[0]


def check_row(r):
    if r["id"] != digest(r["input"]):
        raise ValueError("unbound lesson identity")
    if not 0 <= r["stage"] <= 6:
        raise ValueError("stage out of range")
    gold = newer.evaluate(r["input"])
    if gold != newer.independent_evaluate(r["input"]) or r["gold"] != gold:
        raise ValueError("source gold disagrees with independent finite oracle")
    encoded = newer.encode(r["input"])
    if len(encoded) > MAX_TOKENS or newer.decode(encoded) != r["input"]:
        raise ValueError("lesson token ABI/context binding")
    return r


def existing_ids(data):
    return {r["id"] for stage in data["stages"].values()
            for split in ("train", "eval") for pool in stage[split].values() for r in pool}


def _prior_row(stage, rng):
    return check_row(old_data.lesson(stage, rng, rng.choice(("focus", "composition"))))


def _new_row(stage, family, rng):
    return check_row(new_data.lesson(stage, family, rng, rng.choice(("focus", "composition"))))


def unique_pool(stage, family, target, rng, excluded):
    """New canonical-generator rows only, excluding every inherited train/DEV identity."""
    rows = {}
    for _ in range(target * 750):
        if len(rows) >= target:
            break
        try:
            r = _prior_row(stage, rng) if stage < 5 else _new_row(stage, family, rng)
        except ValueError:
            continue
        if family_key(stage, r["family"]) != family:
            continue
        if r["id"] not in excluded and r["id"] not in rows:
            rows[r["id"]] = r
    if len(rows) != target:
        raise ValueError(f"insufficient fresh canonical lessons U{stage}/{family}: {len(rows)}/{target}")
    excluded.update(rows)
    return list(rows.values())


def _old_expression(w, rng):
    entities = w["base"]["entities"]
    a, b = rng.sample(entities, 2)
    a, b = old_kernel.entity(a), old_kernel.entity(b)
    family = rng.choice(("U1:direction", "U2:quantifier", "U3:entailment"))
    if family == "U1:direction":
        q = old_kernel.relation("PARENT", a, b)
    elif family == "U2:quantifier":
        q = old_kernel.quantify("EXISTS", old_kernel.relation("PARENT", a, old_kernel.bound(0)))
    else:
        q = old_kernel.entails(old_kernel.relation("PARENT", a, b))
    return family, newer.inherited(q)


def cross_case(stage, rng):
    """Require actual counterfactual influence of both semantic arms."""
    family = rng.choice(new_data.FAMILIES[str(stage)])
    w = new_data.make_world(stage, rng)
    q_new = new_data.query(family, w, rng)
    old_family, q_old = _old_expression(w, rng)
    old_gold = newer.evaluate(newer.record(w, q_old))
    new_gold = newer.evaluate(newer.record(w, q_new))
    if old_gold != new_gold or old_gold not in ("TRUE", "FALSE"):
        raise ValueError("nonaligned Boolean operands")
    gate = "AND" if old_gold == "TRUE" else "OR"
    main = newer.op(gate, q_old, q_new)
    old_flip = newer.op(gate, newer.op("NOT", q_old), q_new)
    new_flip = newer.op(gate, q_old, newer.op("NOT", q_new))
    r = new_data.row(newer.record(w, main), stage, f"cross:{old_family}+U{stage}:{family}")
    old_changed = new_data.row(newer.record(w, old_flip), stage, r["family"] + ":old-contrast")
    new_changed = new_data.row(newer.record(w, new_flip), stage, r["family"] + ":new-contrast")
    for item in (r, old_changed, new_changed):
        check_row(item)
    if r["gold"] == old_changed["gold"] or r["gold"] == new_changed["gold"]:
        raise ValueError("inert semantic branch")
    return r, {"base": r["id"], "old_changed": old_changed["id"],
               "new_changed": new_changed["id"], "old_family": old_family,
               "new_family": family, "gate": gate, "operand_gold": old_gold,
               "base_gold": r["gold"], "old_changed_gold": old_changed["gold"],
               "new_changed_gold": new_changed["gold"],
               "old_contrast": old_changed, "new_contrast": new_changed}


def cross_pool(stage, target, rng, excluded):
    rows, witnesses = {}, []
    for _ in range(target * 600):
        if len(rows) >= target:
            break
        try:
            row, proof = cross_case(stage, rng)
        except ValueError:
            continue
        ids = {row["id"], proof["old_changed"], proof["new_changed"]}
        if len(ids) < 3 or ids & excluded or row["id"] in rows:
            continue
        rows[row["id"]] = row
        witnesses.append(proof)
        excluded.update(ids)
    if len(rows) != target:
        raise ValueError(f"insufficient causally active U{stage} cross compositions: {len(rows)}/{target}")
    return list(rows.values()), witnesses


def build_pools(data, seed, updates):
    """All examples and counterfactuals frozen before the first gradient step."""
    rng = random.Random(seed)
    excluded = existing_ids(data)
    forbidden_parent = set(excluded)
    fresh = {}
    # Generate broad earlier-stage rehearsal with independent pools from weak-targeted lessons.
    per_stage = max(28, (updates * MIX["fresh_prior"] + 4) // 5 + 12)
    for stage in range(5):
        if stage in (0, 4):
            family = "Boolean" if stage == 0 else "evidence_state"
            fresh[str(stage)] = unique_pool(stage, family, per_stage, rng, excluded)
        else:
            # Vary the family through the canonical generator, rather than favor a single skill.
            rows = {}
            for _ in range(per_stage * 500):
                if len(rows) == per_stage:
                    break
                try:
                    row = _prior_row(stage, rng)
                except ValueError:
                    continue
                if row["id"] not in excluded and row["id"] not in rows:
                    rows[row["id"]] = row
            if len(rows) < per_stage:
                raise ValueError("insufficient fresh earlier-stage coverage")
            fresh[str(stage)] = list(rows.values())
            excluded.update(rows)
    cross, causal = {}, []
    for stage in (5, 6):
        rows, proof = cross_pool(stage, max(48, updates * CROSS_STAGE_EACH // 2), rng, excluded)
        cross[str(stage)] = rows
        causal.extend(proof)

    # Independent freshly generated family-specific reinforcement, including old and recent skills.
    eligible = {(int(s), family_key(int(s), row["family"]))
                for s, stage in data["stages"].items()
                for split in ("varied", "composite")
                for row in stage["eval"][split]}
    weak = {}
    for stage, family in sorted(eligible):
        weak[f"{stage}:{family}"] = unique_pool(stage, family, max(16, min(32, updates // 2)), rng, excluded)

    # Separate final cohort, excluded from all training and historical DEV identities.
    final = {}
    for stage in range(7):
        final[str(stage)] = {}
        for split, category in (("varied", "focus"), ("composite", "held_composite")):
            rows = {}
            for _ in range(32 * 750):
                if len(rows) >= 32:
                    break
                try:
                    if stage < 5:
                        item = check_row(old_data.lesson(stage, rng, category, varied=True))
                    else:
                        family = rng.choice(new_data.FAMILIES[str(stage)])
                        item = check_row(new_data.lesson(stage, family, rng, category, varied=True))
                except ValueError:
                    continue
                if item["id"] not in excluded and item["id"] not in rows:
                    rows[item["id"]] = item
            if len(rows) != 32:
                raise ValueError(f"insufficient disjoint final U{stage} {split}: {len(rows)}")
            final[str(stage)][split] = list(rows.values())
            excluded.update(rows)
    # The historical familiar readout deliberately overlaps parent TRAIN. Do not
    # re-expose any row that also occurs in a frozen evaluation split.
    frozen_eval = {r["id"] for stage in data["stages"].values()
                   for rows in stage["eval"].values() for r in rows}
    current = [check_row(r) for pool in data["stages"]["6"]["train"].values()
               for r in pool if r["id"] not in frozen_eval]
    if not current:
        raise ValueError("missing frozen U6 training corpus")
    return {"fresh": fresh, "cross": cross, "weak": weak,
            "causal": causal, "final": final,
            "parent_ids_sha256": digest(sorted(forbidden_parent))}


def dev_signals(scores, baseline=None):
    """Observed DEV error + regression against U6 DEV; no final-eval input."""
    result = defaultdict(lambda: [0, 0])
    for stage, pools in scores.items():
        for split in ("varied", "composite"):
            for p in pools[split]["predictions"]:
                key = f"{stage}:{family_key(int(stage), p['family'])}"
                result[key][0] += int(p["prediction"] != p["gold"])
                result[key][1] += 1
    base = {}
    if baseline is not None:
        base = {key: stats["error_rate"] for key, stats in dev_signals(baseline).items()}
    return {key: {"errors": errors, "n": n, "error_rate": errors / n,
                  "regression": max(0., errors / n - base.get(key, errors / n)),
                  "weight": min(3., max(.1, .1 + 2 * errors / n +
                                        2 * max(0., errors / n - base.get(key, errors / n))))}
            for key, (errors, n) in sorted(result.items())}


def _weighted_pick(keys, signals, rng):
    weights = [signals[k]["weight"] for k in keys]
    return rng.choices(keys, weights=weights, k=1)[0]


class Sampler:
    def __init__(self, data, pools, seed, signals):
        self.rng = random.Random(seed)
        self.signals = signals
        self.parent = data
        self.pools = pools
        self.fresh_index = {s: 0 for s in pools["fresh"]}
        self.fresh_order = {s: self.rng.sample(rows, len(rows)) for s, rows in pools["fresh"].items()}
        frozen_eval = {r["id"] for stage in data["stages"].values()
                       for rows in stage["eval"].values() for r in rows}
        self.train = [r for pool in data["stages"]["6"]["train"].values()
                      for r in pool if r["id"] not in frozen_eval]
        self.weak_indices = defaultdict(int)
        self.weak_order = {key: self.rng.sample(rows, len(rows)) for key, rows in pools["weak"].items()}

    def update_signals(self, signals):
        if set(signals) != set(self.pools["weak"]):
            raise ValueError("DEV family coverage changed")
        self.signals = signals

    def _weak(self):
        picked, counts = [], Counter()
        old, recent = sorted(k for k in self.pools["weak"] if int(k.split(":")[0]) < 5), sorted(
            k for k in self.pools["weak"] if int(k.split(":")[0]) >= 5)
        order = ["old"] * WEAK_OLD_FLOOR + ["recent"] * WEAK_NEW_FLOOR + ["either"] * 4
        for group in order:
            available = [k for k in self.pools["weak"] if counts[k] < WEAK_FAMILY_CEILING and
                         (group == "either" or (int(k.split(":")[0]) < 5) == (group == "old"))]
            if not available:
                raise ValueError("weak-skill family ceiling cannot satisfy mix")
            family = _weighted_pick(sorted(available), self.signals, self.rng)
            selection = self.weak_order[family]
            offset = self.weak_indices[family]
            r = selection[offset % len(selection)]
            self.weak_indices[family] += 1
            picked.append((r, family))
            counts[family] += 1
        if (sum(int(r["stage"]) < 5 for r, _ in picked) < WEAK_OLD_FLOOR or
                sum(int(r["stage"]) >= 5 for r, _ in picked) < WEAK_NEW_FLOOR):
            raise ValueError("old/new weakness reinforcement floors")
        return picked

    def batch(self):
        rows, categories, weak_families = [], [], []
        def add(item, name, key=None):
            rows.append(item)
            categories.append(name)
            weak_families.append(key)

        for r in self.rng.choices(self.train, k=MIX["current"]):
            add(r, "current")
        for _ in range(MIX["fresh_prior"]):
            stages = [s for s, order in self.fresh_order.items()
                      if self.fresh_index[s] < len(order)]
            if not stages:
                raise ValueError("fresh earlier-stage reservoir exhausted")
            stage = self.rng.choice(stages)
            r = self.fresh_order[stage][self.fresh_index[stage]]
            self.fresh_index[stage] += 1
            add(r, "fresh_prior")
        for stage in (5, 6):
            for r in self.rng.choices(self.pools["cross"][str(stage)], k=CROSS_STAGE_EACH):
                add(r, "cross_stage")
        for r, family in self._weak():
            add(r, "weak_reinforcement", family)
        indices = list(range(len(rows)))
        self.rng.shuffle(indices)
        rows, categories, weak_families = ([items[i] for i in indices] for items in
                                           (rows, categories, weak_families))
        if len(rows) != 32 or Counter(categories) != Counter(MIX):
            raise ValueError("incorrect spiral batch allocation")
        return rows, categories, weak_families
