# Bilqis U5–U6 standalone handoff

As of 2026-10-11: the authorized helper-guided continuation batch is complete. **Partial neural acquisition; the critical provenance/supersession perturbation is not mastered.** No merge was performed.

## Location and lineage

Repository: Entif-AI/Bilqis. Branch: `codex/u5-u6-helper-development`. Durable worktree: `/Users/emilie/.codex/worktrees/bilqis-u5-u6/Bilqis`.
Stacked base: open PR #109, `codex/108-developmental-micro-universes`, verified head `c858e086df93f5ca1c27be207d72fafd405dae88`.
Implementation freeze: `787f8d2`; cohort/checkpoint freeze: `f94566b`. Review: [draft PR #110](https://github.com/Entif-AI/Bilqis/pull/110), stacked against #109. The review PR contains the later delivery commit. Do not merge this branch without a new explicit user instruction.

Run: `docs/evidence/u5-u6/run-01`. The Git evidence includes the complete compressed corpus, all 768/256 helper vectors and raw native choice requests/responses, graph, new-row initializer, training exposure log, checkpoints and full prediction inventories.

| Checkpoint | Optimizer step | File SHA-256 |
| --- | ---: | --- |
| expanded-U4.pt | 8400 | `2a7844c09631de4ff8034e8a260c42ccf86c4ee3dbc99f295a58d98ef8770bae` |
| after-U5.pt | 10800 | `bb83c77e00faf6581f8cd5ac487b07273c15ad8c2f6e8939c9d270b659a758ca` |
| after-U6.pt | 13400 | `248a82ac92005f7b245751d6ea211d8296189de797f702349451f74383d75799` |

Final model state: `5ec251f79620156a83be5ae3cdcdc961d071e75ff1f6bcc3ed721f4482952034`. Source freeze: `4c67c17a0da6a5337589efa3fd69cab5954c59fbb97efa1dba3467f7b5241f16`.

## Observed result

EG2: 22 concise source-located descriptors, 20 fresh queries, zero truncations, full native 768 references retained. Both 768 and 256 profiles retrieved the focal construction in all 20 top-8 neighborhoods. The selected 768 profile follows prior measured recall and is proposal-only, not #88 qualification.
Kev: 20 actual native trained pointer-head decisions, 20 source/formal admissions, zero selected abstentions/rejections/inert choices. All panels contained a genuine needs-review option. The retrieval receipts preserve 100 scope-excluded rows, 78 unoffered neighborhood rows and two authored invalid collapse alternatives. Invalid alternatives are not misreported as selected helper errors.
Every accepted decision produced 128 specific contrast/composition lesson rows, 2,560 total. All were actually exposed during training. Source → neighborhood → choice → admission → graph relation → lesson → exposure provenance is retained. Helper use is materially in lesson construction; its causal benefit is unmeasured.
One scratch-trained student continued from U4, preserving all trained weights and optimizer history during vocabulary expansion. Old 1,920 probe predictions remained exact at expansion. Vocabulary is 113 identities, 352,512 parameters; new moments zero, inherited shared step counter 8,400. New coordinates come only from validated symbolic descriptors and typed relationships.
U5: 2,400 updates. U6: 2,600 updates. Total additional updates 5,000; final AdamW step 13,400; 160,000 new exposures. Final balanced varied scores: U5 174/320, U6 213/320. Final composite scores: U5 157/320, U6 168/320. Familiar: U5 72/128, U6 98/128.
The frozen single-link lineage diagnostic is 4/10. DERIVED_FROM is wrong in both diagnostic worlds, and SUPERSEDES is wrong when replacement is present. Do not claim neural non-collapse under perturbation. The formal validators and typed identities do remain distinct.
All 26 existing Boolean primitives are retained. Broader forgetting remains: U0 familiar 92/128 → 76/128; U4 familiar 111/128 → 97/128; U4 composites 59/128 → 50/128. Other earlier relational/proof readouts improved. Full errors, class/family totals and real logits are preserved.
Fresh-process replay: 10,398 predictions, maximum absolute numeric error 0.0; checkpoint, optimizer and exposure lineage verified. Historical U0–U4 replay also passed unchanged. Local suite: 63 tests passed.

## Replay and safe continuation

Use the existing student environment, from the durable worktree:

```sh
/Users/emilie/.codex/worktrees/bilqis-alpha-102/Bilqis/.venv/bin/python -m unittest discover -s tests -q
```

The numeric replay command below rejects an existing replay receipt to preserve immutable evidence. For another replay, copy the full run directory to an isolated path, retain the original receipt separately, remove only the copied replay receipt, then run:

```sh
/Users/emilie/.codex/worktrees/bilqis-alpha-102/Bilqis/.venv/bin/python -m bilqis_development.run replay --run <isolated-copy>
```

Never rerun `train` over run-01. Its exclusive training log intentionally rejects repetition. A subsequent developmental tranche must begin from `after-U6.pt` through `bilqis_development.continuation.load`, carrying AdamW moments and declaring new immutable source/corpus/checkpoint lineage. Do not replace it with the expanded U4 checkpoint or a fresh model.
Preserve `bilqis_micro`, `bilqis_logic`, `bilqis_ref/model.py` and now the frozen `bilqis_development` sources. New code inside those frozen source glob scopes would invalidate historical replay. Prefer an isolated successor package or explicit append-only source amendment for a warranted repair.
Remaining capability gaps are reliable typed lineage/evidence distinction under perturbation, broader mathematics transfer, and cumulative retention. The declared 5,000-update batch is complete. Any continuation must declare new immutable run/lineage evidence within the controlling user contract; no merge, broad control matrix or scaling is authorized by this contract.

## Helper runtime recovery

Actual verified EG2 environment: `/Users/emilie/Code/Bilqis/.venv-eg2/bin/python`; existing model `/Users/emilie/.lmstudio/models/mlx-community/embeddinggemma-2-bf16`. Native MLX loader, model hashes, prefixes, package/VCS identities and all vectors remain in `helpers.json.gz`. Its subprocess exited after preparation. No duplicate server or download was created.
Actual verified Kev: existing PID 85208, `http://127.0.0.1:8008`, native MLX/BF16/MPS, rank-16 LoRA and trained pointer head. Run `jaredpalmer/kev-4b@6cfce5c2fa4b4bd64026336ab649c5ca78857d52`; source `/Users/emilie/Code/kev` at `6b719c3c3f367295f6ef336f4f751cf5ff970abc`. Closing readback: 64 total native requests, versus 44 before this batch; no queued requests. Recheck live identity before future reuse.
Existing service interpreter: `/Users/emilie/Library/Logs/entif/bilqis-local-decision/20261006T015823Z/envs/kev-mlx-fixed/bin/python`. Keep its environment and loopback boundary intact; do not substitute ordinary LM Studio loading.
Helper preparation: 34.40s wall; student training process: 191.77s wall. Corpus draft/compilation and freeze costs are accounted separately in `semantic-preparation-accounting.json`; unknown draft CPU time is null. No paid helper provider calls, helper fine-tuning or model downloads occurred.

## Evidence and authority

[RESULTS.md](../evidence/u5-u6/RESULTS.md), [semantics](SEMANTICS.md), [execution contract](CONTRACT.md). `CHECKSUMS.sha256` covers raw run files; `DELIVERY-CHECKSUMS.sha256` covers the report and handoff.
This is a bounded exploratory development result, not full #84/#85 acceptance, complete Rosetta serialization conformance, open-ended retrieval qualification or a controlled attribution result. English reference material remained upstream; student inputs are numeric semantic identities and raw tiny worlds.
Historical DN-01 was not resumed or discarded. PR #106 adapters were reused byte-for-byte; prior helper capability/failure evidence remains authoritative for its original task scope. PRs #109 and #106 were verified open/unmerged in this session. Historical evidence was preserved.
