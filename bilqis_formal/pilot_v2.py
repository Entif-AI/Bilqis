"""Bounded comparative teacher-dialogue experiment. Never reuses v0.1 weights.

The two scratch arms receive the same curriculum, sampled question IDs, seed
and teacher-selected panels. Their only planned training difference is whether
completed teacher/student/feedback turns appear in the attention window.
The held-out promotion gate is sealed until AFTER all instruction/remediation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import time

import torch
from torch.nn import functional as F

from bilqis_ref.model import state_hash
from .course_v2 import (STAGES, STAGE, fixed_gate, mandatory_train, panels,
                        validate_course)
from .dialogue import (ALL_LABELS, CompletedTurn, TOKENS_V2,
                       answer_domain, encode_prompt, verify_protocol)
from .kev_teacher import KevTeacher
from .kev_v2 import choose, error_witnesses, selected_panel
from .student_v2 import (initialize, inputs_for, load_checkpoint, predict,
                         save_checkpoint, typed_logits)

VERSION = "foundation-dialogue-pilot/v0.2.2"
SOURCE_FILES = (
    "bilqis_formal/course_v2.py", "bilqis_formal/dialogue.py",
    "bilqis_formal/kev_v2.py", "bilqis_formal/kev_teacher.py",
    "bilqis_formal/pilot_v2.py", "bilqis_formal/semantics.py",
    "bilqis_formal/student_v2.py", "bilqis_ref/model.py",
)


def source_fingerprint():
    """Freeze the runtime-source bytes for all NEW future epochs."""
    root = Path(__file__).resolve().parent.parent
    hasher = hashlib.sha256()
    for name in SOURCE_FILES:
        hasher.update(name.encode("utf-8") + b"\0")
        hasher.update((root / name).read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


def write_new(path, record):
    with path.open("x", encoding="utf-8") as f:
        json.dump(record, f, sort_keys=True, indent=2, default=str)
        f.write("\n")


def score(predictions):
    def part(ps):
        correct = sum(p["prediction"] == p["gold"] for p in ps)
        return {"correct": correct, "n": len(ps),
                "accuracy": correct / len(ps) if ps else None}
    return {**part(predictions),
            "by_task": {t: part([p for p in predictions if p["task"] == t])
                        for t in sorted({p["task"] for p in predictions})},
            "by_gold": {g: part([p for p in predictions if p["gold"] == g])
                        for g in sorted({p["gold"] for p in predictions})},
            "errors": error_witnesses(predictions, limit=32)}


def mastered(predictions):
    # Local exact-passing provisional gate, NOT a statistically robust criterion.
    return all(p["prediction"] == p["gold"] for p in predictions)


def standard_primer(stage):
    """Two fixed, oracle-validated completed demonstrations from TRAINING ONLY.

    The first student answer is correct; the second is wrong and corrected.
    These same input turns are used across all comparison arms to isolate the
    history intervention, not differences in how a teacher reacted to each arm.
    """
    rows = mandatory_train(stage)
    positive = next(r for r in rows if r["input"]["task"] == "evaluate")
    negative = next(r for r in reversed(rows) if r["input"]["task"] == "judge_answer")
    wrong = next(x for x in answer_domain(negative["input"]) if x != negative["gold"])
    return (CompletedTurn(positive["input"], positive["gold"]),
            CompletedTurn(negative["input"], wrong))


def _balanced_sample(rng, records, count):
    if not records:
        raise ValueError("NO_LESSON_EXAMPLES")
    buckets = {}
    for r in records:
        buckets.setdefault(r["gold"], []).append(r)
    labels = sorted(buckets)
    result = [rng.choice(buckets[labels[i % len(labels)]]) for i in range(count)]
    rng.shuffle(result)
    return result


def train_steps(model, optimizer, new_rows, old_rows, *, steps, seed, use_feedback,
                answer_only=False, mix_standalone=False):
    rng = random.Random(seed)
    mode = "answer_only" if answer_only else "full" if use_feedback else "none"
    lanes = [[] for _ in range(32)]
    correct_feedback = 0
    incorrect_feedback = 0
    answer_context_exposures = 0
    deliberately_standalone_exposures = 0
    token_exposures = 0
    sampled = hashlib.sha256()
    for step_index in range(steps):
        records = (_balanced_sample(rng, new_rows, 24) + _balanced_sample(rng, old_rows, 8)
                   if old_rows else _balanced_sample(rng, new_rows, 32))
        rng.shuffle(records)
        for r in records:
            sampled.update(r["id"].encode("ascii"))
        histories = [tuple(lane) if mode != "none" and (
            not mix_standalone or (i + step_index) % 2 == 0) else ()
            for i, lane in enumerate(lanes)]
        deliberately_standalone_exposures += sum(not h for h in histories)
        (ids, lengths), n_tokens = inputs_for(model, records, histories, history_mode=mode)
        token_exposures += n_tokens
        answer_context_exposures += sum(
            len(encode_prompt(r["input"], h, context=model.cfg.context, history_mode=mode)) >
            len(encode_prompt(r["input"], (), context=model.cfg.context))
            for r, h in zip(records, histories))
        with torch.no_grad():
            model.eval()
            pre = typed_logits(model(ids, lengths), records)
            before_answers = [ALL_LABELS[int(v)] for v in pre.argmax(dim=-1)]
        for lane, record, answer in zip(lanes, records, before_answers):
            if answer == record["gold"]:
                correct_feedback += 1
            else:
                incorrect_feedback += 1
            lane.append(CompletedTurn(record["input"], answer))
            del lane[:-3]
        model.train()
        optimizer.zero_grad(set_to_none=True)
        logits = typed_logits(model(ids, lengths), records)
        labels = torch.tensor([ALL_LABELS.index(r["gold"]) for r in records], dtype=torch.long)
        loss = F.cross_entropy(logits, labels)
        if not bool(torch.isfinite(loss)):
            raise ValueError("NONFINITE_DIALOGUE_LOSS")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
    return {"optimizer_updates": steps, "exposures": 32 * steps,
            "pre_update_correct_feedback": correct_feedback,
            "pre_update_incorrect_feedback": incorrect_feedback,
            "history_bearing_exposures": answer_context_exposures,
            "standalone_exposures": deliberately_standalone_exposures,
            "mixed_standalone_instruction": mix_standalone,
            "token_exposures": token_exposures,
            "sampled_question_sha256": sampled.hexdigest(),
            "final_loss": float(loss.detach())}


def formative(model, rows, *, use_feedback, answer_only=False):
    """Observe actual first attempts, then supply oracle feedback for the next turn."""
    history = []
    out = []
    transcripts = []
    for r in rows:
        mode = "answer_only" if answer_only else "full" if use_feedback else "none"
        result = predict(model, [r], [tuple(history) if mode != "none" else ()],
                         history_mode=mode)[0]
        out.append(result)
        turn = CompletedTurn(r["input"], result["prediction"])
        # This is the *student's* real pre-feedback prediction; correctness is
        # computed independently by gold_label inside encode_completed.
        history.append(turn)
        transcripts.append({"question_id": r["id"], "student_answer": result["prediction"],
                            "oracle_answer": result["gold"],
                            "feedback": ("FEEDBACK.CORRECT" if result["prediction"] == result["gold"]
                                         else "FEEDBACK.INCORRECT"),
                            "correction_if_wrong": (result["gold"] if result["prediction"] != result["gold"]
                                                    else None)})
    return out, transcripts


def _provided_selection(stage, role, candidates, plan, teacher, predictions, anchors):
    if not candidates:
        return {"status": "NO_COMPARABLE_COMPOSITION", "selected_id": None,
                "traces": [], "order_votes": []}, None
    if plan is not None:
        requested = plan.get(role)
        chosen = next((p for p in candidates if p.id == requested), None)
        if requested is not None and chosen is None:
            raise ValueError("PLAN_PANEL_NOT_IN_ELIGIBLE_SET")
        return {"status": "SHARED_FEEDBACK_ARM_DECISION" if chosen else "SHARED_ABSTENTION",
                "selected_id": requested, "traces": [], "order_votes": []}, chosen
    decision = choose(stage, role if role != "remediation" else "lesson", candidates,
                      teacher=teacher, recent_predictions=predictions, anchors=anchors)
    return decision, selected_panel(candidates, decision)


def run_arm(out, *, use_feedback, seed, steps, remedy_steps, max_stages,
            teacher=None, shared_plan=None, answer_only=False):
    out.mkdir(parents=True, exist_ok=False)
    model, initializer = initialize(seed=seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.002, betas=(.9, .95),
                                  eps=1e-8, weight_decay=.01, foreach=False)
    write_new(out / "manifest.json", {
        "version": VERSION, "vocab": {i: t for i, t in enumerate(TOKENS_V2)},
        "source_sha256": source_fingerprint(),
        "stages": [s.__dict__ for s in STAGES], "use_feedback_context": use_feedback,
        "history_mode": "answer_only" if answer_only else "full" if use_feedback else "none",
        "student_pretrained": False, "gold_in_current_student_input": False,
        "no_previous_checkpoints_imported": True, "init": initializer,
        "seed": seed, "steps": steps, "remedy_steps": remedy_steps})
    prior_rows = []
    prior_gates = []
    records = []
    reusable_plan = {}
    status = "MAX_STAGES_REACHED"
    started = time.perf_counter()
    for index, stage in enumerate(STAGES[:max_stages]):
        if shared_plan is not None and stage.id not in shared_plan:
            # The control arm must not create new teacher decisions beyond the
            # experimental arm's observed pedagogical frontier.
            status = "SHARED_PLAN_FRONTIER"
            break
        if not set(stage.prerequisite) <= {s["stage"] for s in records if s["promoted"]}:
            status = "UNMET_PREREQUISITE"
            break
        core = mandatory_train(stage.id)
        pre = predict(model, core)
        anchors = {s["stage"]: {k: s["gate"][k] for k in ("correct", "n")}
                   for s in records if s["promoted"]}
        lesson_options = panels(stage.id, "lesson")
        frozen_plan = shared_plan.get(stage.id) if shared_plan is not None else None
        lesson_selection, lesson = _provided_selection(
            stage.id, "lesson", lesson_options, frozen_plan, teacher, pre, anchors)
        stage_train = core + (list(lesson.rows) if lesson else [])
        train = train_steps(model, optimizer, stage_train, prior_rows, steps=steps,
                            seed=seed + index * 1009, use_feedback=use_feedback,
                            answer_only=answer_only,
                            mix_standalone=stage.id != "D00.PROTOCOL")

        # Formative panels are disjoint from both training and the sealed gate.
        exam_options = panels(stage.id, "exam")
        teaching_probe = predict(model, core)
        exam_selection, exam = _provided_selection(
            stage.id, "exam", exam_options, frozen_plan, teacher, teaching_probe, anchors)
        exam_pred, exam_transcript = (
            formative(model, list(exam.rows), use_feedback=use_feedback,
                      answer_only=answer_only) if exam else ([], []))
        exam_score = score(exam_pred)

        # One bounded remedial response to formative errors, based on admitted
        # alternative lessons. It never trains from the sealed promotion gate.
        remediation_selection = {"status": "NOT_NEEDED", "selected_id": None,
                                 "traces": [], "order_votes": []}
        remediation = None
        remedial_train = None
        if lesson_options and remedy_steps and (
                (bool(exam_score["errors"]) if shared_plan is None
                 else frozen_plan.get("remediation") is not None)):
            remediation_selection, remediation = _provided_selection(
                stage.id, "lesson" if shared_plan is None else "remediation",
                lesson_options, frozen_plan, teacher, exam_pred, anchors)
            if remediation is not None:
                remedial_train = train_steps(
                    model, optimizer, core + list(remediation.rows), prior_rows,
                    steps=remedy_steps, seed=seed + index * 1009 + 997,
                    use_feedback=use_feedback, answer_only=answer_only,
                    mix_standalone=stage.id != "D00.PROTOCOL")

        # One-time sealed post-training gate: not included in Kev context.
        # D00 teaches an INTERACTION protocol; its initial promotion evidence
        # must include a prior completed dialogue. Demanding transfer without
        # any dialogue at D00 repeats e1's premature-composition gate mistake.
        # Subsequent logical competencies must pass with AND without dialogue.
        gate_rows = fixed_gate(stage.id)
        primer = standard_primer(stage.id)
        standalone_predictions = predict(model, gate_rows)
        dialogue_predictions = predict(model, gate_rows,
                                       histories=[primer] * len(gate_rows), history_mode="full")
        standalone = score(standalone_predictions)
        dialogue = score(dialogue_predictions)
        gate = dialogue if stage.id == "D00.PROTOCOL" else standalone
        current_pass = (mastered(dialogue_predictions) if stage.id == "D00.PROTOCOL" else
                        mastered(standalone_predictions) and mastered(dialogue_predictions))
        retention = {}
        for old_stage, old_rows, old_primer in prior_gates:
            s = predict(model, old_rows)
            d = predict(model, old_rows, histories=[old_primer] * len(old_rows))
            retention[old_stage] = {"standalone": score(s), "dialogue": score(d),
                                    "passed": (mastered(d) if old_stage == "D00.PROTOCOL"
                                               else mastered(s) and mastered(d))}
        prior_pass = all(x["passed"] for x in retention.values())
        promoted = current_pass and prior_pass
        if not current_pass:
            status = "MASTERY_STOP"
        elif not prior_pass:
            status = "RETENTION_STOP"
        reuse = {"lesson": lesson.id if lesson else None,
                 "exam": exam.id if exam else None,
                 "remediation": remediation.id if remediation else None}
        reusable_plan[stage.id] = reuse
        entry = {"stage": stage.id, "semantic_id": stage.semantic_id,
                 "prerequisites": list(stage.prerequisite),
                 "pre_training_core": score(pre), "post_training_core": score(teaching_probe),
                 "lesson_selection": lesson_selection, "formative_selection": exam_selection,
                 "remediation_selection": remediation_selection,
                 "chosen": reuse, "formative_score": exam_score,
                 "formative_dialogue": exam_transcript,
                 "train": train, "remedial_train": remedial_train, "gate": gate,
                 "standalone_gate": standalone, "dialogue_gate": dialogue,
                 "gate_policy": "contextual_only" if stage.id == "D00.PROTOCOL" else "both",
                 "primer": [{"record": turn.record, "student_answer": turn.student_answer}
                            for turn in primer],
                 "retention": retention, "promoted": promoted,
                 "student_sha256": state_hash(model)}
        records.append(entry)
        write_new(out / f"stage-{len(records):02d}.json", entry)
        save_checkpoint(out / f"stage-{len(records):02d}.pt",
                        model, optimizer, stage.id, gate, initializer)
        print(f"{out.name} {stage.id}: gate={gate['correct']}/{gate['n']} "
              f"formative={exam_score['correct']}/{exam_score['n']} "
              f"promoted={promoted} lesson={lesson_selection['status']} "
              f"exam={exam_selection['status']}", flush=True)
        if not promoted:
            break
        prior_rows.extend(stage_train)
        prior_gates.append((stage.id, gate_rows, primer))
    report = {
        "version": VERSION, "arm": out.name, "status": status,
        "stages_attempted": len(records), "stages_promoted": sum(x["promoted"] for x in records),
        "optimizer_updates": sum(e["train"]["optimizer_updates"] +
                                 (e["remedial_train"]["optimizer_updates"] if e["remedial_train"] else 0)
                                 for e in records),
        "native_kev_choice_calls": sum(
            sum(t.get("choice_calls", 0) for t in entry[key]["traces"])
            for entry in records
            for key in ("lesson_selection", "formative_selection", "remediation_selection")),
        "state_hash": state_hash(model),
        "elapsed_seconds": time.perf_counter() - started,
        "briefs": [{"stage": e["stage"], "gate": {k: e["gate"][k] for k in ("correct", "n")},
                    "standalone_gate": {k: e["standalone_gate"][k] for k in ("correct", "n")},
                    "dialogue_gate": {k: e["dialogue_gate"][k] for k in ("correct", "n")},
                    "formative": {k: e["formative_score"][k] for k in ("correct", "n")},
                    "promoted": e["promoted"], "chosen": e["chosen"],
                    "train_sample_sha256": e["train"]["sampled_question_sha256"]}
                   for e in records]}
    write_new(out / "report.json", report)
    return report, reusable_plan


def run(out, *, steps=320, remedy_steps=96, max_stages=6, seed=211,
        teacher_endpoint="http://127.0.0.1:8008"):
    if not 1 <= steps <= 512 or not 0 <= remedy_steps <= 256 or not 1 <= max_stages <= len(STAGES):
        raise ValueError("UNBOUNDED_EXPERIMENT")
    verify_protocol()
    validate_course()
    if out.exists():
        raise FileExistsError(str(out))
    locked_source = source_fingerprint()
    teacher = KevTeacher(teacher_endpoint)  # pin identity, fail closed
    out.mkdir(parents=True, exist_ok=False)
    a, plan = run_arm(out / "feedback-context", use_feedback=True, seed=seed, steps=steps,
                      remedy_steps=remedy_steps, max_stages=max_stages, teacher=teacher)
    b, _ = run_arm(out / "answer-only-control", use_feedback=False, answer_only=True,
                   seed=seed, steps=steps, remedy_steps=remedy_steps,
                   max_stages=max_stages, shared_plan=plan)
    c, _ = run_arm(out / "no-context-control", use_feedback=False, seed=seed, steps=steps,
                   remedy_steps=remedy_steps, max_stages=max_stages, shared_plan=plan)
    if source_fingerprint() != locked_source:
        raise ValueError("RUN_SOURCE_CHANGED_MID_EPOCH")
    comparisons = []
    by_arm = ({x["stage"]: x for x in a["briefs"]},
              {x["stage"]: x for x in b["briefs"]},
              {x["stage"]: x for x in c["briefs"]})
    for s in by_arm[0]:
        if s in by_arm[1] and s in by_arm[2]:
            left, middle, right = by_arm[0][s], by_arm[1][s], by_arm[2][s]
            comparisons.append({
                "stage": s,
                "full_feedback": {k: left[k] for k in ("gate", "standalone_gate", "dialogue_gate", "promoted")},
                "answer_only": {k: middle[k] for k in ("gate", "standalone_gate", "dialogue_gate", "promoted")},
                "no_context": {k: right[k] for k in ("gate", "standalone_gate", "dialogue_gate", "promoted")},
                "same_sampled_questions": len({left["train_sample_sha256"],
                                                middle["train_sample_sha256"],
                                                right["train_sample_sha256"]}) == 1})
    summary = {"version": VERSION, "source_sha256": locked_source, "feedback_report": a,
               "answer_only_report": b, "control_report": c,
               "shared_teacher_plan": plan, "comparisons": comparisons,
               "interpretation": "Exploratory three-arm matched-seed comparison; "
               "same standardized full-feedback primer at contextual gates for all arms. "
               "No multi-seed causal or broad mastery claim."}
    write_new(out / "comparison.json", summary)
    return summary


def replay(out):
    comparisons = []
    for arm in ("feedback-context", "answer-only-control", "no-context-control"):
        folder = out / arm
        if not folder.exists():  # e3 v0.2.0 had only two historical arms.
            continue
        report = json.loads((folder / "report.json").read_text())
        manifest = json.loads((folder / "manifest.json").read_text())
        if "source_sha256" in manifest and source_fingerprint() != manifest["source_sha256"]:
            raise ValueError("RUN_SOURCE_FINGERPRINT_MISMATCH")
        last = report["stages_attempted"]
        model, checkpoint = load_checkpoint(folder / f"stage-{last:02d}.pt")
        if checkpoint["state_hash"] != report["state_hash"] or checkpoint["initialization"] != manifest["init"]:
            raise ValueError("CHECKPOINT_REPLAY_MISMATCH")
        stage_log = json.loads((folder / f"stage-{last:02d}.json").read_text())
        if "primer" in stage_log:
            history = tuple(CompletedTurn(t["record"], t["student_answer"])
                            for t in stage_log["primer"])
            standalone = score(predict(model, fixed_gate(checkpoint["stage"])))
            dialogue = score(predict(model, fixed_gate(checkpoint["stage"]),
                                     histories=[history] * len(fixed_gate(checkpoint["stage"]))))
            for key, computed in (("standalone_gate", standalone),
                                  ("dialogue_gate", dialogue)):
                recorded = stage_log[key]
                if (computed["correct"], computed["n"]) != (recorded["correct"], recorded["n"]):
                    raise ValueError("CONTEXT_GATE_REPLAY_MISMATCH")
            gate = dialogue if checkpoint["stage"] == "D00.PROTOCOL" else standalone
        else:
            gate = score(predict(model, fixed_gate(checkpoint["stage"])))
        record = report["briefs"][-1]
        if (gate["correct"], gate["n"]) != (record["gate"]["correct"], record["gate"]["n"]):
            raise ValueError("GATE_REPLAY_MISMATCH")
        comparisons.append({"arm": arm, "state_hash": checkpoint["state_hash"],
                            "gate": {k: gate[k] for k in ("correct", "n")},
                            "stage": checkpoint["stage"]})
    if len(comparisons) < 2:
        raise ValueError("NOT_COMPARATIVE_RUN")
    return {"status": "REPLAY_VERIFIED", "arms": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=320)
    parser.add_argument("--remedy-steps", type=int, default=96)
    parser.add_argument("--max-stages", type=int, default=6)
    parser.add_argument("--seed", type=int, default=211)
    parser.add_argument("--teacher-endpoint", default="http://127.0.0.1:8008")
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    outcome = (replay(args.out) if args.replay else run(
        args.out, steps=args.steps, remedy_steps=args.remedy_steps, max_stages=args.max_stages,
        seed=args.seed, teacher_endpoint=args.teacher_endpoint))
    print("FINAL:", json.dumps(outcome, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
