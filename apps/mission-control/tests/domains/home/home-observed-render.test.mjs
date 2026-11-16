import assert from "node:assert/strict";
import test from "node:test";
import { projectionFromPages } from "../../../renderer/home/home-model.mjs";
import { renderHomeMarkup } from "../../../renderer/home/home-view.mjs";
import { context, observation, runPage } from "./home-observed-fixtures.mjs";

test("generation zero shows observed retention and separates accepted coordinates", () => {
  const model = projectionFromPages({ run: runPage() }, context);
  const html = renderHomeMarkup(model, { nowMs: 1_300_000, locale: "en-US" });
  assert.equal(model.startup, null);
  assert.equal(model.observed.current.phase, "RETENTION");
  assert.match(html, /Observed · provisional/);
  assert.match(html, /1 \/ 4 assessments/);
  assert.match(html, /Accepted generation/);
  assert.match(html, /Candidate optimizer step/);
  assert.match(html, /data-source-unix-seconds="1000"/);
  assert.match(html, />5 minutes ago</);
  assert.doesNotMatch(html, /Waiting for the first accepted/);
  assert.equal(model.runtime.retainedCandidates, 0);
});

test("v2 observation exposes completed-step stage timing and hidden B11 multiplicity", () => {
  const row = observation({
    schema_version: "bilqis.bamf.mission-control.trainer-observation/v2",
    candidate_step_wall_seconds: 1.5,
    pre_neural_source_compile_wall_seconds: 0.2,
    currentness_binding_wall_seconds: 0.05,
    b11_preflight_wall_seconds: 0.3,
    b11_autodiff_wall_seconds: 0.6,
    optimizer_admission_wall_seconds: 0.2,
    motif_staging_wall_seconds: 0.0,
    evidence_capture_wall_seconds: 0.01,
    candidate_terminal_step: true,
    c08_gradient_launches: 2,
    c08_vectorized_microbatches: 1,
    c08_materialization_barriers: 1,
    c08_scalar_fallback_rows: 0,
    c08_logical_batch_wall_seconds: 0.9,
    c08_rows_per_gradient_launch: 4,
    b11_provider_draw_count: 32,
    b11_atlas_reload_count: 8,
    logical_rows: 8,
    compiled_positions: 64,
    retention_wall_seconds: 0.4,
    evidence_finalization_wall_seconds: 0.02,
    publishing_wall_seconds: 0.1,
  });
  const model = projectionFromPages({ run: runPage(row) }, context);
  const html = renderHomeMarkup(model, { nowMs: 1_300_000, locale: "en-US" });
  assert.match(html, /Latest completed step performance/);
  assert.match(html, /Step wall time<\/dt><dd>1.5 s/);
  assert.match(html, /Source \+ compile<\/dt><dd>200 ms/);
  assert.match(html, /B11 provider draws<\/dt><dd>32/);
  assert.match(html, /B11 Atlas reloads<\/dt><dd>8/);
  assert.match(html, /Terminal candidate step<\/dt><dd>Yes/);
  assert.equal(model.observed.current.schema_version,
    "bilqis.bamf.mission-control.trainer-observation/v2");
});

test("v3 observation renders clickable completed and active step timing", () => {
  const completed = {
    candidate_step: 1, candidate_optimizer_step: 8,
    candidate_step_wall_seconds: 1.5,
    pre_neural_source_compile_wall_seconds: 0.2,
    currentness_binding_wall_seconds: 0.05,
    b11_preflight_wall_seconds: 0.3,
    b11_autodiff_wall_seconds: 0.6,
    optimizer_admission_wall_seconds: 0.2,
    motif_staging_wall_seconds: 0.0,
    evidence_capture_wall_seconds: 0.01,
    candidate_terminal_step: false,
    c08_gradient_launches: 2,
    c08_vectorized_microbatches: 1,
    c08_materialization_barriers: 1,
    c08_scalar_fallback_rows: 0,
    c08_logical_batch_wall_seconds: 0.9,
    c08_rows_per_gradient_launch: 4,
    b11_provider_draw_count: 32,
    b11_atlas_reload_count: 8,
    logical_rows: 8,
    compiled_positions: 64,
  };
  const row = observation({
    schema_version: "bilqis.bamf.mission-control.trainer-observation/v3",
    phase: "TRAINING", candidate_step: 2, candidate_horizon: 4,
    candidate_optimizer_step: 9, candidate_step_wall_seconds: 12.3,
    candidate_steps: [completed],
  });
  const html = renderHomeMarkup(
    projectionFromPages({ run: runPage(row) }, context),
    { nowMs: 1_300_000, locale: "en-US" });
  assert.match(html, /Candidate step timing/);
  assert.match(html, /data-test-id="home-observed-step-1"/);
  assert.match(html, /Step 1 · 1.5 s/);
  assert.match(html, /data-test-id="home-observed-step-2"/);
  assert.match(html, /Step 2 · running · 12 seconds/);
  assert.match(html, /Source \+ compile<\/th><td>200 ms/);
});

