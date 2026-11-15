import test from "node:test";
import assert from "node:assert/strict";

import {
  loadNeuralRuntime,
  neuralRuntimeQuery,
} from "../../../renderer/neural/neural-live.mjs";
import { productionNeuralMarkup } from "../../../renderer/neural/neural-production-view.mjs";

const context = Object.freeze({ runId: "accepted-run", generation: 7, mode: "LIVE" });
const datum = (value, units, origin = "MEASURED") => ({ state: "PRESENT", origin, value, units });
const record = (id, observedAt, optimizerStep) => ({
  schema_version: "bilqis.bamf.mission-control.neural-runtime-sample/v1",
  meta: {
    record_id: id,
    observed_at: observedAt,
    materialized_at: observedAt + 2,
    coverage: "COMPLETE",
    authority: "MEASURED",
    source_refs: [`source:${id}`],
    evidence_refs: [`evidence:${id}`],
    receipt_refs: [`receipt:${id}`],
  },
  optimizer_step: optimizerStep,
  step_duration_ms: datum(12.5, "ms"),
  active_parameters: datum(173948416, "parameters"),
  refinement_fraction: datum(0.25, "ratio", "DERIVED"),
});

test("production neural query binds current and historical contexts exactly", () => {
  const current = neuralRuntimeQuery(context);
  assert.equal(current.family, "neural");
  assert.equal(current.mode, "current");
  assert.equal(current.run_id, "accepted-run");
  assert.equal(current.generation, 7);
  const historical = neuralRuntimeQuery({ ...context, mode: "HISTORICAL", generation: 6 });
  assert.equal(historical.mode, "historical");
  assert.equal(historical.generation, 6);
});

test("production neural loader selects the latest accepted observed sample", async () => {
  const records = [record("neural:older", 100, 10), record("neural:newer", 120, 11)];
  const api = { query: async request => ({
    accepted: true, state: "PRESENT", coverage: "COMPLETE",
    records, next_cursor: null, request,
  }) };
  const model = await loadNeuralRuntime(api, context);
  assert.equal(model.snapshot.recordId, "neural:newer");
  assert.equal(model.snapshot.optimizerStep, 11);
  assert.deepEqual(model.snapshot.stepDurationMs, {
    state: "PRESENT", origin: "MEASURED", value: 12.5, units: "ms",
  });
  assert.equal(model.snapshot.refinementFraction.origin, "DERIVED");
});

test("production neural markup renders accepted measurements and source time without fixture copy", () => {
  const snapshot = {
    recordId: "neural:accepted", optimizerStep: 11,
    stepDurationMs: datum(12.5, "ms"),
    activeParameters: datum(173948416, "parameters"),
    refinementFraction: datum(0.25, "ratio", "DERIVED"),
    observedAt: 120, materializedAt: 122, coverage: "COMPLETE", authority: "MEASURED",
    sourceRefs: ["source:accepted"], evidenceRefs: [], receiptRefs: [],
  };
  const markup = productionNeuralMarkup({ state: "PRESENT", snapshot }, context);
  assert.match(markup, /neural:accepted/);
  assert.match(markup, /data-source-unix-seconds="120"/);
  assert.match(markup, /data-source-unix-seconds="122"/);
  assert.match(markup, /12\.5 ms/);
  assert.match(markup, /173948416 parameters/);
  assert.match(markup, /0\.25 ratio/);
  assert.match(markup, /MEASURED/);
  assert.match(markup, /DERIVED/);
  assert.match(markup, /model-neural-help-topology-trigger/);
  assert.match(markup, /model-neural-production-inspect/);
  assert.doesNotMatch(markup, /FIXTURE-BACKED|ILLUSTRATIVE FIXTURE|fixture-run|current fixture/i);
});

test("production neural unavailable state is affirmative and fixture-free", () => {
  const markup = productionNeuralMarkup({ state: "UNAVAILABLE", snapshot: null }, context);
  assert.match(markup, /Neural runtime sample unavailable/);
  assert.doesNotMatch(markup, /fixture|does not prove|does not mean|does not imply/i);
});
