"""Bounded local foundation teaching epoch with real Kev lesson/exam selection.

Run: python -m bilqis_formal.pilot --out runs/formal-foundations-epoch1
This command never downloads model weights, merges branches, or edits prior runs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import random
import time

import torch
from torch.nn import functional as F

from bilqis_ref.model import batch, state_hash
from .curriculum import STAGES, fixed_gate, mandatory_train, panels, validate_course
from .kevlab import KevTeacher, choose, select_panel
from .semantics import LAWS, TOKENS, digest, encode, verify_registry
from .student import StudentConfig, init_student, load_checkpoint, predict, save_checkpoint


VERSION = "foundation-pilot-v0.1"


def write_new(path, obj):
    with path.open("x", encoding="utf8") as f:
        json.dump(obj, f, sort_keys=True, indent=2)
        f.write("\n")


def score(predictions):
    def part(rows):
        good = sum(p["prediction"] == p["gold"] for p in rows)
        return {"correct": good, "n": len(rows), "accuracy": good / len(rows) if rows else None}
    return {**part(predictions), "by_tier": {k: part([p for p in predictions if p["tier"] == k])
                                             for k in sorted({p["tier"] for p in predictions})},
            "errors": [p for p in predictions if p["prediction"] != p["gold"]]}


def mastered(stage, preds):
    result = score(preds)
    # Every case in this tiny fixed gate is required. There is no promotion
    # by mean loss or time budget. A more permissive threshold needs approval.
    return result["correct"] == result["n"]


def train_steps(model, optimizer, rng, new_rows, old_rows, steps):
    if not new_rows:
        raise ValueError("EMPTY_TEACHING_SET")
    tokens = 0
    for i in range(steps):
        batch_rows = rng.choices(new_rows, k=24 if old_rows else 32)
        if old_rows:
            batch_rows += rng.choices(old_rows, k=8)
        rng.shuffle(batch_rows)
        sequences = [encode(r["input"]) for r in batch_rows]
        tokens += sum(len(x) for x in sequences)
        if max(map(len, sequences)) > model.cfg.context:
            raise ValueError("TEACHING_CONTEXT_OVERFLOW")
        ids, lengths = batch(sequences)
        gold = torch.tensor([int(r["gold"]) for r in batch_rows], dtype=torch.long)
        optimizer.zero_grad(set_to_none=True)
        logits = model(ids, lengths)
        loss = F.cross_entropy(logits, gold)
        if not bool(torch.isfinite(loss)):
            raise ValueError("NONFINITE_LOSS")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
    return {"optimizer_updates": steps, "exposures": steps * 32, "tokens": tokens,
            "final_loss": float(loss.detach())}


def run(out: Path, *, max_stages=6, steps=320, seed=211, teacher_endpoint="http://127.0.0.1:8008"):
    if not 1 <= max_stages <= len(STAGES) or not 1 <= steps <= 1024:
        raise ValueError("BOUNDED_BUDGET")
    verify_registry()
    validate_course()
    # Fail early rather than silently pretending the service ran. No open-ended
    # model loading or automatic launch of a heavyweight remote backend.
    teacher = KevTeacher(teacher_endpoint)
    model, init_info = init_student(StudentConfig(), seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.002, betas=(.9, .95),
                                  eps=1.e-8, weight_decay=.01, foreach=False)
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    write_new(out / "manifest.json", {"version": VERSION, "semantic_version": "bilqis.formal.f0/v0.1.0",
               "genesis_sha256": state_hash(model), "token_ids": dict(enumerate(TOKENS)),
               "law_ids": list(LAWS), "initializer": init_info, "seed": seed,
               "max_stages": max_stages, "steps_per_stage": steps,
               "max_native_kev_choice_calls": 6 * max_stages,
               "gold_in_neural_input": False, "student_pretrained": False,
               "teacher_is_truth_authority": False,
               "learned_stages": [], "prior_weights_imported": False})
    logs = []
    prior_rows = []
    retained_gates = []
    status = "BUDGET_COMPLETE"
    for stage in STAGES[:max_stages]:
        if not set(stage.prerequisite) <= {x["stage"] for x in logs if x["promoted"]}:
            status = "UNMET_PREREQUISITE"
            break
        gate = fixed_gate(stage.id)
        before = score(predict(model, gate))
        lesson_panels = panels(stage.id, "lesson")
        selection = (choose(stage.id, "lesson", lesson_panels, teacher=teacher,
                            recent_errors=tuple(e["family"] for e in before["errors"][:5]))
                     if len(lesson_panels) >= 2 else
                     {"status": "NO_COMPOSITION_YET", "selected_id": None, "order_votes": [], "traces": []})
        chosen_lesson = select_panel(lesson_panels, selection)
        stage_train = mandatory_train(stage.id) + (list(chosen_lesson.rows) if chosen_lesson else [])
        training = train_steps(model, optimizer, rng, stage_train, prior_rows, steps)
        post_training_preview = score(predict(model, gate))
        # The same score-and-permute procedure chooses formative exams. It does
        # not define the fixed promotion gate or alter any oracle answer.
        exam_panels = panels(stage.id, "exam")
        exam_selection = (choose(stage.id, "exam", exam_panels, teacher=teacher,
                                 recent_errors=tuple(e["family"] for e in post_training_preview["errors"][:5]))
                          if len(exam_panels) >= 2 else
                          {"status": "NO_COMPOSITION_YET", "selected_id": None,
                           "order_votes": [], "traces": []})
        chosen_exam = select_panel(exam_panels, exam_selection)
        exam = score(predict(model, list(chosen_exam.rows))) if chosen_exam else None
        gate_preds = predict(model, gate)
        after = score(gate_preds)
        promoted = mastered(stage.id, gate_preds)
        retention = {old_stage: score(predict(model, rows)) for old_stage, rows in retained_gates}
        if any(s["correct"] != s["n"] for s in retention.values()):
            promoted = False
            status = "RETENTION_STOP"
        elif not promoted:
            status = "MASTERY_STOP"
        entry = {"stage": stage.id, "new_semantic_id": stage.new_id,
                 "prerequisites": stage.prerequisite, "before": before, "after": after,
                 "lesson_selection": selection, "exam_selection": exam_selection,
                 "lesson_id": chosen_lesson.id if chosen_lesson else None,
                 "exam_id": chosen_exam.id if chosen_exam else None, "exam": exam,
                 "training": training, "retention": retention, "promoted": promoted,
                 "student_state_sha256": state_hash(model),
                 "real_kev_choice_calls": sum(t.get("choice_calls", 0) for t in selection["traces"])
                                          + sum(t.get("choice_calls", 0) for t in exam_selection["traces"])}
        logs.append(entry)
        write_new(out / f"stage-{len(logs):02d}.json", entry)
        save_checkpoint(out / f"stage-{len(logs):02d}.pt", model, optimizer, stage.id, after, init_info)
        print(f"{stage.id}: before {before['correct']}/{before['n']}, "
              f"after {after['correct']}/{after['n']}, "
              f"lesson={selection['status']}, exam={exam_selection['status']}, "
              f"promoted={promoted}", flush=True)
        if not promoted:
            break
        prior_rows += stage_train
        retained_gates.append((stage.id, gate))
    report = {"version": VERSION, "status": status, "stages_completed": len(logs),
              "stages_promoted": sum(bool(x["promoted"]) for x in logs),
              "student_state_sha256": state_hash(model),
              "optimizer_updates": sum(x["training"]["optimizer_updates"] for x in logs),
              "kev_calls": sum(x["real_kev_choice_calls"] for x in logs),
              "elapsed_seconds": time.perf_counter() - start,
              "stage_briefs": [{k: x[k] for k in ("stage", "new_semantic_id", "before", "after",
                              "lesson_id", "exam_id", "retention", "promoted")}
                              for x in logs]}
    write_new(out / "report.json", report)
    print("FINAL:", json.dumps({k: v for k, v in report.items() if k != "stage_briefs"},
                                sort_keys=True), flush=True)
    return report


def replay(out):
    manifest = json.loads((out / "manifest.json").read_text())
    report = json.loads((out / "report.json").read_text())
    checkpoint = out / f"stage-{report['stages_completed']:02d}.pt"
    model, saved = load_checkpoint(checkpoint)
    if state_hash(model) != report["student_state_sha256"] or saved["initializer"] != manifest["initializer"]:
        raise ValueError("REPLAY_STATE_MISMATCH")
    return {"status": "REPLAY_VERIFIED", "model_sha256": state_hash(model),
            "stage": saved["stage"], "final_gate": score(predict(model, fixed_gate(saved["stage"])))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--max-stages", type=int, default=6)
    ap.add_argument("--steps", type=int, default=320)
    ap.add_argument("--seed", type=int, default=211)
    ap.add_argument("--kev", default="http://127.0.0.1:8008")
    ap.add_argument("--replay", action="store_true")
    args = ap.parse_args()
    if args.replay:
        print(json.dumps(replay(args.out), sort_keys=True, indent=2))
    else:
        run(args.out, max_stages=args.max_stages, steps=args.steps, seed=args.seed,
            teacher_endpoint=args.kev)


if __name__ == "__main__":
    main()
