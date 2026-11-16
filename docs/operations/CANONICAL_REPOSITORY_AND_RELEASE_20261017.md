# Bilqis MLX canonical repository and release transition

> **Historical status notice:** This 2026-10-17 migration/release record is retained for provenance. It is not the current setup or operator guide. Use [OPERATOR_GUIDE.md](OPERATOR_GUIDE.md) and the repository root [README](../../README.md) for current human-facing procedures.


Status: internal private engineering record, October 17, 2026. This describes independently verified operations, not an agent authorization to train the live student or to delete unique checkpoint history.

## One operational checkout

`~/Code/bilqis-mlx` is the canonical checkout. Active Python packages and operator commands are internal to this root. The previous root `bilqis-triplets-v16` is no longer required at runtime: pinned historical `bilqis_*` Python modules, the teacher implementation and its reference oracle source files were vendored without edits into `vendor/legacy-v16/`. Their existing exact source digests were preserved and the candidate Grade A source manifest still verifies all 216 rows. The original historical FP32 bootstrap checkpoint and teacher-state receipt are stored in the ignored `vendor/legacy-v16/runs/primitive-consolidation-v16-triplets/` path. The bootstrap checkpoint's copied SHA-256 equals the original (`646d8590cf8fddb7b3c412ecead4ac185a0578f93baadf24e05f92dd15068a78`).

The current student resides in ignored `runs/school-mlx-v1/`, with its complete matching native AdamW, native semantic graph, source/oracle/cohort receipts, teacher history, frozen soups, champions, retention peaks, event history and immutable state generations. The archive `runs/archive/pre-parity-school-20261017/` preserves the former canonical student at optimizer step 220008. Old duplicated control and experimental runs were not deleted during migration.

## Verified state migration, not reset

The previously human-operated experimental current-student run was SHA-copied from the isolated experimental checkout and promoted to the canonical run location after the human process stopped. Exactly **4,361 files / 7,184,160,281 bytes** matched source-to-destination SHA-256. The migration baseline was generation **8390**, native AdamW optimizer step **223256**, full model SHA-256 `a65697c6c85c015f4e66cc7373e565d3e4a12e79d1f060b10ca6c05629b0c6ec`. The identity of `state.json` matched its immutable generation, and the recorded checkpoint hash and optimizer step matched the safetensors bundle. This is one intact evolving student, not best-of-history weights. The subsequently human-launched canonical run progressed beyond that step; read its own state to obtain current results.

The reloaded canonical checkout passed `python3 -B -m bilqis_mlx.cli train --dry-run --resume --experimental-retention --verify-source`, with no blockers and source root `vendor/legacy-v16`. All actual neural updates belong to the human. Never run `--human-run` from an agent or switch the current model/AdamW unilaterally.

## Path and storage discipline

The default model home is `runs/school-mlx-v1/`, ignored by Git. Historical bootstrap data is also ignored; no safetensors or `.pt` weights belong in Git. `BILQIS_STORAGE_ROOT` can select the active run root, but the **current experimental candidate gate additionally constrains its data home to a descendant of this checkout's `runs/` directory**. Do not claim that configuring an arbitrary external directory for experimental training is verified. Separate, explicit external backup of retired models is supported through the repository backup tool once a suitable writable drive has been chosen.

`npm run storage:plan` previews candidate immutable JSON state generations. `npm run storage:compact -- --max-files 0` performs independently hashed, lossless archive compression **only while no human trainer lock is held**. Normal human training stop paths compress a bounded number of old generations, not actual model/AdamW bundles. The latest four generations and explicitly pinned curriculum history are preserved uncompressed. Diagnostics read verified archived generations with the original error-code semantics.

The exact regular `.DS_Store` file created by Finder inside a bundles directory is metadata, not a model. The trainer now discards that single known file under its exclusive lock before checking/retiring bundles, while symlinks, unknown filenames, unexpected bundle contents and model tampering still fail closed. This fixes `HUMAN_TRAINER_UNCOMMITTED_BUNDLE_UNSAFE_PATH` without weakening student custody.

## Disk and archival status

The disk size discrepancy arose from ignored checkpoint histories inside isolated worktrees, not their tracked source. The two experimental runs initially occupied roughly **12.66 GiB** together; the original saved canonical run another **5.95 GiB**. The new canonical copy adds an independently verified current lineage to that inventory rather than magically reclaiming the historical storage. Actual disk recovery requires verified external backup followed by separately authorized retirement.

At the last drive inspection, `/Volumes/Disk Inventory Y` was an **11 MiB, read-only disk image**, unsuitable for model archiving. No other large writable external drive was identified. Do not infer permission to use a drive from its mount name, and do not delete unique historical checkpoints or their receipts until a verified copy exists. The previously prepared `scripts/operations/relocate_legacy_worktrees.py` can organize a fixed allowlist of old worktrees reversibly after checking for live users; it does not free disk space when the destination is on the same volume.

## Release checks

The source release is prepared as **v0.2.0**. `pyproject.toml` and `package.json` have matching Semantic Version numbers, `CHANGELOG.md` records changes and limitations, `CONTRIBUTING.md` defines Conventional Commit subjects, and `scripts/maintenance/release_version.py` verifies the tag/changelog contract. `.github/workflows/quality.yml` and `.github/workflows/release.yml` adapt the former Bilqis repository's test-and-code-hygiene pipeline to portable public-repository non-neural verification, using its existing code-smell audit approach and a separately established Bilqis MLX baseline. Linux CI does **not** pretend to run MLX training.

No release tag, remote push, or GitHub Release should be reported as complete until read back from Git and GitHub. First verify the full disposable suite on Apple Silicon, exact private source/code boundaries, current Git branch, and a clean commit; update `main` without force, push and read back; then create the immutable annotated tag and let the tag workflow publish its private release notes. A release tag does not qualify the student's numerical competence or certify a future Grade D curriculum.

## Outstanding external cleanup

The original isolated comparison records and historical `bilqis-*` worktrees remain intact until the canonical run and source release are verified and external archive capacity is available. They are **not** runtime dependencies. Move them out of the `~/Code` root through the fixed reversible relocation mechanism only when their process references and Git registrations are safe. Do not leave top-level symlink placeholders behind.