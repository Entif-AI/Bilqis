"""Immutable U6 successor: freeze -> train -> evaluate -> numeric replay.

Existing U5/U6 evidence and probes are read only. Its repeatedly inspected
varied/composite snapshots are DEV for adaptive decisions. A wholly disjoint
final cohort is frozen before the epoch, opened only after training completes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import time

import torch

from bilqis_logic.kernel import canonical, digest
from bilqis_micro.graph import STATES
from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import batch, state_hash
from bilqis_development import run as development
from bilqis_development.continuation import load, save
from bilqis_development.kernel import encode
from .sampler import MIX, Sampler, build_pools, check_row, dev_signals, family_key

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "docs/evidence/u5-u6/run-01"
CURRENT = PARENT / "after-U6.pt"
CORPUS = PARENT / "data.json.gz"
BASELINE = PARENT / "after-U6.json.gz"
VERSION = "spiral-consolidation-0.1.0"
SOURCES = tuple([
    "bilqis_spiral/sampler.py", "bilqis_spiral/run.py",
    "bilqis_micro/data.py", "bilqis_micro/kernel.py",
    "bilqis_development/data.py", "bilqis_development/kernel.py",
    "bilqis_development/continuation.py", "bilqis_development/run.py",
])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def write(path, obj):
    with path.open("xb") as f:
        f.write(canonical(obj) + b"\n")


def compressed(path, obj):
    with path.open("xb") as f:
        f.write(gzip.compress(canonical(obj) + b"\n", mtime=0))


def sources():
    return {path: sha(ROOT / path) for path in SOURCES}


def dev(model, corpus):
    return {s: {split: development.score(model, stage["eval"][split])
                for split in ("varied", "composite")}
            for s, stage in corpus["stages"].items()}


def freeze(run, *, updates=64, seed=11819):
    if run.exists():
        raise FileExistsError("a frozen epoch may never be rewritten")
    if not 1 <= updates <= 256:
        raise ValueError("bounded exploratory epoch requires 1..256 optimizer updates")
    parent_sha, corpus_sha, baseline_sha = sha(CURRENT), sha(CORPUS), sha(BASELINE)
    corpus = read(CORPUS)
    model, optimizer, payload = load(CURRENT)
    if optimizer_receipt(optimizer)["steps"] != [13400] or \
            payload["state_sha256"] != "5ec251f79620156a83be5ae3cdcdc961d071e75ff1f6bcc3ed721f4482952034":
        raise ValueError("not the verified U6 learner and optimizer")
    pools = build_pools(corpus, seed, updates)
    final = pools.pop("final")
    # Eager oracle/codec checks; final is never exposed to optimizer or weak-skill scorer.
    for group in ("fresh", "cross", "weak"):
        for rows in pools[group].values():
            for row in rows:
                check_row(row)
    for stage in final.values():
        for rows in stage.values():
            for row in rows:
                check_row(row)
    original_eval = {r["id"] for s in corpus["stages"].values()
                     for rows in s["eval"].values() for r in rows}
    train_ids = {r["id"] for group in ("fresh", "cross", "weak")
                 for rows in pools[group].values() for r in rows}
    final_ids = {r["id"] for s in final.values() for rows in s.values() for r in rows}
    if (train_ids & original_eval or train_ids & final_ids or
            final_ids & original_eval or len(final_ids) != 448):
        raise ValueError("frozen TRAIN / DEV / final overlap")
    start = dev(model, corpus)
    archived = read(BASELINE)
    if any(start[s][split]["predictions"] != archived[s][split]["predictions"]
           for s in corpus["stages"] for split in ("varied", "composite")):
        # Float changes between supported torch versions can differ narrowly;
        # compare semantic predictions, not version-sensitive decimal logits.
        for s in corpus["stages"]:
            for split in ("varied", "composite"):
                left = start[s][split]["predictions"]
                right = archived[s][split]["predictions"]
                if [(p["id"], p["gold"], p["prediction"]) for p in left] != \
                   [(p["id"], p["gold"], p["prediction"]) for p in right]:
                    raise ValueError("U6 DEV baseline no longer replays")
    try:
        run.mkdir(parents=True, exist_ok=False)
        compressed(run / "train-pools.json.gz", pools)
        compressed(run / "final-evaluation.json.gz", final)
        compressed(run / "dev-before.json.gz", start)
        policy = {
            "version": VERSION, "epoch": "U7-consolidation", "seed": seed,
            "updates": updates, "batch_size": 32, "categories": MIX,
            "fresh_prior": "new canonical bilqis_micro.data.lesson U0-U4, no parent TRAIN/DEV identities; without replacement per epoch",
            "cross_stage": "U5 and U6 typed expression joined with inherited U1-U3; paired old/new NOT contrasts each change oracle result",
            "weak_reinforcement": "new canonical family-specific oracle rows, 2 old + 2 recent minimum, family ceiling 3, DEV 16-update refresh",
            "weak_signal": "existing repeatedly inspected U0-U6 varied+composite readouts classified DEV; smoothed error plus deterioration from parent",
            "final_evaluation": "distinct source-generated varied/composite cohort; lock before updates, score only after training",
            "evaluation_claim": "exploratory, repeated DEV is adaptive; fresh final is a single unused cohort without independent scientific preregistration",
            "optimizer": "same continuing U6 student/AdamW hyperparameters, full moments and step counters; no reset",
            "source_hashes": sources(), "parent_checkpoint_sha256": parent_sha,
            "parent_state_sha256": payload["state_sha256"],
            "parent_optimizer": optimizer_receipt(optimizer),
            "prior_corpus_sha256": corpus_sha, "parent_dev_sha256": baseline_sha,
            "train_pools_sha256": sha(run / "train-pools.json.gz"),
            "final_evaluation_sha256": sha(run / "final-evaluation.json.gz"),
            "dev_before_sha256": sha(run / "dev-before.json.gz"),
            "final_rows": len(final_ids),
            "new_train_rows": len(train_ids),
            "cross_causal_witnesses": len(pools["causal"]),
            "old_eval_ids_excluded": len(original_eval)
        }
        write(run / "freeze.json", policy)
    except Exception:
        # The path intentionally remains as partial evidence; no replay/overwrite.
        raise
    return {"status": "FROZEN", "run": str(run), "new_train_rows": len(train_ids),
            "cross_causal_witnesses": len(pools["causal"]), "final_rows": len(final_ids),
            "parent_optimizer_steps": 13400}


def verify(run):
    policy = read(run / "freeze.json")
    if policy["version"] != VERSION or policy["categories"] != MIX or \
            policy["source_hashes"] != sources() or \
            policy["parent_checkpoint_sha256"] != sha(CURRENT) or \
            policy["prior_corpus_sha256"] != sha(CORPUS) or \
            policy["parent_dev_sha256"] != sha(BASELINE):
        raise ValueError("frozen policy/source/parent drift")
    for filename, key in (("train-pools.json.gz", "train_pools_sha256"),
                          ("final-evaluation.json.gz", "final_evaluation_sha256"),
                          ("dev-before.json.gz", "dev_before_sha256")):
        if sha(run / filename) != policy[key]:
            raise ValueError("frozen input changed: " + filename)
    pools, corpus = read(run / "train-pools.json.gz"), read(CORPUS)
    if len(pools["causal"]) != policy["cross_causal_witnesses"]:
        raise ValueError("cross-arm witness count changed")
    return policy, pools, corpus


def _step(model, optimizer, rows):
    encoded = [encode(row["input"]) for row in rows]
    ids, lengths = batch(encoded)
    labels = torch.tensor([STATES.index(row["gold"]) for row in rows])
    model.train()
    optimizer.zero_grad(set_to_none=True)
    loss = torch.nn.functional.cross_entropy(model(ids, lengths), labels)
    if not bool(torch.isfinite(loss)):
        raise ValueError("nonfinite spiral loss")
    loss.backward()
    norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True))
    optimizer.step()
    return float(loss.detach()), norm, int(lengths.sum()), int(ids.numel())


def _execute(policy, pools, corpus, model, optimizer, log=None):
    base = read(PARENT / "after-U6.json.gz")
    before = read(Path(policy["_run"]) / "dev-before.json.gz")
    signals = dev_signals(before, base)
    sampler = Sampler(corpus, pools, policy["seed"] + 1, signals)
    exposures, category_counts = Counter(), Counter()
    rows_logged = 0
    for iteration in range(policy["updates"]):
        if iteration and iteration % 16 == 0:
            updated = dev(model, corpus)
            sampler.update_signals(dev_signals(updated, base))
        rows, categories, weak_families = sampler.batch()
        if any(check_row(row) is not row for row in rows):
            raise ValueError("unvalidated spiral row")
        loss, norm, tokens, padded = _step(model, optimizer, rows)
        step = 13401 + iteration
        receipt = {"step": step, "categories": categories,
                   "category_counts": dict(Counter(categories)),
                   "row_ids": [r["id"] for r in rows],
                   "stages": [r["stage"] for r in rows],
                   "families": [r["family"] for r in rows],
                   "weak_keys": weak_families,
                   "signals_sha256": digest(sampler.signals),
                   "weak_signals": {key: sampler.signals[key] for key in sorted(
                       set(k for k in weak_families if k is not None))},
                   "loss": loss, "gradient_norm": norm,
                   "tokens": tokens, "padded_positions": padded}
        if log is not None:
            log.write(canonical(receipt) + b"\n")
        exposures.update(receipt["row_ids"])
        category_counts.update(categories)
        rows_logged += 1
    return {"optimizer_step": 13400 + policy["updates"],
            "updates": rows_logged, "exposures": dict(exposures),
            "categories": dict(category_counts), "final_state_sha256": state_hash(model),
            "optimizer": optimizer_receipt(optimizer)}


def train(run):
    policy, pools, corpus = verify(run)
    for name in ("training.jsonl.gz", "after.pt", "training-result.json"):
        if (run / name).exists():
            raise FileExistsError("successor is immutable; use a new run directory")
    model, optimizer, parent = load(CURRENT)
    if state_hash(model) != policy["parent_state_sha256"] or \
            optimizer_receipt(optimizer) != policy["parent_optimizer"]:
        raise ValueError("AdamW or model changed before train")
    start = time.perf_counter()
    with (run / "training.jsonl.gz").open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as f:
            outcome = _execute(dict(policy, _run=str(run)), pools, corpus, model, optimizer, f)
    if outcome["optimizer"]["steps"] != [13400 + policy["updates"]]:
        raise ValueError("AdamW continuity lost")
    save(run / "after.pt", model, optimizer, parent["graph"],
         {"step": outcome["optimizer_step"], "parent_checkpoint_sha256": sha(CURRENT),
          "freeze_sha256": sha(run / "freeze.json"), "start_state_sha256": policy["parent_state_sha256"],
          "optimizer_before": policy["parent_optimizer"]})
    outcome.update({"checkpoint_sha256": sha(run / "after.pt"),
                    "training_sha256": sha(run / "training.jsonl.gz"),
                    "freeze_sha256": sha(run / "freeze.json"),
                    "wall_seconds": time.perf_counter() - start})
    write(run / "training-result.json", outcome)
    return {"status": "TRAINED", "optimizer_step": outcome["optimizer_step"],
            "state_sha256": outcome["final_state_sha256"], "categories": outcome["categories"]}


def evaluate(run):
    policy, _, corpus = verify(run)
    result = read(run / "training-result.json")
    if (run / "final-results.json.gz").exists():
        raise FileExistsError("final cohort has already been opened")
    if sha(run / "after.pt") != result["checkpoint_sha256"]:
        raise ValueError("trained checkpoint changed")
    model, optimizer, _ = load(run / "after.pt")
    if state_hash(model) != result["final_state_sha256"]:
        raise ValueError("trained state mismatch")
    dev_after = dev(model, corpus)
    final = read(run / "final-evaluation.json.gz")
    final_after = {s: {split: development.score(model, rows)
                       for split, rows in splits.items()} for s, splits in final.items()}
    original, _, _ = load(CURRENT)
    final_before = {s: {split: development.score(original, rows)
                        for split, rows in splits.items()} for s, splits in final.items()}
    compressed(run / "dev-after.json.gz", dev_after)
    compressed(run / "final-results.json.gz", {
        "status": "ONE_TIME_FINAL_OPENING", "epoch": policy["epoch"],
        "post_training_only": True, "before": final_before, "after": final_after})
    return {"status": "EVALUATED", "final_pairs": sum(
        len(rows) for splits in final.values() for rows in splits.values()),
        "dev_after_sha256": sha(run / "dev-after.json.gz"),
        "final_result_sha256": sha(run / "final-results.json.gz")}


def replay(run):
    policy, pools, corpus = verify(run)
    result = read(run / "training-result.json")
    if (sha(run / "after.pt") != result["checkpoint_sha256"] or
            sha(run / "training.jsonl.gz") != result["training_sha256"]):
        raise ValueError("training artifacts drift")
    model, optimizer, _ = load(CURRENT)
    receipts = []
    with gzip.open(run / "training.jsonl.gz", "rt") as stream:
        for line in stream:
            r = json.loads(line)
            if Counter(r["categories"]) != Counter(MIX) or len(r["row_ids"]) != 32:
                raise ValueError("per-step 12/4/8/8 mismatch")
            receipts.append(r)
    if len(receipts) != policy["updates"]:
        raise ValueError("missing gradient/exposure receipts")
    expected = []
    def capture(line):
        expected.append(json.loads(line))
    generated = _execute(dict(policy, _run=str(run)), pools, corpus, model, optimizer, capture)
    for a, b in zip(receipts, expected):
        if (a["step"], a["row_ids"], a["categories"], a["weak_keys"], a["signals_sha256"]) != \
                (b["step"], b["row_ids"], b["categories"], b["weak_keys"], b["signals_sha256"]):
            raise ValueError("stochastic sampler replay diverged")
        if abs(a["loss"] - b["loss"]) > 1e-6 or abs(a["gradient_norm"] - b["gradient_norm"]) > 1e-6:
            raise ValueError("numeric training replay diverged")
    if generated["final_state_sha256"] != result["final_state_sha256"] or \
            generated["optimizer"]["state_sha256"] != result["optimizer"]["state_sha256"] or \
            generated["exposures"] != result["exposures"]:
        raise ValueError("checkpoint/AdamW/exposure replay diverged")
    return {"status": "REPRODUCED", "updates": policy["updates"],
            "optimizer_step": generated["optimizer_step"], "state_sha256": generated["final_state_sha256"],
            "exact_32_per_step": True, "old_final_unseen_during_selection": True}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("freeze", "train", "evaluate", "replay"))
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--updates", type=int, default=64)
    p.add_argument("--seed", type=int, default=11819)
    a = p.parse_args()
    if a.action == "freeze":
        result = freeze(a.run, updates=a.updates, seed=a.seed)
    else:
        result = {"train": train, "evaluate": evaluate, "replay": replay}[a.action](a.run)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
