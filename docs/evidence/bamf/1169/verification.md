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
