"""Read-only 2x4 context ablation on already-preserved dialogue checkpoints.

No gradients, optimizer steps, model loading from network, or new teacher calls.
Historical checkpoints and sealed gate files are never modified.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .course_v2 import fixed_gate, mandatory_train
from .dialogue import CompletedTurn, gold_label
from .pilot_v2 import score
from .student_v2 import load_checkpoint, predict


def diagnose(out):
    reports = {}
    for arm in ("feedback-context", "answer-only-control", "no-context-control"):
        root = out / arm
        if not root.exists():
            continue
        report = json.loads((root / "report.json").read_text())
        if report["stages_attempted"] == 0:
            continue
        model, checkpoint = load_checkpoint(root / f"stage-{report['stages_attempted']:02d}.pt")
        stage = checkpoint["stage"]
        gate = fixed_gate(stage)
        completed = mandatory_train(stage)
        # Explicit, oracle-checked contrasting examples, not the held-out gate.
        good = CompletedTurn(completed[0]["input"], gold_label(completed[0]["input"]))
        wrong = CompletedTurn(
            completed[-1]["input"],
            ("ATOM.FALSE" if gold_label(completed[-1]["input"]) == "ATOM.TRUE" else
             "ATOM.TRUE" if gold_label(completed[-1]["input"]) == "ATOM.FALSE" else
             "FEEDBACK.INCORRECT" if gold_label(completed[-1]["input"]) == "FEEDBACK.CORRECT"
             else "FEEDBACK.CORRECT"))
        contexts = {
            "closed_book": (),
            "one_correct_turn": (good,),
            "one_corrected_error": (wrong,),
            "two_contrasting_turns": (good, wrong),
        }
        reports[arm] = {"stage": stage, "results": {}}
        for label, history in contexts.items():
            ps = predict(model, gate, histories=[history] * len(gate))
            s = score(ps)
            reports[arm]["results"][label] = {
                "correct": s["correct"], "n": s["n"],
                "by_task": s["by_task"], "by_gold": s["by_gold"],
                "errors": s["errors"]}
    return reports


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(diagnose(args.out), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
