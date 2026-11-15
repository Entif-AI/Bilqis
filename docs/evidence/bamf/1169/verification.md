# #1169 streaming candidate identity evidence

As of 2026-11-15, implementation and bounded proofs use unified baseline
`2c8cda55d1344626bc6c6f11d9b5db5836a36604`.

## Design and review

[Design](../../../architecture/STREAMING_STATE_IDENTITY_1169.md), reviewed at
SHA-256 `53e0c37bf2acfba59db795095d0fbcdaad2a1d7f428ff3de97173e6d1883c9b3`.
Pinned Google EGM: `b3a35956759bf7f024af2ff061b2e0b44b438e4c`.
Independent GPT-6.1 Terra / High Implementation Readiness review found one Major:
missing concrete constructor/codec ownership detail. The added owner section
resolved it; affected-scope re-review passed before implementation.

Post-implementation source review found one proof gap: legacy chunk-size bounds
were not directly observed. The new spy regression checks every hex input, maximum
64 KiB, complete byte coverage and multiple chunks. It exposed duplicate logical
helper imports; all new helper consumers now import its canonical physical module.
Scoped re-review passed with no outstanding findings. Self-review checked framing,
mutable-array invalidation, scheme selection and copies, and source compatibility.
No speculative cache or unrelated restructuring was introduced.

Scope audit: the touched state constructors, codec, genesis and historical fixture
owners implement #1169's framing, compatibility and exact-state custody clauses.
The missing `BAMF_BUNDLE_SCHEMA` import in publication storage prevented the existing
historical feature-migration test from reaching its acceptance assertion; restoring
that import is required for the historical verification claim. The unchanged
GUI1143 record lacked the canonical authority pointer required by a mandatory
static gate; an append-only annotation supplies it. Generated error documentation
was refreshed because the baseline catalog omitted four existing control-plane
error sites. None changes curriculum, trainer policy or source admission.

## Bounded correctness receipts

- Original implementation: 8 identity tests, 9 failing assertions (red).
- Final framing suite: 11 tests pass, including independent framing oracle,
  names/shapes/dtypes/bytes/counts/step, ordering/strides, cold process, mutable
  content, legacy oracle equivalence and observed chunk bounds.
- Initial focused identity/custody/candidate suite: 28 tests and 19 subtests pass.
- Final custody scheme suite: 5 tests and 6 subtests pass, including accepted
  legacy genesis, raw-v2 successor, complete publication readback and retry.
- Owner suite initial pass: 213 tests, 106 subtests, 1 explicit source-fixture skip;
  three failures isolated to the old-writer fixture scheme and missing historical
  migration import. Focused repaired historical surface: 6 tests pass.
- Changed-file quality/structure/governance, legacy authority and flow-control
  checks pass. Historical ABI check reports advisory success, with independent
  expected fingerprint absent; no enforcement claim.

Leaf and premerge aggregate results remain separate gates. The local canonical
logs live under `.local/1169/`; no aggregate pass is claimed by these owner proofs.

## Full-size content-identity benchmark

[Machine-readable measurements](benchmark.json), produced with
`python3 -B -m scripts.bamf.benchmark_candidate_identity`.
Each arm constructs the same complete B01 topology in a cold process with seed1169,
6 GiB MLX memory limit, disabled free-buffer cache and the 100 GiB disk reserve.
No optimizer step, forward pass, training run or original checkpoint mutation.

| Measurement | Original hex/JSON | Streaming legacy | Raw v2 |
| --- | ---: | ---: | ---: |
| Hash CPU seconds | 5.018 | 1.294 | 0.391 |
| Hash wall seconds | 5.281 | 1.348 | 0.421 |
| Peak process RSS bytes | 5,606,146,048 | 1,084,899,328 | 1,083,097,088 |

State: 79,469,798 parameters; 856 numerical tensors; 953,848,264 bytes across
parameters, AdamW m/v and counts. Raw v2 shows a 12.83× hashing CPU speedup and
80.68% less total peak process RSS in this single controlled comparison. RSS
includes setup and MLX allocations; CPU/wall measures the hash call only.
This is an identity benchmark, not an end-to-end retention throughput measurement.
The historical digest agrees exactly between original and streaming legacy.
Two cold raw-v2 processes agree exactly (0.391 and 0.399 CPU seconds).

## Boundaries and controls

Incident `PM-2026-11-15-001` was filed and read back in the native internal ledger;
existing `PM-2026-10-16-003` remains historical context. IPR-0220 remains open.
Only the human starts real student training. Neural learning is unmeasured here.
New raw-v2 manifests explicitly record the scheme. Old software rejects them;
rollback uses the preserved historical parent, without rewriting accepted records.
Existing v1 identities retain their historical shape/dtype omissions. New v2
identities bind those fields. Every verification re-reads mutable tensor bytes.

## Verification harness reconciliation

`PM-2026-11-15-002` records the required leaf runner's namespace and transport
failures. The first xdist run reported 33 failed / 495 passed / 25 skipped;
serial pytest removed the transport errors and isolated 26 failures, all
`ModuleNotFoundError: tests.bamf_disposable_retention`. A bounded probe reproduced
`scripts/tests/governance/test_error_inventory.py` prepending `scripts/` at
collection, then resolving `tests` to `scripts/tests`. Prebinding and verifying
root `tests/__init__.py` fixes that namespace; a 3-test probe passed.
The reconciled invocation uses serial pytest (`BILQIS_TEST_WORKERS=0` means no
xdist subprocesses), no pytest cache/testmon selection, and a local startup helper
that verifies the canonical test-package path and applies 6 GiB MLX / zero cache
limits. Product checks are unchanged. Its required aggregate result is recorded
separately when complete; these failures are not reported as passing evidence.

