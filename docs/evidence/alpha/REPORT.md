# BILQIS-ALPHA-01 — frozen exploratory result

As of 2026-10-11, terminal disposition: **ALPHA_DEMO_REPRODUCED** under the
exploratory replay/learning definition. This does not certify reliable compositional
reasoning. Generalization beyond this two-object domain is unproven.

The sourced #80/#7 semantic registry and #81/#62 initializer are alpha version
0.1.0. Exact live issue bodies/comments are preserved in `source-contracts.json`.
The base is `97de3909f11652255de2fa60d932ac71578f0665`; training code is
`32bed02cc4dd871016db23e25319b8c789194d7d`. The model inherits no pretrained weights.
CP0008 code, ABI and requirements remain byte-identical to the base.

| Plane | Before training | Trained | Trained macro accuracy |
| --- | ---: | ---: | ---: |
| TRAIN | 848/2,944 | 1,735/2,944 (58.9%) | 58.8% |
| DEV | 323/1,152 | 676/1,152 (58.7%) | 59.0% |
| HELDOUT | 414/1,024 | 476/1,024 (46.5%) | 45.5% |
| Named neural boundaries | 4/15 | 6/15 | 45.8% |

The before-training witness uses the same semantic-aligned model before any
optimizer step; it is not a trained IID control. Heldout macro accuracy rose
from 31.2% to 45.5%. The withheld patterns are NOT(AND), AND with a negated
relation, EXISTS over a mutual relation conjunction, and OR with a negated
relation. Complete memberships, label counts and corpus hashes predate training.
All 1,024 heldout predictions, including 548 mistakes, are retained.

Learning is modest. Direct relation and negation accuracy remain poor; sparse
named worlds often elicit UNKNOWN even for TRUE, FALSE or CONFLICT. Nine of the
15 named neural boundaries fail, including positive evidence, negative evidence,
role reversal, conflict and logical/evidential contrasts. The scope pair
NOT(EXISTS R) versus EXISTS(NOT R), equality, and one previously unseen mutual
EXISTS composition are answered correctly. These successes cannot erase failures.
See every case in `epoch-01/predictions.jsonl` and the full failure inventory.

One complete cycle: seed 102, 76,160 trainable parameters, two transformer layers,
width 64, four heads, expansion 2, context 128, vocabulary 33. AdamW lr 0.001,
weight decay 0.01, batch 32, 1,536 steps: **49,152 exposures, 2,415,782 nonpadding
tokens, 3,492,608 padded tokens**. A stage checkpoint survives at step 512.
No second cycle or efficacy-control run was used. Initializer, gradient and
checkpoint engineering fixtures (including historical reference smoke tests) are
separate from the complete exploratory-cycle budget.

CPU FP32 arithmetic with ternary-forward/int8 activation emulation; embeddings,
answer readout, master weights and optimizer remain FP32. Apple M3 Ultra,
Python 3.13.12, Torch 2.10.0. Full preparation/train/probe/evaluation cycle:
**41.95 s wall, 41.62 s CPU, peak process RSS 378,568,704 bytes**. This is process
memory, not model-only memory. Energy and development-token costs were not measured.
MPS was available but unqualified here; no GPU or packed low-bit efficiency claim.

Checkpoint file SHA-256:
`002cffcfbdf44eec2e509704d5a530bb134d655919ec129f46eeffda6b99a3eb`.
Final model-state SHA-256:
`850e579506d6c68fa0873900d2f9a6b920058c52108cd0e03cdd0ca2f28aef10`.
Initial state:
`331c5294a2023a8aacec26f6166b36c7583175035e70480b1e7cbd59e817e542`.
See `epoch-01/run.json` for semantic, token, initializer, split and source bindings.
Binaries are preserved locally at `runs/alpha/epoch-01/` under contribution policy.

Verification: 40 test methods, zero failures/errors/skips, including all 29
historical reference tests. Authored four-state tables, raw evidence fixtures,
binding/scope, illegal input rejection, canonical codec round trips, split isolation,
pre-step geometry, semantic/token permutations, ternary forward/gradient, changed
parameters, checkpoint reload, and inference with the oracle disabled pass.
The intentionally injected UNKNOWN→FALSE label defect is caught and restored;
no corrupted label entered training. Fresh-process inference replays all 5,135
saved final predictions at absolute logit tolerance 1e-6.

Before training, tests caught the absent alpha package/feature modules during red
and a missing `x` variable token mapping during implementation. The mapping was
corrected and inputs frozen before step one. There were no failed full training
attempts. All neural mistakes are retained, rather than treated as harness errors.

Missing qualification: cold human/specification audit, a second independent oracle,
independent sealed generator families, multiple seeds, matched trained controls,
MPS/CPU parity and recovery qualification, native low-bit implementation, full
T0–T4/proofs/ambiguity, mathematical and Rosetta epistemic substrate, full curriculum
and #86 freeze. None of #52/#64 or #22–#25's acceptance is fulfilled by this result.

Next smallest justified experiment, not executed: isolate directed-relation binding
on the already frozen role-reversal and sparse evidence cases before widening the
domain or spending on another architecture/backend. A separate next epoch can test
whether the weak atomic lookup is representation access, optimization or capacity;
these data are alpha-exposed and cannot become independent SYS-01 sealed tests.
