"""Freeze one cohort, train one continuing learner, replay every stage checkpoint."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import resource
import subprocess
import time

import torch

from bilqis_logic.kernel import canonical, digest
from bilqis_logic.geometry import tensor_hash
from bilqis_ref.model import ModelConfig, batch, state_hash
from .data import build_data, audit_data, NAMES
from .graph import catalog, TOKENS, STATES, RULE
from .kernel import world, entity, relation, logic, bound, quantify, entails, observe, record, encode, evaluate
from .model import initialize, predict, save_checkpoint, load_checkpoint

ROOT = Path(__file__).resolve().parents[1]
VERSION = "micro-development-0.1.0"


def write_json(path, value):
    with path.open("xb") as stream:
        stream.write(canonical(value) + b"\n")


def read_json(path):
    return json.loads(path.read_bytes())


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    paths = list((ROOT / "bilqis_micro").glob("*.py")) + list((ROOT / "bilqis_logic").glob("*.py")) + [ROOT / "bilqis_ref/model.py"]
    return {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(paths)}


def default_config():
    return {"version": VERSION, "seed": 108, "model": {"vocab_size": len(TOKENS), "width": 96, "layers": 3,
            "heads": 6, "context": 96, "expansion": 4, "precision": "fp32"}, "stage_steps": [800, 1800, 2200, 2000, 1600],
            "batch_size": 32, "mixture": {"focus": 12, "composition": 8, "contrast": 4, "rehearsal": 8},
            "optimizer": {"lr": .0015, "betas": [.9, .95], "eps": 1e-8, "weight_decay": .01, "clip_norm": 1.0},
            "device": "cpu", "threads": 1, "run_class": "EXPLORATORY_CUMULATIVE"}


def validate_config(cfg):
    if (cfg["version"] != VERSION or cfg["device"] != "cpu" or cfg["threads"] != 1 or cfg["model"]["precision"] != "fp32"
            or cfg["batch_size"] != 32 or cfg["mixture"] != {"focus": 12, "composition": 8, "contrast": 4, "rehearsal": 8}
            or len(cfg["stage_steps"]) != 5 or any(type(s) is not int or s < 1 for s in cfg["stage_steps"])):
        raise ValueError("cumulative development configuration")


def optimizer_receipt(optimizer):
    state = optimizer.state_dict()
    normalized = {"param_groups": state["param_groups"], "state": {str(k): {name: tensor_hash(v) if isinstance(v, torch.Tensor) else v
                   for name, v in value.items()} for k, value in state["state"].items()}}
    return {"state_sha256": digest(normalized), "steps": sorted({int(v["step"]) for v in state["state"].values()}),
            "parameter_states": len(state["state"])}


def make_optimizer(model, cfg):
    c = cfg["optimizer"]
    return torch.optim.AdamW(model.parameters(), lr=c["lr"], betas=tuple(c["betas"]), eps=c["eps"], weight_decay=c["weight_decay"], foreach=False)


def score(model, rows):
    predictions = []
    for start in range(0, len(rows), 32):
        chunk = rows[start:start + 32]
        predictions += [dict(p, id=r["id"], gold=r["gold"], family=r["family"])
                        for r, p in zip(chunk, predict(model, [r["input"] for r in chunk]))]
    correct = sum(p["gold"] == p["prediction"] for p in predictions)
    labels = {s: {"n": sum(p["gold"] == s for p in predictions), "correct": sum(p["gold"] == s and p["prediction"] == s for p in predictions)} for s in STATES}
    families = {f: {"n": sum(p["family"] == f for p in predictions), "correct": sum(p["family"] == f and p["prediction"] == p["gold"] for p in predictions)} for f in sorted({p["family"] for p in predictions})}
    return {"n": len(rows), "correct": correct, "accuracy": correct / len(rows), "by_label": labels, "by_family": families,
            "majority_label_accuracy": max(v["n"] for v in labels.values()) / len(rows), "predictions": predictions}


def score_stages(model, data, through):
    return {i: {split: score(model, rows) for split, rows in data["stages"][i]["eval"].items()} for i in map(str, range(through + 1))}


def summaries(scores):
    return {i: {split: {k: v for k, v in s.items() if k != "predictions"} for split, s in pools.items()} for i, pools in scores.items()}


def example_inputs():
    a, b, c = map(entity, "ABC")
    w = world(list("ABC"), [("PARENT", "A", "B"), ("PARENT", "B", "C")])
    changed = world(list("ABC"), [("PARENT", "A", "B"), ("PARENT", "C", "B")])
    q = quantify("EXISTS", logic("AND", relation("PARENT", a, bound(0)), relation("PARENT", bound(0), c)))
    proof_world = world(list("ABC"), w["facts"], rules=[RULE])
    proof = entails(relation("GRANDPARENT", a, c))
    evidence_world = world(list("ABC"), w["facts"], propositions={"J0": relation("PARENT", a, b)})
    refuted = world(list("ABC"), w["facts"], propositions=evidence_world["propositions"], reports=[("S0", "J0", "refute", 0)])
    return [(1, "parent direction", record(w, relation("PARENT", a, b))),
            (1, "inverse child", record(w, relation("CHILD", b, a))),
            (1, "parent is not transitive", record(w, relation("PARENT", a, c))),
            (2, "bound two-hop witness", record(w, q)), (2, "reverse one edge", record(changed, q)),
            (3, "declared two-hop rule", record(proof_world, proof)), (3, "remove one rule", record(w, proof)),
            (4, "no report", record(evidence_world, observe("J0"))), (4, "explicit refutation", record(refuted, observe("J0")))]


def freeze(cfg, out):
    wall, cpu = time.perf_counter(), time.process_time()
    validate_config(cfg)
    data = build_data()
    manifest = audit_data(data)
    if manifest["max_input_tokens"] > cfg["model"]["context"]:
        raise ValueError("dataset exceeds context")
    model, initializer = initialize(ModelConfig(**cfg["model"]), cfg["seed"])
    out.mkdir(parents=True, exist_ok=False)
    samples = []
    for stage, label, r in example_inputs():
        ids = encode(r)
        samples.append({"stage": stage, "description": label, "input": r, "ids": ids,
                        "semantic_tokens": [TOKENS[t] for t in ids], "gold": evaluate(r), "untrained_neural": predict(model, [r])[0]})
    artifacts = {"config.json": cfg, "graph.json": catalog(), "initializer.json": initializer, "data.json": data, "manifest.json": manifest,
                 "samples.json": samples, "token-abi.json": {"tokens": TOKENS, "answer_order": list(STATES), "labels_in_input": False,
                 "syntax": "raw asserted world and unreduced typed prefix query; legacy Boolean ABI preserved", "natural_language_in_input": False},
                 "provenance.json": {"authority": "project-owned developmental micro-universe execution contract",
                 "contract_sha256": file_hash(ROOT / "docs/micro-universes/CONTRACT.md"), "helpers": [], "helper_calls": 0, "helper_seconds": 0,
                 "helper_external_spend": 0, "pretrained_neural_transfer": False, "historical_evidence_modified": False,
                 "accepted_semantics": "typed finite-world definitions; set/table and adjacency/operational cross-checks; no external teacher labels"}}
    for name, value in artifacts.items():
        write_json(out / name, value)
    save_checkpoint(out / "initial.pt", model, initializer, {"step": 0, "parent_checkpoint_sha256": None, "data_sha256": digest(data)})
    write_json(out / "step-zero.json", score_stages(model, data, 4))
    receipt = {"version": VERSION, "created_at_utc": datetime.now(timezone.utc).isoformat(), "source_hashes": source_hashes(),
               "source_git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "artifacts": {name: file_hash(out / name) for name in [*artifacts, "initial.pt", "step-zero.json"]},
               "initial_state_sha256": state_hash(model), "initial_tensor_hashes": {k: tensor_hash(v) for k, v in model.state_dict().items()},
               "parameter_count": sum(p.numel() for p in model.parameters()), "semantic_preparation_seconds": time.perf_counter() - wall,
               "semantic_preparation_cpu_seconds": time.process_time() - cpu,
               "environment": {"python": platform.python_version(), "torch": torch.__version__, "platform": platform.platform(), "device": "cpu",
                               "threads": 1, "deterministic_algorithms": True}, "run_class": cfg["run_class"], "independent_seal": False}
    write_json(out / "freeze.json", receipt)
    # Alignment readout precedes any training and prints the exact numeric inputs.
    print(json.dumps({"neural_interface": {"inputs": "IDs and lengths only", "output": "five neural logits; argmax in answer_order",
                      "answer_order": STATES, "oracle_at_inference": False}, "samples": [{k: s[k] for k in ("stage", "description", "ids", "gold")} for s in samples]}, indent=2), flush=True)
    return {"freeze_sha256": file_hash(out / "freeze.json"), "parameter_count": receipt["parameter_count"], "max_input_tokens": manifest["max_input_tokens"]}


def verify_freeze(run):
    frozen = read_json(run / "freeze.json")
    if source_hashes() != frozen["source_hashes"]:
        raise ValueError("frozen executable source changed")
    for name, expected in frozen["artifacts"].items():
        if file_hash(run / name) != expected:
            raise ValueError("frozen artifact changed: " + name)
    cfg, data = read_json(run / "config.json"), read_json(run / "data.json")
    validate_config(cfg)
    if audit_data(data) != read_json(run / "manifest.json"):
        raise ValueError("frozen lesson binding")
    return frozen, cfg, data


def _balanced(pool, count, rng):
    labels = sorted({r["gold"] for r in pool})
    groups = {s: [r for r in pool if r["gold"] == s] for s in labels}
    return [rng.choice(groups[rng.choice(labels)]) for _ in range(count)]


def training_rows(data, stage, rng):
    s = data["stages"][str(stage)]
    rows = _balanced(s["train"]["focus"], 12, rng) + _balanced(s["train"]["composition"], 8, rng)
    by_id = {r["id"]: r for pool in s["train"].values() for r in pool}
    for _ in range(2):
        pair = rng.choice(data["contrast_pairs"][str(stage)])
        rows += [by_id[pair["before"]], by_id[pair["after"]]]
    # Four Boolean examples at every later stage, plus four earlier-world examples.
    rows += _balanced(data["stages"]["0"]["train"]["focus"], 4, rng)
    rows += _balanced(data["stages"]["0"]["train"]["composition"], 4, rng) if stage == 0 else [
        rng.choice(data["stages"][str(rng.randrange(stage))]["train"][rng.choice(("focus", "composition"))]) for _ in range(4)]
    rng.shuffle(rows)
    return rows


def train(run):
    wall, cpu = time.perf_counter(), time.process_time()
    frozen, cfg, data = verify_freeze(run)
    # Exclusive log creation fails closed for completed or interrupted runs.
    stream = (run / "training.jsonl.gz").open("xb")
    model, initial = load_checkpoint(run / "initial.pt")
    if state_hash(model) != frozen["initial_state_sha256"]:
        stream.close()
        raise ValueError("genesis binding")
    # Exactly one training model and optimizer, outside the stage loop.
    optimizer = make_optimizer(model, cfg)
    rng = random.Random(cfg["seed"])
    encoded = {r["id"]: encode(r["input"]) for s in data["stages"].values() for pool in s["train"].values() for r in pool}
    exposures = Counter()
    receipts = []
    totals = {"examples": 0, "nonpadding_tokens": 0, "padded_positions": 0}
    step, parent = 0, file_hash(run / "initial.pt")
    observed_tokens = set()
    with stream, gzip.GzipFile(fileobj=stream, mode="wb", mtime=0) as log:
        for stage, updates in enumerate(cfg["stage_steps"]):
            start, start_cpu = time.perf_counter(), time.process_time()
            start_state, before = state_hash(model), optimizer_receipt(optimizer)
            if receipts and (start_state != receipts[-1]["end_state_sha256"] or before != receipts[-1]["optimizer_after"]):
                raise ValueError("stage transition reset weights or optimizer")
            start_step, losses, stage_exposures = step, [], Counter()
            stage_tokens = {t for pool in data["stages"][str(stage)]["train"].values() for r in pool for t in encoded[r["id"]]}
            print(json.dumps({"stage": stage, "name": NAMES[stage], "start_step": step, "updates": updates}), flush=True)
            for local_step in range(updates):
                rows = training_rows(data, stage, rng)
                ids, lengths = batch([encoded[r["id"]] for r in rows])
                labels = torch.tensor([STATES.index(r["gold"]) for r in rows])
                model.train()
                optimizer.zero_grad(set_to_none=True)
                loss = torch.nn.functional.cross_entropy(model(ids, lengths), labels)
                if not bool(torch.isfinite(loss)):
                    raise ValueError("nonfinite developmental loss")
                loss.backward()
                gradient = float(torch.nn.utils.clip_grad_norm_(model.parameters(), cfg["optimizer"]["clip_norm"], error_if_nonfinite=True))
                optimizer.step()
                step += 1
                value = float(loss.detach())
                losses.append(value)
                exposures.update(r["id"] for r in rows)
                stage_exposures.update(r["id"] for r in rows)
                totals["examples"] += len(rows)
                totals["nonpadding_tokens"] += int(lengths.sum())
                totals["padded_positions"] += int(ids.numel())
                log.write(canonical({"stage": stage, "step": step, "loss": value, "gradient_norm": gradient,
                          "row_ids": [r["id"] for r in rows], "tokens": int(lengths.sum()), "padded_positions": int(ids.numel())}) + b"\n")
                if (local_step + 1) % 200 == 0:
                    print(json.dumps({"stage": stage, "step": step, "mean_recent_loss": sum(losses[-100:]) / len(losses[-100:])}), flush=True)
            after = optimizer_receipt(optimizer)
            if after["steps"] != [step]:
                raise ValueError("optimizer step continuity")
            checkpoint = f"after-U{stage}.pt"
            metadata = {"stage": stage, "step": step, "parent_checkpoint_sha256": parent, "start_state_sha256": start_state,
                        "optimizer_before": before, "optimizer_after": after, "freeze_sha256": file_hash(run / "freeze.json"), **totals}
            save_checkpoint(run / checkpoint, model, initial["initializer"], metadata, optimizer)
            checkpoint_hash = file_hash(run / checkpoint)
            training_seconds = time.perf_counter() - start
            scores = score_stages(model, data, stage)
            write_json(run / f"after-U{stage}.json", scores)
            receipt = {"stage": stage, "name": NAMES[stage], "start_step": start_step, "end_step": step, "updates": updates,
                       "start_state_sha256": start_state, "end_state_sha256": state_hash(model), "optimizer_before": before, "optimizer_after": after,
                       "parent_checkpoint_sha256": parent, "checkpoint": checkpoint, "checkpoint_sha256": checkpoint_hash,
                       "introduced_input_identities": [TOKENS[t] for t in sorted(stage_tokens - observed_tokens)],
                       "introduced_semantic_identities": [n["id"] for n in catalog()["nodes"] if n["stage"] == stage],
                       "exposures_by_row": dict(stage_exposures), "loss_first_100": sum(losses[:100]) / len(losses[:100]),
                       "loss_last_100": sum(losses[-100:]) / len(losses[-100:]), "training_seconds": training_seconds,
                       "stage_wall_seconds": time.perf_counter() - start, "stage_cpu_seconds": time.process_time() - start_cpu,
                       "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system() == "Darwin" else 1024),
                       "scores": summaries(scores)}
            write_json(run / f"stage-U{stage}.json", receipt)
            receipts.append(receipt)
            observed_tokens |= stage_tokens
            parent = checkpoint_hash
            print(json.dumps({"completed_stage": stage, "optimizer_step": step, "current_scores": {s: [v["correct"], v["n"]] for s, v in scores[str(stage)].items()}}), flush=True)
    files = [name for stage in range(5) for name in (f"after-U{stage}.pt", f"after-U{stage}.json", f"stage-U{stage}.json")] + ["training.jsonl.gz"]
    result = {"version": VERSION, "status": "EXPLORATORY_MEASURED", "training_pid": os.getpid(), "stages": receipts,
              "steps": step, **totals, "exposures_by_row": dict(exposures), "wall_seconds": time.perf_counter() - wall,
              "cpu_seconds": time.process_time() - cpu, "peak_process_rss_bytes": receipts[-1]["peak_process_rss_bytes"],
              "final_state_sha256": state_hash(model), "freeze_sha256": file_hash(run / "freeze.json"),
              "evidence_sha256": {name: file_hash(run / name) for name in files}, "helper_calls": 0, "helper_seconds": 0, "helper_external_spend": 0,
              "semantic_preparation_seconds": frozen["semantic_preparation_seconds"], "model_instances_during_training": 1,
              "optimizer_instances_during_training": 1, "parameter_or_optimizer_resets": 0, "pretrained_neural_transfer": False,
              "limits": ["one aligned scratch learner; exploratory development, no attribution or confirmatory controls",
                         "familiar overlaps training; varied/composite inputs excluded from training; developer-authored evaluation",
                         "finite closure and candidate countermodel checking; no general theorem prover",
                         "five identities and tiny topologies; imperfect transfer and forgetting retained", "FP32 CPU; energy not measured"], "energy_joules": None}
    write_json(run / "result.json", result)
    return {"steps": step, "final_state_sha256": result["final_state_sha256"], "wall_seconds": result["wall_seconds"]}


def replay(run):
    frozen, cfg, data = verify_freeze(run)
    result = read_json(run / "result.json")
    for name, expected in result["evidence_sha256"].items():
        if file_hash(run / name) != expected:
            raise ValueError("trained evidence changed: " + name)
    initial_hash = file_hash(run / "initial.pt")
    previous_state, previous_optimizer, parent = frozen["initial_state_sha256"], None, initial_hash
    count, maximum = 0, 0.
    for stage in range(-1, 5):
        checkpoint = "initial.pt" if stage == -1 else f"after-U{stage}.pt"
        model, payload = load_checkpoint(run / checkpoint)
        archived = read_json(run / ("step-zero.json" if stage == -1 else f"after-U{stage}.json"))
        through = 4 if stage == -1 else stage
        actual = score_stages(model, data, through)
        if stage >= 0:
            receipt = result["stages"][stage]
            if read_json(run / f"stage-U{stage}.json") != receipt:
                raise ValueError("stage receipt binding")
            optimizer = make_optimizer(model, cfg)
            optimizer.load_state_dict(payload["optimizer"])
            if (receipt["start_state_sha256"] != previous_state or receipt["parent_checkpoint_sha256"] != parent
                    or payload["metadata"]["parent_checkpoint_sha256"] != parent or receipt["end_state_sha256"] != state_hash(model)
                    or receipt["end_step"] != sum(cfg["stage_steps"][:stage + 1]) or receipt["start_step"] != sum(cfg["stage_steps"][:stage])
                    or receipt["optimizer_after"] != optimizer_receipt(optimizer)
                    or (previous_optimizer is not None and receipt["optimizer_before"] != previous_optimizer)):
                raise ValueError("checkpoint or optimizer lineage changed")
            previous_state, previous_optimizer, parent = state_hash(model), receipt["optimizer_after"], file_hash(run / checkpoint)
        for i, pools in actual.items():
            for split, scores in pools.items():
                expected = archived[i][split]
                if len(scores["predictions"]) != len(expected["predictions"]):
                    raise ValueError("prediction count changed")
                for got, prior in zip(scores["predictions"], expected["predictions"]):
                    if any(got[k] != prior[k] for k in ("id", "prediction", "gold", "family")):
                        raise ValueError("neural replay label/identity mismatch")
                    delta = max(abs(a - b) for a, b in zip(got["logits"] + got["probabilities"], prior["logits"] + prior["probabilities"]))
                    maximum = max(maximum, delta)
                    if delta > 1e-6:
                        raise ValueError("numerical replay mismatch")
                    count += 1
                if {k: v for k, v in scores.items() if k != "predictions"} != {k: v for k, v in expected.items() if k != "predictions"}:
                    raise ValueError("score summary mismatch")
        if stage >= 0 and summaries(actual) != result["stages"][stage]["scores"]:
            raise ValueError("result score binding")
    if previous_state != result["final_state_sha256"] or result["freeze_sha256"] != file_hash(run / "freeze.json"):
        raise ValueError("result lineage binding")
    by_id = {r["id"]: r for s in data["stages"].values() for pool in s["train"].values() for r in pool}
    exposures, stage_exposures = Counter(), [Counter() for _ in range(5)]
    totals = {"examples": 0, "nonpadding_tokens": 0, "padded_positions": 0}
    updates = 0
    with gzip.open(run / "training.jsonl.gz", "rt") as log:
        for line in log:
            entry = json.loads(line)
            updates += 1
            stage = next(i for i in range(5) if updates <= sum(cfg["stage_steps"][:i + 1]))
            ids = entry["row_ids"]
            if entry["step"] != updates or entry["stage"] != stage or len(ids) != 32 or any(i not in by_id or by_id[i]["stage"] > stage for i in ids):
                raise ValueError("exposure stage/step binding")
            lengths = [len(encode(by_id[i]["input"])) for i in ids]
            if (entry["tokens"] != sum(lengths) or entry["padded_positions"] != max(lengths) * len(ids)
                    or not math.isfinite(entry["loss"]) or not math.isfinite(entry["gradient_norm"])):
                raise ValueError("training accounting changed")
            exposures.update(ids)
            stage_exposures[stage].update(ids)
            totals["examples"] += len(ids)
            totals["nonpadding_tokens"] += sum(lengths)
            totals["padded_positions"] += max(lengths) * len(ids)
    if (updates != result["steps"] or exposures != Counter(result["exposures_by_row"])
            or any(result[k] != v for k, v in totals.items())
            or any(stage_exposures[i] != Counter(r["exposures_by_row"]) for i, r in enumerate(result["stages"]))):
        raise ValueError("exposure/result binding")
    receipt = {"status": "REPRODUCED", "predictions": count, "max_absolute_error": maximum, "atol": 1e-6,
               "stages": 5, "optimizer_steps": updates, "checkpoint_lineage_verified": True, "exposures_verified": True,
               "freeze_sha256": result["freeze_sha256"], "final_state_sha256": previous_state,
               "different_process_than_training": os.getpid() != result["training_pid"], "replay_pid": os.getpid()}
    if not (run / "replay.json").exists():
        write_json(run / "replay.json", receipt)
    else:
        prior = read_json(run / "replay.json")
        if any(prior[k] != v for k, v in receipt.items() if k not in ("different_process_than_training", "replay_pid")):
            raise ValueError("replay evidence changed")
    return receipt


def formal(e):
    k = e["kind"]
    if k == "entity":
        return e["name"]
    if k == "bound":
        return "v" + str(e["index"])
    if k == "literal":
        return "TRUE" if e["value"] else "FALSE"
    if k == "variable":
        return e["name"]
    if k in ("apply", "evidence", "relation", "compare"):
        op = e.get("operator", e.get("name"))
        return ("EVIDENCE_" if k == "evidence" else "") + op + "(" + ",".join(map(formal, e["args"])) + ")"
    if k == "quantify":
        return e["operator"] + "[" + formal(e["body"]) + "]"
    if k == "compose":
        return ";".join(e["relations"]) + "(" + ",".join(map(formal, e["args"])) + ")"
    if k == "observe":
        return "OBSERVE(" + e["proposition"] + ")"
    return k.upper() + "(" + ",".join(map(formal, e.get("premises", []) + [e["conclusion"]])) + ")"


def display_input(r):
    if r["task"] == "evaluate":
        return formal(r["expression"]) + (" " + str(r["assignments"]) if r["assignments"] else "")
    if r["task"] == "equivalent":
        return formal(r["left"]) + " == " + formal(r["right"])
    w = r["world"]
    facts = "; ".join(f"{name}({a},{b})" for name, a, b in w["facts"])
    suffix = " + GP rule" if w["rules"] else ""
    if w["propositions"]:
        suffix += "; reports=" + str(w["reports"]) + "; live=" + str(w["live"])
    return "{" + facts + "}" + suffix + " => " + formal(r["query"])


def report(run):
    result, data = read_json(run / "result.json"), read_json(run / "data.json")
    final = read_json(run / "after-U4.json")
    model, _ = load_checkpoint(run / "after-U4.pt")
    demos = []
    for stage, label, r in example_inputs():
        stage_model, _ = load_checkpoint(run / f"after-U{stage}.pt")
        demos.append({"stage": stage, "description": label, "input": r, "formal": display_input(r), "ids": encode(r), "gold": evaluate(r),
                      "at_introduction": predict(stage_model, [r])[0], "final": predict(model, [r])[0]})
    selected, contrasts = [], []
    for stage in range(5):
        s = data["stages"][str(stage)]
        for split, scores in final[str(stage)].items():
            by_id = {r["id"]: r for r in s["eval"][split]}
            for correct in (True, False):
                matches = [p for p in scores["predictions"] if (p["prediction"] == p["gold"]) == correct][:2]
                selected += [dict(p, stage=stage, split=split, input=by_id[p["id"]]["input"], formal=display_input(by_id[p["id"]]["input"])) for p in matches]
        by_id = {r["id"]: r for pool in s["train"].values() for r in pool}
        for pair in data["contrast_pairs"][str(stage)][:4]:
            rows = [by_id[pair[key]] for key in ("before", "after")]
            predicted = predict(model, [r["input"] for r in rows])
            contrasts.append({"stage": stage, "factor": pair["factor"], "familiar_training_pair": True,
                              "pair": [dict(r, neural=p, formal=display_input(r["input"])) for r, p in zip(rows, predicted)]})
    gallery = {"answer_order": STATES, "demonstrations": demos, "selected_successes_and_mistakes": selected, "perturbations": contrasts}
    write_json(run / "gallery.json", gallery)
    lines = ["# Bilqis developmental micro-universes", "", "One scratch learner continued through U0–U4 with one AdamW optimizer. This is an exploratory capability-building run.", "",
             "| Universe | At introduction: familiar / varied / composite | After U4: familiar / varied / composite |", "| --- | --- | --- |"]
    for stage in range(5):
        introduced = result["stages"][stage]["scores"][str(stage)]
        fmt = lambda pools: " / ".join(f"{pools[s]['correct']}/{pools[s]['n']}" for s in ("familiar", "varied", "composite"))
        lines.append(f"| U{stage}: {NAMES[stage]} | {fmt(introduced)} | {fmt(final[str(stage)])} |")
    lines += ["", f"{result['steps']:,} optimizer updates; {result['examples']:,} example exposures; {result['nonpadding_tokens']:,} nonpadding tokens.",
              f"Training process: {result['wall_seconds']:.1f}s wall, {result['cpu_seconds']:.1f}s CPU; peak RSS {result['peak_process_rss_bytes']/2**20:.1f} MiB. Semantic preparation: {result['semantic_preparation_seconds']:.1f}s, accounted separately.",
              "", "The semantic graph freezes 68 identities with type signatures, roles, inverses, binding, composition, proof rules and evidence distinctions. SHA-256 keyed feature coordinates are row-local; appending a node leaves old rows and IDs exact. All neural weights are scratch initialized. Helper calls and external helper spend were zero.",
              "", "Familiar examples overlap the training pools. Varied and composite inputs are excluded from every training pool; varied worlds have 4–5 entities while training uses 2–4. Composite readouts add new nesting. These are authored development readouts, not a sealed benchmark or evidence of general reasoning.",
              "", "Proof means finite Horn-rule closure and candidate countermodel satisfaction. Evidence reports remain separate from closed-world facts: no report is UNKNOWN; explicit refutation is FALSE; support and refutation is CONFLICT; divergent live interpretation outcomes are AMBIGUOUS. Boolean operations retain their original identities; evidence operations use separate identities.",
              "", "## Real neural demonstrations", "", "All answers below come from the trained transformer. The complete inputs, logits, per-stage scores, successes and mistakes are retained in [gallery.json](run-01/gallery.json) and the checkpoint readouts.", "",
              "| Universe | Input / perturbation | Gold | At introduction | After U4 |", "| --- | --- | --- | --- | --- |"]
    for d in demos:
        lines.append(f"| U{d['stage']} | `{d['formal']}` | {d['gold']} | {d['at_introduction']['prediction']} | {d['final']['prediction']} |")
    lines += ["", "## Retained mistakes", "", "Examples below are deterministic first mistakes from the final varied readouts. The gallery also preserves composite failures and successful answers.", ""]
    for stage in range(5):
        mistakes = [p for p in selected if p["stage"] == stage and p["split"] == "varied" and p["prediction"] != p["gold"]][:1]
        for p in mistakes:
            lines.append(f"- U{stage}: `{p['formal']}` — neural {p['prediction']}; oracle {p['gold']}.")
    replay_receipt = read_json(run / "replay.json")
    lines += ["", "## Reproduction and evidence", "", f"Fresh-process replay: {replay_receipt['predictions']:,} predictions; maximum absolute logit/probability error {replay_receipt['max_absolute_error']}; optimizer/checkpoint lineage and all exposures verified.",
              "", "[Freeze](run-01/freeze.json), [initializer](run-01/initializer.json), [stage and exposure result](run-01/result.json), [replay](run-01/replay.json), [pre-training encoded examples](run-01/samples.json), [handoff](../../micro-universes/HANDOFF.md).", "",
              "No random/permuted controls, ablations, helper qualification, SYS-01 experiment, pretrained transfer or merge was performed. #107 and all earlier evidence are preserved."]
    report_path = run.parent / "RESULTS.md"
    with report_path.open("x") as stream:
        stream.write("\n".join(lines) + "\n")
    checksums = {p.name: file_hash(p) for p in sorted(run.iterdir()) if p.is_file() and p.name != "CHECKSUMS.sha256"}
    with (run / "CHECKSUMS.sha256").open("x") as stream:
        stream.write("".join(f"{h}  {name}\n" for name, h in checksums.items()))
    return {"results": str(report_path), "gallery": str(run / "gallery.json"), "files_hashed": len(checksums)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    freezing = commands.add_parser("freeze")
    freezing.add_argument("--out", type=Path, required=True)
    freezing.add_argument("--config", type=Path)
    for command in ("train", "replay", "report"):
        commands.add_parser(command).add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    result = freeze(read_json(args.config) if args.config else default_config(), args.out) if args.command == "freeze" else {"train": train, "replay": replay, "report": report}[args.command](args.run)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
