# #1171 planner throughput timing witness

## Preimplementation control

Date: 2026-11-15

This control was frozen before #1171 implementation. It uses the existing neural-inert
foundation-planning fixture and exercises the realistic 21-capability C03 planning,
offer and requalification path without starting a neural optimizer update.

Exact test:

```sh
BILQIS_TEST_WORKERS=1 /usr/bin/time -p python3 -m unittest \
  bilqis_mlx.runtime.tests.operator.test_pre_neural_journey_guards.\
PreNeuralJourneyGuardTests.test_priority_planning_reports_operator_visible_substages
```

Observed control samples on the same local Apple-Silicon Studio host:

| Sample | unittest runtime | process real time |
| --- | ---: | ---: |
| 1 | 19.469 s | 20.96 s |
| 2 | 17.605 s | 18.86 s |
| 3 | 17.604 s | 18.49 s |

Frozen process-real median: **18.86 s**.

The fixture completed with `TEACHER_SELECTED` and 21 admitted executable
capabilities. The full pre-neural guard module also passed **5/5** in 83.103 s before
implementation.

## Predeclared acceptance threshold

After implementation, one cold invocation may populate the trusted candidate-frontier
release and process-live planning transaction. Measure three subsequent warm-path
invocations on the same host/fixture and use their median.

The timing claim passes only if all of the following hold:

- warm process-real median is at least **20% lower** than 18.86 s;
- warm process-real median is at least **2.0 s lower** than 18.86 s;
- therefore the binding wall-clock threshold is **<= 15.088 s**;
- selected priority/visit identity remains identical to the control;
- builder launches, B13 deep-custody validations and C09 deep-registry resolutions are
  counted explicitly;
- no neural optimizer update occurs; and
- the current #1174 `prepared_rows` / `prepared_source_rows` behavior remains intact.

The final section of this receipt will record exact implementation head, current
unified base, warm samples, call counts, semantic equality and disposition. No result
is claimed yet.

## Postimplementation witness

Integrated semantic head measured: `800a930ebc310d2aee3237f6b3e1e78d89d84c36`.
Current unified base consumed by that head: `d2815e3151013c51fe11a298157625dce1aee6f5`.

The original shell command above creates a fresh unittest fixture, temporary DataPlane,
and run directory for every process. Repeating that command therefore cannot exercise a
warm content-addressed frontier row across invocations. This was discovered during
implementation profiling and is recorded rather than hidden. The binding postimplementation
witness consequently keeps one production-shaped fixture alive, executes one cold visit,
then times three additional visits through the same `select_foundation_priority_visit(...)`
entrypoint. No learner mutation occurs.

For an apples-to-apples implementation-effect check, the same in-fixture timing shape was
also run at the frozen preimplementation commit `495be606`. Its three selection samples
were **13.882379 s**, **14.686724 s**, and **13.937186 s**, median **13.937186 s**; each
reported `TEACHER_SELECTED` and rebuilt the frontier because reuse did not yet exist.

Integrated-head samples:

| Sample | Planning wall time | Frontier disposition | Result |
| --- | ---: | --- | --- |
| cold | 10.660754 s | rebuilt | `TEACHER_SELECTED` |
| warm 1 | 10.081268 s | reused | `TEACHER_SELECTED` |
| warm 2 | 9.823177 s | reused | `TEACHER_SELECTED` |
| warm 3 | 10.296672 s | reused | `TEACHER_SELECTED` |

Warm median: **10.081268 s**.

- versus the same-shape frozen preimplementation median, reduction is **27.66%** and
  **3.855918 s**;
- versus the predeclared absolute ceiling, **10.081268 s <= 15.088 s**;
- the 21-capability path remains `TEACHER_SELECTED`;
- `test_priority_planning_authenticates_generation_once_for_all_capabilities` proves
  exactly **1** accepted planning-cache bind across the fan-out;
- `test_priority_planning_deep_custody_binds_once_then_uses_currentness` proves exactly
  **1 B13** deep-custody bind and **1 C09** deep source-authority bind, followed only by
  cheap currentness fences;
- `test_priority_target_registration_reuses_authenticated_c09_runtime` fails if target
  registration reopens `_accepted_correction_registry` after the planning transaction is
  bound;
- the trusted-frontier tests prove an unchanged second visit does not launch the builder,
  while builder/source/release/input identity drift invalidates reuse;
- the source offer still performs one authoritative owner redraw through `bind_rows()` at
  each currentness boundary and compares the exact retained/prepared rows to the sealed
  offer; the eliminated redraw was a duplicate immediately following that owner redraw;
- #1174 `prepared_rows` / `prepared_source_rows` remains supported; and
- all measurements are neural-inert.

Disposition: **PASS** for #1171 acceptance item 6.

## Turn-in evidence reuse after current-unified synchronization

The final turn-in branch subsequently consumed reviewed unified
`d280a3e8d47efdba34e1262ffa59018d93f7c443`. The intervening unified range from
`4d743ecf` to `d280a3e8` changes Model Forensics JavaScript/CSS/tests plus
`package.json`; it does not change the Python planner, candidate-frontier, B13/C09
currentness, accepted-correction, source-offer, qualification, or pre-neural journey
owners measured above.

The final #1171 repair moves accepted-target registrar issuance to **after** the
already-required pointer/acceptance stability fence. On the stable success path it
adds no builder launch, deep custody bind, registry resolution, source redraw, or
other planning operation; it only prevents issuing a downstream process-live handle
when the planning transaction has already drifted. Therefore the timing witness and
its deterministic hot-path call-count evidence remain valid for turn-in under the
repository passing-evidence reuse rule. `TEST_EVIDENCE_REUSED`: measured head
`800a930ebc310d2aee3237f6b3e1e78d89d84c36`; comparison range through final turn-in
contains no dependency-surface change that can plausibly invalidate the measured
planner throughput claim.
