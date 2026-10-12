"""Cumulative, developmental teacher loop for the existing U6 Bilqis learner.

Unlike the scratch formal experiments, this executable takes the verified
13,400-step U6 model, its AdamW moments and semantic graph as its living
parent. It practices derivation-vs-supersession counterfactuals alongside old
skills, monitors capability, and keeps the strongest viable descendant.

DEV/previously inspected probes are intentionally available to guide teaching:
this is *development*, not an attribution or confirmatory-science experiment.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import time

import torch
from torch.nn import functional as F

from bilqis_logic.kernel import digest
from bilqis_micro.graph import STATES
from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import batch, state_hash
from bilqis_development import kernel as semantics
from bilqis_development import run as development
from bilqis_development.continuation import load, save
from bilqis_spiral import run as spiral
from .lessons import build, paired_batch, validate_pair

VERSION = "bilqis.cumulative-development/v0.1"
ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "docs/evidence/u5-u6/run-01"
CHECKPOINT = PARENT / "after-U6.pt"
PARENT_SHA = "248a82ac92005f7b245751d6ea211d8296189de797f702349451f74383d75799"
PARENT_STATE = "5ec251f79620156a83be5ae3cdcdc961d071e75ff1f6bcc3ed721f4482952034"
RUN = ROOT / "runs" / "u7e-cumulative-lineage-20261012"
BUDGET = 640
REVIEW_EVERY = 32
START_LR = 0.0003


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    partial = path.with_name(path.name + ".partial")
    with partial.open("xb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    if path.exists():
        raise FileExistsError(str(path))
    partial.replace(path)


def parent():
    if sha(CHECKPOINT) != PARENT_SHA:
        raise ValueError("WRONG_CUMULATIVE_PARENT_CHECKPOINT")
    model, optimizer, payload = load(CHECKPOINT)
    if (state_hash(model) != PARENT_STATE or
        optimizer_receipt(optimizer)["steps"] != [13400] or
        model.config.vocab_size != len(payload["graph"]["tokens"]) or
        len(payload["graph"]["tokens"]) != 113):
        raise ValueError("U6_PARENT_MODEL_OR_SEMANTIC_ABI_DRIFT")
    return model, optimizer, payload


def memory(corpus):
    """Prior semantic families must actually receive gradient rehearsal."""
    pools = {}
    for stage, value in corpus["stages"].items():
        rows = [r for pool in value["train"].values() for r in pool]
        seen = {r["id"]: r for r in rows}
        if not seen:
            raise ValueError("NO_PRIOR_REHEARSAL_FOR_STAGE_" + stage)
        pools[int(stage)] = list(seen.values())
    return pools


def _retrieval(rows, rng):
    return rng.choice(rows)


def recall_batch(pools, rng):
    """16 real old-world examples, with explicit U0 and U4 protection."""
    quotas = {0: 3, 1: 1, 2: 1, 3: 1, 4: 6, 5: 2, 6: 2}
    if sum(quotas.values()) != 16:
        raise ValueError("BAD_REHEARSAL_QUOTA")
    rows = [rng.choice(pools[stage]) for stage, count in quotas.items()
            for _ in range(count)]
    rng.shuffle(rows)
    return rows


def batch_rows(easy, complex_set, pools, *, iteration, rng):
    new = paired_batch(easy, complex_set, iteration=iteration, rng=rng)
    old = recall_batch(pools, rng)
    if len(new) != 16 or len(old) != 16:
        raise ValueError("INVALID_CUMULATIVE_BATCH")
    return new + old


def step(model, reference, optimizer, rows):
    sequences = [semantics.encode(r["input"]) for r in rows]
    if len(rows) != 32 or any(len(seq) > model.config.context for seq in sequences):
        raise ValueError("CUMULATIVE_INPUT_LENGTH_INVALID")
    labels = torch.tensor([STATES.index(r["gold"]) for r in rows])
    model.train()
    optimizer.zero_grad(set_to_none=True)
    ids, lengths = batch(sequences)
    logits = model(ids, lengths)
    new_loss = F.cross_entropy(logits[:16], labels[:16])
    old_loss = F.cross_entropy(logits[16:], labels[16:])
    # Keep previously learned predictive structure, not just token identities.
    with torch.no_grad():
        reference.eval()
        old_reference = reference(*batch(sequences[16:]))
    memory_loss = F.kl_div(F.log_softmax(logits[16:] / 1.5, dim=-1),
                           F.softmax(old_reference / 1.5, dim=-1),
                           reduction="batchmean") * (1.5 ** 2)
    loss = new_loss + 0.9 * old_loss + 0.35 * memory_loss
    if not bool(torch.isfinite(loss)):
        raise ValueError("NONFINITE_DEVELOPMENT_LOSS")
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
    optimizer.step()
    return {"loss": float(loss.detach()), "new_loss": float(new_loss.detach()),
            "old_loss": float(old_loss.detach()),
            "memory_loss": float(memory_loss.detach())}


@torch.no_grad()
def _pair_score(model, episodes):
    results = {"both": 0, "pairs": 0, "by_relation": {}}
    for relation, pairs in episodes.items():
        # Every family contains direct and chain examples with fresh entities,
        # event types and polarities. This is a practical skill dashboard.
        sampled = pairs[:20]
        success = 0
        for first, second in sampled:
            pred = development.predict(model, [first["input"], second["input"]])
            success += int(all(p["prediction"] == r["gold"] for p, r in
                               zip(pred, (first, second))))
        results["by_relation"][relation] = {"both": success, "pairs": len(sampled)}
        results["both"] += success
        results["pairs"] += len(sampled)
    return results


def dashboard(model, corpus, direct, chained):
    primitives = [dict(row, family="Boolean-primitive") for row in
                  spiral.read(PARENT / "primitive-retention.json")["rows"]]
    distinction = spiral.read(PARENT / "distinction-probes.json")
    targets = {
        "primitives": primitives,
        "u0_composite": corpus["stages"]["0"]["eval"]["composite"],
        "u4_composite": corpus["stages"]["4"]["eval"]["composite"],
        "u4_varied": corpus["stages"]["4"]["eval"]["varied"],
        "u5_varied": corpus["stages"]["5"]["eval"]["varied"],
        "u6_varied": corpus["stages"]["6"]["eval"]["varied"],
        "lineage_10": distinction,
    }
    scores = {name: development.score(model, rows)["correct"] for name, rows in
              targets.items()}
    scores["direct_pairs"] = _pair_score(model, direct["episodes"])
    scores["chain_pairs"] = _pair_score(model, chained["episodes"])
    return scores


def viable(candidate, parent_scores):
    """Keep gains without trading away old critical functionality."""
    return (
        candidate["primitives"] == parent_scores["primitives"] and
        candidate["u0_composite"] >= parent_scores["u0_composite"] - 3 and
        candidate["u4_composite"] >= parent_scores["u4_composite"] - 3 and
        candidate["u4_varied"] >= parent_scores["u4_varied"] - 4 and
        candidate["u5_varied"] >= parent_scores["u5_varied"] - 12 and
        candidate["u6_varied"] >= parent_scores["u6_varied"] - 12
    )


def utility(scores, base):
    """Functionality first; old retention deficits are costly, not invisible."""
    pairs = (scores["direct_pairs"]["both"] + scores["chain_pairs"]["both"])
    penalties = (max(0, base["u0_composite"] - scores["u0_composite"]) * 2 +
                 max(0, base["u4_composite"] - scores["u4_composite"]) * 3 +
                 max(0, base["u4_varied"] - scores["u4_varied"]) +
                 max(0, base["u6_varied"] - scores["u6_varied"]) * .5)
    return (pairs * 2 + scores["lineage_10"] * 4 + scores["u4_composite"] * .25 -
            penalties)


def run(out=RUN, *, updates=BUDGET):
    if updates <= 0 or updates > BUDGET or updates % REVIEW_EVERY:
        raise ValueError("BAD_DEVELOPMENT_BUDGET")
    if out.exists():
        raise FileExistsError("cumulative development run must be append-only")
    model, optimizer, prior = parent()
    before_sha = state_hash(model)
    init_optimizer = optimizer_receipt(optimizer)
    reference = copy.deepcopy(model).eval()
    for param in reference.parameters():
        param.requires_grad_(False)
    for group in optimizer.param_groups:
        group["lr"] = START_LR
    corpus = spiral.read(PARENT / "data.json.gz")
    pools = memory(corpus)
    direct_train = build(14831, 100, compositional=False)
    chain_train = build(14837, 100, compositional=True)
    direct_eval = build(94477, 40, compositional=False)
    chain_eval = build(94489, 40, compositional=True)
    for lessons in (direct_train, chain_train):
        for pairs in lessons["episodes"].values():
            for a, b in pairs:
                validate_pair(a, b)
    seen = {r["id"] for data in (direct_train, chain_train)
            for pairs in data["episodes"].values() for a, b in pairs
            for r in (a, b)}
    novel = {r["id"] for data in (direct_eval, chain_eval)
             for pairs in data["episodes"].values() for a, b in pairs
             for r in (a, b)}
    if seen & novel:
        raise ValueError("NEW_SKILL_DASHBOARD_EXPOSED_IN_TRAINING")
    baseline = dashboard(model, corpus, direct_eval, chain_eval)
    out.mkdir(parents=True, exist_ok=False)
    write_new(out / "start.json", {
        "version": VERSION, "parent_checkpoint": str(CHECKPOINT),
        "parent_checkpoint_sha256": PARENT_SHA,
        "parent_model_sha256": before_sha,
        "parent_optimizer_sha256": init_optimizer["state_sha256"],
        "parent_step": init_optimizer["steps"][0],
        "initial_vocab": len(prior["graph"]["tokens"]),
        "initial_graph_sha256": digest(prior["graph"]),
        "optimizer_learning_rate": START_LR,
        "parent_optimizer_moments_preserved": True,
        "no_weights_reinitialized": True,
        "no_new_token_ids": True,
        "train_rows": len(seen), "development_dashboard_rows": len(novel),
        "parent_dashboard": baseline, "budget": updates,
    })
    write_new(out / "score-0000.json", {"step": 13400, "dashboard": baseline,
                                       "utility": utility(baseline, baseline),
                                       "viable": True})
    best = {"updates": 0, "step": 13400, "score": baseline,
            "utility": utility(baseline, baseline), "checkpoint": str(CHECKPOINT),
            "source": "inherited_U6"}
    rng = random.Random(21137)
    history, consumed = [], 0
    begin = time.perf_counter()
    for index in range(updates):
        rows = batch_rows(direct_train, chain_train, pools, iteration=index, rng=rng)
        loss = step(model, reference, optimizer, rows)
        consumed += 1
        history.append({"step": 13400 + consumed, **loss})
        if consumed % REVIEW_EVERY:
            continue
        if optimizer_receipt(optimizer)["steps"] != [13400 + consumed]:
            raise ValueError("ADAMW_STEP_HISTORY_RESET")
        scores = dashboard(model, corpus, direct_eval, chain_eval)
        score = utility(scores, baseline)
        healthy = viable(scores, baseline)
        candidate = {"step": 13400 + consumed, "dashboard": scores,
                     "utility": score, "viable": healthy,
                     "model_sha256": state_hash(model),
                     "optimizer_sha256": optimizer_receipt(optimizer)["state_sha256"],
                     "training_losses": history[-REVIEW_EVERY:],
                     "actual_update_count": consumed}
        write_new(out / f"score-{consumed:04d}.json", candidate)
        if healthy and score > best["utility"]:
            destination = out / f"best-after-{consumed:04d}.pt"
            save(destination, model, optimizer, prior["graph"], {
                "epoch": VERSION, "parent_step": 13400,
                "step": 13400 + consumed,
                "inherited_parent_sha256": PARENT_SHA,
                "retained_initial_embeddings": True,
                "model_reinitialized": False})
            best = {"updates": consumed, "step": 13400 + consumed, "score": scores,
                    "utility": score, "checkpoint": str(destination),
                    "checkpoint_sha256": sha(destination), "source": VERSION}
        print(json.dumps({"update": consumed, "viable": healthy,
                          "lineage": scores["lineage_10"],
                          "direct_pairs": scores["direct_pairs"]["both"],
                          "chain_pairs": scores["chain_pairs"]["both"],
                          "u4_comp": scores["u4_composite"],
                          "u0_comp": scores["u0_composite"],
                          "primitives": scores["primitives"],
                          "best_at": best["updates"]}, sort_keys=True), flush=True)
    write_new(out / "result.json", {
        "version": VERSION, "parent_step": 13400,
        "actual_updates": consumed, "final_step": 13400 + consumed,
        "final_optimizer_step": optimizer_receipt(optimizer)["steps"],
        "final_model_sha256": state_hash(model),
        "best": best, "baseline": baseline,
        "final": scores, "best_is_developmental_successor": best["updates"] > 0,
        "elapsed_seconds": time.perf_counter() - begin,
        "original_U6_unchanged": sha(CHECKPOINT) == PARENT_SHA,
        "one_student_continuation": True, "fresh_start_control_arms": 0,
        "weights_reset": False,
        "evaluation_posture": "repeated practical development dashboard, not a sealed proof",
    })
    return {"updates": consumed, "parent_step": 13400, "best": best,
            "baseline": baseline, "last": scores}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--updates", type=int, default=BUDGET)
    parser.add_argument("--out", type=Path, default=RUN)
    args = parser.parse_args()
    print(json.dumps(run(args.out, updates=args.updates), sort_keys=True))


if __name__ == "__main__":
    main()
