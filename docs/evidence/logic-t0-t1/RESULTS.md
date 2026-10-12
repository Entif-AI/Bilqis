# T0/T1 logic pilot: partial acquisition with a retention failure

As of October 11, 2026, one real scratch neural cycle is complete and replayed.
The exhaustive primitive score rose **12/26 → 24/26 after Phase A**, then fell to
**23/26 after Phase B**. All three required lessons were correct after Phase A.
The final checkpoint forgot `XOR(TRUE,TRUE)=FALSE`, predicting TRUE at probability
0.906686. Preserve the Phase A and final checkpoints. The complete mission's
mastery/retention criterion is not established by this exploratory result.

| Plane | Step zero | Fixed-budget final |
|---|---:|---:|
| Exhaustive primitives | 12/26 (46.15%) | 23/26 (88.46%) |
| Familiar short algebra | 52/108 (48.15%) | 93/108 (86.11%) |
| Familiar equivalence pairs | 20/40 (50.00%) | 34/40 (85.00%) |
| DEV compositions | 11/24 (45.83%) | 15/24 (62.50%) |
| Unseen composition trees | 91/192 (47.40%) | 112/192 (58.33%) |
| Unseen equivalence pairs | 24/64 (37.50%) | 39/64 (60.94%) |
| Directional implication negative | 0/1 (0.00%) | 1/1 (100.00%) |

Phase A: 256 steps, 8,192 exposures, 24/26 (92.31%). By operator: NOT 2/2, AND 4/4,
OR 3/4, XOR 3/4, XNOR 4/4, IMPLIES 4/4, IFF 4/4. Its two failures are OR(FALSE,FALSE)
and XOR(FALSE,FALSE). Final failures are IFF(FALSE,FALSE), XOR(TRUE,TRUE), and
IMPLIES(FALSE,FALSE). All 26 neural predictions are in `epoch-01/primitive-predictions.csv`;
raw logits and probabilities are in `step-zero.json`, `after-A.json`, and
`final-predictions.json`.

Final composition accuracy is 58.33%, compared with a constant-majority baseline
of 101/192 (52.60%); label-macro accuracy is 59.25%. Held-out equivalence is balanced:
19/32 equivalent and 20/32 non-equivalent pairs are correct, total 39/64 (60.94%),
compared with a 50% constant baseline. These are descriptive one-seed results;
there is no independent seal, trained initializer control, or confirmatory inference.
The initial semantic features already contain the authorized primitive operator
signatures. No claim that their alignment causes a learning advantage is possible.

Concrete unseen success: with P=TRUE, Q=TRUE,
`XNOR(XNOR(P,Q),NOT(P))` has formal FALSE and neural FALSE (probability 0.784461).
Concrete unseen failure: with P=FALSE, Q=TRUE,
`XOR(IFF(P,Q),NOT(P))` has formal TRUE but neural FALSE (probability 0.933371).
The directional pair `IMPLIES(P,Q)` / `IMPLIES(Q,P)` is correctly judged non-equivalent.
At P=TRUE, Q=FALSE their independent formal outputs are FALSE / TRUE.
`epoch-01/gallery.json` retains exact typed ASTs, encoded inputs and neural outputs.

## Frozen system and attempt

Source/training commit: `9feac699983c22201cb6aafa465a7c0b5e4f06bd`. Independent branch:
`codex/t0-t1-logic-pilot`, based on main `97de3909f11652255de2fa60d932ac71578f0665`.
Package SemVer 0.2.0; kernel/data/student/initializer contracts 0.1.0.
The unchanged reference transformer blocks, batching and hash functions are reused.
Architecture: vocabulary 17, context 64, width 64, two causal decoder layers,
four heads, expansion 4, tied FALSE/TRUE embedding readout; **103,808 trainable
parameters**. CPU FP32 throughout; no pretrained weights, vectors or hidden states.

Initializer: `cogal-dct-0.1.0`, profile `semantic_aligned`, seed 111. Formal features
encode stable identities, Boolean type, arity, argument roles, primitive truth
signatures, symmetry, directionality, equivalent IFF/XNOR and validated complement
edges. A fixed DCT-II projection, row RMS 0.02 and FP32 cast produces embeddings.
The complete graph, feature basis, transform hash, token mapping, per-tensor
initial hashes and preparation provenance were frozen before optimization.
`iid_random` and `semantic_permuted` share the same architecture/interface; tests
verify reproducibility and preserved permutation vector multiset. Neither control
was trained. Embeddings are unquantized; this is not a ternary-efficiency result.

AdamW: lr 0.002, betas (0.9,0.95), eps 1e-8, weight decay 0.01, clip norm 1.
One fixed cycle: **1,024 steps × batch 32 = 32,768 exposures**, **253,755 nonpadding
tokens**, **341,696 padded computation positions**. Phase B has 8 primitive,
12 equivalence and 12 composition items per batch. Its 40 equivalence lessons are
balanced; all 174 distinct TRAIN rows received exposures. No adaptive selection,
score-driven repair, second experimental cycle or comparison training occurred.
Normal unit validation also performs tiny two-example gradient/update checks;
those checks are separate from this experimental budget.

