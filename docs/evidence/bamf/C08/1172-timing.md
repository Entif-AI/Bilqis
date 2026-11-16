# Issue #1172 | True C08 MLX microbatch timing witness

Date: 2026-11-15

Issue: `#1172` — BAMF training throughput | Execute true vectorized C08 MLX microbatches

Baseline consumed for this witness:

- unified: `3b149403c61f3a291fe34eab635a4fa38768bdcb`
- feature head before this evidence-only commit: `3c9e627b77b702ec22c6c80836818a82c1db0f66`

## Witness boundary

This is a bounded raw neural-gradient throughput witness, not a claim about end-to-end
student learning rate or retained capability gain. It uses the same real pinned A01
artifact-backed B11 fixture as the #1172 FP32 parity test and compares the same four
logical teaching rows in two execution shapes after warming both paths:

1. four scalar `bamf_value_and_grad(...)` calls;
2. one four-row `bamf_microbatch_value_and_grad(...)` call.

Both paths use the same parameters, compiled row, answer plan, targets, and mask. The
vector path still returns four row-scoped loss executions; only the shared neural
forward/loss/backward dispatch is vectorized.

## Observed result

```text
rows=4
scalar_gradient_launches=4
vector_gradient_launches=1
scalar_seconds=45.492695083026774
vector_seconds=27.30164770799456
scalar_rows_per_second=0.08792620425542542
vector_rows_per_second=0.1465113037418876
speedup=1.666298516836603
vector_execution_rows=4
```

The bounded raw gradient path therefore processed the four-row fixture about **1.67x
faster** while reducing MLX value-and-grad launches from four to one. This is material
for the acceptance criterion but deliberately narrower than a retained-learning or
whole-trainer throughput claim.

## Correctness witnesses paired with the timing result

The timing result is accepted only alongside the deterministic correctness tests:

```text
python -m pytest \
  bilqis_mlx/runtime/tests/model/execution/test_atlas_model_microbatch.py \
  bilqis_mlx/runtime/tests/batch/factory/test_factory_training_microbatch.py -q

3 passed, 215 subtests passed
```

Those witnesses prove the four-row vectorized gradient/loss matches the scalar FP32
reference within the declared tolerance, one MLX value-and-grad launch serves the
compatible four-row group, and row-scoped executions remain attributable.

The existing C08.1 resource contract remains authoritative for deterministic fallback:
`32/16/8/4/2/1`. Its focused resource suite passed with:

```text
10 passed, 7 subtests passed
```

The native candidate-step custody witness separately proves the vectorized logical
batch reaches exactly one AdamW update while preserving the existing plan and source
binding. No retention publication rule or multi-writer optimizer semantic is changed
by this patch.
