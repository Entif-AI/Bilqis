# #1238 verification receipt

## Candidate identity behavior

- #1169 raw-v2 and legacy fixed-vector compatibility remains green.
- Cold accepted-state loading performs exactly one full candidate identity computation before issuing the process-local binding.
- Same-process accepted publication with the exact bound state performs zero full candidate identity computations and hashes zero numerical candidate-identity bytes.
- Full-B01 disposable benchmark: 953,848,264 numerical bytes; first canonical proof 0.449231917 s; 25 repeated requires averaged 0.001866115 s; approximately 303.65x first-bind/require wall ratio; full-computation count remained exactly one.
- Ordinary accepted operator flow reuses `FactoryRetentionEvaluation.candidate_state`; motif bundle derivation accepts and preserves the already-resolved state.
- Supported MLX 0.31.1 and isolated MLX 0.32.4 environments both pass the binding capability probe and candidate identity/binding regression suites.

## Focused verification

The consolidated #1238-focused matrix completed with:

- 109 passed
- 1 existing environment-gated skip
- 36 subtests
- `python3.14 -m compileall -q bilqis_mlx scripts/bamf/benchmark_candidate_identity_binding.py` passed
- `git diff --check` passed

Additional targeted publication, genesis, Factory-owner, operator, fallback, shared-storage refcount, and cold/hot hash-count tests remained green after Stage-6 drift repairs.

## Repository gates

`npm run verify:leaf` passed after restoring the worktree's Node dependencies from the checked-in lockfile with `npm ci`. The first attempt had reached the Electron security stage before failing solely because the local install lacked `ajv/dist/2020`; no repository source change was needed to repair that environment.

The successful leaf gate included the governance/changed-test checks, the 460-test Mission Control suite, the 66-test Electron security suite, and Python bridge security checks.

`npm run verify:premerge` passed once on the final verified candidate after Stage-6 EGM drift reconciliation. No persistent/human learner was started.

## Stage-6 EGM drift

See `drift.md`. Current verdict: **PASS**, no Blocker/Major drift. Reconciled findings included the private guard-module structural split, refreshed #1231 census authority, unsupported-runtime fallback, reviewed Factory binding fields, expanded guard self-test coverage, and dual MLX 0.31.1/0.32.4 verification.

## Remaining review boundary

Repository-native live Factory/motif tests that require an external integration environment remain correctly skipped locally. Hosted CI is still required before human review. This receipt is not merge authorization.