Preparation/freeze, including step-zero inference: 0.455622 s wall,
0.439520 s CPU. Training process: **3.224755 s wall**,
3.172154 s CPU, **286,539,776 bytes peak RSS**.
Measured buckets: 0.251226 s batch preparation,
2.512160 s optimization, 0.022584 s evaluation.
These process timings exclude interpreter startup, implementation and unit-test work;
peak RSS includes imports/optimizer state. Energy was not measured.
Helper preparation: **zero EG2/Kev calls, zero helper seconds, zero external spend**.
Qualified helpers remain admissible upstream; the frozen truth tables suffice here.

TRAIN/DEV/HELDOUT were audited before training. No exact evaluation input enters
optimizer batches; commutative operator-tree signatures ignoring literal values
and variable names distinguish TRAIN from DEV/HELDOUT and DEV from HELDOUT.
Held-out composition has 48 unfamiliar tree structures and all four P/Q assignments.
Held-out equivalence has 32 positives / 32 negatives with novel endpoint structures.
The hard negative intentionally uses familiar primitive operator endpoints in a
new pair; it is reported separately from composition transfer. No reduced truth
function, evaluated subtree or gold label appears in input encoding or per-example
initialization. Two independent executable grading paths agree on every frozen row.
Both use developer-authored formal semantics; human/specification independence is
not claimed. Prescheduled step-zero inference includes HELDOUT; scores never alter
the fixed curriculum. Only primitive rows are scored at the Phase A boundary.

## Artifact identities and verification

- Freeze SHA-256: `7de651d2aff1999fa23269a920826aca8cb01e6189bf72e3980f29a27626948a`
- Full data SHA-256: `5a2f54eeb7616075f54f8b4358d1b4a2281e889c674200331e116c7aeb93aa73`
- Initial embedding SHA-256: `31b22f09ff9de436753bff7a168e68519e5ee48261fc8bc35abddb529c0619de`
- Initial model-state SHA-256: `dd7bb9d516abf4b704857731e861b6c3ef0c087e82bef539ba1a419a61d34926`
- Initial checkpoint SHA-256: `036b9e1ae088a0977ad0c3e0595d8fedf0b1783505ebad5c6a1aada7ac506869`
- Phase A checkpoint SHA-256: `f597fcaa8e917616a864cc4187452bcc9acf7a9f3bd8ebabe3d386011e64a1ec`
- Final checkpoint SHA-256: `464e68cf81ed4ce235be6bbfd1ac474c11f97d2a4e13e95397a3943d55df5cfa`
- Final model-state SHA-256: `877a818ed6e87529bf67fef21047580a9ff7aa9b4241d7a4a18c33241e0d75e6`

Per-split, token-ABI, graph, feature, projection and every tensor hash are in
`epoch-01/{splits,initializer,freeze,result}.json`. All text artifacts, full raw
optimizer exposure trace and complete predictions are committed in `epoch-01/`.
Model/optimizer binaries remain in ignored `runs/logic-t0-t1/epoch-01/` under
repository contribution policy. `CHECKSUMS.sha256` binds the committed text bundle.

**40 tests passed**, zero failures/errors/skips. The tests include incorrect-label
injection, leakage rejection, numerical initializer controls, oracle-free neural
prediction and actual gradient/parameter updates. The full recorded optimizer
trace independently verifies all 32,768 exposures belong to TRAIN and reproduces
both token totals. A fresh process reloaded initial, Phase A and final checkpoints
and reproduced **936 predictions/logits/probabilities**, maximum absolute error
**0.0** (allowed atol 1e-6). No experimental repair was needed.

From this worktree, replay the preserved binaries with the proven local interpreter:

```sh
/Users/emilie/.codex/worktrees/bilqis-alpha-102/Bilqis/.venv/bin/python -m bilqis_logic.pilot replay --run runs/logic-t0-t1/epoch-01
```

A new reproduction directory can be frozen and trained using the commands in
`../../logic-t0-t1/HANDOFF.md` and the committed config. An existing training log
is a hard stop against overwriting or repeating this attempt. Exact numerical
replay is proven on this local Python 3.13.12/PyTorch
2.10.0 CPU runtime; other hardware/runtime reproduction
is untested. There is no blocker to reviewing this complete measured attempt.
Full primitive mastery, reliable retention and robust compositional generalization
remain unmet. No additional run is hidden or selected away.

Historical ALPHA-01/02 and Decision Epoch 02 were untouched. PRs #104/#105/#106
remain open and unmerged at their previous heads; both historical worktrees are
clean. This pilot's source is independent of those PRs. No merge or release occurred.
