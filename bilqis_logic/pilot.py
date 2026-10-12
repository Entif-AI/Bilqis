"""Freeze -> one fixed A/B training cycle -> fresh-process replay. CPU, offline."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import resource
import subprocess
import time

import torch

from bilqis_ref.model import ModelConfig, batch, state_hash
from .data import VERSION as DATA_VERSION, audit_splits, build_data
from .geometry import feature_map, registry, tensor_hash
from .kernel import canonical, digest, encode, token_manifest
from .model import initialize, load_checkpoint, predict, save_checkpoint

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, obj):
    with path.open("xb") as stream:
        stream.write(canonical(obj) + b"\n")


def read_json(path):
    return json.loads(path.read_bytes())


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    paths = list((ROOT / "bilqis_logic").glob("*.py")) + list((ROOT / "bilqis_ref").glob("*.py"))
    return {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(paths)}


def tensor_hashes(model):
    return {k: tensor_hash(v) for k, v in sorted(model.state_dict().items())}


def validate_config(cfg):
    if (cfg["version"] != "cogal-pilot-0.1.0" or cfg["profile"] != "semantic_aligned"
            or cfg["model"]["precision"] != "fp32" or cfg["batch_size"] != 32
            or cfg["phase_b_primitive_rehearsal"] != 8 or cfg["phase_b_equivalence_examples"] != 12
            or any(type(cfg[k]) is not int or cfg[k] < 1 for k in ("phase_a_steps", "phase_b_steps"))):
        raise ValueError("fixed primary pilot configuration")


def score(model, rows):
    predictions = []
    for start in range(0, len(rows), 32):
        chunk = rows[start:start + 32]
        predictions += [dict(p, id=r["id"], gold=r["gold"], family=r["family"])
                        for r, p in zip(chunk, predict(model, [r["input"] for r in chunk]))]
    correct = sum(p["prediction"] == p["gold"] for p in predictions)
    by_label = {str(v).lower(): {"n": sum(p["gold"] == v for p in predictions),
                                  "correct": sum(p["gold"] == v and p["prediction"] == v for p in predictions)} for v in (False, True)}
    families = {}
    for family in sorted({p["family"] for p in predictions}):
        subset = [p for p in predictions if p["family"] == family]
        families[family] = {"correct": sum(p["prediction"] == p["gold"] for p in subset), "n": len(subset)}
    return {"correct": correct, "n": len(rows), "accuracy": correct / len(rows),
            "by_label": by_label, "by_family": families, "predictions": predictions}


def freeze(cfg, out):
    wall, cpu = time.perf_counter(), time.process_time()
    validate_config(cfg)
    data = build_data()
    splits = audit_splits(data)
    if max(v["max_input_tokens"] for v in splits.values()) > cfg["model"]["context"]:
        raise ValueError("dataset exceeds model context")
    model, initializer = initialize(ModelConfig(**cfg["model"]), cfg["seed"], cfg["profile"])
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {"config.json": cfg, "registry.json": registry(), "features.json": feature_map()[1],
                 "token-abi.json": token_manifest(), "initializer.json": initializer,
                 "data.json": data, "splits.json": {"version": DATA_VERSION, "splits": splits,
                 "isolation": "no exact evaluation input in TRAIN; value/name-erased commutative tree signatures disjoint from TRAIN and DEV; hard-negative primitive endpoints may be familiar"},
                 "provenance.json": {"authority": "unified T0/T1 execution contract, frozen literal truth tables",
                 "contract_sha256": file_hash(ROOT / "docs/logic-t0-t1/CONTRACT.md"),
                 "helpers": [], "helper_inference_calls": 0, "helper_seconds": 0, "helper_external_spend": 0,
                 "pretrained_neural_transfer": False, "english_student_examples": False,
                 "historical_experiments_modified": False}}
    for name, obj in artifacts.items():
        write_json(out / name, obj)
    metadata = {"step": 0, "data_sha256": digest(data), "config_sha256": digest(cfg)}
    save_checkpoint(out / "initial.pt", model, initializer, metadata)
    # Prescheduled step-zero inference is evidence only, never a curriculum/tuning input.
    write_json(out / "step-zero.json", {s: score(model, rows) for s, rows in data.items()})
    hashes = {name: file_hash(out / name) for name in [*artifacts, "initial.pt", "step-zero.json"]}
    receipt = {"version": "cogal-freeze-0.1.0", "created_at_utc": datetime.now(timezone.utc).isoformat(),
               "source_git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "source_hashes": source_hashes(), "artifacts": hashes, "initial_state_sha256": state_hash(model),
               "initial_tensor_hashes": tensor_hashes(model), "parameter_count": sum(p.numel() for p in model.parameters()),
               "architecture": cfg["model"], "semantic_preparation_wall_seconds": time.perf_counter() - wall,
               "semantic_preparation_cpu_seconds": time.process_time() - cpu,
               "environment": {"python": platform.python_version(), "torch": torch.__version__, "platform": platform.platform(),
                               "device": "cpu", "threads": 1, "deterministic_algorithms": True},
               "run_class": "EXPLORATORY", "independent_seal": False,
               "evaluation_policy": "step-zero all planes; Phase A primitives; fixed-budget final all planes; no adaptive decisions"}
    # Final receipt is the freeze commit point. Partial directories are never silently reused.
    write_json(out / "freeze.json", receipt)
    return {"freeze_sha256": file_hash(out / "freeze.json"), "splits": splits,
            "initial_state_sha256": receipt["initial_state_sha256"], "parameter_count": receipt["parameter_count"]}


def verify_freeze(run):
    receipt = read_json(run / "freeze.json")
    if receipt["source_hashes"] != source_hashes():
        raise ValueError("frozen executable source changed")
    for name, expected in receipt["artifacts"].items():
        if file_hash(run / name) != expected:
            raise ValueError("frozen artifact changed: " + name)
    data = read_json(run / "data.json")
    if audit_splits(data) != read_json(run / "splits.json")["splits"]:
        raise ValueError("split binding")
    return receipt, read_json(run / "config.json"), data


def train(run):
    wall, cpu = time.perf_counter(), time.process_time()
    freeze_receipt, cfg, data = verify_freeze(run)
    validate_config(cfg)
    # Opening exclusively prevents an accidental second cycle or overwrite after interruption.
    log = (run / "training.jsonl").open("x")
    model, initial = load_checkpoint(run / "initial.pt")
    if state_hash(model) != freeze_receipt["initial_state_sha256"]:
        raise ValueError("genesis state binding")
    optcfg = cfg["optimizer"]
    optimizer = torch.optim.AdamW(model.parameters(), lr=optcfg["lr"], betas=tuple(optcfg["betas"]),
                                 eps=optcfg["eps"], weight_decay=optcfg["weight_decay"], foreach=False)
    rng = random.Random(cfg["seed"])
    exposures = Counter()
    totals = {"examples": 0, "nonpadding_tokens": 0, "padded_positions": 0}
    cost = {"batch_preparation_seconds": 0., "optimization_seconds": 0., "evaluation_seconds": 0.}
    first_update = None
    phase_a = None
    steps = cfg["phase_a_steps"] + cfg["phase_b_steps"]
    with log:
        for step in range(1, steps + 1):
            t0 = time.perf_counter()
            phase = "A" if step <= cfg["phase_a_steps"] else "B"
            if phase == "A":
                rows = rng.choices(data["TRAIN_A"], k=cfg["batch_size"])
            else:
                rows = (rng.choices(data["TRAIN_A"], k=8) + rng.choices(data["TRAIN_B_EQUIVALENCE"], k=12)
                        + rng.choices(data["TRAIN_B_COMPOSITION"], k=12))
                rng.shuffle(rows)
            inputs, lengths = batch([encode(r["input"]) for r in rows])
            targets = torch.tensor([int(r["gold"]) for r in rows])
            cost["batch_preparation_seconds"] += time.perf_counter() - t0
            model.train()
            optimizer.zero_grad(set_to_none=True)
            t0 = time.perf_counter()
            before = state_hash(model) if step == 1 else None
            logits = model(inputs, lengths)
            loss = torch.nn.functional.cross_entropy(logits, targets)
            if not bool(torch.isfinite(loss)):
                raise ValueError("nonfinite loss")
            loss.backward()
            gradient = float(torch.nn.utils.clip_grad_norm_(model.parameters(), optcfg["clip_norm"]))
            if not (0 < gradient < float("inf")):
                raise ValueError("zero/nonfinite gradient")
            optimizer.step()
            cost["optimization_seconds"] += time.perf_counter() - t0
            if step == 1:
                after = state_hash(model)
                if before == after:
                    raise ValueError("no neural parameter update")
                first_update = {"before_state_sha256": before, "after_state_sha256": after,
                                "loss": float(loss.detach()), "gradient_norm": gradient,
                                "row_ids": [r["id"] for r in rows]}
                print(json.dumps({"first_genuine_training_step": first_update}), flush=True)
            exposures.update(r["id"] for r in rows)
            totals["examples"] += len(rows)
            totals["nonpadding_tokens"] += int(lengths.sum())
            totals["padded_positions"] += int(inputs.numel())
            log.write(canonical({"step": step, "phase": phase, "loss": float(loss.detach()),
                                 "gradient_norm": gradient, "row_ids": [r["id"] for r in rows],
                                 "tokens": int(lengths.sum()), "padded_positions": int(inputs.numel())}).decode() + "\n")
            if step == cfg["phase_a_steps"]:
                t0 = time.perf_counter()
                phase_a = score(model, data["TRAIN_A"])
                cost["evaluation_seconds"] += time.perf_counter() - t0
                write_json(run / "after-A.json", phase_a)
                save_checkpoint(run / "after-A.pt", model, initial["initializer"], dict(totals, step=step), optimizer)
                print(json.dumps({"phase_A_primitive_correct": phase_a["correct"], "n": phase_a["n"]}), flush=True)
    t0 = time.perf_counter()
    final = {s: score(model, rows) for s, rows in data.items()}
    cost["evaluation_seconds"] += time.perf_counter() - t0
    save_checkpoint(run / "final.pt", model, initial["initializer"], dict(totals, step=steps), optimizer)
    write_json(run / "final-predictions.json", final)
    all_train_ids = {r["id"] for s in data if s.startswith("TRAIN") for r in data[s]}
    if set(exposures) != all_train_ids:
        raise ValueError("training coverage mismatch")
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt = {"version": "cogal-result-0.1.0", "status": "EXPLORATORY_MEASURED",
               "freeze_sha256": file_hash(run / "freeze.json"), "source_git_sha": freeze_receipt["source_git_sha"],
               "steps": steps, "phase_a_steps": cfg["phase_a_steps"], "phase_b_steps": cfg["phase_b_steps"],
               "batch_size": cfg["batch_size"], **totals, "cost": cost,
               "training_process_wall_seconds": time.perf_counter() - wall,
               "training_process_cpu_seconds": time.process_time() - cpu,
               "peak_process_rss_bytes": rss if platform.system() == "Darwin" else rss * 1024,
               "energy_joules": None, "helper_training_seconds": 0, "external_spend": 0,
               "first_update": first_update, "state_sha256": state_hash(model),
               "final_tensor_hashes": tensor_hashes(model), "parameter_count": freeze_receipt["parameter_count"],
               "checkpoint_sha256": {name: file_hash(run / name) for name in ("initial.pt", "after-A.pt", "final.pt")},
               "evidence_sha256": {name: file_hash(run / name) for name in ("training.jsonl", "after-A.json", "final-predictions.json")},
               "exposures_by_row": dict(sorted(exposures.items())),
               "primitive_after_A": {k: v for k, v in phase_a.items() if k != "predictions"},
               "final_scores": {s: {k: v for k, v in scores.items() if k != "predictions"} for s, scores in final.items()},
               "limits": ["one seed, one aligned cycle, no trained control", "developer-authored evaluation; no independent seal",
                          "training equivalence lesson shapes are familiar; HELDOUT uses novel endpoint trees",
                          "FP32 CPU; no claim of ternary efficiency or general semantic intelligence"]}
    write_json(run / "result.json", receipt)
    return {"steps": steps, **totals, "scores": {s: [v["correct"], v["n"]] for s, v in final.items()},
            "final_checkpoint_sha256": receipt["checkpoint_sha256"]["final.pt"],
            "training_process_wall_seconds": receipt["training_process_wall_seconds"]}


def replay(run):
    verify_freeze(run)
    data = read_json(run / "data.json")
    result = read_json(run / "result.json")
    for name, expected in {**result["checkpoint_sha256"], **result["evidence_sha256"]}.items():
        if file_hash(run / name) != expected:
            raise ValueError("trained evidence changed: " + name)
    checks = [("initial.pt", read_json(run / "step-zero.json"), data),
              ("after-A.pt", {"TRAIN_A": read_json(run / "after-A.json")}, {"TRAIN_A": data["TRAIN_A"]}),
              ("final.pt", read_json(run / "final-predictions.json"), data)]
    count, maximum = 0, 0.
    for checkpoint, archived, pools in checks:
        model, _ = load_checkpoint(run / checkpoint)
        for split, rows in pools.items():
            actual = score(model, rows)
            for got, expected in zip(actual["predictions"], archived[split]["predictions"]):
                if got["id"] != expected["id"] or got["prediction"] != expected["prediction"] or got["gold"] != expected["gold"]:
                    raise ValueError("neural prediction replay mismatch")
                delta = max(abs(a - b) for a, b in zip(got["logits"] + got["probabilities"], expected["logits"] + expected["probabilities"]))
                maximum = max(maximum, delta)
                if delta > 1e-6:
                    raise ValueError("neural numerical replay mismatch")
                count += 1
    receipt = {"status": "REPRODUCED", "predictions": count, "max_absolute_error": maximum,
               "atol": 1e-6, "checkpoint_sha256": result["checkpoint_sha256"],
               "final_state_sha256": result["state_sha256"], "freeze_sha256": result["freeze_sha256"]}
    if not (run / "replay.json").exists():
        write_json(run / "replay.json", receipt)
    elif read_json(run / "replay.json") != receipt:
        raise ValueError("replay receipt changed")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    freezing = commands.add_parser("freeze")
    freezing.add_argument("--config", type=Path, required=True)
    freezing.add_argument("--out", type=Path, required=True)
    for command in ("train", "replay"):
        commands.add_parser(command).add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "freeze":
        result = freeze(read_json(args.config), args.out)
    else:
        result = {"train": train, "replay": replay}[args.command](args.run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
