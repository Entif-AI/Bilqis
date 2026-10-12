"""Advance the *best U7E descendant*, not the random-init or old U6 parent.

This second developmental pass protects previous skills with more live
rehearsal and model memory while continuing exact provenance lesson pairs.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import random
import time

import torch
from torch.nn import functional as F

from bilqis_micro.graph import STATES
from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import batch, state_hash
from bilqis_development.continuation import load, save
from bilqis_development.kernel import encode
from bilqis_u7e import run as earlier
from bilqis_u7e.lessons import build, paired_batch, without_exposed

VERSION = "bilqis.cumulative-memory/v0.1"
ROOT = earlier.ROOT
PARENT_RUN = earlier.RUN
RUN = ROOT / "runs" / "u7f-cumulative-memory-20261012"
UPDATES = 384
REVIEW_EVERY = 32
LR = 0.00013


def resume():
    first = json.loads((PARENT_RUN / "result.json").read_text())
    chosen = first["best"]
    if (first["version"] != earlier.VERSION or chosen["updates"] != 128 or
        chosen["step"] != 13528 or chosen["checkpoint_sha256"] !=
            "39167cec6000873938ac8afefad333db092756f9fe42bca9737f93bf1b3bb5e5" or
        earlier.sha(Path(chosen["checkpoint"])) != chosen["checkpoint_sha256"]):
        raise ValueError("WRONG_BEST_U7E_DESCENDANT")
    model, optimizer, original = load(Path(chosen["checkpoint"]))
    if (optimizer_receipt(optimizer)["steps"] != [chosen["step"]] or
        state_hash(model) != "c118c6086bef09b862bfc7e19a544ac2081506c115fb09f203e47127c944a401"):
        raise ValueError("CUMULATIVE_OPTIMIZER_OR_MODEL_RESET")
    ancestor, _, base = earlier.parent()
    if original["graph"] != base["graph"] or len(original["graph"]["tokens"]) != 113:
        raise ValueError("SEMANTIC_IDENTITY_MAP_CHANGED")
    # Verifying U6 via load() restores U6's RNG globally. Restore the selected
    # U7E descendant's own RNG so *all* continuation state is inherited.
    torch.set_rng_state(original["torch_rng"])
    return model, optimizer, original, chosen


def batch_rows(direct, chained, old, *, iteration, rng):
    new = paired_batch(direct, chained, iteration=iteration+128, rng=rng)[:12]
    quotas = {0: 5, 1: 1, 2: 1, 3: 1, 4: 8, 5: 3, 6: 1}
    prior = [rng.choice(old[stage]) for stage, n in quotas.items()
             for _ in range(n)]
    rng.shuffle(prior)
    if len(new) != 12 or len(prior) != 20:
        raise ValueError("BAD_CUMULATIVE_MEMORY_BATCH")
    return new + prior


def learn(model, previous, optimizer, rows):
    examples = [encode(r["input"]) for r in rows]
    if len(rows) != 32 or any(len(x) > 96 for x in examples):
        raise ValueError("INVALID_FAMILY_CONTEXT")
    labels = torch.tensor([STATES.index(r["gold"]) for r in rows])
    model.train()
    optimizer.zero_grad(set_to_none=True)
    logits = model(*batch(examples))
    current = F.cross_entropy(logits[:12], labels[:12])
    remembered = F.cross_entropy(logits[12:], labels[12:])
    with torch.no_grad():
        previous.eval()
        inherited = previous(*batch(examples[12:]))
    memory = F.kl_div(F.log_softmax(logits[12:] / 1.5, dim=-1),
                      F.softmax(inherited / 1.5, dim=-1),
                      reduction="batchmean") * 2.25
    loss = current + 1.25 * remembered + 0.7 * memory
    if not bool(torch.isfinite(loss)):
        raise ValueError("NONFINITE_CUMULATIVE_LOSS")
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
    optimizer.step()
    return float(loss.detach())


def viable(candidate, parent):
    return (candidate["primitives"] == 26 and
            candidate["u0_composite"] >= parent["u0_composite"] and
            candidate["u4_composite"] >= parent["u4_composite"] and
            candidate["u4_varied"] >= parent["u4_varied"] - 3 and
            candidate["u5_varied"] >= parent["u5_varied"] - 3 and
            candidate["u6_varied"] >= parent["u6_varied"] - 4 and
            candidate["lineage_10"] >= parent["lineage_10"])


def utility(score, origin):
    return (2 * (score["direct_pairs"]["both"] + score["chain_pairs"]["both"]) +
            5 * score["lineage_10"] +
            2 * score["u0_composite"] +
            3 * score["u4_composite"] +
            score["u4_varied"] * .5 +
            score["u5_varied"] * .2 +
            score["u6_varied"] * .2)


def run(out=RUN, updates=UPDATES):
    if out.exists() or updates <= 0 or updates % REVIEW_EVERY or updates > UPDATES:
        raise ValueError("BAD_NEW_DEVELOPMENT_EPOCH")
    model, optimizer, graph, parent = resume()
    teacher = copy.deepcopy(model).eval()
    for p in teacher.parameters():
        p.requires_grad_(False)
    for group in optimizer.param_groups:
        group["lr"] = LR
    corpus = earlier.spiral.read(earlier.PARENT / "data.json.gz")
    old = earlier.memory(corpus)
    direct = build(14831, 100, compositional=False)
    chained = build(14837, 100, compositional=True)
    exposed = {r["id"] for d in (direct, chained)
               for pairs in d["episodes"].values() for a,b in pairs for r in (a,b)}
    dev_direct = without_exposed(build(94477,40,compositional=False), exposed)
    dev_chain = without_exposed(build(94489,40,compositional=True), exposed)
    start = earlier.dashboard(model, corpus, dev_direct, dev_chain)
    if start != parent["score"]:
        raise ValueError("BEST_U7E_DEVELOPMENT_DASHBOARD_NO_LONGER_REPRODUCES")
    out.mkdir(parents=True, exist_ok=False)
    earlier.write_new(out / "start.json", {
        "version": VERSION, "ancestor": parent, "parent_AdamW_step": 13528,
        "graph_tokens": 113, "no_parameter_reset": True,
        "learning_rate": LR, "updates": updates,
        "protection": "20 of every 32 rows cover seven previous skill stages",
        "inherited_checkpoint": parent["checkpoint_sha256"],
        "baseline": start})
    best = {"step": parent["step"], "after_updates": 0,
            "checkpoint": parent["checkpoint"], "checkpoint_sha256": parent["checkpoint_sha256"],
            "score": start, "utility": utility(start, start),
            "retained_parent": True}
    rng = random.Random(23471)
    since = time.perf_counter()
    latest = start
    for n in range(1, updates+1):
        examples = batch_rows(direct, chained, old, iteration=n-1, rng=rng)
        loss = learn(model, teacher, optimizer, examples)
        if n % REVIEW_EVERY:
            continue
        if optimizer_receipt(optimizer)["steps"] != [13528+n]:
            raise ValueError("U7F_AdamW_HISTORY_RESET")
        latest = earlier.dashboard(model, corpus, dev_direct, dev_chain)
        healthy = viable(latest, start)
        rank = utility(latest, start)
        earlier.write_new(out / f"score-{n:04d}.json", {
            "step": 13528+n, "score": latest, "utility": rank,
            "viable": healthy, "loss_last": loss, "model_sha256": state_hash(model),
            "optimizer_sha256": optimizer_receipt(optimizer)["state_sha256"]})
        if healthy and rank > best["utility"]:
            path = out / f"best-after-{n:04d}.pt"
            save(path, model, optimizer, graph["graph"], {
                "epoch": VERSION, "step": 13528+n,
                "parent_checkpoint_sha256": parent["checkpoint_sha256"],
                "continued_without_reset": True})
            best = {"step": 13528+n, "after_updates": n,
                    "checkpoint": str(path), "checkpoint_sha256": earlier.sha(path),
                    "score": latest, "utility": rank, "retained_parent": False}
        print(json.dumps({"after_updates": n, "best_step": best["step"],
                          "viable": healthy, "lineage": latest["lineage_10"],
                          "direct_pair_success": latest["direct_pairs"]["both"],
                          "chain_pair_success": latest["chain_pairs"]["both"],
                          "old_u0": latest["u0_composite"],
                          "old_u4": latest["u4_composite"],
                          "old_u5": latest["u5_varied"],
                          "old_u6": latest["u6_varied"]}, sort_keys=True), flush=True)
    earlier.write_new(out / "result.json", {
        "version": VERSION, "parent": parent,
        "attempted_updates": updates,
        "attempted_final_optimizer_step": optimizer_receipt(optimizer)["steps"],
        "best": best, "before": start, "attempted_last": latest,
        "selected_is_new_model": not best["retained_parent"],
        "elapsed_seconds": time.perf_counter()-since,
        "old_parent_U6_preserved": earlier.sha(earlier.CHECKPOINT) == earlier.PARENT_SHA,
        "U7E_parent_preserved": earlier.sha(Path(parent["checkpoint"])) == parent["checkpoint_sha256"],
        "science_attribution_runs": 0, "scratch_weight_resets": 0})
    return {"best": best, "before": start,
            "attempted_last": latest, "attempted_updates": updates}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--updates", type=int, default=UPDATES)
    arguments = parser.parse_args()
    print(json.dumps(run(updates=arguments.updates), sort_keys=True))


if __name__ == "__main__":
    main()
