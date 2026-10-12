"""One frozen exploratory cycle, text evidence, and fresh-process verification."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random
import resource
import subprocess
import sys
import time

import torch
from torch.nn import functional as F

from bilqis_ref.model import ModelConfig, batch, state_hash
from . import ROOT, VERSION
from .codec import encode, token_manifest
from .data import composition, frozen_corpus, known_cases
from .features import feature_map, tensor_hash
from .model import initialize, load_checkpoint, predict, save_checkpoint
from .semantics import LABELS, digest, registry


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def metrics(rows):
    by_class = {}
    for label in LABELS:
        group = [r for r in rows if r["expected"] == label]
        by_class[label] = {"n": len(group), "correct": sum(r["correct"] for r in group),
                           "accuracy": sum(r["correct"] for r in group) / len(group) if group else None}
    present = [v["accuracy"] for v in by_class.values() if v["accuracy"] is not None]
    by_pattern = {}
    for pattern in sorted({r["pattern"] for r in rows}):
        group = [r for r in rows if r["pattern"] == pattern]
        by_pattern[pattern] = {"n": len(group), "correct": sum(r["correct"] for r in group)}
    return {"n": len(rows), "correct": sum(r["correct"] for r in rows),
            "accuracy": sum(r["correct"] for r in rows) / len(rows) if rows else None,
            "macro_accuracy": sum(present) / len(present) if present else None,
            "by_class": by_class, "by_pattern": by_pattern,
            "confusion": {a: dict(Counter(r["prediction"] for r in rows if r["expected"] == a)) for a in LABELS}}


def evaluate_rows(model, cases):
    result = []
    for start in range(0, len(cases), 64):
        part = cases[start:start + 64]
        predictions = predict(model, [r["semantic"] for r in part])
        for r, prediction in zip(part, predictions):
            result.append({"id": r["id"], "split": r.get("split", "KNOWN"),
                           "pattern": r.get("pattern", composition(r["semantic"]["query"])),
                           "semantic_sha256": digest(r["semantic"]), "expected": r["expected"],
                           **prediction, "correct": r["expected"] == prediction["prediction"]})
    return result


def source_identity():
    tracked = list((ROOT / "bilqis_alpha").glob("*.py")) + [ROOT / "bilqis_ref/model.py",
              ROOT / "configs/alpha-01.json", ROOT / "requirements-alpha.txt",
              ROOT / "schemas/alpha-semantic.schema.json"] + list((ROOT / "fixtures/alpha").glob("*.json"))
    git = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    return {"commit": git, "working_tree_dirty": bool(dirty),
            "files": {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(tracked)},
            "version": VERSION}


def environment():
    def sysctl(name):
        if sys.platform != "darwin":
            return None
        p = subprocess.run(["sysctl", "-n", name], capture_output=True, text=True)
        return p.stdout.strip() if p.returncode == 0 else None
    return {"python": sys.version, "torch": str(torch.__version__), "platform": platform.platform(),
            "machine": platform.machine(), "chip": sysctl("machdep.cpu.brand_string"),
            "physical_memory_bytes": sysctl("hw.memsize"), "backend": "cpu", "threads": 1,
            "device": "CPU FP32; no Apple-GPU/native-low-bit qualification",
            "mps_available": torch.backends.mps.is_available(),
            "dependency_freeze": subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
                                  if __import__("importlib.util").util.find_spec("pip") else "uv-managed environment; see dependency-lock.txt"}


def train(output: Path):
    config = json.loads((ROOT / "configs/alpha-01.json").read_text())
    if output.exists():
        raise ValueError("run directory exists; never overwrite an evidence epoch")
    output.parent.mkdir(parents=True, exist_ok=True)
    attempts = output.parent / "attempts.jsonl"
    previous = [json.loads(s) for s in attempts.read_text().splitlines()] if attempts.exists() else []
    same_epoch = [r for r in previous if r["event"] == "started" and r["config_sha256"] == digest(config)]
    if len(same_epoch) >= config["attempt_limit"]:
        raise ValueError("bounded alpha attempt limit exhausted")
    if same_epoch:
        raise ValueError("second attempt requires an explicit diagnosed repair recorded before execution")
    output.mkdir()
    with attempts.open("a") as f:
        f.write(json.dumps({"event": "started", "output": str(output.resolve()), "config_sha256": digest(config)}) + "\n")
    started, cpu_start = time.perf_counter(), time.process_time()
    try:
        corpus = frozen_corpus()
        # Freeze all inputs before optimizer creation, without evaluating heldout predictions.
        write_json(output / "split-manifest.json", corpus["split_manifest"])
        write_json(output / "config.json", config)
        c = ModelConfig(vocab_size=len(token_manifest()["tokens"]), **config["architecture"])
        model, initializer = initialize(c, config["seed"], config["initialization"])
        write_json(output / "initializer.json", initializer)
        write_json(output / "features.json", feature_map()[2])
        write_json(output / "token-manifest.json", token_manifest())
        write_json(output / "semantic-registry.json", registry())
        original = {k: v.detach().clone() for k, v in model.state_dict().items()}
        initial_hash = state_hash(model)
        source = source_identity()
        env = environment()
        write_json(output / "pre-step.json", {"source": source, "environment": env,
                   "state_sha256": initial_hash, "embedding_sha256": tensor_hash(model.embedding.weight),
                   "initializer_sha256": digest(initializer), "config_sha256": digest(config),
                   "split_sha256": digest(corpus["split_manifest"]), "heldout_predictions_examined": False})
        save_checkpoint(output / "initial.pt", model, initializer, {"step": 0, "trained": False})
        training = [r for r in corpus["cases"] if r["split"] == "TRAIN"]
        dev = [r for r in corpus["cases"] if r["split"] == "DEV"]
        known = known_cases()
        first_stage = [r for r in training if r["pattern"] in ("RELATION", "EQUAL", "NOT(RELATION)")]
        encoded = {r["id"]: encode(r["semantic"]) for r in training}
        if max(map(len, encoded.values())) > c.context:
            raise ValueError("frozen corpus exceeds model context")
        optimizer = torch.optim.AdamW(model.parameters(), lr=config["optimizer"]["learning_rate"],
                                      weight_decay=config["optimizer"]["weight_decay"], foreach=False)
        rng = random.Random(config["seed"])
        trajectory = []

        def probe(step, loss):
            rows = evaluate_rows(model, dev)
            smoke = evaluate_rows(model, known)
            train_probe = evaluate_rows(model, training[:128])
            point = {"step": step, "stage": 0 if step <= config["stage_transition_step"] else 1,
                     "loss_window": loss, "DEV": metrics(rows), "TRAIN_probe": metrics(train_probe),
                     "KNOWN": metrics(smoke), "known_rows": smoke,
                     "state_sha256": state_hash(model), "wall_seconds": time.perf_counter() - started}
            trajectory.append(point)
            with (output / "trajectory.jsonl").open("a") as f:
                f.write(json.dumps(point, allow_nan=False) + "\n")
            print(f"step={step} DEV={point['DEV']['correct']}/{point['DEV']['n']} known={point['KNOWN']['correct']}/{point['KNOWN']['n']} loss={loss}", flush=True)

        probe(0, None)
        exposures = tokens = padded = 0
        losses = []
        for step in range(1, config["steps"] + 1):
            pool = first_stage if step <= config["stage_transition_step"] else training
            chosen = rng.sample(pool, config["batch_size"])
            sequences = [encoded[r["id"]] for r in chosen]
            x, lengths = batch(sequences)
            y = torch.tensor([LABELS.index(r["expected"]) for r in chosen])
            model.train()
            optimizer.zero_grad()
            loss = F.cross_entropy(model(x, lengths), y)
            if not bool(torch.isfinite(loss)):
                raise ValueError("nonfinite training loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
            optimizer.step()
            exposures += len(chosen); tokens += int(lengths.sum()); padded += x.numel()
            losses.append(float(loss.detach()))
            if step % config["probe_every"] == 0:
                probe(step, sum(losses) / len(losses)); losses.clear()
            if step == config["stage_transition_step"]:
                save_checkpoint(output / "stage-0.pt", model, initializer, {"step": step, "trained": True}, optimizer=optimizer)
        changed = {k: float((v - original[k]).double().square().sum().sqrt()) for k, v in model.state_dict().items()
                   if not torch.equal(v, original[k])}
        if not changed or state_hash(model) == initial_hash:
            raise ValueError("optimizer did not change trainable parameters")
        save_checkpoint(output / "model.pt", model, initializer,
                        {"step": config["steps"], "trained": True, "split_sha256": digest(corpus["split_manifest"])}, optimizer=optimizer)
        # Evaluate actual saved parameters, and only now obtain HELDOUT predictions.
        loaded, payload = load_checkpoint(output / "model.pt")
        rows = evaluate_rows(loaded, corpus["cases"] + known)
        baseline, _ = load_checkpoint(output / "initial.pt")
        baseline_rows = evaluate_rows(baseline, corpus["cases"] + known)
        for name, values in (("predictions.jsonl", rows), ("baseline-predictions.jsonl", baseline_rows)):
            (output / name).write_text("".join(json.dumps(r, allow_nan=False) + "\n" for r in values))
        scores = {k: metrics([r for r in rows if r["split"] == k]) for k in ("TRAIN", "DEV", "HELDOUT", "KNOWN")}
        baseline_scores = {k: metrics([r for r in baseline_rows if r["split"] == k]) for k in scores}
        learns = (scores["TRAIN"]["accuracy"] > baseline_scores["TRAIN"]["accuracy"]
                  and trajectory[-1]["loss_window"] < trajectory[1]["loss_window"])
        heldout_signal = (scores["HELDOUT"]["macro_accuracy"] > baseline_scores["HELDOUT"]["macro_accuracy"]
                          and scores["HELDOUT"]["correct"] > 0)
        # Operational exploratory classification, no invented confirmatory threshold.
        status = "ALPHA_DEMO_REPRODUCED" if learns and heldout_signal else (
                 "ALPHA_LEARNS_BUT_GENERALIZATION_UNPROVEN" if learns else "ALPHA_LEARNING_FAILED")
        failures = [r for r in rows if not r["correct"]]
        write_json(output / "failures.json", {"all_failed_case_ids": [r["id"] for r in failures],
                   "failed_known": [r for r in failures if r["split"] == "KNOWN"],
                   "failure_inventory": dict(Counter(f"{r['split']}:{r['expected']}->{r['prediction']}" for r in failures)),
                   "missing": ["cold human oracle review", "sealed independent generator", "causal initializer/representation controls", "MPS parity", "native low-bit kernel", "full T0-T4/Rosetta/mathematics"]})
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result = {"epoch": config["epoch"], "terminal_state": status, "source": source,
                  "environment": env, "config": config, "architecture": asdict(c),
                  "trainable_parameters": sum(p.numel() for p in model.parameters()),
                  "embedding_parameters": model.embedding.weight.numel(), "steps": config["steps"],
                  "semantic_manifest_sha256": digest(registry()), "token_abi_sha256": digest(token_manifest()),
                  "initializer_manifest_sha256": digest(initializer), "split_manifest_sha256": digest(corpus["split_manifest"]),
                  "initial_state_sha256": initial_hash, "final_state_sha256": payload["state_sha256"],
                  "checkpoint_file_sha256": file_hash(output / "model.pt"), "changed_parameters_l2": changed,
                  "resources": {"training_examples": exposures, "training_nonpadding_tokens": tokens,
                                "training_padded_tokens": padded, "wall_seconds": time.perf_counter() - started,
                                "cpu_seconds": time.process_time() - cpu_start,
                                "peak_process_rss_bytes": int(rss if sys.platform == "darwin" else rss * 1024),
                                "energy_joules": None, "developer_tokens": None, "paid_compute": False},
                  "scores": scores, "untrained_baseline_scores": baseline_scores,
                  "classification_basis": {"training_improved": learns, "heldout_macro_improved": heldout_signal,
                     "rule": "replayable checkpoint plus observed learning and informative heldout response; exploratory only"},
                  "limitations": "one seed, four withheld AST shapes over same two-object micro-domain; not broad semantic generalization or SYS-01",
                  "failed_training_attempts": [], "unsupported": registry()["omissions"]}
        write_json(output / "run.json", result)
        artifacts = {p.name: file_hash(p) for p in sorted(output.iterdir()) if p.is_file()}
        write_json(output / "artifact-checksums.json", artifacts)
        with attempts.open("a") as f:
            f.write(json.dumps({"event": "completed", "output": str(output.resolve()), "config_sha256": digest(config), "terminal_state": status}) + "\n")
        print(json.dumps({"terminal_state": status, "scores": {k: {"correct": v["correct"], "n": v["n"]} for k, v in scores.items()},
                          "checkpoint_sha256": result["checkpoint_file_sha256"], "resources": result["resources"]}), flush=True)
        return result
    except Exception as error:
        write_json(output / "blocked.json", {"terminal_state": "ALPHA_HARNESS_BLOCKED", "error": repr(error),
                    "wall_seconds": time.perf_counter() - started})
        with attempts.open("a") as f:
            f.write(json.dumps({"event": "failed", "output": str(output.resolve()), "config_sha256": digest(config), "error": repr(error)}) + "\n")
        raise


def verify(output: Path):
    run = json.loads((output / "run.json").read_text())
    for name, expected in json.loads((output / "artifact-checksums.json").read_text()).items():
        if file_hash(output / name) != expected:
            raise ValueError("artifact hash: " + name)
    for path, expected in run["source"]["files"].items():
        if file_hash(ROOT / path) != expected:
            raise ValueError("source drift: " + path)
    corpus = frozen_corpus()
    if digest(corpus["split_manifest"]) != run["split_manifest_sha256"]:
        raise ValueError("split binding")
    model, payload = load_checkpoint(output / "model.pt")
    if payload["state_sha256"] != run["final_state_sha256"] or file_hash(output / "model.pt") != run["checkpoint_file_sha256"]:
        raise ValueError("checkpoint receipt binding")
    expected = [json.loads(line) for line in (output / "predictions.jsonl").read_text().splitlines()]
    actual = evaluate_rows(model, corpus["cases"] + known_cases())
    if len(actual) != len(expected):
        raise ValueError("prediction cardinality")
    for a, b in zip(actual, expected):
        if any(a[k] != b[k] for k in ("id", "expected", "prediction", "correct", "semantic_sha256")):
            raise ValueError("prediction replay: " + a["id"])
        torch.testing.assert_close(torch.tensor(a["logits"]), torch.tensor(b["logits"]), atol=1e-6, rtol=0)
    print(json.dumps({"verified_rows": len(actual), "checkpoint_sha256": run["checkpoint_file_sha256"],
                      "fresh_process_inference": True, "logit_tolerance": {"atol": 1e-6, "rtol": 0}}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("train", "verify"):
        p = sub.add_parser(name); p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "train":
        train(args.output.resolve())
    else:
        verify(args.output.resolve())


if __name__ == "__main__":
    main()
