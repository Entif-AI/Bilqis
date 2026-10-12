"""v0.4 standalone-first exploratory Boolean-learning pilot.

This is deliberately NOT a curriculum-learning comparison between teacher
models. It asks whether a scratch learner can progress beyond primitive
Boolean evaluation without dialogue-history semantics blocking its gates.
The e6/v0.3 policy and its source remain unchanged and recoverable.
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
from .course_v3 import (
    STAGES, fixed_gate, mandatory_train, missing_prerequisites,
    panels, structural_transfer_probe, validate_course)
from .dialogue_v3 import verify_protocol
from .pilot_v3 import (
    diagnostic_probe, evaluate_gate, mastered, score, train_steps, write_new)
from .student_v3 import initialize, load_checkpoint, predict, save_checkpoint

VERSION = "bilqis.formal.pilot/v0.4.0"
SEEDS = (463, 467, 479)
STEPS_PER_STAGE = 320
# V00 Boolean, V01 NOT, V02 AND, V03-V05 unary/conjunction compositions.
# J00 is explicitly deferred. The operator sequence is not full Stage A.
STAGE_IDS = (
    "V00.BOOLEAN", "V01.NOT", "V02.AND",
    "V03.AND_NOT_RIGHT", "V04.AND_NOT_LEFT", "V05.NOT_AND",
)
if tuple(s.id for s in STAGES if s.id != "J00.PROPOSED_ANSWER") != STAGE_IDS:
    raise ValueError("STANDALONE_CURRICULUM_CHANGED_WITHOUT_VERSION_LOCK")
OUT_NAME = "formal-foundations-20261012-e7-standalone-v04"
SOURCE_FILES = (
    "bilqis_formal/pilot_v4.py", "bilqis_formal/pilot_v3.py",
    "bilqis_formal/kev_v3.py", "bilqis_formal/kev_v2.py",
    "bilqis_formal/kev_teacher.py",
    "bilqis_formal/course_v2.py",
    "bilqis_formal/course_v3.py", "bilqis_formal/dialogue_v3.py",
    "bilqis_formal/dialogue.py", "bilqis_formal/student_v3.py",
    "bilqis_formal/semantics.py", "bilqis_ref/model.py",
    "bilqis_ref/codec.py", "bilqis_ref/semantics.py",
    "docs/formal/DIALOGUE_V04_STANDALONE.md",
)


def source_sha256():
    root = Path(__file__).resolve().parent.parent
    hash_ = hashlib.sha256()
    for path in SOURCE_FILES:
        hash_.update(path.encode() + b"\0")
        hash_.update((root / path).read_bytes())
        hash_.update(b"\0")
    return hash_.hexdigest()


def fixed_lesson(stage):
    """No LLM choice. Cover *both* controlled contrasts when composed."""
    core = mandatory_train(stage)
    extras = [r for panel in panels(stage, "lesson") for r in panel.rows]
    # Same question identity is never silently repeated to boost exposure.
    unique = {}
    for r in core + extras:
        unique[r["id"]] = r
    return list(unique.values())


def fixed_formative(stage):
    """Diagnostic rows are not optimizer or promotion data."""
    unique = {}
    for panel in panels(stage, "exam"):
        for row in panel.rows:
            unique[row["id"]] = row
    return list(unique.values())


def eligible_stage(stage, accepted):
    return not missing_prerequisites(stage, accepted)


def standalone_admitted(gate_score, retention):
    """Only the current truth evaluation and old standalone truth gates decide."""
    return (gate_score["n"] > 0 and gate_score["correct"] == gate_score["n"]
            and all(r["n"] > 0 and r["correct"] == r["n"] for r in retention.values()))


def run_seed(folder, *, seed, locked_source, steps=STEPS_PER_STAGE):
    if source_sha256() != locked_source:
        raise ValueError("SOURCE_CHANGED_BEFORE_STUDENT")
    folder.mkdir(exist_ok=False)
    model, init = initialize(seed=seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.002, betas=(.9, .95),
                                  eps=1e-8, weight_decay=.01, foreach=False)
    write_new(folder / "manifest.json", {
        "version": VERSION, "source_sha256": locked_source,
        "seed": seed, "student_init": init, "steps": steps,
        "student_task": "evaluate_only", "context_mode_during_training": "none",
        "teacher_selection_calls": 0, "preregistered_stages": list(STAGE_IDS),
    })
    accepted, rehearsal, prior = set(), [], []
    stage_entries, skipped, stopped_after_retention = [], [], []
    status = "ALL_ELIGIBLE_ATTEMPTED"
    started = time.perf_counter()
    for index, stage in enumerate(STAGE_IDS):
        missing = missing_prerequisites(stage, accepted)
        if missing:
            skipped.append({"stage": stage, "reason": "UNMET_PREREQUISITE",
                            "blocked_by": list(missing)})
            continue
        core = mandatory_train(stage)
        lesson = fixed_lesson(stage)
        if any(r["input"]["task"] != "evaluate" for r in lesson):
            raise ValueError("EARLY_STUDENT_JUDGMENT_FORBIDDEN")
        pre_train_core = score(predict(model, core, mode="none"))
        train = train_steps(
            model, optimizer, lesson, rehearsal,
            seed=seed + index * 1009, steps=steps, arm="no_history")
        if train["context_exposures"]:
            raise ValueError("DIALOGUE_HISTORY_ENTERED_STANDALONE_TRAINING")
        post_train_core = score(predict(model, core, mode="none"))
        exam_rows = fixed_formative(stage)
        formative = score(predict(model, exam_rows, mode="none")) if exam_rows else None
        # Only after instruction may this stage's sealed gate be consulted.
        fixed = fixed_gate(stage)
        standalone_predictions = predict(model, fixed, mode="none")
        standalone_gate = score(standalone_predictions)
        passed = mastered(standalone_predictions)
        # Contextual behavior is measured on the SAME frozen question identities,
        # but never determines promotion at this early pedagogical stage.
        observed = evaluate_gate(model, stage)
        structural = structural_transfer_probe(stage)
        structural_score = score(predict(model, structural, mode="none")) if structural else None
        retention = {
            old: score(predict(model, fixed_gate(old), mode="none"))
            for old in prior
        }
        retained = all(
            m["correct"] == m["n"] for m in retention.values())
        promoted = standalone_admitted(standalone_gate, retention)
        if promoted != (passed and retained):
            raise ValueError("STANDALONE_PROMOTION_POLICY_DRIFT")
        entry = {
            "stage": stage, "semantic_id": next(s.semantic_id for s in STAGES if s.id == stage),
            "student_task": "evaluate", "pre_train_core": pre_train_core,
            "post_train_core": post_train_core, "formative": formative,
            "train": train, "standalone_gate": standalone_gate,
            "contextual_gate_diagnostic_only": observed["contextual"],
            "history_probe_diagnostic_only": diagnostic_probe(model, stage),
            "structural_transfer_diagnostic_only": structural_score,
            "retention": retention, "promoted": promoted,
            "state_sha256": state_hash(model),
            "no_teacher_selection": True,
            "fixed_lesson_question_ids": [r["id"] for r in lesson],
        }
        stage_entries.append(entry)
        save_checkpoint(folder / f"stage-{len(stage_entries):02d}.pt", model, optimizer,
                        stage, standalone_gate, init)
        write_new(folder / f"stage-{len(stage_entries):02d}.json", entry)
        print(f"seed {seed} {stage}: standalone "
              f"{standalone_gate['correct']}/{standalone_gate['n']}, "
              f"contextual (diagnostic) "
              f"{observed['contextual']['correct']}/{observed['contextual']['n']}, "
              f"promoted={promoted}", flush=True)
        if not retained:
            status = "RETENTION_STOP"
            stopped_after_retention = list(STAGE_IDS[index + 1:])
            break
        if promoted:
            accepted.add(stage)
            prior.append(stage)
            rehearsal.extend(lesson)
        # A failed current stage blocks only its dependencies. Independent
        # AND remains eligible even if the NOT branch failed.
    if source_sha256() != locked_source:
        raise ValueError("SOURCE_CHANGED_DURING_STUDENT")
    if status == "ALL_ELIGIBLE_ATTEMPTED" and any(
            not e["promoted"] for e in stage_entries):
        status = "ONE_OR_MORE_FAILED_STANDALONE_GATES"
    report = {
        "version": VERSION, "seed": seed, "status": status,
        "stages_attempted": len(stage_entries), "stages_promoted": sorted(accepted),
        "unmet_prerequisites": skipped,
        "not_attempted_after_retention_loss": stopped_after_retention,
        "total_optimizer_updates": sum(e["train"]["optimizer_updates"] for e in stage_entries),
        "total_context_exposures": sum(e["train"]["context_exposures"] for e in stage_entries),
        "native_kev_calls": 0, "student_state_sha256": state_hash(model),
        "elapsed_seconds": time.perf_counter() - started,
        "summaries": [
            {"stage": e["stage"], "promoted": e["promoted"],
             "standalone": {k: e["standalone_gate"][k] for k in ("correct", "n")},
             "contextual": {k: e["contextual_gate_diagnostic_only"][k]
                            for k in ("correct", "n")},
             "structural": ({k: e["structural_transfer_diagnostic_only"][k]
                             for k in ("correct", "n")}
                            if e["structural_transfer_diagnostic_only"] else None),
             "training_sha256": e["train"]["sample_sha256"]}
            for e in stage_entries],
    }
    write_new(folder / "report.json", report)
    return report


def run(out, *, seeds=SEEDS, steps=STEPS_PER_STAGE):
    if tuple(seeds) != SEEDS or steps != STEPS_PER_STAGE:
        raise ValueError("PREREGISTERED_SCOPE_DRIFT")
    root = Path(__file__).resolve().parent.parent
    if out.resolve() != (root / "runs" / OUT_NAME).resolve():
        raise ValueError("PREREGISTERED_OUTPUT_PATH")
    if out.exists():
        raise FileExistsError(str(out))
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root, text=True).strip():
        raise ValueError("SOURCE_MUST_BE_COMMITTED_AND_CLEAN")
    verify_protocol()
    validate_course()
    locked = source_sha256()
    source_git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                               cwd=root, text=True).strip()
    out.mkdir(parents=True, exist_ok=False)
    prereg = {
        "version": VERSION, "source_sha256": locked, "source_commit": source_git_commit,
        "seeds": list(seeds), "steps": steps, "stages": list(STAGE_IDS),
        "student_abi": "bilqis.formal.dialogue/v0.3.0",
        "training": "standalone question/current-answer only; zero completed prior turns",
        "teaching": "fixed oracle-labeled core plus both bounded composition contrasts",
        "promotion": "exact stand-alone fixed gate AND all previously accepted standalone retention",
        "independent_branches": "V02 AND may proceed after failed V01 NOT; compositions require both",
        "contextual": "same-stage frozen evaluation diagnostic only, NEVER promotion",
        "structural_transfer": "predefined diagnostic only, NEVER promotion",
        "delayed": ["J00.PROPOSED_ANSWER", "named algebraic laws", "Ithkuil"],
        "no_kev_calls": True, "no_seed_retries": True, "no_optimizer_on_heldouts": True,
        "runtime": {"python": platform.python_version(), "torch": torch.__version__,
                    "machine": platform.machine()},
    }
    try:
        write_new(out / "preregistration.json", prereg)
        results = []
        for seed in seeds:
            results.append(run_seed(
                out / f"seed-{seed}", seed=seed, locked_source=locked, steps=steps))
        if source_sha256() != locked:
            raise ValueError("SOURCE_CHANGED_AFTER_EXPERIMENT")
        summary = {
            "version": VERSION, "preregistration": prereg,
            "per_seed": results,
            "limitations": [
                "tiny fixed Boolean gates and one architecture, not population-level mastery",
                "no teacher dialogue in training; contextual assessment is out-of-distribution",
                "no randomized presentation/order transfer or named-law acceptance",
                "structural transfer and contextual sensitivity are diagnostics, not gates",
                "no efficacy comparison against v0.3 due distinct scientific objectives and seeds",
            ],
        }
        write_new(out / "comparison.json", summary)
        return summary
    except BaseException as exc:
        # Only this invocation's successful mkdir permits an abort receipt.
        # Failed path/clean-Git preflights never write into somebody else's
        # pre-existing run directory. A process kill cannot be caught here;
        # replay still treats any missing aggregate as incomplete.
        try:
            if not (out / "aborted.json").exists():
                write_new(out / "aborted.json", {
                    "status": "INCOMPLETE_NOT_RETRYABLE", "exception": type(exc).__name__,
                    "message": str(exc), "source_sha256": locked,
                })
        except OSError:
            pass  # Preserve original exception.
        raise


def replay(out):
    frozen = json.loads((out / "preregistration.json").read_text())
    if (frozen["version"] != VERSION or frozen["source_sha256"] != source_sha256()
            or tuple(frozen["seeds"]) != SEEDS or tuple(frozen["stages"]) != STAGE_IDS
            or frozen["steps"] != STEPS_PER_STAGE
            or not isinstance(frozen.get("source_commit"), str)
            or len(frozen["source_commit"]) != 40):
        raise ValueError("FROZEN_SOURCE_OR_PLAN_MISMATCH")
    if not (out / "comparison.json").exists():
        raise ValueError("INCOMPLETE_EXPERIMENT")
    if (out / "aborted.json").exists():
        raise ValueError("ABORTED_EPOCH_CANNOT_BE_COMPLETE")
    aggregate = json.loads((out / "comparison.json").read_text())
    if (aggregate.get("version") != VERSION
            or aggregate.get("preregistration") != frozen
            or len(aggregate.get("per_seed", ())) != len(SEEDS)):
        raise ValueError("AGGREGATE_PREREGISTRATION_MISMATCH")
    replays = []
    for seed_index, seed in enumerate(SEEDS):
        folder = out / f"seed-{seed}"
        manifest = json.loads((folder / "manifest.json").read_text())
        report = json.loads((folder / "report.json").read_text())
        if (manifest["source_sha256"] != frozen["source_sha256"]
                or manifest["seed"] != seed or report["seed"] != seed
                or report["version"] != VERSION
                or manifest["steps"] != frozen["steps"]
                or manifest["student_init"]["pretrained_weights"] is not False):
            raise ValueError("ARM_MANIFEST_MISMATCH")
        if aggregate["per_seed"][seed_index] != report:
            raise ValueError("AGGREGATE_SEED_REPORT_MISMATCH")
        if not report["summaries"] or report["stages_attempted"] != len(report["summaries"]):
            raise ValueError("STAGE_COUNT_MISMATCH")
        accepted = []
        previous_index = -1
        updates = 0
        for number, overview in enumerate(report["summaries"], start=1):
            saved = json.loads((folder / f"stage-{number:02d}.json").read_text())
            model, snapshot = load_checkpoint(folder / f"stage-{number:02d}.pt")
            if (saved["stage"] != overview["stage"] or saved["stage"] != snapshot["stage"]
                    or state_hash(model) != saved["state_sha256"]
                    or snapshot["initializer"] != manifest["student_init"]):
                raise ValueError("CHECKPOINT_IDENTITY_MISMATCH")
            if saved["stage"] not in STAGE_IDS:
                raise ValueError("UNDECLARED_TRAINING_STAGE")
            stage_index = STAGE_IDS.index(saved["stage"])
            if stage_index <= previous_index or missing_prerequisites(
                    saved["stage"], set(accepted)):
                raise ValueError("PREREQUISITE_OR_ORDER_VIOLATION")
            previous_index = stage_index
            if saved["student_task"] != "evaluate" or saved["train"]["context_exposures"]:
                raise ValueError("DIALOGUE_OR_GRADING_TRAINING_VIOLATION")
            if (saved["fixed_lesson_question_ids"] !=
                    [r["id"] for r in fixed_lesson(saved["stage"])]
                    or overview["training_sha256"] != saved["train"]["sample_sha256"]
                    or saved["train"]["optimizer_updates"] != frozen["steps"]):
                raise ValueError("TRAINING_CURRICULUM_OR_BUDGET_DRIFT")
            actual = score(predict(model, fixed_gate(saved["stage"]), mode="none"))
            if (actual["correct"], actual["n"]) != (
                    saved["standalone_gate"]["correct"], saved["standalone_gate"]["n"]):
                raise ValueError("STANDALONE_GATE_REPLAY_MISMATCH")
            if (snapshot["gate"]["correct"], snapshot["gate"]["n"]) != (
                    actual["correct"], actual["n"]):
                raise ValueError("CHECKPOINT_GATE_RECEIPT_MISMATCH")
            # AdamW state is the independent optimizer-step receipt; a
            # self-reported count in stage JSON is insufficient.
            expected_optimizer_step = updates + frozen["steps"]
            optimizer_steps = [
                int(state["step"]) for state in snapshot["optimizer"]["state"].values()
                if "step" in state
            ]
            if not optimizer_steps or max(optimizer_steps) != expected_optimizer_step:
                raise ValueError("OPTIMIZER_CHECKPOINT_STEP_MISMATCH")
            contextual = evaluate_gate(model, saved["stage"])["contextual"]
            recorded = saved["contextual_gate_diagnostic_only"]
            if (contextual["correct"], contextual["n"]) != (
                    recorded["correct"], recorded["n"]):
                raise ValueError("CONTEXTUAL_DIAGNOSTIC_REPLAY_MISMATCH")
            observed_retention = {
                prior: score(predict(model, fixed_gate(prior), mode="none"))
                for prior in accepted
            }
            if set(observed_retention) != set(saved["retention"]):
                raise ValueError("RETENTION_PROVENANCE_MISMATCH")
            for prior, current in observed_retention.items():
                recorded_retention = saved["retention"][prior]
                if (current["correct"], current["n"]) != (
                        recorded_retention["correct"], recorded_retention["n"]):
                    raise ValueError("RETENTION_SCORE_REPLAY_MISMATCH")
            expected_promoted = standalone_admitted(actual, observed_retention)
            if saved["promoted"] != expected_promoted or overview["promoted"] != expected_promoted:
                raise ValueError("PROGRESSION_RECEIPT_MISMATCH")
            if any(r["correct"] != r["n"] for r in observed_retention.values()):
                if number != len(report["summaries"]) or report["status"] != "RETENTION_STOP":
                    raise ValueError("RETENTION_FAILURE_NOT_TERMINAL")
            structural_rows = structural_transfer_probe(saved["stage"])
            saved_structural = saved["structural_transfer_diagnostic_only"]
            if structural_rows:
                structural = score(predict(model, structural_rows, mode="none"))
                if (saved_structural is None or
                        (structural["correct"], structural["n"]) !=
                        (saved_structural["correct"], saved_structural["n"])):
                    raise ValueError("STRUCTURAL_DIAGNOSTIC_REPLAY_MISMATCH")
            elif saved_structural is not None:
                raise ValueError("UNPLANNED_STRUCTURAL_DIAGNOSTIC")
            replay_history_probe = diagnostic_probe(model, saved["stage"])
            for key in ("valid_opposite_label_prediction_changes",
                        "isolated_corruption_prediction_changes"):
                if replay_history_probe[key] != saved["history_probe_diagnostic_only"][key]:
                    raise ValueError("HISTORY_DIAGNOSTIC_REPLAY_MISMATCH")
            updates += saved["train"]["optimizer_updates"]
            if expected_promoted:
                accepted.append(saved["stage"])
            replays.append({"seed": seed, "stage": saved["stage"],
                            "state_sha256": state_hash(model),
                            "standalone_correct": actual["correct"],
                            "standalone_n": actual["n"],
                            "contextual_correct": contextual["correct"],
                            "contextual_n": contextual["n"]})
        if updates != report["total_optimizer_updates"]:
            raise ValueError("OPTIMIZER_UPDATE_COUNT_MISMATCH")
        if sorted(accepted) != report["stages_promoted"]:
            raise ValueError("PROMOTED_SET_MISMATCH")
        if report["status"] == "RETENTION_STOP":
            if report["not_attempted_after_retention_loss"] != list(
                    STAGE_IDS[STAGE_IDS.index(report["summaries"][-1]["stage"]) + 1:]):
                raise ValueError("RETENTION_STOP_FRONTIER_MISMATCH")
        elif report["not_attempted_after_retention_loss"]:
            raise ValueError("FALSE_RETENTION_STOP")
        attempted_ids = [x["stage"] for x in report["summaries"]]
        skip_by_id = {x["stage"]: x for x in report["unmet_prerequisites"]}
        if len(skip_by_id) != len(report["unmet_prerequisites"]):
            raise ValueError("DUPLICATE_SKIPPED_STAGE")
        current_accepted = set()
        processed = 0
        for stage in STAGE_IDS:
            if processed < len(attempted_ids) and stage == attempted_ids[processed]:
                if missing_prerequisites(stage, current_accepted):
                    raise ValueError("REPLAY_ADMISSION_GRAPH_VIOLATION")
                if report["summaries"][processed]["promoted"]:
                    current_accepted.add(stage)
                processed += 1
            elif stage in skip_by_id:
                blocked = missing_prerequisites(stage, current_accepted)
                if not blocked or list(blocked) != skip_by_id[stage]["blocked_by"]:
                    raise ValueError("SKIPPED_STAGE_NOT_BLOCKED")
            elif report["status"] == "RETENTION_STOP":
                # A retention collapse intentionally ends the entire arm.
                continue
            else:
                raise ValueError("UNACCOUNTED_STAGE")
        if processed != len(attempted_ids) or current_accepted != set(accepted):
            raise ValueError("DAG_REPLAY_INCOMPLETE")
        if (report["total_context_exposures"] != 0
                or report["native_kev_calls"] != 0):
            raise ValueError("STANDALONE_ONLY_RECEIPT_MISMATCH")
        if state_hash(model) != report["student_state_sha256"]:
            raise ValueError("FINAL_MODEL_HASH_MISMATCH")
    return {"status": "REPLAY_VERIFIED", "stages": replays}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    result = replay(args.out) if args.replay else run(args.out)
    print("FINAL:", json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
