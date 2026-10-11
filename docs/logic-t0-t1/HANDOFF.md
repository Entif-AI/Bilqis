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

Current state: the one authorized aligned cycle is complete. Training source commit:
`9feac699983c22201cb6aafa465a7c0b5e4f06bd`. See
[`RESULTS.md`](../evidence/logic-t0-t1/RESULTS.md) and the complete committed text
bundle under `docs/evidence/logic-t0-t1/epoch-01/`.

Primitive accuracy: step zero 12/26, Phase A 24/26, final 23/26. All three required
lessons are correct after Phase A; the final checkpoint forgets TRUE XOR TRUE.
Final unseen composition: 112/192; balanced equivalence: 39/64; directional
implication negative: 1/1. The disposition is partial acquisition with a retention
failure, not complete mastery. Preserve both checkpoint outcomes.

All 1,024 steps / 32,768 exposures are accounted for; 253,755 nonpadding tokens,
341,696 padded positions. Recorded training interval: 3.224755 seconds wall,
3.172154 seconds CPU, peak process RSS 286,539,776 bytes. Semantic preparation and
step-zero freeze: 0.455622 seconds wall, 0.439520 seconds CPU. Zero helper calls.
40 tests pass, no failures/errors/skips. Fresh-process replay reproduces 936
predictions, logits and probabilities with maximum absolute error 0.0.

Checkpoint file SHA-256:

- Initial: `036b9e1ae088a0977ad0c3e0595d8fedf0b1783505ebad5c6a1aada7ac506869`
- Phase A: `f597fcaa8e917616a864cc4187452bcc9acf7a9f3bd8ebabe3d386011e64a1ec`
- Final: `464e68cf81ed4ce235be6bbfd1ac474c11f97d2a4e13e95397a3943d55df5cfa`

Next executable step is read-only replay of the preserved run, using an installed
Python 3.13/PyTorch environment from this worktree:

```sh
python -m unittest discover -s tests -v
python -m bilqis_logic.pilot replay --run runs/logic-t0-t1/epoch-01
```

To reproduce the fixed cycle elsewhere, use a fresh directory and the unchanged
config; this does not overwrite or extend the recorded attempt:

```sh
python -m bilqis_logic.pilot freeze --config configs/logic-t0-t1.json --out runs/logic-t0-t1/reproduction-01
python -m bilqis_logic.pilot train --run runs/logic-t0-t1/reproduction-01
python -m bilqis_logic.pilot replay --run runs/logic-t0-t1/reproduction-01
```

The proven local interpreter is
`/Users/emilie/.codex/worktrees/bilqis-alpha-102/Bilqis/.venv/bin/python`.
No model service is required. Freeze/training files are immutable; an existing
`training.jsonl` prevents starting another cycle. Preserve a partial run and its
failure; do not overwrite or tune/retrain on the held-out scores. Binaries remain
under ignored `runs/`; compact text evidence and the final result will be committed
under `docs/evidence/logic-t0-t1/epoch-01/`. No experimental repair or second cycle
was performed. No remaining execution blocker; full mastery and retention are unmet.

No merge is authorized. The independent branch and its source/evidence review PR
are the publication boundary. `git rev-parse HEAD` identifies the publication
commit; `gh pr view --repo Entif-AI/Bilqis codex/t0-t1-logic-pilot` resolves its PR.
