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
