"""Fixed-budget versus adaptive trainee comptroller, source-frozen e8.

Only original three atomic Boolean competencies; J00 and historical dialogue
remain deferred. All state is local, sealed gates determine promotion ONCE,
and no old experiment can be overwritten by this runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

import torch

from bilqis_ref.model import state_hash
from .controller_v5 import (ARMS, BUDGET, SEEDS, accuracy, by_gold, decide_after_block,
                             optimizer_steps, optimizer_digest, run_stage,
                             trained_literal_score, weakest_retained, prior_formative,
                             declined_prior, inspect_progress, dev_summary,
                             training_priorities, sample_ledger)
from .curriculum_v5 import DEPENDENCIES, STAGES, VERSION as COURSE_VERSION, split, validate
from .dialogue_v3 import verify_protocol
from .pilot_v3 import write_new
from .student_v3 import initialize, load_checkpoint, predict, save_checkpoint

VERSION = "bilqis.formal.pilot/v0.5.0"
OUT_NAME = "formal-foundations-20261012-e8-adaptive-v05"
SOURCE_FILES = (
    "bilqis_formal/pilot_v5.py", "bilqis_formal/controller_v5.py",
    "bilqis_formal/curriculum_v5.py", "bilqis_formal/pilot_v4.py",
    "bilqis_formal/course_v3.py", "bilqis_formal/pilot_v3.py",
    "bilqis_formal/student_v3.py", "bilqis_formal/dialogue_v3.py",
    "bilqis_formal/dialogue.py", "bilqis_formal/semantics.py",
    "bilqis_formal/course_v2.py", "bilqis_formal/kev_v3.py",
    "bilqis_formal/kev_v2.py", "bilqis_formal/kev_teacher.py",
    "bilqis_ref/model.py", "bilqis_ref/codec.py", "bilqis_ref/semantics.py",
    "docs/formal/ADAPTIVE_V05_PROTOCOL.md", "tests/test_formal_adaptive_v5.py",
)


def source_sha256():
    root = Path(__file__).resolve().parent.parent
    hasher = hashlib.sha256()
    for path in SOURCE_FILES:
        hasher.update(path.encode() + b"\0")
        hasher.update((root / path).read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


def equal_serialized(a, b):
    """Treat checkpoint expression tuples as their JSON-reported array equivalents."""
    return json.dumps(a, sort_keys=True, separators=(",", ":")) == json.dumps(
        b, sort_keys=True, separators=(",", ":"))


def attest_git_source(root, source_head):
    """Every runtime-locked file must be versioned at the exact source commit."""
    verified = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{source_head}^{{commit}}"],
        cwd=root, text=True).strip()
    if verified != source_head:
        raise ValueError("UNVERIFIABLE_SOURCE_COMMIT")
    for relative in SOURCE_FILES:
        tracked = subprocess.check_output(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=root, text=True).strip()
        if tracked != relative:
            raise ValueError("SOURCE_NOT_TRACKED")
        blob = subprocess.check_output(
            ["git", "show", f"{source_head}:{relative}"], cwd=root)
        if blob != (root / relative).read_bytes():
            raise ValueError("SOURCE_BLOB_DRIFT_FROM_PREREG")
    return True


def public_progress(progress):
    # No optimizer-sampled individual predictions or unpublished model weights
    return {"blocks": len(progress["blocks"]),
            "attempted_updates": progress["attempted_updates"],
            "committed_updates": progress["committed_updates"],
            "repair_updates": progress["repair_updates"],
            "decision": progress["decision"],
            "rolled_back": progress["rolled_back"],
            "sealed": ({k: progress["sealed_gate"][k] for k in ("correct", "n")}
                       if progress["sealed_gate"] is not None else None),
            "prior_retention": {
                k: {name: val[name] for name in ("correct", "n")}
                for k, val in (progress["sealed_retention"] or {}).items()},
            "promoted": progress["promoted"]}


def run_arm(folder, *, seed, arm, locked_source):
    if source_sha256() != locked_source:
        raise ValueError("SOURCE_CHANGED_BEFORE_ARM")
    folder.mkdir(exist_ok=False)
    model, initializer = initialize(seed=seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.002, betas=(.9, .95),
                                  eps=1e-8, weight_decay=.01, foreach=False)
    write_new(folder / "manifest.json", {
        "version": VERSION, "seed": seed, "arm": arm,
        "source_sha256": locked_source, "initializer": initializer,
        "budget": vars(BUDGET), "stages": list(STAGES),
        "student_task": "evaluate_only", "history_mode": "none",
        "native_teacher_calls": 0,
    })
    accepted, exposed, stages, skipped = [], [], [], []
    expected_net_updates = 0
    status = "ALL_ATOMIC_STAGES_CONSIDERED"
    start = time.perf_counter()
    for stage_index, stage in enumerate(STAGES):
        missing = [dep for dep in DEPENDENCIES[stage] if dep not in accepted]
        if missing:
            skipped.append({"stage": stage, "reason": "UNMET_PREREQUISITE",
                            "missing": missing})
            continue
        number = len(stages) + 1

        def save_block(block):
            block["state_after_block"] = state_hash(model)
            block["optimizer_state_sha256"] = optimizer_digest(optimizer.state_dict())
            save_checkpoint(
                folder / f"stage-{number:02d}-block-{block['block']:02d}.pt",
                model, optimizer, stage, None, initializer)
            if block["block"] % 4 == 0 or block["decision"] != "CONTINUE_CURRENT":
                print(f"seed {seed}, {arm}, {stage}, block {block['block']}: "
                      f"updates={block['updates_total']}, "
                      f"DEV={block['development']['dev']['correct']}/"
                      f"{block['development']['dev']['n']}, "
                      f"next={block['decision']}", flush=True)

        entry = run_stage(
            model, optimizer, stage=stage, accepted=accepted, monitored=exposed,
            rehearsal=exposed,
            seed=seed, arm=arm,
            budget=BUDGET, trace=save_block)
        entry["optimizer_state_sha256"] = optimizer_digest(optimizer.state_dict())
        effective_steps = optimizer_steps(optimizer)
        expected_net_updates += entry["committed_updates"]
        if effective_steps != {expected_net_updates}:
            raise ValueError("OPTIMIZER_STEP_ACCOUNTING_MISMATCH")
        if state_hash(model) != entry["state_after"]:
            raise ValueError("STAGE_CHECKPOINT_HASH_MISMATCH")
        save_checkpoint(folder / f"stage-{number:02d}.pt", model, optimizer,
                        stage, entry["sealed_gate"], initializer)
        write_new(folder / f"stage-{number:02d}.json", entry)
        stages.append(entry)
        if entry["committed_updates"]:
            exposed.append(stage)
        print(f"seed {seed}, {arm}, {stage}: "
              f"updates={entry['attempted_updates']}, "
              f"stop={entry['decision']}, "
              f"gate={(entry['sealed_gate'] or {}).get('correct')}/"
              f"{(entry['sealed_gate'] or {}).get('n')}, "
              f"promoted={entry['promoted']}", flush=True)
        if entry["promoted"]:
            accepted.append(stage)
        old_gate_lost = any(
            value["correct"] != value["n"]
            for value in (entry.get("sealed_retention") or {}).values())
        old_literal_lost = any(
            value["correct"] != value["n"]
            for value in entry.get("old_taught_coverage", {}).values())
        if old_gate_lost or old_literal_lost:
            status = "PREVIOUS_COMPETENCY_RETENTION_FAILURE_STOP"
            skipped += [
                {"stage": later, "reason": "PREVIOUS_COMPETENCY_RETENTION_FAILURE"}
                for later in STAGES[stage_index + 1:]
            ]
            break
    if source_sha256() != locked_source:
        raise ValueError("SOURCE_CHANGED_DURING_ARM")
    report = {
        "version": VERSION, "seed": seed, "arm": arm, "status": status,
        "source_sha256": locked_source,
        "stages_attempted": len(stages),
        "accepted": accepted, "skipped": skipped,
        "attempted_updates": sum(x["attempted_updates"] for x in stages),
        "committed_updates": sum(x["committed_updates"] for x in stages),
        "repair_updates": sum(x["repair_updates"] for x in stages),
        "rollback_updates": sum(x["attempted_updates"] - x["committed_updates"]
                                for x in stages),
        "history_training_exposures": 0, "native_kev_calls": 0,
        "final_student_sha256": state_hash(model),
        "elapsed_seconds": time.perf_counter() - start,
        "summaries": [{**{"stage": e["stage"]}, **public_progress(e)} for e in stages],
    }
    write_new(folder / "report.json", report)
    return report


def run(out, *, seeds=SEEDS, arms=ARMS):
    if tuple(seeds) != SEEDS or tuple(arms) != ARMS or not BUDGET.validate():
        raise ValueError("PREREGISTERED_V05_SCOPE_DRIFT")
    root = Path(__file__).resolve().parent.parent
    if out.resolve() != (root / "runs" / OUT_NAME).resolve():
        raise ValueError("WRONG_PREREGISTERED_OUTPUT")
    if out.exists():
        raise FileExistsError(str(out))
    if subprocess.check_output(
            ["git", "status", "--porcelain=v1"], cwd=root, text=True).strip():
        raise ValueError("SOURCE_MUST_BE_COMMITTED_AND_CLEAN")
    if not validate() or not verify_protocol():
        raise ValueError("COURSE_OR_DIALOGUE_NOT_VALID")
    locked = source_sha256()
    source_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    attest_git_source(root, source_head)
    out.mkdir(parents=True, exist_ok=False)
    try:
        prereg = {
        "version": VERSION, "source_sha256": locked, "source_commit": source_head,
        "course": COURSE_VERSION, "seeds": list(seeds), "arms": list(arms),
        "atomic_stages": list(STAGES), "budget": vars(BUDGET),
        "comparison": "matched initial seed; fixed320, fixed1280, adaptive on same v05 split",
        "no_history_training": True, "no_kev_calls": True,
        "no_retries": True, "no_extra_seeds": True,
        "training_splits": {stage: {k: [r["id"] for r in value]
                                   for k, value in split(stage).items()}
                            for stage in STAGES},
        "promotion": "sealed held-out only after teaching, taught literal coverage, past sealed retention",
        "feedback": "DEV and taught-domain only; sealed gates never choose lessons, repairs, or updates",
        "runtime": {"python": platform.python_version(), "torch": torch.__version__,
                    "machine": platform.machine()},
        }
        write_new(out / "preregistration.json", prereg)
        reports = []
        for seed in seeds:
            for arm in arms:
                reports.append(run_arm(
                    out / f"seed-{seed}-{arm}", seed=seed, arm=arm,
                    locked_source=locked))
        if source_sha256() != locked:
            raise ValueError("SOURCE_CHANGED_AFTER_E8")
        comparison = {"version": VERSION, "preregistration": prereg,
                      "reports": reports,
                      "limitations": [
                          "literal NOT is exhaustively taught, not unseen literal transfer",
                          "DEV contains few reused items and can be overfit adaptively",
                          "fixed320 is an efficiency anchor; fixed1280 is the long-compute reference",
                          "adaptive runs can stop earlier than fixed1280; report all actual updates",
                          "small sealed variable transfer; not formal logic mastery",
                          "replay validates checkpoints and progression, not all historical gradients",
                      ]}
        write_new(out / "comparison.json", comparison)
        return comparison
    except BaseException as exc:
        # Only we created this directory. No writes on preflight/duplicate-run errors.
        try:
            if not (out / "aborted.json").exists():
                write_new(out / "aborted.json", {
                    "status": "INCOMPLETE_NOT_RETRYABLE",
                    "exception": type(exc).__name__, "message": str(exc),
                    "locked_source": locked})
        except OSError:
            pass
        raise


def replay(out):
    prereg = json.loads((out / "preregistration.json").read_text())
    if (prereg["version"] != VERSION or prereg["source_sha256"] != source_sha256()
            or tuple(prereg["seeds"]) != SEEDS or tuple(prereg["arms"]) != ARMS
            or tuple(prereg["atomic_stages"]) != STAGES
            or prereg["budget"] != vars(BUDGET)
            or not isinstance(prereg["source_commit"], str)
            or len(prereg["source_commit"]) != 40):
        raise ValueError("V05_PREREGISTRATION_INVALID")
    attest_git_source(Path(__file__).resolve().parent.parent, prereg["source_commit"])
    for stage in STAGES:
        if prereg["training_splits"][stage] != {
                k: [r["id"] for r in v] for k, v in split(stage).items()}:
            raise ValueError("V05_SPLIT_CHANGED")
    if (out / "aborted.json").exists() or not (out / "comparison.json").exists():
        raise ValueError("ABORTED_OR_INCOMPLETE_V05")
    aggregate = json.loads((out / "comparison.json").read_text())
    if (aggregate["version"] != VERSION or aggregate["preregistration"] != prereg
            or len(aggregate["reports"]) != len(SEEDS) * len(ARMS)):
        raise ValueError("V05_AGGREGATE_MISMATCH")
    replays = []
    for report_index, (seed, arm) in enumerate(
            (s, a) for s in SEEDS for a in ARMS):
        folder = out / f"seed-{seed}-{arm}"
        report = json.loads((folder / "report.json").read_text())
        manifest = json.loads((folder / "manifest.json").read_text())
        if (report != aggregate["reports"][report_index] or report["seed"] != seed
                or report["arm"] != arm or report["source_sha256"] != prereg["source_sha256"]
                or manifest["seed"] != seed or manifest["arm"] != arm
                or manifest["version"] != VERSION or manifest["stages"] != list(STAGES)
                or manifest["student_task"] != "evaluate_only"
                or manifest["history_mode"] != "none"
                or manifest["native_teacher_calls"] != 0
                or manifest["initializer"]["pretrained_weights"] is not False
                or manifest["source_sha256"] != prereg["source_sha256"]
                or manifest["budget"] != vars(BUDGET)):
            raise ValueError("V05_PER_ARM_MANIFEST_MISMATCH")
        accepted, monitored, effective, total_attempted, total_repair = [], [], 0, 0, 0
        last_state = manifest["initializer"]["initial_sha256"]
        previous_model = None
        if report["stages_attempted"] != len(report["summaries"]):
            raise ValueError("V05_STAGE_COUNT_MISMATCH")
        if (len(list(folder.glob("stage-??.json"))) != report["stages_attempted"] or
                len(list(folder.glob("stage-??.pt"))) != report["stages_attempted"]
                or list(folder.glob("*.partial"))):
            raise ValueError("V05_ORPHAN_STAGE_ARTIFACT")
        seen_exposures, seen_attempts = [], []
        for number, overview in enumerate(report["summaries"], start=1):
            evidence = json.loads((folder / f"stage-{number:02d}.json").read_text())
            model, snapshot = load_checkpoint(folder / f"stage-{number:02d}.pt")
            stage = evidence["stage"]
            if (stage != overview["stage"] or stage != snapshot["stage"]
                    or stage not in STAGES or
                    not equal_serialized(snapshot["gate"], evidence["sealed_gate"]) or
                    any(dep not in accepted for dep in DEPENDENCIES[stage])
                    or state_hash(model) != evidence["state_after"]
                    or evidence["state_before"] != last_state
                    or snapshot["initializer"] != manifest["initializer"]):
                raise ValueError("V05_STAGE_IDENTITY_MISMATCH")
            stage_position = STAGES.index(stage)
            if stage in seen_attempts or (seen_attempts and
                    stage_position <= STAGES.index(seen_attempts[-1])):
                raise ValueError("V05_DUPLICATE_OR_REORDERED_STAGE")
            seen_attempts.append(stage)
            if evidence["monitored_at_entry"] != monitored:
                raise ValueError("V05_MONITOR_FROM_SEALED_DRIFT")
            if previous_model is not None and not equal_serialized(
                    evidence["prior_retention_at_entry"],
                    prior_formative(previous_model, monitored)):
                raise ValueError("V05_ENTRY_RETENTION_BASELINE_MISMATCH")
            if previous_model is None and evidence["prior_retention_at_entry"]:
                raise ValueError("V05_UNEXPECTED_PRIOR_BASELINE")
            before, attempted, repaired, next_priorities = [], 0, 0, {}
            for i, block in enumerate(evidence["blocks"]):
                if (block["block"] != i + 1 or block["step_count"] != BUDGET.block
                        or block["context_exposures"] != 0
                        or block["updates_total"] != attempted + BUDGET.block):
                    raise ValueError("V05_BLOCK_ACCOUNTING_CHANGED")
                expected_mode = ("current" if i == 0 or
                                 evidence["blocks"][i-1]["decision"] != "REPAIR_PRIOR"
                                 else "repair")
                if block["mode"] != expected_mode:
                    raise ValueError("V05_REPAIR_MODE_CHANGED")
                expected_repair = None
                if expected_mode == "repair":
                    expected_repair = weakest_retained(
                        evidence["blocks"][i-1]["development"])
                expected_priorities = (next_priorities if
                                       expected_mode == "current" else {})
                if block["start_priorities"] != expected_priorities:
                    raise ValueError("V05_TRAINING_PRIORITY_CHANGED")
                ledger = sample_ledger(
                    stage=stage, rehearsal=seen_exposures, seed=seed,
                    block_number=i, repair=expected_repair,
                    priorities=expected_priorities, budget=BUDGET)
                if any(block[key] != ledger[key] for key in ledger):
                    raise ValueError("V05_TRAINING_SAMPLE_LEDGER_DRIFT")
                if (block["examples"] != BUDGET.block * 32 or
                        block["correct_pre_update"] +
                        block["incorrect_pre_update"] != block["examples"] or
                        sum(block["families"].values()) != block["examples"] or
                        len(block["sample_sha256"]) != 64):
                    raise ValueError("V05_EXPOSURE_RECEIPT_CHANGED")
                development = block["development"]
                if (development["retention_baseline"] != evidence[
                        "prior_retention_at_entry"] or
                        development["declined_prior"] != declined_prior(
                            development["retention"],
                            development["retention_baseline"]) or
                        development["retention_healthy"] !=
                        (not development["declined_prior"])):
                    raise ValueError("V05_RETENTION_TREND_FORGED")
                if expected_mode == "repair":
                    if not expected_repair or block["primary_stage"] != expected_repair:
                        raise ValueError("V05_REPAIR_TARGET_FORGED")
                elif block["primary_stage"] != stage:
                    raise ValueError("V05_CURRENT_STAGE_FORGED")
                attempted += BUDGET.block
                repaired += BUDGET.block if block["mode"] == "repair" else 0
                block_path = folder / f"stage-{number:02d}-block-{i + 1:02d}.pt"
                block_model, block_snapshot = load_checkpoint(block_path)
                if (block_snapshot["stage"] != stage or block_snapshot["gate"] is not None
                        or block_snapshot["initializer"] != manifest["initializer"]
                        or state_hash(block_model) != block["state_after_block"]
                        or optimizer_digest(block_snapshot["optimizer"]) !=
                        block["optimizer_state_sha256"]):
                    raise ValueError("V05_BLOCK_CHECKPOINT_DIVERGED")
                block_steps = {int(s["step"]) for s in
                               block_snapshot["optimizer"]["state"].values()
                               if "step" in s}
                if block_steps != {effective + attempted}:
                    raise ValueError("V05_BLOCK_OPTIMIZER_STEP_DIVERGED")
                actual_observed = inspect_progress(
                    block_model, stage, monitored,
                    baseline=evidence["prior_retention_at_entry"])
                if not equal_serialized(
                        dev_summary(actual_observed), block["development"]):
                    raise ValueError("V05_BLOCK_FORMATIVE_REPLAY_MISMATCH")
                actual = decide_after_block(
                    arm=arm, updates=attempted,
                    observed=block["development"],
                    previous_observations=before,
                    repair_updates=repaired, budget=BUDGET)
                if (actual != block["decision"]
                        or block["repair_updates"] != repaired):
                    raise ValueError("V05_DECISION_REPLAY_FAILED")
                before.append(block["development"])
                if actual == "CONTINUE_CURRENT":
                    next_priorities = training_priorities(
                        block_model, stage, actual_observed,
                        adaptive=(arm == "adaptive"))
            if (attempted != evidence["attempted_updates"]
                    or repaired != evidence["repair_updates"]
                    or evidence["decision"] != evidence["blocks"][-1]["decision"]
                    or evidence["last_dev"] != evidence["blocks"][-1]["development"]):
                raise ValueError("V05_STAGE_BUDGET_CHANGED")
            if len(list(folder.glob(f"stage-{number:02d}-block-??.pt"))) != len(
                    evidence["blocks"]):
                raise ValueError("V05_ORPHAN_BLOCK_CHECKPOINT")
            total_attempted += attempted
            total_repair += repaired
            if evidence["rolled_back"]:
                if (evidence["committed_updates"] != 0 or
                        evidence["decision"] != "ROLLBACK_EXHAUSTED" or
                        evidence["sealed_gate"] is not None or
                        evidence["state_before"] != evidence["state_after"]):
                    raise ValueError("V05_ROLLBACK_FORGED")
            else:
                if evidence["committed_updates"] != attempted or evidence["sealed_gate"] is None:
                    raise ValueError("V05_SEALED_RECEIPT_MISSING")
                frozen_predictions = predict(model, split(stage)["gate"], mode="none")
                gate = {"n": len(frozen_predictions),
                        "correct": sum(p["gold"] == p["prediction"] for p in frozen_predictions)}
                recorded = evidence["sealed_gate"]
                if (gate["correct"], gate["n"]) != (recorded["correct"], recorded["n"]):
                    raise ValueError("V05_GATE_REPLAY_MISMATCH")
                if by_gold(frozen_predictions) != evidence["sealed_by_gold"]:
                    raise ValueError("V05_SEALED_CLASS_BREAKDOWN_CHANGED")
                coverage = trained_literal_score(model, stage)
                if (coverage["correct"], coverage["n"]) != (
                        evidence["taught_domain"]["correct"], evidence["taught_domain"]["n"]):
                    raise ValueError("V05_COVERAGE_REPLAY_MISMATCH")
                for prior in accepted:
                    prior_gate = accuracy(model, split(prior)["gate"])
                    saved = evidence["sealed_retention"][prior]
                    if (prior_gate["correct"], prior_gate["n"]) != (
                            saved["correct"], saved["n"]):
                        raise ValueError("V05_RETENTION_REPLAY_MISMATCH")
                    previous_coverage = trained_literal_score(model, prior)
                    retained_coverage = evidence["old_taught_coverage"][prior]
                    if (previous_coverage["correct"], previous_coverage["n"]) != (
                            retained_coverage["correct"], retained_coverage["n"]):
                        raise ValueError("V05_LITERAL_RETENTION_REPLAY_MISMATCH")
                expected_admit = (
                    gate["correct"] == gate["n"] and
                    coverage["correct"] == coverage["n"] and
                    all(x["correct"] == x["n"]
                        for x in evidence["sealed_retention"].values()) and
                    all(x["correct"] == x["n"]
                        for x in evidence["old_taught_coverage"].values()))
                if bool(evidence["promoted"]) != expected_admit:
                    raise ValueError("V05_FORGED_PROMOTION")
                if evidence["promoted"]:
                    accepted.append(stage)
            effective += evidence["committed_updates"]
            if optimizer_digest(snapshot["optimizer"]) != evidence[
                    "optimizer_state_sha256"]:
                raise ValueError("V05_OPTIMIZER_STATE_DIGEST_MISMATCH")
            optimizer_state_steps = {
                int(s["step"]) for s in snapshot["optimizer"]["state"].values()
                if "step" in s}
            if optimizer_state_steps != {effective}:
                raise ValueError("V05_OPTIMIZER_STEP_MISMATCH")
            if overview != (public_progress(evidence) | {"stage": stage}):
                raise ValueError("V05_SUMMARY_INTEGRITY")
            if evidence["committed_updates"]:
                seen_exposures.append(stage)
                monitored.append(stage)
            last_state = evidence["state_after"]
            previous_model = model
            replays.append({"seed": seed, "arm": arm, "stage": stage,
                            "decision": evidence["decision"],
                            "state": last_state})
        if (report["accepted"] != accepted or
                report["committed_updates"] != effective or
                report["attempted_updates"] != total_attempted or
                report["repair_updates"] != total_repair or
                report["rollback_updates"] != total_attempted - effective or
                report["final_student_sha256"] != last_state or
                report["history_training_exposures"] or report["native_kev_calls"]):
            raise ValueError("V05_FINAL_REPORT_INVALID")
        expected_skipped, reconstructed_accepted = [], []
        attempt = 0
        stopped = False
        for stage in STAGES:
            if stopped:
                expected_skipped.append({
                    "stage": stage, "reason": "PREVIOUS_COMPETENCY_RETENTION_FAILURE"})
                continue
            missing = [dep for dep in DEPENDENCIES[stage]
                       if dep not in reconstructed_accepted]
            if missing:
                expected_skipped.append({
                    "stage": stage, "reason": "UNMET_PREREQUISITE", "missing": missing})
                continue
            if (attempt >= len(seen_attempts) or seen_attempts[attempt] != stage):
                raise ValueError("V05_INCOMPLETE_STAGE_FRONTIER")
            entry = json.loads(
                (folder / f"stage-{attempt + 1:02d}.json").read_text())
            if entry["promoted"]:
                reconstructed_accepted.append(stage)
            if (any(p["correct"] != p["n"]
                    for p in (entry.get("sealed_retention") or {}).values())
                    or any(p["correct"] != p["n"]
                           for p in entry.get("old_taught_coverage", {}).values())):
                stopped = True
            attempt += 1
        expected_status = (
            "PREVIOUS_COMPETENCY_RETENTION_FAILURE_STOP" if stopped
            else "ALL_ATOMIC_STAGES_CONSIDERED")
        if (attempt != len(seen_attempts) or
                report["accepted"] != reconstructed_accepted or
                report["skipped"] != expected_skipped or
                report["status"] != expected_status):
            raise ValueError("V05_UNACCOUNTED_ATOMIC_FRONTIER")
    return {"status": "V05_CHECKPOINTS_VERIFIED", "stages": replays}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    result = replay(args.out) if args.replay else run(args.out)
    print("FINAL:", json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
