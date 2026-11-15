# Streaming candidate content identity (#1169)

Outcome: exact deterministic optimizer content identity without full-state hex/JSON
allocation. Baseline unified `2c8cda55d1344626bc6c6f11d9b5db5836a36604`.
Scope: identity implementation and custody codec; no semantics, teacher policy,
optimizer algorithm or actual student updates. B13 remains publication authority.

## Framing and owner

Add `bilqis_mlx/learning/_retention/candidate_identity.py`; keep
`atlas_acceptance.candidate_identity_digest` as its existing import surface.
`CandidateState.identity_scheme` selects the hash; new states default to
`bilqis.mlx.candidate-identity/raw-v2`. Unknown schemes fail through the existing
MODEL_TOPOLOGY.INVALID error. The legacy scheme is
`bilqis.mlx.candidate-identity/hex-json-v1`.

Raw v2 uses SHA-256 over the following bytes, with no locale or Python repr:

1. ASCII domain `bilqis.mlx.candidate-identity/raw-v2` followed by NUL.
2. Optimizer step as unsigned big-endian 64-bit integer.
3. For groups in fixed order `parameters`, `m`, `v`, `update_counts`: a
   length-prefixed UTF-8 group name, then unsigned 64-bit tensor count.
4. For each tensor sorted by name: length-prefixed UTF-8 name, length-prefixed
   NumPy `dtype.str` (including byte order), unsigned 64-bit rank, unsigned
   64-bit dimensions, unsigned 64-bit byte count, then raw C-order tensor bytes.

Every length/count is unsigned big-endian 64-bit. Reject negative or oversized
step/dimension/length, non-string names, and object/structured/subarray dtypes.
Numerical validation remains with AdamWStateTree; framing also supports ordinary
fixed-width numeric NumPy fixtures for dtype/shape tests. Logical C-order content
identifies arrays irrespective of strides. Hash contiguous arrays through a
memoryview; copy only the current noncontiguous tensor, never aggregate trees.
Do not call `tobytes().hex()` or canonical JSON on the raw-v2 path.

Legacy v1 must reproduce the old canonical JSON byte stream exactly: sorted keys,
compact separators, ensure_ascii=False, final newline, tensor bytes in lowercase
hex, optimizer_step plus four named groups. Stream one tensor in bounded 64 KiB
chunks, converting only that chunk to hex. Compare against a test-only copy of
the original JSON implementation. Legacy hashes retain their historical omissions
of shape/dtype; raw-v2 explicitly binds those fields.

## Compatibility and lifecycle

Persist `identity_scheme` inside the immutable manifest's optimizer record.
Absent field means legacy-v1 only; a present unknown or malformed value fails.
The existing manifest digest authenticates scheme selection before identity
verification. Accept exactly the old optimizer key set or that set plus the
scheme field. Old records and hashes are never rewritten. Saving legacy state
keeps the old optimizer shape (absent field), preserving its identity contract.

Rehydrate CandidateState with the manifest's explicit scheme or legacy fallback.
Genesis's reconstructed expected state uses the supplied candidate's scheme.
All existing digest consumers then select consistently from their state: genesis
run identity, successor authority, teacher/cache identity, acceptance, retry and
publication. Parent and child are hashed with their respective schemes. A newly
resolved updated candidate uses raw-v2; rejection and no-update return the exact
parent, preserving its scheme. Neural-inert policy/promotion state copies preserve
the parent's scheme to keep unchanged-state comparisons. Parameter extension
preserves the parent's scheme only when it admits no new parameter rows; admitting
rows changes the retained extension state and migrates a historical legacy-v1 parent
to raw-v2 so the successor binds shape and dtype as well as bytes.
A historical lineage migrates on its first accepted updated candidate; parent
acceptance and teacher references remain historical and verifiable. Rollback to
old software requires using the preserved historical parent, since old software
must reject a manifest carrying the new scheme rather than misinterpret it.
No in-place migration or live-run mutation is part of this change.

