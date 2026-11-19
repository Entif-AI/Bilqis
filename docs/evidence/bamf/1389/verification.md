# #1389 C05 retention throughput verification

Issue #1389 targets the minutes-long native BAMF C05 retention screen without
weakening target-first retention, source gold, model inference, B13 publication,
or learner custody.

## Root cause and production change

The current FOUNDATION target screen called `_fresh_rows` with its default
independent-family/episode requirement. Factory source rows resolve to one source
family per capability, so B.AND could exhaust 32 redraws before reaching C05
inference. ADR-133 explicitly says `FOUNDATION_ACQUISITION` does not require an
independent source family, fresh episode, or unseen specimen.

The production change is therefore narrow: the FOUNDATION target remains a fresh,
candidate-specific source-oracled redraw, but `_target_stage` passes
`require_independent=False`. Later-stage source-independence behavior is unchanged.
Target-first parent/candidate inference, protection-plan custody, championship
evidence and final C05 decision authority remain intact.

## Measured native B.AND result

The issue records the 2026-11-17 production B.AND symptom as 16 optimizer steps at
~14.7 s median/step followed by `retention_wall_seconds = 1,739.8 s`, ending
REJECTED. Historical telemetry did not expose C05 subphases, so no retrospective
subphase values are invented.

The disposable M3 Ultra witness at `ce75c4ef11c59c8cf6d44cb2005bbdedfccb67cc`
chains 16 real speculative B.AND optimizer updates, finalizes the candidate only on
step 16, then invokes the production C05 owner once. It does not publish the
candidate and the detached source mutation guard remained unchanged.

Measured after:

- training wall: 766.406 s
- C05 retention wall: **81.583 s**
- full attempt wall: 847.989 s
- decision: `ELIGIBLE / PAIRED_SCREEN_WITHIN_BUDGET`
- B.AND score: parent 2/6, candidate 4/6
- 6 target cases; 0 protected cases; 12 championship cases
- target inference: 2 shared-backbone launches, 0 scalar launches
- championship inference: 1 shared-backbone launch, 0 scalar launches
- peak MLX memory: 17,112,634,212 bytes (~15.94 GiB)
- peak host RSS: 4,339,826,688 bytes (~4.04 GiB)
- attempted steps/hour: **67.93**
- retained steps/hour: **67.93**

Against the issue's measured 1,739.8 s B.AND retention phase, this is a
**21.33x reduction in retention wall time**. Using the issue's 14.7 s median step
only as an approximation for its 16-step training span gives a ~1,975 s historical
full attempt, or ~29.16 attempted steps/hour. The new 847.989 s attempt is ~2.33x
faster end to end despite this witness's slower training steps. The historical
attempt retained zero steps because it was rejected; the measured after attempt
retained all 16 candidate steps.

## After profile

The new telemetry isolates where the remaining 81.583 s goes. The largest
authority-preserving cost is championship evidence: 38.141 s total, comprising
11.178 s preparation, 1.081 s solver construction and 25.880 s candidate inference.
Target work comprises 13.018 s preparation, 2.141 s solver construction, 13.816 s
parent inference and 13.785 s candidate inference. Decision finalization is ~3 ms.

An experimental attempt to reuse the generation-independent compiled championship
cohort was measured separately and rejected: cold C05 was 75.44 s and warm C05 was
76.30 s (0.989x) with exact semantic equivalence. That optimization was reverted;
no non-performing cache change remains in the feature diff.

## Evidence boundary

The historical control provides whole-retention timing only because the requested
subphase instrumentation did not exist in that production run. The post-change
profile is fully decomposed and machine-readable in `benchmark.json`. The benchmark
does not claim that the 16-step training workload is identical in per-step cost to
the historical run; the comparison claimed for acceptance is the same previously
slow B.AND / 16-step retention class and its C05 wall-clock result.

The detached benchmark receipt reported `source_mutated=false`. The witness uses a
temporary generation and never calls B13 publication, so no persistent learner,
accepted optimizer, teacher or champion state is advanced.
