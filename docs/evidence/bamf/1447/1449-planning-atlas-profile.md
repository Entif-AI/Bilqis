# #1449 authenticated Atlas reuse profile

The priority planner now reuses the Atlas snapshot that the execution context already authenticated. The legacy fallback remains available when no authenticated snapshot is supplied.

The real-artifact comparison used the pinned A01 bundle `5f8fba20ecc0adebf39c3b663fdffa4f766e780915197f09d116713042a479e7`, release `58e0c281b5da18b9b7e6c803709b29eeeb0a88f16b06f48de692808e2fb88306`. The bundle contains 9,307 ABI entries and produces 9,307 source lessons.

The three-run diagnostic comparison measured a 12.460195 s mean for the loader-backed compile and 11.600248 s for the authenticated-snapshot compile. Snapshot reuse saved 0.859947 s per compile, a 1.074x speedup. The two paths produced structurally identical `CurriculumCandidateSet` values on every run.

The committed rerunnable profile is `scripts/bamf/planning_atlas_reuse_profile.py`. Its one-repeat machine receipt, `1449-planning-atlas-profile.json`, also passed: 12.442425 s loader-backed versus 12.157438 s with the authenticated snapshot, saving 0.284986 s. The focused regression `test_priority_planning_uses_authenticated_snapshot_without_loader_backed_compile` makes the loader-backed compiler fail if the authenticated planning path calls it. That test passes.

The benchmark also identifies the remaining dominant planning cost. Semantic curriculum compilation itself takes about 11.6 s on this artifact. The operator surface now reports that work as `planner: compiling semantic curriculum` instead of hiding it under accepted-Atlas selection.

No planner selection outcome, learner authority, or student state changes because the authenticated snapshot is reused.
