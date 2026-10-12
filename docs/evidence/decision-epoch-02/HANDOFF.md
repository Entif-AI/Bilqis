# BILQIS-DN-01 completed handoff

As of 2026-10-11: **HYBRID_PILOT_NULL_OR_REVERSAL**. Fixed HELDOUT paths 3/34, guided 2/34; −1 case / −2.94 percentage points. Both native engines, the one matched pair, frozen evaluation, archived replay and live replay completed. No remaining authorized training or evaluation work exists for this epoch. Do not rerun or tune it to improve the result.

Repository: [Entif-AI/Bilqis](https://github.com/Entif-AI/Bilqis). Branch: `codex/bilqis-decision-epoch-02`. Durable checkout: `/Users/emilie/.codex/worktrees/bilqis-decision-epoch-02/Bilqis`.

Executable source lineage:

- Recovered implementation: `7c0ad9d2aa3ab83e7b7a0bcdf3ca84123cac3822`.
- Frozen preparation / qualification / both training arms / primary evaluation / archived replay: [46db1650dfd870f698b9323c65017fe165e37136](https://github.com/Entif-AI/Bilqis/commit/46db1650dfd870f698b9323c65017fe165e37136).
- Exact-request live replay repair: [7b3f29bdfbc8fd8e9e0c8800f0aee4ff3e397291](https://github.com/Entif-AI/Bilqis/commit/7b3f29bdfbc8fd8e9e0c8800f0aee4ff3e397291).
- Predecessor [PR #105](https://github.com/Entif-AI/Bilqis/pull/105), head `04809bd8729558961b1d57889ecba78ccd484133`, remains open and depends on open [PR #104](https://github.com/Entif-AI/Bilqis/pull/104), head `d59c20d914fd8380909068017ca9fa2ef72d942f`. The successor review PR targets `codex/103-alpha-microscope`. The published PR head identifies the delivery commit containing these text receipts. No PR was merged.

Completed phases, in order:

1. Recovered the existing worktree; verified remote/local branch identity, historical checkpoint, native engines and prior preflight. No replacement worktree or reset.
2. Completed the bounded explicit-input audit and token-only cue baseline. The repository suite passed 82 tests. Committed/pushed the freeze revision.
3. `prepare`: immutable dataset/splits/batches/features/token map/initializer/fresh checkpoint/source manifest created.
4. `qualify`: cached 359 real native EG2 encodings and captured 24 actual Kev Choice calls on 12 DEV panels. Neither helper supplies student oracle authority.
5. `train-pair`: one exclusive training attempt; both arms reached 1,536 steps. Matching initialization, exposures, token budgets and fresh optimizer specification verified. Thirty-two intermediate checkpoints remain local.
6. `evaluate`: both actual student rollouts evaluated once. Negative primary result preserved; every successful HELDOUT path was a reserved outcome.
7. Archived replay: 46 neural case/arm records reproduced in a fresh process.
8. Detected sorted receipt-map option reordering in the live adapter. Preserved the frozen source, manifest and evaluation; committed a replay-only correction, passed 12 focused tests, and wrote the append-only source amendment.
9. Live replay: 46 neural records reproduced; native EG2 matched 196/196 rankings; three Kev requests had identical archived request hashes, choices and complete probability vectors.
10. Exported public-safe evidence and raw-file checksums. Vectors, raw runtime files and checkpoints remain ignored locally. Five-second resource sampling was stopped. The existing single Kev loopback service remains available.

Local run: `/Users/emilie/.codex/worktrees/bilqis-decision-epoch-02/Bilqis/runs/decision-epoch-02`.

Public review material: `/Users/emilie/.codex/worktrees/bilqis-decision-epoch-02/Bilqis/docs/evidence/decision-epoch-02`. [RESULTS.md](RESULTS.md) supplies numerical results and limits. [source-evidence-ledger.json](source-evidence-ledger.json) binds claims to original receipts/checkpoints. `artifact-checksums.json` covers the exported files. The fixed/guided prediction JSONL files and candidate inventory retain every observed error and offered identity.

Important ignored artifacts:

- `manifest.json`, `dataset.json`, `retrieval-input.json`, `input-audit.json`, `initial.pt`.
- `retrieval.json`, `qualification.json`, `training-start.json`, `paired-training.json`, `fixed-training.json`, `guided-training.json`.
- `fixed.pt`, `guided.pt` and each `*-step-*.pt` checkpoint; their file hashes are in the ledger.
- `evaluation.json`, `evaluation-binding.json`, `replay.json` and per-phase transcripts / process resource receipts.
- `live-replays/9654afbb-ad43-4c9c-9e68-a2fd1b4695f2/retrieval.json` and `replay.json`.
- `replay-source-amendment-01.json`, the exact patch and `preflight/frozen-decision-experiment.py`. The original manifest still names the frozen revision; the amendment admits only the committed replay-source repair. These files must accompany local replay.

Historical alpha remains at `/Users/emilie/.codex/worktrees/bilqis-alpha-102/Bilqis/runs/alpha/epoch-01/model.pt`, SHA-256 `002cffcfbdf44eec2e509704d5a530bb134d655919ec129f46eeffda6b99a3eb`. Every phase's input check verified it. Its original four-class checkpoint was neither regenerated nor retrained.

Qualified engines:

- EG2 Python: `/Users/emilie/Code/Bilqis/.venv-eg2/bin/python`; existing model: `/Users/emilie/.lmstudio/models/mlx-community/embeddinggemma-2-bf16`. MLX 0.32.3 / MLX-VLM 0.7.4, native BF16 embedding loader, local-only tokenizer, task prefixes retained. Exact executable/model/loader identities and local file hashes reside in the raw retrieval receipt. The embedding subprocess exited after encoding; no duplicate EG2 server was started.
- Kev source: `/Users/emilie/Code/kev`, commit `6b719c3c3f367295f6ef336f4f751cf5ff970abc`; native environment `/Users/emilie/Library/Logs/entif/bilqis-local-decision/20261006T015823Z/envs/kev-mlx-fixed/bin/python`. The closing readback observed PID 85208 at `http://127.0.0.1:8008`, pinned run `jaredpalmer/kev-4b@6cfce5c2fa4b4bd64026336ab649c5ca78857d52`, MLX/BF16/MPS, rank-16 LoRA and trained pointer head. It recorded 44 requests including smoke/qualification/guidance/live replay. Recheck identity before reuse; process state can change.
- Student `.venv` reuses the predecessor's existing Torch environment via an ignored symlink. Training was CPU, one thread, ternary forward emulated in floating point, FP32 master weights. No new model download or paid inference occurred.

To replay the existing completed run, from the durable decision checkout:

```sh
.venv/bin/python -m bilqis_alpha.decision_experiment replay
.venv/bin/python -m bilqis_alpha.decision_experiment replay --live
```

Archived mode reruns saved students and validates hashes, identities, complete step counts and numeric tolerance. Live mode also revalidates the exact qualified EG2 runtime/model and Kev runtime. Each new live replay writes a separate UUID directory. It does not overwrite frozen outputs or retrain. Checkpoint binaries are local; the Git-only evidence package alone cannot execute neural replay.

If the existing task-owned Kev service has stopped, use the same installed environment and pinned assets from `/Users/emilie/Code/kev`:

```sh
/Users/emilie/Library/Logs/entif/bilqis-local-decision/20261006T015823Z/envs/kev-mlx-fixed/bin/python \
  -m kev.serve \
  --run jaredpalmer/kev-4b@6cfce5c2fa4b4bd64026336ab649c5ca78857d52 \
  --host 127.0.0.1 --port 8008
```

The original `prepare`, `qualify`, `train-pair` and `evaluate` commands are historical completed phases. Their exclusive receipts intentionally reject blind repetition. A partial training attempt would have required reconciliation; this one completed, so no recovery or second pair is authorized.

The one accepted scheduling intervention swapped B03 and B02; 15 other decisions fell back. Neither arm demonstrated successful truth resolution on HELDOUT. Binding/orientation/update and availability inputs contain explicit cues, and the baseline's 4/34 reserved paths are not independent reasoning. The historically exposed domain is not SEALED. The initializer is shared, and DEV adaptation belongs to the combined teaching intervention. Native low-bit acceleration and universal efficiency are unmeasured.

Reusable ownership handoff: #70 receives deterministic panels / transition validation and replay checks; #62/#81 receive the versioned geometric compiler with preserved historical regression; #65/#88/#89 receive real native-engine adapters, distributions, costs and explicit failure/fallback evidence; #5 receives the matched exploratory comparison. These are scoped contributions, not complete acceptance, issue closure, merge, deployment, publication production or a new research plan.
