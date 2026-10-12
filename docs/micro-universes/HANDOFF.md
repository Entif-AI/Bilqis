# Bilqis developmental micro-universes handoff

## Mission and authority

Implement and train one continuing scratch learner through U0–U3, adding evidence if practical. The controlling execution contract is `docs/micro-universes/CONTRACT.md`, copied from the user prompt for Bilqis #108. It supersedes older training directions. Commit, push and create a PR stacked against the open #107 were authorized. Merge is not authorized. Do not resume DN-01, ALPHA, controls, ablations, SYS-01, helper qualification or auxiliary fine-tuning.

## Identities and current increment

Repository: Entif-AI/Bilqis. Branch: `codex/108-developmental-micro-universes`.
Worktree: `/Users/emilie/.codex/worktrees/bilqis-micro-universes/Bilqis`.
Starting predecessor: PR #107, branch `codex/t0-t1-logic-pilot`, head `d4a7d36dabfd0c322589888a56c220d96da866bb`. It was verified open and unmerged. The implementation used for training is commit `4e4caba3dcf1ea562512225536825b38eee2424a`; the run also binds every executable source file by SHA-256. `bilqis_logic`, `bilqis_ref` and their historical evidence are unchanged.

The feature is implemented in `bilqis_micro/` at component version 0.1.0; project version is 0.3.0. The complete run is `docs/evidence/micro-universes/run-01/`. See `docs/evidence/micro-universes/RESULTS.md` for measured scores and mistakes.

## Completed execution

- Complete 68-token typed semantic catalog, preserving the first 17 IDs. Features encode signatures, families, roles, inverses, negation, binding, quantifiers, prerequisites, composition, proof and evidence. Stable keyed projection and append-only tests preserve all old initial coordinates and IDs.
- Typed closed finite worlds with 2–5 entities, raw directional PARENT facts, inverse CHILD, symmetric LINK, equality/inequality, de Bruijn binding, EXISTS/FORALL and two-hop composition. PARENT is not transitive.
- Declared parent-parent GRANDPARENT inference, rule-step validity, closure entailment and candidate countermodels. This is finite Horn-rule closure, not unrestricted proof search.
- Explicit evidence support/refutation bits, independent of closed-world fact truth; missing reports UNKNOWN, both channels CONFLICT, divergent live interpretation results AMBIGUOUS. Boolean and evidence operators keep separate identities.
- Set/table versus adjacency/operational gold cross-checks, exhaustive small-world tests, strict field/type/scope validation, lossless raw-world/unreduced-AST codec, and an inference test forbidding gold-oracle calls.
- One 348,192-parameter FP32 scratch student, width 96, three layers, six heads, context 96, seed 108. One AdamW optimizer with lr 0.0015. Both persisted through all stages without reset. No pretrained numerical transfer, helpers, external helper spend or previous learner checkpoint was used.
- Stage budgets U0=800, U1=1800, U2=2200, U3=2000, U4=1600. Total 8,400 updates, 268,800 examples, 6,718,889 nonpadding tokens. Each batch includes 12 focus, 8 compositions, two contrast pairs and 8 rehearsal examples. Four rehearsal examples always carry Boolean primitives.
- Stage/checkpoint parent hashes, optimizer-step and moment hashes, identity exposure, all row exposures, training loss, time and RSS recorded. Student process took 150.4s wall; peak RSS 381.3 MiB. Semantic preparation took 3.8s separately.
- Fresh-process replay reproduced 7,680 predictions with maximum absolute error 0.0, and checked complete checkpoint/optimizer lineage and exposure accounting.

## Measured capability and limitations

At introduction, familiar scores were U1 108/128, U2 114/128, U3 111/128 and U4 111/128. Novel-world and composite transfer is weak. By the end, familiar scores were U1 83/128, U2 88/128, U3 68/128 and U4 111/128. Forgetting is preserved, especially inference after evidence training. Final primitives: 26/26.

The canonical chain demonstration correctly distinguishes declared GRANDPARENT inference from absence of its rule at the final checkpoint. Other demonstrations fail, including the canonical U2 edge contrast and out-of-distribution single-proposition evidence examples. All such failures are in RESULTS and the gallery. Do not describe the learner as a reliable reasoner or claim semantic-embedding attribution, efficiency, general theorem proving, or Rosetta semantic acceptance.

Familiar readouts overlap training. Varied/composite exact inputs are excluded from every training pool; varied domains use 4–5 entities against training's 2–4. These are developer-authored exploratory evaluations, not a sealed benchmark. The two evaluators share typed syntax traversal; their relation closure and truth/evidence algebra are independently implemented.

## Frozen and portable evidence

Initial state SHA-256: `21a535c3a5a9c8d6e49f9ef50da8a626121cbafcbbb1fba403a60ac3634718c6`.
Final state SHA-256: `d9dfbf2545e2e4b4f8497d91cda68b8b51bc65d0cc8b5292ff860fcc7ddd68b0`.
Freeze receipt SHA-256: `914c18c3ffb0da5bbde7ad847d42d4776394a22e2991238cfc5f63d2719246a1`.

`freeze.json` binds sources, graph, transform, token map, provenance, raw lessons, initial tensors and encoded pre-training examples. `initial.pt` and `after-U0.pt` through `after-U4.pt` are portable weights; stage files include optimizer states and parent hashes. `training.jsonl.gz` retains every exposure. `after-U*.json`, `stage-U*.json`, `result.json`, `replay.json`, `gallery.json`, `state-gallery.json`, `primitive-retention.json` and `CHECKSUMS.sha256` retain readouts and integrity evidence. Checkpoints are deliberately committed despite the general model-artifact ignore rule.

## Exact verification and next executable step

From this checkout with the installed CPU environment:

```sh
/Users/emilie/.codex/worktrees/bilqis-alpha-102/Bilqis/.venv/bin/python -m bilqis_micro.run replay --run docs/evidence/micro-universes/run-01
```

Portable reproduction uses Python 3.13 and repository requirements, then:

```sh
python -m unittest discover -s tests -v
python -m bilqis_micro.run replay --run docs/evidence/micro-universes/run-01
```

For an independently named new run, `python -m bilqis_micro.run freeze --out runs/new-development` then `train --run runs/new-development` performs the fixed cohort path. Existing run directories are exclusive; do not rerun train against run-01. Do not overwrite the frozen evidence to tune a new curriculum.

Any future continued development should explicitly record a continuation from `after-U4.pt`, preserve its model state and AdamW moments, and focus on retention and genuine relational/compositional generalization. The current implementation does not provide a generic stage-5 continuation CLI or live trained-vocabulary expansion. `append_catalog` proves semantic/initial-coordinate stability; it does not automatically resize trained parameters or optimizer state.

No implementation or training blocker remains for this increment. Review the stacked PR and current hosted CI state before any later work. Leave #107 and this PR unmerged unless a new explicit instruction authorizes integration.
