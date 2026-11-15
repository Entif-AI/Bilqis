# #1167 fixed-school batching timing and memory witness

## Fixture and environment

- Date: 2026-11-15
- Host: local Studio execution host (Apple Silicon)
- Pinned A01 artifact: `/Users/emilie/Code/371-c02-complete-20261106/.local/c02-a01-rebuild/5f8fba20ecc0adebf39c3b663fdffa4f766e780915197f09d116713042a479e7`
- Factory capability: `A.IDENTITY`
- Source seed: `37144`
- Fixed-school cases: `4`
- Candidate/generation: identical between scalar control and batched path
- Largest shared compiled width: `17` positions
- MLX memory policy: `bilqis.mlx.training-memory/no-free-buffer-cache-v1`
- MLX cache limit during witness: `0` bytes
- Repository allocation ceiling: `51,539,607,552` bytes (48 GiB)

The comparison warmed MLX with one scalar case before measurement so first-dispatch compilation was outside both measured paths. Each measured solver was then freshly constructed over the same four real Factory instruments and generation. `mx.clear_cache()` and `mx.reset_peak_memory()` were called immediately before each measurement, and `mx.synchronize()` was called before stopping the wall clock.

## Results

| Metric | Scalar control | Batched |
| --- | ---: | ---: |
| Wall time | 43.9659 s | 22.0249 s |
| Neural/source-backbone launches | 4 | 1 |
| Rows in shared launches | 0 | 4 |
| Largest shared rows | 0 | 4 |
| Largest shared compiled positions | 0 | 17 |
| MLX peak memory | 1,067,139,596 B | 1,067,139,596 B |
| MLX active memory at completion | 1,029,390,580 B | 1,029,603,620 B |
| MLX cache memory at completion | 0 B | 0 B |

Observed wall-clock speedup on the current-unified integrated candidate: **1.996×**. The batched path reduced the four real neural executions to one shared B11 backbone execution.

Peak memory was identical between scalar and batched measurements in this witness and remained at approximately 2.1% of the repository's 48 GiB allocation ceiling. The exercised four-row/17-position chunk is therefore comfortably inside the current trainer envelope.

## Semantic equality

The scalar and batched paths produced:

- identical generation bindings;
- identical per-case `CapabilityResult.replay_record()` values;
- identical per-case solver-contract digests;
- identical typed answers and routes;
- identical assessment digest and `candidate_work_disposition()` in the checked regression suite.

The dedicated #1167 regression suite also verifies that a second evaluation of already-materialized contexts performs no new shared or scalar neural launch, preserving C04 cached-composition semantics.

## Commands

Focused regression:

```sh
BILQIS_A01_ATLAS_BUNDLE=/Users/emilie/Code/371-c02-complete-20261106/.local/c02-a01-rebuild/5f8fba20ecc0adebf39c3b663fdffa4f766e780915197f09d116713042a479e7 \
BILQIS_ATLAS_REAL_ARTIFACT=/Users/emilie/Code/371-c02-complete-20261106/.local/c02-a01-rebuild/5f8fba20ecc0adebf39c3b663fdffa4f766e780915197f09d116713042a479e7 \
python3 -m unittest bilqis_mlx.runtime.tests.capability.factory.test_factory_evaluation_batching
```

Result on the current-unified integrated candidate: `Ran 10 tests in 423.201s — OK`.

The timing witness used the same fixture and constructed separate scalar (`contexts_for=None`) and batched Factory complete solvers over the same four instruments, measuring wall time plus `mx.get_peak_memory()`, `mx.get_active_memory()`, and `mx.get_cache_memory()` under `training_memory_policy(mx)`.