The canonical-package, single-process leaf Python gate completed: 529 passed,
25 skipped, 362 subtests passed (101.40s). Mission Control's ordinary Node suite
passed in that invocation; its security stage initially lacked the declared Ajv
installation. Lockfile-only `npm ci --ignore-scripts` restored the development
dependency. The final optional-runtime regression passes (11 framing tests), and
the error-control gate passes with zero new debt. The lazy NumPy import and named
uint64 limit preserve the previously proved numerical behavior; owner evidence is
reused for those mechanical changes. Required premerge remains pending.

Security-stage reconciliation also isolates `BILQIS_ACTIVE_CONTROL_PLANE_DIR`
from the operator's advertised endpoint: the default-locator test otherwise sees
the currently running operator instead of its repository-local fallback. This is
verification environment isolation; no bridge or operator behavior changes.

## First aggregate result and repaired preflight

The immutable-snapshot aggregate at source head `1b8dd162` failed after
714.564 test seconds (771.206 gate seconds): 4,278 passed, 246 skipped, two
failures and 16 setup errors; source mutation guard passed. This is a failed
gate, not a readiness receipt. The two failures were the owner inventory's old
51-module expectation (the designed helper adds the 52nd owner) and the local
verification policy eagerly importing MLX before a source-only import test.
All 16 setup errors were missing historical-parent fixture access.

The inventory now includes the new owner. The resource helper applies its
6 GiB / zero-cache limits on actual `mlx.core` import, preserving lazy source
imports; a cold subprocess verifies both absence before import and applied limits
after import. Read-only independent copies of the SHA-pinned historical parent
and its required teacher-state fixture were restored for disposable tests;
original source bytes were verified unchanged. No fixture binaries enter Git.

A named preflight now validates both fixture content identities, invokes all 16
actual failed setup owners, and runs the layout/framing/custody contracts before
another aggregate. The first cheap preflight caught the additional missing
teacher-state sidecar; after restoring it, all 16 setup owners and 21 tests passed,
with zero skips. Independent bounded review found no material issue in this
repair. PM-2026-11-15-002 was enriched and native-ledger read back.

Current unified `bb3785a98f1523bab0b91ed0b9988f0ec5bf7a6c` was merged cleanly;
its affected C05 compilation/reuse owner suite passes 13/13 with zero skips.
The identity implementation and benchmark surface are unchanged; their earlier
proof is reused. Full quality checks pass against the consumed unified head.
The next aggregate remains a separate required gate; no PR is opened before its
receipt is reconciled.

## Second aggregate and current integration boundary

R2 at `f1347553` ran 4,622 tests: 4,399 passed, 222 skipped, one error;
787.335 test seconds / 842.189 gate seconds. Source mutation guard and fixture
postflight both passed. The remaining error was a test-double signature lagging
unified's new `steps_per_visit` CLI forwarding. The probe now explicitly accepts
the keyword and asserts its declared default16. Focused red→green: one test
failed with TypeError, then passed in19.851s. No production identity code changed.
R2 remains a failed aggregate receipt; individual passes are evidence only for
their unchanged dependency surfaces.

Current unified `55a53d1e70a98164ca08e0744125f7c0ad83a960` was merged cleanly.
It adds accepted-parent assessment caching and reorganizes exam ownership. The
cache calls candidate_identity_digest, so new integration tests exercise legacy
and raw schemes through its actual identity builder and evaluator: unchanged
state reuses; mutations to parameters/m/v/counts force a fresh assessment; equal
bytes under distinct schemes do not reuse. Two tests / eight mutation subcases
pass. Only the accepted-cache authentication boundary is isolated; this is not
live publication-authority or learning proof. Affected cache/retention/exam owners
pass25/25 with zero skips. Detached-only full-model owner witnesses stay outside
this cheap ring under their existing policies.

The cheap preflight now also runs the complete formerly failing resume test and
these cache interactions before a new canonical gate. The newly consumed cache
and exam production changes require fresh integration evidence; a third run is
not described as reuse of a passing R2 gate. PM-2026-11-15-002 was enriched and
native-ledger read back. The benchmark and raw identity implementation are
unchanged. No actual student/optimizer/teacher/champion was updated.

## Current-unified closeout

The feature branch consumed unified `c8877477c43b93aff4e2be12d002a5787adc6bac`.
Final compatibility review found one historical-lineage edge: a parameter-extension
state that admits new rows must not retain legacy-v1 identity, because legacy-v1
omits shape and dtype. The extension owner now preserves legacy-v1 only when no new
parameter rows are admitted and selects raw-v2 for a changed extension state. A
focused regression proves that byte-equal `(1, 2)` and `(1, 1, 2)` extensions from a
legacy parent receive distinct raw-v2 identities; a companion regression proves an
unchanged legacy extension remains legacy-v1. The affected differential gate passes
43 tests, 6 deselections and 13 subtests.

One fresh bounded `verify:premerge` aggregate reached 4,452 passes and 233 skips
before one unrelated unified-base test error. The failing test
`CompiledEvaluationReuseTests.test_parent_candidate_solvers_add_two_generation_authentications_only`
patches private symbol `_generation`, which no longer exists in the current Factory
complete-solver owner. The exact test fails identically on a clean detached worktree
at unified `c8877477`, proving this is pre-existing base test drift rather than a
#1169 regression. The #1169 preflight itself passed 27/27 with zero skips, and source
and historical-fixture custody remained unchanged. No production or test change for
that unrelated base defect is included in this issue branch.
