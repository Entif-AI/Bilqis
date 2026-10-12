"""Source-frozen matched e9 semantic-grouping and retention-rehearsal experiment.

No Kev, no conversational history or pretrained student. All decisions that
affect a stage's training are made before that stage's sealed gate is opened.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess

import torch

from bilqis_ref.model import state_hash
from .controller_v6 import (ARMS, BLOCK_UPDATES, SEEDS, STEPS_PER_STAGE,
                            VERSION as CONTROLLER_VERSION, evaluate_panel,
                            ledger, optimizer_digest, predictions, score,
                            train_block, training_batches, optimizer_steps)
from .curriculum_v6 import (DEPENDENCIES, EXPRESSIONS, RELATIONS, STAGES,
                            VERSION as COURSE_VERSION, depth, signature, rows, split,
                            validate)
from .semantics import equivalent
from .student_v3 import initialize, save_checkpoint, load_checkpoint

VERSION = "bilqis.formal.pilot/v0.6.0"
OUT_NAME = "formal-foundations-20261012-e9-semantic-v06"
SOURCE_FILES = (
    "bilqis_ref/model.py", "bilqis_ref/codec.py", "bilqis_ref/semantics.py",
    "bilqis_formal/semantics.py",
    "bilqis_formal/course_v3.py", "bilqis_formal/dialogue.py",
    "bilqis_formal/dialogue_v3.py", "bilqis_formal/student_v3.py",
    "bilqis_formal/curriculum_v6.py", "bilqis_formal/controller_v6.py",
    "bilqis_formal/pilot_v6.py", "tests/test_formal_semantic_v6.py",
    "docs/formal/SEMANTIC_V06_PROTOCOL.md",
)
ROOT = Path(__file__).resolve().parent.parent


def locked_source_sha():
    digest = hashlib.sha256()
    for filename in SOURCE_FILES:
        data = (ROOT / filename).read_bytes()
        digest.update(filename.encode() + b"\0" + str(len(data)).encode() + b"\0" + data)
    return digest.hexdigest()


def _git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def attest_source(commit):
    """Every source/protocol/test must be committed before first gradient."""
    for filename in SOURCE_FILES:
        if not (ROOT / filename).is_file():
            raise ValueError("V06_MISSING_FROZEN_SOURCE")
        tracked = _git("ls-files", "--error-unmatch", "--", filename)
        if filename.encode() not in tracked:
            raise ValueError("V06_UNTRACKED_SOURCE")
        committed = _git("show", f"{commit}:{filename}")
        if committed != (ROOT / filename).read_bytes():
            raise ValueError("V06_SOURCE_NOT_ATTESTED")
    return True


def write_new(path, payload):
    """A partial file survives a crash without masquerading as a final JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, sort_keys=True, indent=2, allow_nan=False).encode() + b"\n"
    tmp = path.with_name(path.name + ".partial")
    with tmp.open("xb") as file:
        file.write(data)
        file.flush()
        os.fsync(file.fileno())
    if path.exists():
        raise FileExistsError(str(path))
    os.replace(tmp, path)


def _same(a, b):
    return json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(
        b, sort_keys=True, allow_nan=False)


def _semantic_pairs(preds):
    """Read-only paired success on equivalent held-out formula shapes."""
    items = [(p["input"]["expression"], p["input"]["valuation"],
              p["prediction"] == p["gold"]) for p in preds]
    matched = both = 0
    for i, (a, env_a, correct_a) in enumerate(items):
        for b, env_b, correct_b in items[i + 1:]:
            if env_a == env_b and a != b and equivalent(a, b):
                matched += 1
                both += int(correct_a and correct_b)
    return {"both_correct": both, "pairs": matched}


def _gate_score(model, stage):
    gate_rows = rows(stage, "gate")
    pred = predictions(model, gate_rows)
    return {"accuracy": score(pred),
            "true": score([p for p in pred if p["gold"] == "ATOM.TRUE"]),
            "false": score([p for p in pred if p["gold"] == "ATOM.FALSE"]),
            "pairs": _semantic_pairs(pred),
            "by_depth": {str(d): score([p for p in pred if depth(
                p["input"]["expression"]) == d]) for d in sorted({depth(
                r["input"]["expression"]) for r in gate_rows})},
            "items": {p["id"]: p["prediction"] == p["gold"] for p in pred}}


def _formative(model, stage, exposed):
    return {"current": evaluate_panel(model, rows(stage, "dev")),
            "previous": {name: evaluate_panel(model, rows(name, "dev"))
                         for name in exposed}}