No cross-call memoization: AdamW mappings are read-only but MLX leaves allow
indexed mutation. Re-read tensor content at every verification boundary. Whole-state
hash recomputation cannot safely be eliminated without an independently immutable
state owner; removing hex/JSON allocation addresses the avoidable work now.

## Implementation and proof

1. Red tests for raw framing, deterministic independent oracle/golden and cold
   subprocess restart; name/order, byte, group, shape, dtype, counts and step
   differences; mutable leaves must change digest. Compare streaming legacy to
   original implementation, including escaped/non-ASCII names and chunk bounds.
2. Implement framing helper and CandidateState scheme validation/selection;
   re-export from atlas_acceptance. Update loader, codec manifest validation/write,
   neural-inert copies and genesis reconstruction as above.
3. Regression tests for new/legacy bundle readback, malformed scheme, legacy
   accepted genesis and successor authority, mixed-scheme parent/child acceptance,
   rejection rollback, publication retries, and existing cache/teacher owners.
4. Run bounded single-worker owner tests with MLX cache disabled. Compare old
   implementation, streaming legacy, and raw-v2 on a disposable full BAMF topology,
   initialized parameters plus native AdamW/counts, without a forward/backward or
   optimizer update. Measure cold-process CPU/wall and peak RSS, same topology/seed
   and tensor byte count. Apply MLX memory/cache limits; preserve 100 GiB reserve.
   The benchmark must assert the legacy digest agrees before reporting performance.
5. Review design-to-code drift and run required leaf/premerge/static/ABI gates;
   consume current unified before ready PR. No merge and no actual neural run.

## Concrete owner changes (readiness clarification)

All paths below are relative to the repository root.

- `bilqis_mlx/learning/_retention/atlas_acceptance.py`: replace the existing
  function with an import of the new helper, preserving the public import name.
- `bilqis_mlx/learning/_retention/_atlas_candidate/state.py`: append the
  `identity_scheme` field after `schema_version` (preserve positional callers),
  default raw-v2; validate membership. In
  `_load_retained_candidate_state_with_parts` assign from validated manifest
  optimizer, default legacy only on absence. In both
  `_issue_promotion_transition_state` assigns the parent's scheme explicitly.
  `_issue_parameter_extension_state` preserves it for a no-row-change copy, but
  selects raw-v2 when new parameter rows are introduced; this prevents legacy-v1's
  historical shape/dtype omissions from becoming successor identity collisions.
- `bilqis_mlx/learning/_retention/_atlas_candidate/transaction.py`:
  `resolve_candidate` assigns raw-v2 explicitly in both normal construction and
  `object.__new__` paths for an updated state. Rejection/no-update returns parent.
- `bilqis_mlx/learning/_retention/atlas_package_import.py`: `_reset_state`
  assigns raw-v2 explicitly to changed imported numerical state.
- `bilqis_mlx/runtime/_custody/bamf_bundle/codec.py`: save adds identity_scheme
  only for raw-v2. `validate_bamf_bundle_custody` accepts the two exact optimizer
  key sets and validates any present scheme before tensor construction. No other
  optimizer or bundle schema changes.
- `bilqis_mlx/runtime/_custody/bamf_bundle/genesis/preparation_authority.py`:
  `_validate_candidate_b01_authority` reconstructs expected_state with
  `identity_scheme=candidate.retained_state.identity_scheme`.

Proof paths: new focused framing tests
`bilqis_mlx/learning/_retention/tests/test_candidate_identity.py`; custody
regressions `bilqis_mlx/runtime/tests/custody/bamf_bundle/contracts/test_identity_scheme.py`;
benchmark `scripts/bamf/benchmark_candidate_identity.py`. Existing retention,
publication, genesis, cache and teacher owner suites supply integration coverage.
Review finding R1 above is addressed by these explicit owner assignments; no
behavioral contract changes beyond the previously described scheme selection.