test("epoch-millisecond trainer heartbeat projected to Unix seconds renders near the real observation time", () => {
  const heartbeatMs = Date.UTC(2026, 10, 15, 13, 0, 0, 123);
  const projectedSeconds = Math.floor(heartbeatMs / 1000);
  const row = observation({
    meta: { run: { run_id: "trainer-run", generation: 0 }, observed_at: projectedSeconds },
  });
  const model = projectionFromPages({ run: runPage(row) }, context);
  const html = renderHomeMarkup(model, { nowMs: heartbeatMs + 60_000, locale: "en-US" });
  assert.match(html, /data-source-unix-seconds="1794747600"/);
  assert.match(html, />1 minute ago</);
  assert.doesNotMatch(html, /year/);
});

test("observed elapsed and CPU values render human durations and round fractional seconds", () => {
  const cases = [
    { elapsed_ms: 4_000, cpu_seconds: 0.4, expected: ["4 seconds", "0 seconds"] },
    { elapsed_ms: 64_000, cpu_seconds: 61.25, expected: ["1 minute and 4 seconds", "1 minute and 1 second"] },
    { elapsed_ms: 3_664_000, cpu_seconds: 3_661.5, expected: ["1 hour, 1 minute, and 4 seconds", "1 hour, 1 minute, and 2 seconds"] },
    { elapsed_ms: 93_784_500, cpu_seconds: 90_061.02, expected: ["1 day, 2 hours, 3 minutes, and 5 seconds", "1 day, 1 hour, 1 minute, and 1 second"] },
    { elapsed_ms: 34_560_000_000, cpu_seconds: 34_560_000, expected: ["400 days"] },
  ];
  for (const sample of cases) {
    const row = observation(sample);
    const model = projectionFromPages({ run: runPage(row) }, context);
    const html = renderHomeMarkup(model, { nowMs: 1_300_000, locale: "en-US" });
    for (const value of sample.expected) assert.match(html, new RegExp(value.replaceAll(".", "\\.")));
    assert.doesNotMatch(html, /\b(?:month|year)s?\b/);
  }
  const unavailable = projectionFromPages({ run: runPage(observation({ cpu_seconds: null })) }, context);
  const html = renderHomeMarkup(unavailable, { nowMs: 1_300_000, locale: "en-US" });
  assert.match(html, /Measured process CPU time<\/dt><dd>Unavailable<\/dd>/);
});

test("accepted, rejected and held observations never change retained counts", () => {
  for (const outcome of ["ACCEPTED", "REJECTED", "HELD", "INTERRUPTED"]) {
    const model = projectionFromPages({ run: runPage(observation({ phase: "COMPLETED", outcome,
      connection_state: "FINISHED" })) }, context);
    assert.equal(model.runtime.retainedCandidates, 0);
    assert.equal(model.observed.history[0].outcome, outcome);
    assert.match(renderHomeMarkup(model), new RegExp(outcome));
  }
});

test("interrupted visit history renders the observed failure code and detail", () => {
  const row = observation({
    phase: "COMPLETED", outcome: "INTERRUPTED", connection_state: "FINISHED",
    error_code: "SCHOOL.MODEL_TOPOLOGY.INVALID",
    error_detail: "B11_EXECUTION_BINDING_MISMATCH",
  });
  const model = projectionFromPages({ run: runPage(row) }, context);
  const html = renderHomeMarkup(model, { nowMs: 1_300_000, locale: "en-US" });
  assert.match(html, /Observed · terminated/);
  assert.match(html, /A\.IDENTITY · INTERRUPTED · candidate 1\/1/);
  assert.match(html, /SCHOOL\.MODEL_TOPOLOGY\.INVALID/);
  assert.match(html, /B11_EXECUTION_BINDING_MISMATCH/);
  assert.doesNotMatch(html, /COMPLETED · INTERRUPTED · FINISHED/);
});

test("historical and wrong-run observations remain absent", () => {
  const historical = projectionFromPages({ run: runPage() }, { ...context, mode: "HISTORICAL" });
  assert.equal(historical.observed.current, null);
  assert.doesNotMatch(renderHomeMarkup(historical, { historical: true }), /Observed · provisional/);
  const wrong = observation({ meta: { run: { run_id: "elsewhere" }, observed_at: 1000 } });
  assert.equal(projectionFromPages({ run: runPage(wrong) }, context).observed.current, null);
});

test("disconnected observations preserve last values without claiming current activity", () => {
  const row = observation({ connection_state: "DISCONNECTED" });
  const model = projectionFromPages({ run: runPage(row) }, context);
  assert.match(renderHomeMarkup(model), /Disconnected · last observed/);
  assert.equal(model.observed.current.retention_completed, 1);
});
