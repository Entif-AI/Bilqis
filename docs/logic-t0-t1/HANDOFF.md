# T0/T1 logic pilot recovery handoff

Mission: train one tiny scratch neural student on classical Boolean cognitive
algebra, then independently measure primitive acquisition, unseen compositions,
and universal equivalence over variables P/Q. The controlling contract is
`CONTRACT.md`. This is an exploratory pilot, not SYS-01 or full COGAL acceptance.

Branch: `codex/t0-t1-logic-pilot`, independently based on main `97de390`.
Historical ALPHA-01/02 and Decision Epoch 02, PRs #104/#105/#106, are preserved.
No inherited checkpoints, pretrained weights, vectors or hidden states are used.
EG2/Kev remain admissible upstream helpers; exhaustive truth tables suffice here,
so this epoch uses zero helper calls. Numeric inputs contain unreduced typed
prefix expressions and explicit assignments, or two expressions for equivalence.

Implementation: `bilqis_logic/{kernel,geometry,model,data,pilot}.py`. Reuses
`bilqis_ref.model.Block`, batching and state hashes. The neural prediction path
does not call the oracle. The two independent evaluators are a frozen table lookup
and operational Boolean algebra. T0 here covers Boolean typing, P/Q, arity and
operand order; no relational, proof, unknown/conflict or natural-language curriculum.

The fixed primary run uses seed 111, semantic_aligned, CPU FP32, width 64, two
layers, four heads, context 64, AdamW lr 0.002, batch 32. Phase A: 256 primitive
steps over all 26 truth-table rows. Phase B: 768 steps, each with 8 primitive,
12 equivalence and 12 short-composition examples. Total: 1,024 steps / 32,768
exposures. All inputs and gold are frozen before optimization. Step-zero inference
over all planes is prescribed baseline evidence; no scores alter the fixed schedule.

Aligned/random/permuted initializer interfaces exist, but only the aligned pilot
is trained. No attempt to claim an initialization advantage is possible here.

Current state: source implemented; formal/codec/geometry/neural-update tests pass.
Next executable step: run the full suite, commit source, freeze once, then train
once and replay in a fresh process. Commands from this worktree, using an installed
Python 3.13/PyTorch environment:

```sh
python -m unittest discover -s tests -v
python -m bilqis_logic.pilot freeze --config configs/logic-t0-t1.json --out runs/logic-t0-t1/epoch-01
python -m bilqis_logic.pilot train --run runs/logic-t0-t1/epoch-01
python -m bilqis_logic.pilot replay --run runs/logic-t0-t1/epoch-01
```

The proven local interpreter is
`/Users/emilie/.codex/worktrees/bilqis-alpha-102/Bilqis/.venv/bin/python`.
No model service is required. Freeze/training files are immutable; an existing
`training.jsonl` prevents starting another cycle. Preserve a partial run and its
failure; do not overwrite or tune/retrain on the held-out scores. Binaries remain
under ignored `runs/`; compact text evidence and the final result will be committed
under `docs/evidence/logic-t0-t1/epoch-01/`.

No merge is authorized. Push the independent branch and create a review PR after
recording the actual outcomes, numerical resources, replay and remaining limits.
