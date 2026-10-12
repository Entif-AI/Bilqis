# Completed exploratory alpha batch — #102 → #103

As of 2026-10-11, both review PRs are open and unmerged:

- [#104 / ALPHA-01](https://github.com/Entif-AI/Bilqis/pull/104), branch
  `codex/102-alpha-semantic-learner`, head `d59c20d914fd8380909068017ca9fa2ef72d942f`.
- [#105 / ALPHA-02](https://github.com/Entif-AI/Bilqis/pull/105), branch
  `codex/103-alpha-microscope`, stacked on #104. Execution code:
  `26733370c2b7d896904c03e83dcb5850fde2bd64`; later commits add text evidence/audits.

Base: `97de3909f11652255de2fa60d932ac71578f0665`. Training code:
`32bed02cc4dd871016db23e25319b8c789194d7d`. Semantic registry, token codec,
feature map, initializer and microscope have independent 0.1.0 identities;
reference package advances 0.1.0→0.2.0→0.3.0. Exact versions/hashes are in the
frozen source, initializer, token and split manifests. The CP0008 implementation
and original ABI remain unchanged.

ALPHA-01 terminal: **ALPHA_DEMO_REPRODUCED**, the exploratory replay/partial-learning
disposition; broad or reliable generalization is unproven. One seed-102 cycle,
76,160 parameters, two width-64 transformer layers, four heads, context 128,
33 tokens, AdamW lr 0.001, batch 32, 1,536 steps. No second full cycle.
49,152 training exposures, 2,415,782 nonpadding tokens, CPU FP32 master/embedding/
optimizer/readout with ternary-forward and int8 activation emulation. Full cycle
41.95 s wall, 41.62 s CPU, peak process RSS 378,568,704 bytes. Energy and developer
cost were not measured; no paid compute or native low-bit/MPS qualification.

| Evaluation | Initial model | Trained model |
| --- | ---: | ---: |
| TRAIN | 848/2,944 | 1,735/2,944 |
| DEV | 323/1,152 | 676/1,152 (58.7%) |
| Composition HELDOUT | 414/1,024 | 476/1,024 (46.5%) |
| Named neural boundaries | 4/15 | 6/15 |

Heldout macro accuracy is 45.5%, versus 31.2% initially. All 548 heldout mistakes
and nine named misses survive. ALPHA-02 replays 20 cases, **7 correct/13 wrong**,
with one formal rejection, five single-factor interventions, equivalence and
label-defect checks, and a wrong intermediate relation/correct terminal formal
verdict witness. Formal traces are not attributed to the network; its intermediate
relation interface is MISSING. All 43 local unit methods pass, none skipped;
all 5,135 final predictions and the microscope replay in fresh processes at
absolute logit/probability tolerance 1e-6. Hosted checks are tracked on the PRs.

Checkpoint file SHA-256:
`002cffcfbdf44eec2e509704d5a530bb134d655919ec129f46eeffda6b99a3eb`.
Final state:
`850e579506d6c68fa0873900d2f9a6b920058c52108cd0e03cdd0ca2f28aef10`.
Persistent worktree: `/Users/emilie/.codex/worktrees/bilqis-alpha-102/Bilqis`.
Binary/optimizer/stage checkpoint: `runs/alpha/epoch-01/`, ignored under contribution
policy and deliberately retained. No binary is published through these PRs.

One command from that worktree reproduces the frozen demonstration:

```sh
.venv/bin/python -m bilqis_alpha.microscope --run runs/alpha/epoch-01 --verify docs/evidence/alpha/microscope/replay.json
```

Use `--json` for full canonical inputs, live logits, probability vectors, independent
oracle results, semantic deltas and split/provenance identities. A missing or
different checkpoint is a blocker, never an oracle/untrained/pretrained substitute.

Material limits/deviations: sparse role/negative/conflict cases often collapse to
UNKNOWN; adding refutation can cause the wrong TRUE prediction. Initial source/
target role rows coincide in the coarse geometry; causal relevance is untested.
Two named heldout-pattern cases received intermediate diagnostic probes despite
the declared final-only policy, with no optimization or tuning use. Full known
vectors were assembled before training after evaluator code existed; the original
blanket before-implementation prose is corrected by an append-only audit. Cold
human/specification-independent review, independent SEALED generators, trained
causal controls and replicated seed evidence are absent.

The slice supplies T0 typed roles/identity, T1 NOT/AND/OR, T2 finite quantification,
and T4 support/refutation under declared local Belnap-Dunn semantics. It omits the
remaining logic/proof/ambiguity, mathematics and Rosetta epistemic families. Full
#7/#80/#81/#62/#86, #17/#82, #52/#64, and SYS-01 #22–#25 acceptance remains unmet.
[REUSE.md](REUSE.md) maps immediate reuse, qualification and exploratory-only outputs
to their original owners. No new normative semantic authority is created.

Next smallest follow-up, not executed: isolate role-token geometry and directed
binding on the already frozen role/sparse-evidence contrasts. Keep the domain and
budget fixed before considering expansion, another backend or paid compute.

Evidence: [ALPHA-01 report](REPORT.md), [ALPHA-02 report](microscope/REPORT.md),
[`epoch-01/run.json`](epoch-01/run.json), [`microscope/replay.json`](microscope/replay.json),
[`protocol-audit.json`](microscope/protocol-audit.json), raw per-case results,
named test transcripts and checksum indexes. The batch stops here; no merges,
releases, deployments or full developmental-program continuation were executed.
