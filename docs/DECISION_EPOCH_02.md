# Decision epoch 02

BILQIS-DN-01 extends the sourced alpha with typed, multi-step semantic decisions.
The formal cognitive algebra owns transitions and oracle targets. Native local
EmbeddingGemma 2 supplies frozen neighborhoods; trained native Kev chooses legal
continuations and orders prerequisite-eligible curriculum blocks. Two fresh
students learn oracle targets from exactly the same frozen batches.

This is one exploratory matched pair, with a historically exposed semantic
domain. The newly withheld compositions are not independent SEALED evidence.
The role-sensitive initializer is shared by both arms, so this pair cannot
attribute its effect independently. Treatment also receives nonsealed DEV
feedback; the comparison measures that integrated teaching policy.

From the decision worktree, using the existing separate local environments:

```sh
.venv/bin/python -m bilqis_alpha.decision_experiment prepare
.venv/bin/python -m bilqis_alpha.decision_experiment qualify
.venv/bin/python -m bilqis_alpha.decision_experiment train-pair
.venv/bin/python -m bilqis_alpha.decision_experiment evaluate
.venv/bin/python -m bilqis_alpha.decision_experiment replay
.venv/bin/python -m bilqis_alpha.decision_experiment replay --live
```

`prepare` binds the old alpha checkpoint, source files, dataset, splits, feature
projection, control codec and fresh checkpoint. `qualify` uses the already
installed EG2 environment and local BF16 weights, and verifies actual native
Kev System One responses at `http://127.0.0.1:8008`. No helper vectors, weights,
soft labels, or held-out feedback enter the student optimizer.

The default run is `runs/decision-epoch-02`. Preparation, qualification,
training and evaluation create exclusive receipts. Training admits one pair
only: 16 blocks × 96 optimizer steps × batch 32 per arm. Do not rerun training
to improve an observed outcome. Each live replay creates a separate immutable
directory under `live-replays/`; archived replay reruns the saved neural
students and verifies their recorded choices and numeric outputs.

The primary endpoint is exact held-out semantic-path correctness under actual
student rollout. Final truth accuracy, wrong-intermediate/right-terminal cases,
retrieval recall, hard-negative margins, Kev decision/fallback frequencies and
resources are reported separately. Ternary-forward arithmetic uses FP32 master
weights and float emulation; it does not establish native low-bit acceleration.

Text evidence and the result report are in `docs/evidence/decision-epoch-02/`.
Checkpoints remain local and ignored. See that directory's handoff for the
exact local paths, checksums and qualified runtimes. The historical alpha and
its microscope remain separate evidence.

Focused tests: `.venv/bin/python -m unittest discover -s tests -p 'test_decision*.py' -v`.
Repository suite: `.venv/bin/python -m unittest discover -s tests -v`.
