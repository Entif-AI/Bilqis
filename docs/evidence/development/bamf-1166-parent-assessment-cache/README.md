# #1166 parent-assessment reuse evidence

Issue #1166 removes repeated accepted-parent evaluation from successive C05
fixed-school candidate screens. The cache applies only to the accepted parent.
Each challenger is still evaluated on every screen.

## Reproduce the timing witness

```sh
.venv/bin/python -B \
  bilqis_mlx/runtime/tests/capability/factory/retention/parent_assessment_cache_timing.py
```

`timing.json` records one local run with the repository's deterministic C05
test fixture. Treat the wall-clock values as a local comparison, not a
performance guarantee. The solver call counts are the stronger acceptance
signal.

The recorded run used a 16-case fixed-school parent assessment. The first
screen executed all 16 parent contexts. The second screen left the parent call
count at 16, so it performed no additional parent solver work. Candidate
context calls increased from 12 to 24, which proves that the challenger was
evaluated again.

The first screen took 245,143,000 ns and the second took 94,939,792 ns on this
machine. The second screen was 0.387 times the first-screen duration. Both
screens produced the same retention decision and evidence digest.

The cache receipt binds the exact accepted generation, parent model identity,
fixed cohort, Factory release, source authority, rubric, policy, correction
frontier, topology, extents, implementation, and evaluator contract. A cache
receipt is audit evidence only. It cannot mint C05 acceptance authority.
