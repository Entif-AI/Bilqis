# #1448 bounded retention throughput profile

The production-shaped C05 witness ran on a disposable generation and did not publish the candidate. The detached runner reported `PASS`, return code 0, and `source_mutated=false`.

The witness evaluated `B.AND` with one genuine candidate update step. The retention decision was `ELIGIBLE` with reason `PAIRED_SCREEN_WITHIN_BUDGET`.

## Timing

Total retention wall time was **39.093 s**. The dominant measured substages were:

- target parent assessment: **12.657 s**;
- target candidate assessment: **12.536 s**;
- target preparation: **11.285 s**;
- target solver work: **2.035 s**;
- decision finalization: **0.003 s**.

The remaining cost is therefore concentrated in the paired target assessments and their preparation, not decision finalization or bookkeeping.

Training before retention took **61.622 s**. The full attempt took **100.715 s**, equivalent to about **35.74 attempted and retained steps/hour** for this one-step disposable witness.

## Progress and protected timing semantics

This specific benchmark had no protected capability in its current protection plan, so `retention_protected_case_count` was 0. That does not collapse the protected timing contract. Exact-head regressions separately prove target/protected progress and timing semantics:

- `test_target_first_retention.py`: 6/6 passed;
- `test_retention_observed.py`: 4/4 passed.

Those fixtures verify completed/total progress, subject, parent/candidate role, target timing fields, and protected assessment sequencing. Protected timing fields are emitted only when protected work actually runs.

## Safety and authority

The benchmark is non-authorizing and non-publishing. It uses a temporary BAMF run and an isolated temporary `BILQIS_DATA_PLANE`, so its genesis trust record does not collide with or persist into workstation production custody. No live human trainer was run or mutated, and no device synchronization was added solely for measurement.
