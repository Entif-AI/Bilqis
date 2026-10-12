"""Source-locked v0.3 experiment: Boolean competence before metacognition.

Every seed and training condition is declared BEFORE the first optimizer step.
Teacher feedback may appear in earlier turns, but student judgment labels are
not targets until the separate metacognitive prerequisite gate is reached.
All results, including failed prerequisite gates, are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import time

import torch
from torch.nn import functional as F

from bilqis_ref.model import state_hash
from .course_v3 import (STAGES, STAGE, fixed_gate, mandatory_train,
                        missing_prerequisites, panels, structural_transfer_probe, validate_course)
from .dialogue_v3 import (CompletedTurn, STUDENT_LABELS, TOKENS_V3,
                          answer_domain, counterfactual_feedback_prompt,
                          encode_prompt, gold_label, paired_valid_primers, verify_protocol)
from .kev_teacher import KevTeacher
from .kev_v3 import choose, selected_panel
from .student_v3 import (initialize, inputs_for, load_checkpoint, predict,
                         predict_tokens, save_checkpoint, typed_logits)

VERSION = "bilqis.formal.pilot/v0.3.0"
DEFAULT_SEEDS = (401, 409, 419)
DEFAULT_STEPS = 320
DEFAULT_REMEDY_STEPS = 96
ARMS = ("full_feedback", "answer_only", "answer_only_padded", "no_history")
SOURCE_FILES = (
    "bilqis_formal/course_v3.py", "bilqis_formal/dialogue_v3.py",
    "bilqis_formal/kev_v3.py", "bilqis_formal/kev_v2.py",
    "bilqis_formal/kev_teacher.py", "bilqis_formal/pilot_v3.py",
    "bilqis_formal/student_v3.py", "bilqis_formal/dialogue.py",
    "bilqis_formal/semantics.py", "bilqis_ref/model.py",
    "docs/formal/DIALOGUE_V03_PROTOCOL.md",
)


def source_sha256():
    root = Path(__file__).resolve().parent.parent
    hasher = hashlib.sha256()
    for item in SOURCE_FILES:
        hasher.update(item.encode() + b"\0")
        hasher.update((root / item).read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


def write_new(path, obj):
    if path.exists():
        raise FileExistsError(str(path))
    partial = path.with_name(path.name + ".partial")
    with partial.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(partial, path)


def score(predictions):
    def tally(items):
        n = len(items)
        hits = sum(p["prediction"] == p["gold"] for p in items)
        return {"correct": hits, "n": n, "accuracy": hits / n if n else None}
    return {**tally(predictions),
            "by_gold": {label: tally([p for p in predictions if p["gold"] == label])
                        for label in STUDENT_LABELS if any(p["gold"] == label for p in predictions)},
            "errors": [{"id": p["id"], "input": p["input"], "expected": p["gold"],
                        "observed": p["prediction"], "prob_gold": round(p["prob_gold"], 7)}
                       for p in predictions if p["prediction"] != p["gold"]]}


def mastered(results):
    return bool(results) and all(p["prediction"] == p["gold"] for p in results)


def sample_balanced(rng, rows, n):
    if not rows:
        raise ValueError("EMPTY_LESSON")
    by_answer = {}
    for r in rows:
        by_answer.setdefault(r["gold"], []).append(r)
    keys = sorted(by_answer)
    sample = [rng.choice(by_answer[keys[i % len(keys)]]) for i in range(n)]
    rng.shuffle(sample)
    return sample


def _history_mode(arm):
    return {"full_feedback": "full", "answer_only": "answer_only",
            "answer_only_padded": "answer_only_padded",
            "no_history": "none"}[arm]


def train_steps(model, optimizer, rows, rehearsal, *, seed, steps, arm):
    """Real pre-update student answers generate subsequent oracle feedback."""
    rng = random.Random(seed)
    lanes = [[] for _ in range(32)]
    identifier_hash = hashlib.sha256()
    history_exposures, standalone_exposures = 0, 0
    wrong_attempts, correct_attempts = 0, 0
    total_tokens = 0
    mode = _history_mode(arm)
    for step_index in range(steps):
        sample = (sample_balanced(rng, rows, 24) + sample_balanced(rng, rehearsal, 8)
                  if rehearsal else sample_balanced(rng, rows, 32))
        rng.shuffle(sample)
        for r in sample:
            identifier_hash.update(r["id"].encode())
        # Instruction explicitly includes BOTH conversation and independent
        # examples from stage zero, unlike the v0.2 all-dialogue NOT lesson.
        histories = [
            tuple(lanes[i]) if mode != "none" and (step_index + i) % 2 == 0 else ()
            for i in range(32)
        ]
        standalone_exposures += sum(not h for h in histories)
        (ids, lengths), sequences = inputs_for(model, sample, histories, mode=mode)
        total_tokens += sum(map(len, sequences))
        history_exposures += sum(
            len(seq) > len(encode_prompt(r["input"], (), context=model.cfg.context, mode="none"))
            for r, seq in zip(sample, sequences))
        with torch.no_grad():
            model.eval()
            pre = typed_logits(model(ids, lengths), sample)
            guesses = [STUDENT_LABELS[int(v)] for v in pre.argmax(dim=-1)]
        for i, (record, guess) in enumerate(zip(sample, guesses)):
            if guess == record["gold"]:
                correct_attempts += 1
            else:
                wrong_attempts += 1
            lanes[i].append(CompletedTurn(record["input"], guess))
            del lanes[i][:-3]
        model.train()
        optimizer.zero_grad(set_to_none=True)
        logits = typed_logits(model(ids, lengths), sample)
        golds = torch.tensor([STUDENT_LABELS.index(r["gold"]) for r in sample])
        loss = F.cross_entropy(logits, golds)
        if not bool(torch.isfinite(loss)):
            raise ValueError("NONFINITE_TRAINING_LOSS")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
    return {
        "optimizer_updates": steps, "examples": steps * 32,
        "sample_sha256": identifier_hash.hexdigest(),
        "correct_first_attempts": correct_attempts,
        "incorrect_first_attempts": wrong_attempts,
        "context_exposures": history_exposures,
        "standalone_exposures": standalone_exposures,
        "seen_tokens": total_tokens, "final_loss": float(loss.detach()),
    }


def formative(model, rows, arm):
    history, predictions, transcript = [], [], []
    for r in rows:
        result = predict(model, [r], [tuple(history)], mode=_history_mode(arm))[0]
        predictions.append(result)
        transcript.append({"id": r["id"], "gold": r["gold"], "student": result["prediction"],
                           "teacher_feedback": "FEEDBACK.CORRECT" if result["prediction"] == r["gold"]
                           else "FEEDBACK.INCORRECT",
                           "teacher_correction": r["gold"] if result["prediction"] != r["gold"]
                           else None})
        history.append(CompletedTurn(r["input"], result["prediction"]))
        del history[:-3]
    return predictions, transcript


def select(stage, role, options, *, teacher, errors, anchors, plan=None):
    if not options:
        return {"status": "NO_MEANINGFUL_CHOICE", "selected_id": None,
                "traces": []}, None
    if plan is not None:
        selected_id = plan.get(role)
        chosen = next((x for x in options if x.id == selected_id), None)
        if selected_id is not None and chosen is None:
            raise ValueError("FROZEN_TEACHER_CHOICE_INVALID")
        return {"status": "SHARED_CHOICE" if chosen else "SHARED_ABSTENTION",
                "selected_id": selected_id, "traces": []}, chosen
    decision = choose(stage, role if role != "remediation" else "lesson", options,
                      teacher=teacher, recent_predictions=errors, anchors=anchors)
    return decision, selected_panel(options, decision)


def evaluate_gate(model, stage):
    gate = fixed_gate(stage)
    a, b = paired_valid_primers(mandatory_train(stage))
    # Include BOTH teacher outcomes: a CORRECT verdict and a genuine
    # INCORRECT + CORRECT_ANSWER. Neither is chosen using gate gold.
    primer = (CompletedTurn(a.record, gold_label(a.record)), b)
    standalone_predictions = predict(model, gate, mode="none")
    contextual_predictions = predict(model, gate, [primer] * len(gate), mode="full")
    return {
        "standalone": score(standalone_predictions),
        "contextual": score(contextual_predictions),
        "passed": mastered(standalone_predictions) and mastered(contextual_predictions),
        "primer": [{"input": t.record, "student": t.student_answer} for t in primer],
    }


def diagnostic_probe(model, stage):
    """Frozen-read-only sensitivity. Invalid counterfactual is NEVER a lesson/gate."""
    gate = fixed_gate(stage)
    positive, negative = paired_valid_primers(mandatory_train(stage))
    modes = {}
    for label, historical in (("valid_a", positive), ("valid_b", negative)):
        seqs = [encode_prompt(row["input"], [historical], context=model.cfg.context)
                for row in gate]
        modes[label] = predict_tokens(model, gate, seqs)
    original, corrupt = zip(*[
        counterfactual_feedback_prompt(row["input"], positive, context=model.cfg.context)
        for row in gate])
    modes["counterfactual_invalid_feedback"] = predict_tokens(model, gate, list(corrupt))
    padded = [encode_prompt(row["input"], [positive], context=model.cfg.context,
                            mode="answer_only_padded") for row in gate]
    if any(len(a) != len(b) or len(a) != len(c)
           for a, b, c in zip(original, corrupt, padded)):
        raise ValueError("CONTEXT_LENGTH_CONFOUND")
    modes["answer_only_length_matched"] = predict_tokens(model, gate, padded)
    modes["no_history"] = predict(model, gate, mode="none")
    honest = modes["valid_a"]
    opposite = modes["valid_b"]
    invalid = modes["counterfactual_invalid_feedback"]
    return {
        "n": len(gate),
        "interventions_use_gate_gold": False,
        "invalid_feedback_is_diagnostic_only": True,
        "all_feedback_probes_have_equal_length": True,
        "scores": {key: score(value) for key, value in modes.items()},
        "valid_opposite_label_prediction_changes":
            sum(a["prediction"] != b["prediction"] for a, b in zip(honest, opposite)),
        "isolated_corruption_prediction_changes":
            sum(a["prediction"] != b["prediction"] for a, b in zip(honest, invalid)),
        "mean_corruption_gold_probability_delta":
            sum(b["prob_gold"] - a["prob_gold"] for a, b in zip(honest, invalid)) / len(gate),
        "notes": "A response to corrupted teacher text shows token sensitivity, NOT"
                 " proof that correct feedback is semantically understood.",
    }


def run_arm(folder, *, seed, arm, steps, remedy_steps, max_stages, locked_source,
            teacher=None, shared_choices=None):
    if source_sha256() != locked_source:
        raise ValueError("SOURCE_DRIFT_BEFORE_ARM")
    folder.mkdir(exist_ok=False)
    model, init = initialize(seed=seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.002, betas=(.9, .95),
                                  eps=1e-8, weight_decay=.01, foreach=False)
    write_new(folder / "manifest.json", {
        "version": VERSION, "source_sha256": locked_source,
        "seed": seed, "arm": arm, "init": init, "vocab": list(TOKENS_V3),
        "steps": steps, "remedy_steps": remedy_steps,
        "stages": [stage.__dict__ for stage in STAGES],
    })
    accepted = set()
    old_rows, old_gates, records, plan, skipped = [], [], [], {}, []
    status = "ALL_ELIGIBLE_GATES_PASSED"
    started = time.perf_counter()
    for index, stage in enumerate(STAGES[:max_stages]):
        missing = missing_prerequisites(stage.id, accepted)
        if missing:
            skipped.append({
                "stage": stage.id,
                "blocked_by": list(missing),
                "reason": "UNMET_PREREQUISITE",
            })
            continue
        if shared_choices is not None and stage.id not in shared_choices:
            status = "SHARED_TEACHER_FRONTIER"
            break
        core = mandatory_train(stage.id)
        pre = predict(model, core, mode="none")
        anchors = {entry["stage"]: {k: entry["gate"]["standalone"][k]
                   for k in ("n", "correct")} for entry in records}
        frozen = None if shared_choices is None else shared_choices[stage.id]
        choices = panels(stage.id, "lesson")
        decision, lesson = select(stage.id, "lesson", choices, teacher=teacher,
                                  errors=pre, anchors=anchors, plan=frozen)
        if choices and lesson is None:  # Kev abstention must not become an easy fallback.
            status = "TEACHER_ABSTAIN"
            skipped.append({"stage": stage.id, "reason": "TEACHER_ABSTAIN",
                            "lesson_decision": decision})
            continue
        # Preselect the future formative exam using the *pre-training* error
        # witnesses. If the non-authoritative teacher abstains, no optimizer
        # step is spent on a stage whose evaluation plan is unavailable.
        exams = panels(stage.id, "exam")
        exam_choice, exam = select(stage.id, "exam", exams, teacher=teacher,
                                   errors=pre, anchors=anchors, plan=frozen)
        if exams and exam is None:
            status = "TEACHER_EXAM_ABSTAIN"
            skipped.append({"stage": stage.id, "reason": "TEACHER_EXAM_ABSTAIN",
                            "lesson_decision": decision, "exam_decision": exam_choice})
            continue
        instruction = core + (list(lesson.rows) if lesson else [])
        training = train_steps(model, optimizer, instruction, old_rows,
                               seed=seed + index * 1009, steps=steps, arm=arm)
        after_core = predict(model, core, mode="none")
        attempts, transcript = (formative(model, exam.rows, arm) if exam else ([], []))
        exam_score = score(attempts)
        remediation = None
        remediation_result = {"status": "NOT_NEEDED", "selected_id": None, "traces": []}
        extra_training = None
        failed_remediation = False
        # Each student earns remediation from its OWN incorrect first
        # attempts. Never retrain a control that passed merely because the
        # full-feedback arm made a mistake. A control can reuse its admissible
        # shared lesson if the reference arm never needed a separate remedial
        # choice; do not invoke an unmatched extra Kev decision.
        if choices and remedy_steps and bool(exam_score["errors"]):
            control_plan = frozen
            if frozen is not None and frozen.get("remediation") is None:
                control_plan = {"remediation": frozen.get("lesson")}
            remediation_result, remediation = select(
                stage.id, "remediation", choices, teacher=teacher,
                errors=attempts, anchors=anchors, plan=control_plan)
            if frozen is not None and frozen.get("remediation") is None:
                remediation_result["status"] = (
                    "SHARED_LESSON_REMEDIATION" if remediation is not None
                    else "NO_SHARED_REMEDIATION")
            if remediation is not None:
                extra_training = train_steps(
                    model, optimizer, core + list(remediation.rows), old_rows,
                    seed=seed + index * 1009 + 997,
                    steps=remedy_steps, arm=arm)
            else:
                failed_remediation = True
        # The gate and post-gate probes are looked at only after instruction.
        gate = evaluate_gate(model, stage.id)
        retention = {name: evaluate_gate(model, name) for name in old_gates}
        retained = all(g["passed"] for g in retention.values())
        promoted = gate["passed"] and retained and not failed_remediation
        if failed_remediation:
            status = "REMEDIATION_ABSTAIN"
        elif not gate["passed"]:
            status = "ONE_OR_MORE_FAILED_GATES"
        elif not retained:
            status = "RETENTION_STOP"
        selected = {
            "lesson": lesson.id if lesson else None,
            "exam": exam.id if exam else None,
            "remediation": remediation.id if remediation else None,
        }
        plan[stage.id] = selected
        record = {
            "stage": stage.id, "task": stage.student_task, "prerequisites": list(stage.prerequisite),
            "before": score(pre), "after_training_core": score(after_core),
            "lesson": decision, "exam": exam_choice, "remediation": remediation_result,
            "selected": selected, "formative": exam_score,
            "formative_transcript": transcript,
            "train": training, "extra_train": extra_training,
            "gate": gate, "retention": retention, "promoted": promoted,
            "sensitivity": diagnostic_probe(model, stage.id),
            "structural_transfer": score(predict(
                model, structural_transfer_probe(stage.id), mode="none"))
                if structural_transfer_probe(stage.id) else None,
            "model_sha256": state_hash(model),
        }
        records.append(record)
        save_checkpoint(folder / f"stage-{len(records):02d}.pt",
                        model, optimizer, stage.id, gate, init)
        write_new(folder / f"stage-{len(records):02d}.json", record)
        print(f"{folder.parent.name}/{arm} {stage.id}: "
              f"standalone={gate['standalone']['correct']}/{gate['standalone']['n']} "
              f"contextual={gate['contextual']['correct']}/{gate['contextual']['n']} "
              f"promoted={promoted}", flush=True)
        if promoted:
            accepted.add(stage.id)
            old_rows.extend(instruction)
            old_gates.append(stage.id)
        if not retained:
            # Once earlier mastery is lost, *all* later work must stop:
            # accepted ancestors no longer constitute live prerequisites.
            break
    if source_sha256() != locked_source:
        raise ValueError("SOURCE_CHANGED_DURING_RUN")
    report = {
        "version": VERSION, "arm": arm, "seed": seed, "status": status,
        "attempted": len(records), "promoted": [x["stage"] for x in records if x["promoted"]],
        "skipped": skipped, "unmet_prerequisites": [
            x for x in skipped if x["reason"] == "UNMET_PREREQUISITE"],
        "last_model_sha256": state_hash(model), "elapsed_seconds": time.perf_counter() - started,
        "optimizer_updates": sum(
            e["train"]["optimizer_updates"] +
            (e["extra_train"]["optimizer_updates"] if e["extra_train"] else 0)
            for e in records),
        "kev_native_calls": sum(
            sum(t.get("choice_calls", 0) for t in e[key]["traces"])
            for e in records for key in ("lesson", "exam", "remediation")) +
            sum(t.get("choice_calls", 0) for s in skipped
                for key in ("lesson_decision", "exam_decision")
                for t in s.get(key, {}).get("traces", [])),
        "briefs": [{
            "stage": e["stage"], "task": e["task"], "promoted": e["promoted"],
            "standalone": {k: e["gate"]["standalone"][k] for k in ("correct", "n")},
            "contextual": {k: e["gate"]["contextual"][k] for k in ("correct", "n")},
            "training_sha256": e["train"]["sample_sha256"],
            "actual_optimizer_updates": e["train"]["optimizer_updates"] + (
                e["extra_train"]["optimizer_updates"] if e["extra_train"] else 0),
            "actual_exposed_tokens": e["train"]["seen_tokens"] + (
                e["extra_train"]["seen_tokens"] if e["extra_train"] else 0),
            "valid_prefix_switches": e["sensitivity"]["valid_opposite_label_prediction_changes"],
            "corrupt_correction_switches": e["sensitivity"]["isolated_corruption_prediction_changes"],
            "structural_transfer": (
                {k: e["structural_transfer"][k] for k in ("correct", "n")}
                if e["structural_transfer"] is not None else None),
        } for e in records],
    }
    write_new(folder / "report.json", report)
    return report, plan


def run(out, *, seeds=DEFAULT_SEEDS, steps=DEFAULT_STEPS,
        remedy_steps=DEFAULT_REMEDY_STEPS, max_stages=len(STAGES),
        endpoint="http://127.0.0.1:8008"):
    if (not seeds or len(set(seeds)) != len(seeds)
            or tuple(seeds) != DEFAULT_SEEDS or steps != DEFAULT_STEPS
            or remedy_steps != DEFAULT_REMEDY_STEPS or max_stages != len(STAGES)):
        raise ValueError("PREREGISTRATION_DRIFT")
    expected = Path(__file__).resolve().parent.parent / "runs" / "formal-foundations-20261012-e6-v03"
    if out.resolve() != expected.resolve():
        raise ValueError("PREREGISTERED_OUTPUT_PATH")
    verify_protocol()
    validate_course()
    if out.exists():
        raise FileExistsError(str(out))
    root = Path(__file__).resolve().parent.parent
    if subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root, text=True).strip():
        raise ValueError("UNCOMMITTED_EXPERIMENT_SOURCE")
    git_head = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       cwd=root, text=True).strip()
    locked = source_sha256()
    # Resolve/fail-closed on the pinned Kev runtime before reserving a unique
    # experiment directory. No empty "attempt" is created on auth/runtime
    # failure, and nobody needs to delete/reuse a failed seed directory.
    teacher = KevTeacher(endpoint)
    if source_sha256() != locked:
        raise ValueError("SOURCE_DRIFT_DURING_PREFLIGHT")
    out.mkdir(parents=True, exist_ok=False)
    prereg = {
        "version": VERSION, "source_sha256": locked, "source_git_commit": git_head,
        "seeds": list(seeds),
        "runtime": {"python": platform.python_version(),
                    "machine": platform.machine(), "torch": torch.__version__},
        "steps_per_attempted_stage": steps, "max_remediation_steps": remedy_steps,
        "max_stages": max_stages, "arms": list(ARMS),
        "order": "paired seed, full_feedback first to select panels, three controls reuse choices",
        "learning_rate": .002,
        "gate": "exact on both standalone and contextual independent held-outs",
        "no_seed_retry": True,
        "no_training_on_promotion_or_diagnostic_items": True,
        "counterfactual_feedback_never_in_training": True,
        "stop": "failed competency blocks dependent DAG nodes; retention failure halts arm",
    }
    write_new(out / "preregistration.json", prereg)
    write_new(out / "teacher_runtime.json", {
        "run": teacher.identity["run"], "backend": teacher.identity["backend"],
        "device": teacher.identity["device"], "dtype": teacher.identity["dtype"],
        "lora": teacher.identity["lora"]})
    comparisons = []
    for seed in seeds:
        directory = out / f"seed-{seed}"
        directory.mkdir(exist_ok=False)
        reference, plan = run_arm(
            directory / "full_feedback", seed=seed, arm="full_feedback",
            steps=steps, remedy_steps=remedy_steps, max_stages=max_stages,
            locked_source=locked, teacher=teacher)
        controls = {}
        for arm in ARMS[1:]:
            report, _ = run_arm(
                directory / arm, seed=seed, arm=arm,
                steps=steps, remedy_steps=remedy_steps, max_stages=max_stages,
                locked_source=locked, shared_choices=plan)
            controls[arm] = report
        for stage in STAGES:
            shared = [
                next((e for e in report["briefs"] if e["stage"] == stage.id), None)
                for report in (reference, *(controls[a] for a in ARMS[1:]))
            ]
            if all(shared):
                comparisons.append({
                    "seed": seed, "stage": stage.id,
                    "all_training_item_digests_equal":
                        len({x["training_sha256"] for x in shared}) == 1,
                    "learner_dependent_teacher_plan": True,
                    **{arm: {
                        "standalone": x["standalone"], "contextual": x["contextual"],
                        "promoted": x["promoted"],
                        "actual_optimizer_updates": x["actual_optimizer_updates"],
                        "actual_exposed_tokens": x["actual_exposed_tokens"],
                        "counterfactual_correction_switches": x["corrupt_correction_switches"]}
                       for arm, x in zip(ARMS, shared)},
                })
        write_new(directory / "comparison.json", {
            "seed": seed, "reference": reference, "controls": controls, "panels": plan,
        })
        if source_sha256() != locked:
            raise ValueError("SOURCE_CHANGED_DURING_EXPERIMENT")
    summary = {"version": VERSION, "preregistration": prereg,
               "comparison": comparisons,
               "limitations": [
                   "single tiny model per preregistered seed and arm",
                   "exact passing of tiny gates is a provisional criterion",
                   "feedback-history arms have self-generated divergent prior predictions",
                   "rehearsal question IDs can differ after divergent branch promotion",
                   "teacher panels are selected using the full-feedback learner, not learner-independent",
                   "common full-feedback contextual gate is out-of-training-distribution for controls",
                   "per-arm error-based remediation means optimizer budgets can diverge",
                   "corrupted teacher correction is a probe, not valid pedagogy",
                   "context dependence is not by itself learned correction semantics",
                   "never infer success for unattempted stages",
               ]}
    write_new(out / "comparison.json", summary)
    return summary


def replay(out):
    saved = json.loads((out / "preregistration.json").read_text())
    if saved["version"] != VERSION or saved["source_sha256"] != source_sha256():
        raise ValueError("SOURCE_OR_PROTOCOL_REPLAY_MISMATCH")
    if tuple(saved["seeds"]) != DEFAULT_SEEDS or tuple(saved["arms"]) != ARMS:
        raise ValueError("EXPERIMENT_SCOPE_CHANGED")
    if not (out / "comparison.json").exists():
        raise ValueError("INCOMPLETE_EXPERIMENT_NO_AGGREGATE_RECEIPT")
    outcomes = []
    for seed in saved["seeds"]:
        for arm in ARMS:
            folder = out / f"seed-{seed}" / arm
            report = json.loads((folder / "report.json").read_text())
            manifest = json.loads((folder / "manifest.json").read_text())
            if (manifest["source_sha256"] != saved["source_sha256"] or
                    manifest["seed"] != seed or manifest["arm"] != arm or
                    manifest["init"]["token_sha256"] !=
                    hashlib.sha256(json.dumps(TOKENS_V3).encode()).hexdigest()):
                raise ValueError("ARM_MANIFEST_DRIFT")
            if report["attempted"] < 1:
                raise ValueError("NO_CHECKPOINT")
            n = report["attempted"]
            if len(report["briefs"]) != n:
                raise ValueError("REPORT_STAGE_ACCOUNTING")
            total_updates = 0
            for index in range(1, n + 1):
                model, snapshot = load_checkpoint(folder / f"stage-{index:02d}.pt")
                stage_record = json.loads((folder / f"stage-{index:02d}.json").read_text())
                if (state_hash(model) != stage_record["model_sha256"]
                        or snapshot["stage"] != stage_record["stage"]
                        or snapshot["initializer"] != manifest["init"]):
                    raise ValueError("STAGE_CHECKPOINT_PROVENANCE")
                gate = evaluate_gate(model, snapshot["stage"])
                recorded = stage_record["gate"]
                for condition in ("standalone", "contextual"):
                    if (gate[condition]["correct"], gate[condition]["n"]) != (
                            recorded[condition]["correct"], recorded[condition]["n"]):
                        raise ValueError("SEALED_GATE_REPLAY_DIFFERENCE")
                total_updates += stage_record["train"]["optimizer_updates"]
                if stage_record["extra_train"] is not None:
                    total_updates += stage_record["extra_train"]["optimizer_updates"]
                outcomes.append({
                    "seed": seed, "arm": arm, "stage": snapshot["stage"],
                    "state_sha256": state_hash(model),
                    "standalone": {k: gate["standalone"][k] for k in ("correct", "n")},
                    "contextual": {k: gate["contextual"][k] for k in ("correct", "n")},
                })
            if total_updates != report["optimizer_updates"]:
                raise ValueError("TRAINING_ACCOUNTING_MISMATCH")
            if state_hash(model) != report["last_model_sha256"]:
                raise ValueError("LAST_MODEL_REPLAY_DIFFERENCE")
    return {"status": "VERIFIED", "arms": outcomes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8008")
    args = parser.parse_args()
    try:
        summary = replay(args.out) if args.replay else run(args.out, endpoint=args.endpoint)
    except Exception as exc:
        # A partial epoch is never a successful epoch or an excuse to
        # overwrite the original path. Preserve an explicit cause receipt
        # when the output was already reserved, then propagate the failure.
        if (not args.replay and args.out.exists()
                and not (args.out / "comparison.json").exists()
                and not (args.out / "aborted.json").exists()):
            write_new(args.out / "aborted.json", {
                "status": "ABORTED_PARTIAL_EXPERIMENT",
                "exception": type(exc).__name__, "message": str(exc),
                "source_sha256": source_sha256(),
            })
        raise
    print("FINAL:", json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