def _arm_one(folder, *, seed, arm, source_sha):
    folder.mkdir(parents=True, exist_ok=False)
    model, initializer = initialize(seed=seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.002, betas=(.9, .95),
                                  eps=1e-8, weight_decay=.01)
    accepted, exposed, stages, skipped = [], [], [], []
    status = "ALL_ELIGIBLE_STAGES_ATTEMPTED"
    for stage_index, stage in enumerate(STAGES):
        missing = [d for d in DEPENDENCIES[stage] if d not in accepted]
        if missing:
            skipped.append({"stage": stage, "reason": "UNMET_SEALED_PREREQUISITE",
                            "dependencies": missing})
            continue
        stage_number = len(stages) + 1
        before = state_hash(model)
        prior = tuple(exposed)
        blocks = []
        for block_number in range(STEPS_PER_STAGE // BLOCK_UPDATES):
            receipt = train_block(model, optimizer, seed=seed, stage=stage,
                                  block=block_number, arm=arm, prior=prior)
            receipt.update({"block": block_number + 1,
                            "after_sha256": state_hash(model),
                            "formative": _formative(model, stage, exposed)})
            expected_steps = STEPS_PER_STAGE * len(stages) + (
                block_number + 1) * BLOCK_UPDATES
            if optimizer_steps(optimizer) != {expected_steps}:
                raise ValueError("V06_WRONG_OPTIMIZER_STEP_COUNT")
            save_checkpoint(folder / f"stage-{stage_number:02d}-block-"
                            f"{block_number+1:02d}.pt", model, optimizer,
                            stage, None, initializer)
            blocks.append(receipt)
        # IMPORTANT: this is the first access to this stage's SEALED rows.
        current_gate = _gate_score(model, stage)
        old_gates = {previous: _gate_score(model, previous) for previous in accepted}
        old_gates_healthy = all(v["accuracy"]["correct"] == v["accuracy"]["n"]
                                for v in old_gates.values())
        promoted = (current_gate["accuracy"]["correct"] ==
                    current_gate["accuracy"]["n"] and old_gates_healthy)
        entry = {"stage": stage, "stage_number": stage_number,
                 "updates": STEPS_PER_STAGE, "before_sha256": before,
                 "after_sha256": state_hash(model),
                 "optimizer_sha256": optimizer_digest(optimizer.state_dict()),
                 "prior_exposure": list(prior), "blocks": blocks,
                 "sealed_current": current_gate, "sealed_retention": old_gates,
                 "promoted": promoted}
        save_checkpoint(folder / f"stage-{stage_number:02d}.pt", model,
                        optimizer, stage, current_gate["accuracy"], initializer)
        write_new(folder / f"stage-{stage_number:02d}.json", entry)
        stages.append(entry)
        exposed.append(stage)
        if promoted:
            accepted.append(stage)
        print(f"seed={seed} arm={arm} stage={stage}: "
              f"gate={current_gate['accuracy']['correct']}/"
              f"{current_gate['accuracy']['n']} retained={old_gates_healthy} "
              f"promoted={promoted}", flush=True)
        if not old_gates_healthy:
            status = "PRIOR_SEALED_RETENTION_FAILURE_STOP"
            skipped.extend({"stage": later, "reason": "PRIOR_SEALED_RETENTION_FAILURE"}
                           for later in STAGES[stage_index + 1:])
            break
    if locked_source_sha() != source_sha:
        raise ValueError("V06_SOURCE_MUTATED_DURING_RUN")
    report = {"version": VERSION, "seed": seed, "arm": arm,
              "initializer": initializer, "source_sha256": source_sha,
              "accepted": accepted, "exposed": exposed, "skipped": skipped,
              "status": status, "updates": STEPS_PER_STAGE * len(stages),
              "stage_count": len(stages), "history_exposures": 0,
              "kev_calls": 0, "final_state_sha256": state_hash(model),
              "stage_summaries": [{k: item[k] for k in (
                  "stage", "updates", "sealed_current", "sealed_retention",
                  "promoted")} for item in stages]}
    write_new(folder / "report.json", report)
    return report


def _prereg(sha, commit):
    return {"version": VERSION, "controller": CONTROLLER_VERSION,
            "course": COURSE_VERSION, "source_sha256": sha,
            "source_commit": commit, "sources": list(SOURCE_FILES),
            "seeds": list(SEEDS), "arms": {k: list(v) for k, v in ARMS.items()},
            "stages": list(STAGES), "dependencies": DEPENDENCIES,
            "block": BLOCK_UPDATES, "updates_per_stage": STEPS_PER_STAGE,
            "batch_size": 32, "no_history": True, "no_kev": True,
            "no_retries": True, "no_heldout_adaptation": True,
            "paired_row_multisets": "exact per seed, stage, prior-exposure, rehearsal-dose and block",
            "curriculum_rows": {name: {kind: [r["id"] for r in rows]
                                       for kind, rows in split(name).items()}
                                for name in STAGES},
            "expression_signatures": {name: {
                role: [{"expression": expr, "truth_signature": signature(expr)}
                       for expr in exprs]
                for role, exprs in EXPRESSIONS[name].items()}
                for name in STAGES},
            "oracle_relations": [list(pair) for pair in RELATIONS],
            "runtime": {"python": platform.python_version(),
                        "torch": torch.__version__, "machine": platform.machine()},
            "interpretation": "Order/organization and retention-dose feasibility; exploratory, not general logical mastery"}


def _aggregate(reports, prereg):
    by_seed = {}
    for seed in SEEDS:
        by_seed[str(seed)] = {
            arm: {"updates": item["updates"], "accepted": item["accepted"],
                  "current_gate": {stage["stage"]: stage["sealed_current"]["accuracy"]
                                   for stage in item["stage_summaries"]},
                  "final_retained_all": set(item["accepted"]) == set(STAGES)}
            for arm in ARMS
            for item in reports if item["seed"] == seed and item["arm"] == arm}
    return {"version": VERSION, "source_sha256": prereg["source_sha256"],
            "comparisons": {"uniform8_vs_semantic8": "same rows/block",
                            "uniform8_vs_sham8": "same rows/block",
                            "uniform16_vs_semantic16": "same rows/block",
                            "eight_vs_sixteen": "rehearsal-dose difference, not fixed-row matched"},
            "by_seed": by_seed,
            "reports": reports,
            "limitations": ["5 exploratory seeds, no population-effect claim",
                            "historical expressions may have appeared in e7/e8",
                            "the tiny finite Boolean grammar constrains novelty",
                            "sealed scores govern prerequisites, never current-stage scheduling",
                            "block checkpoint replay does not recompute historical gradients",
                            "different gate outcomes can yield different stage attempts"]}


def run(out):
    if out.resolve() != (ROOT / "runs" / OUT_NAME).resolve():
        raise ValueError("V06_WRONG_OUTPUT_PATH")
    if out.exists():
        raise FileExistsError(str(out))
    if _git("status", "--porcelain=v1").strip():
        raise ValueError("V06_REQUIRES_CLEAN_COMMITTED_SOURCE")
    if not validate():
        raise ValueError("V06_INVALID_CURRICULUM")
    sha = locked_source_sha()
    head = _git("rev-parse", "HEAD").decode().strip()
    attest_source(head)
    out.mkdir(parents=True, exist_ok=False)
    try:
        prereg = _prereg(sha, head)
        write_new(out / "preregistration.json", prereg)
        reports = []
        for seed in SEEDS:
            for arm in ARMS:
                reports.append(_arm_one(out / f"seed-{seed}-{arm}",
                                        seed=seed, arm=arm, source_sha=sha))
        result = _aggregate(reports, prereg)
        write_new(out / "comparison.json", result)
        return result
    except BaseException as error:
        write_new(out / "abort.json", {"type": type(error).__name__,
                                      "message": str(error),
                                      "source_sha256": sha, "source_commit": head})
        raise


def replay(out):
    prereg = json.loads((out / "preregistration.json").read_text())
    expected_prereg = _prereg(locked_source_sha(), prereg["source_commit"])
    if any(not _same(prereg.get(k), v)
           for k, v in expected_prereg.items() if k != "runtime"):
        raise ValueError("V06_PREREGISTRATION_DRIFT")
    attest_source(prereg["source_commit"])
    if (out / "abort.json").exists() or list(out.rglob("*.partial")):
        raise ValueError("V06_INCOMPLETE_OR_ABORTED_RUN")
    reports = []
    for seed in SEEDS:
        for arm in ARMS:
            folder = out / f"seed-{seed}-{arm}"
            report = json.loads((folder / "report.json").read_text())
            if (report["seed"] != seed or report["arm"] != arm or
                report["source_sha256"] != prereg["source_sha256"] or
                report["history_exposures"] or report["kev_calls"]):
                raise ValueError("V06_FORGED_REPORT_IDENTITY")
            accepted, exposed, expected_skips, expected_summaries = [], [], [], []
            expected_before = report["initializer"]["initial_sha256"]
            halted = False
            for stage in STAGES:
                missing = [d for d in DEPENDENCIES[stage] if d not in accepted]
                if halted:
                    expected_skips.append({"stage": stage,
                                           "reason": "PRIOR_SEALED_RETENTION_FAILURE"})
                    continue
                if missing:
                    expected_skips.append({"stage": stage,
                                           "reason": "UNMET_SEALED_PREREQUISITE",
                                           "dependencies": missing})
                    continue
                n = len(exposed) + 1
                entry = json.loads((folder / f"stage-{n:02d}.json").read_text())
                if (entry["stage"] != stage or entry["stage_number"] != n or
                    entry["updates"] != STEPS_PER_STAGE or
                    entry["prior_exposure"] != exposed or
                    len(entry["blocks"]) != STEPS_PER_STAGE // BLOCK_UPDATES or
                    entry["before_sha256"] != expected_before):
                    raise ValueError("V06_STAGE_ORDER_OR_ACCOUNTING")
                for block_index, block in enumerate(entry["blocks"]):
                    expected = ledger(training_batches(seed=seed, stage=stage,
                        block=block_index, arm=arm, prior=tuple(exposed)), stage=stage)
                    if any(block.get(key) != value for key, value in expected.items()):
                        raise ValueError("V06_TRAINING_EXPOSURE_REPLAY_MISMATCH")
                    checkpoint, raw = load_checkpoint(
                        folder / f"stage-{n:02d}-block-{block_index+1:02d}.pt")
                    expected_step = STEPS_PER_STAGE * len(exposed) + (
                        block_index + 1) * BLOCK_UPDATES
                    raw_optimizer = torch.optim.AdamW(checkpoint.parameters())
                    raw_optimizer.load_state_dict(raw["optimizer"])
                    if (state_hash(checkpoint) != block["after_sha256"] or
                        optimizer_digest(raw["optimizer"]) != block["optimizer_sha256"] or
                        raw["stage"] != stage or
                        optimizer_steps(raw_optimizer) != {expected_step}):
                        raise ValueError("V06_BLOCK_CHECKPOINT_MISMATCH")
                    if not _same(_formative(checkpoint, stage, exposed), block["formative"]):
                        raise ValueError("V06_BLOCK_DEV_REPLAY_MISMATCH")
                model, state = load_checkpoint(folder / f"stage-{n:02d}.pt")
                final_opt = torch.optim.AdamW(model.parameters())
                final_opt.load_state_dict(state["optimizer"])
                if (state_hash(model) != entry["after_sha256"] or
                    optimizer_digest(state["optimizer"]) != entry["optimizer_sha256"] or
                    state_hash(model) != entry["blocks"][-1]["after_sha256"] or
                    optimizer_steps(final_opt) != {STEPS_PER_STAGE * n}):
                    raise ValueError("V06_FINAL_STATE_REPLAY_MISMATCH")
                # All gate reads are independent of the recorded sealed scores.
                if (not _same(_gate_score(model, stage), entry["sealed_current"]) or
                    not _same({x: _gate_score(model, x) for x in accepted},
                              entry["sealed_retention"])):
                    raise ValueError("V06_SEALED_EVIDENCE_MISMATCH")
                retained = all(v["accuracy"]["correct"] == v["accuracy"]["n"]
                               for v in entry["sealed_retention"].values())
                promoted = (entry["sealed_current"]["accuracy"]["correct"] ==
                            entry["sealed_current"]["accuracy"]["n"] and retained)
                if promoted != entry["promoted"]:
                    raise ValueError("V06_PROMOTION_REPLAY_MISMATCH")
                exposed.append(stage)
                expected_before = entry["after_sha256"]
                if promoted:
                    accepted.append(stage)
                expected_summaries.append({k: entry[k] for k in (
                    "stage", "updates", "sealed_current", "sealed_retention", "promoted")})
                if not retained:
                    halted = True
            if (accepted != report["accepted"] or exposed != report["exposed"] or
                report["updates"] != STEPS_PER_STAGE * len(exposed) or
                report["stage_count"] != len(exposed) or
                expected_skips != report["skipped"] or
                expected_summaries != report["stage_summaries"] or
                report["final_state_sha256"] != expected_before or
                report["status"] != ("PRIOR_SEALED_RETENTION_FAILURE_STOP" if halted
                                      else "ALL_ELIGIBLE_STAGES_ATTEMPTED") or
                len(list(folder.glob("stage-*.json"))) != len(exposed) or
                len(list(folder.glob("stage-*.pt"))) !=
                    len(exposed) * (1 + STEPS_PER_STAGE // BLOCK_UPDATES)):
                raise ValueError("V06_REPORT_AGGREGATE_MISMATCH")
            reports.append(report)
    expected = _aggregate(reports, prereg)
    actual = json.loads((out / "comparison.json").read_text())
    if not _same(actual, expected):
        raise ValueError("V06_COMPARISON_REPLAY_MISMATCH")
    return {"status": "CHECKPOINT_REPLAY_PASSED", "arms": len(reports),
            "source_sha256": prereg["source_sha256"],
            "updates": sum(r["updates"] for r in reports)}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "runs" / OUT_NAME))
    parser.add_argument("--replay", action="store_true")
    options = parser.parse_args()
    outcome = replay(Path(options.out)) if options.replay else run(Path(options.out))
    print(json.dumps({"status": "OK", "version": VERSION,
                      "source_sha256": outcome["source_sha256"],
                      "replay": options.replay}, sort_keys=True))


if __name__ == "__main__":
    main()
