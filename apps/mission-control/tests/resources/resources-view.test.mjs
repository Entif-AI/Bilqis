import test from "node:test";
import assert from "node:assert/strict";
import { createResourceController } from "../../renderer/resources/resource-controller.mjs";
import {
  decomposition,
  historicalResourceQuery,
  resourceProfileFromPage,
  resourceQuery,
} from "../../renderer/resources/resource-model.mjs";
import { referenceResourceState, RESOURCE_FIXTURE_MESSAGES } from "../../renderer/resources/resource-fixture-state.mjs";
import { RESOURCE_MESSAGES } from "../../renderer/resources/resource-messages.mjs";
import { renderResourceMarkup } from "../../renderer/resources/resource-view.mjs";
import { createShellState, inspect, openSelectionOwner } from "../../renderer/shell-state.mjs";

const context = Object.freeze({ runId: "fixture-run", generation: 44239, mode: "LIVE" });
const renderFixture = (state = referenceResourceState(), options = {}) =>
  renderResourceMarkup(state, { ...options, messages: RESOURCE_FIXTURE_MESSAGES });

function datum(value, units, origin = "MEASURED") {
  return { state: "PRESENT", origin, value, units };
}

function record(id = "resource:live:1") {
  return {
    schema_version: "bilqis.bamf.mission-control.resource-sample/v1",
    meta: {
      record_id: id,
      observed_at: 100,
      materialized_at: 101,
      source_refs: ["source:resource"],
      evidence_refs: ["evidence:resource"],
      receipt_refs: ["receipt:resource"],
      run: { generation: 7 },
    },
    memory_used_bytes: datum(16 * 1024 ** 3, "bytes"),
    memory_budget_bytes: datum(64 * 1024 ** 3, "bytes", "SOURCE_AUTHORITATIVE"),
    disk_used_bytes: datum(100 * 1024 ** 3, "bytes"),
    step_rate_per_minute: datum(2.5, "steps/minute"),
  };
}

function page(records = [record()], state = "PRESENT") {
  return { accepted: true, family: "resource", mode: "current", state, coverage: "COMPLETE", records };
}

function fakeHost() {
  return { hidden: false, innerHTML: "", querySelectorAll: () => [], querySelector: () => null };
}

test("GUI15 fixture exposes literal budget, MLX, batching, density, and timing diagnostics", () => {
  const state = referenceResourceState();
  const markup = renderFixture(state);
  for (const label of [
    "Unified memory used", "MLX allocated", "MLX cache", "Disk reserve floor",
    "Accepted optimizer steps / h", "Compiled sequence density", "Compiled frame density",
    "Batch size", "Actual length p50", "Actual length p95", "Preparation / compile", "MLX wall time",
  ]) assert.match(markup, new RegExp(label));
  assert.match(markup, /48\.0 GiB/);
  assert.match(markup, /34\.0 GiB/);
  assert.match(markup, /420 steps\/hour/);
  assert.match(markup, /73\.0%/);
  assert.match(markup, /Throughput reports the accepted optimizer-step rate/);
});

test("decomposition reconciles measured categories and reports an explicit remainder", () => {
  const profile = referenceResourceState().current;
  const totals = decomposition(profile);
  assert.equal(totals.aggregate, 48 * 1024 ** 3);
  assert.equal(totals.allocated, 40 * 1024 ** 3);
  assert.equal(totals.remainder, 8 * 1024 ** 3);
  assert.equal(totals.complete, false);
  const markup = renderFixture();
  assert.match(markup, /Unallocated \/ uninstrumented remainder/);
  assert.match(markup, /8\.0 GiB/);
  assert.match(markup, /The remainder is memory outside the recorded categories/);
});

test("Resources uses one peer tab layer with shared help and recorded time", () => {
  const markup = renderFixture();
  assert.equal((markup.match(/role="tablist"/g) ?? []).length, 1);
  assert.equal((markup.match(/role="tab"/g) ?? []).length, 4);
  assert.match(markup, /aria-selected="true"[^>]*data-test-id="resources-tab-overview"/);
  for (const id of ["value-types", "decomposition", "compute", "reserve", "length", "timeline", "comparison"]) {
    assert.match(markup, new RegExp(`data-test-id="resources-help-${id}-trigger"`));
  }
  assert.match(markup, /data-source-unix-seconds="[^"]+"[^>]*data-test-id="resources-time-0"/);
  assert.doesNotMatch(markup, /Observed at \(Unix seconds\)/);
});

test("production Resources keeps fixture strings outside the production message catalog", () => {
  const profile = resourceProfileFromPage(page(), { runId: "run-7", generation: 7, mode: "LIVE" });
  const markup = renderResourceMarkup({ current: profile, comparison: null, comparisonState: "EMPTY" });
  assert.doesNotMatch(markup, /REFERENCE RESOURCE DATA|FIXTURE-BACKED|resource:fixture|44239/);
  assert.equal(Object.hasOwn(RESOURCE_MESSAGES["en-US"], "resource.fixture"), false);
});

test("Resources owned copy is affirmative and avoids unsolicited negative-capability language", () => {
  const markup = renderFixture();
  assert.doesNotMatch(markup, /does not (?:prove|establish|imply|demonstrate|mean)|not evidence of|not measured peaks|not measurements|No generation is inferred/i);
});

test("configured limit, measured value, and estimate have distinct semantic presentation", () => {
  const markup = renderFixture();
  assert.match(markup, /data-resource-semantic="measured"/);
  assert.match(markup, /data-resource-semantic="configured-limit"/);
  assert.match(markup, /data-resource-semantic="estimate"/);
  assert.match(markup, /Measured value/);
  assert.match(markup, /CONFIGURED LIMIT/);
  assert.match(markup, /ESTIMATE/);
});

test("live CP03 resource projection refuses to fabricate unavailable decomposition", () => {
  const profile = resourceProfileFromPage(page(), { runId: "run-7", generation: 7, mode: "LIVE" });
  assert.equal(profile.aggregate.unifiedMemoryUsed.value, 16 * 1024 ** 3);
  assert.equal(profile.aggregate.diskUsed.value, 100 * 1024 ** 3);
  assert.equal(profile.aggregate.diskReserve.state, "UNAVAILABLE");
  assert.equal(profile.aggregate.mlxAllocatedMemory.state, "UNAVAILABLE");
  assert.equal(profile.aggregate.batchSize.state, "UNAVAILABLE");
  assert.equal(profile.aggregate.acceptedStepsHour.value, 150);
  assert.equal(profile.aggregate.acceptedStepsHour.origin, "DERIVED");
  assert.ok(profile.memoryDecomposition.every((item) => item.state === "UNAVAILABLE"));
  assert.equal(decomposition(profile).remainder, 16 * 1024 ** 3);
});

test("resource timeline preserves exact accepted references without inventing correlation classes", () => {
  const profile = resourceProfileFromPage(page([record("resource:<unsafe>")]), context);
  const sample = profile.timeline[0];
  assert.deepEqual(sample.exactRefs, ["source:resource", "evidence:resource", "receipt:resource"]);
  const markup = renderResourceMarkup({ current: profile, comparison: null, comparisonState: "EMPTY" });
  assert.doesNotMatch(markup, /resource:<unsafe>/);
  assert.match(markup, /resource:&lt;unsafe&gt;/);
  assert.match(markup, /MLX.*UNAVAILABLE/s);
});

test("fixture spike selection carries episode, batch, checkpoint, source-workload, and resource identities", () => {
  const spike = referenceResourceState().current.timeline.find((row) => row.unifiedMemoryUsed === 54 * 1024 ** 3);
  assert.equal(spike.id, "resource:fixture:44239:0003");
  assert.equal(spike.episodeId, "episode-record:fixture:interference-44239");
  assert.equal(spike.batchId, "batch:fixture:44239:03");
  assert.equal(spike.checkpointId, "checkpoint:fixture:candidate-44239");
  assert.equal(spike.sourceWorkload, "factory:fixture:compile:03");
  assert.equal(spike.expansionCount, 7);
});

test("historical comparison binds only an explicit exact generation", () => {
  const request = historicalResourceQuery({ runId: "run-7", generation: 9, mode: "LIVE" }, 6);
  assert.equal(request.mode, "historical");
  assert.equal(request.run_id, "run-7");
  assert.equal(request.generation, 6);
  assert.throws(() => historicalResourceQuery(context, -1), /GUI15_HISTORICAL_GENERATION_REQUIRED/);
  assert.throws(() => historicalResourceQuery(context, 1.5), /GUI15_HISTORICAL_GENERATION_REQUIRED/);
  const markup = renderFixture({ current: referenceResourceState().current, comparison: null, comparisonState: "EMPTY" });
  assert.match(markup, /Loads the exact generation through a read-only CP03 historical query/);
});

test("live GUI15 refreshes only for resource events and never opens a historical subscription", async () => {
  const calls = [];
  let listener = null;
  let subscriptions = 0;
  const api = {
    async query(request) {
      calls.push(request);
      return page();
    },
    subscribeEvents(next) {
      subscriptions += 1;
      listener = next;
      return async () => { listener = null; };
    },
  };
  const controller = createResourceController(api);
  await controller.activate({ runId: "run-7", generation: 7, mode: "LIVE" }, {
    target: fakeHost(), onInspect: () => {}, defense: { historical: false },
  });
  assert.equal(subscriptions, 1);
  const baseline = calls.length;
  await listener({ event_family: "capability.changed" });
  assert.equal(calls.length, baseline);
  await listener({ event_family: "resource.health.sample" });
  assert.equal(calls.length, baseline + 1);
  assert.equal(calls.at(-1).family, "resource");
  await controller.deactivate();

  const historicalApi = {
    async query(request) { calls.push(request); return page(); },
    subscribeEvents() { subscriptions += 1; return async () => {}; },
  };
  const historicalController = createResourceController(historicalApi);
  const before = subscriptions;
  await historicalController.activate({ runId: "run-7", generation: 6, mode: "HISTORICAL" }, {
    target: fakeHost(), onInspect: () => {}, defense: { historical: true },
  });
  assert.equal(subscriptions, before);
  await historicalController.deactivate();
});

test("comparison loader performs a bounded historical CP03 resource query", async () => {
  const calls = [];
  const controller = createResourceController({
    async query(request) { calls.push(request); return page(); },
    subscribeEvents() { return async () => {}; },
  });
  await controller.activate({ runId: "run-7", generation: 7, mode: "LIVE" }, {
    target: fakeHost(), onInspect: () => {}, defense: { historical: false },
  });
  await controller.loadComparison(5);
  assert.equal(calls.at(-1).family, "resource");
  assert.equal(calls.at(-1).mode, "historical");
  assert.equal(calls.at(-1).generation, 5);
  assert.equal(controller.currentState().comparison.generation, 5);
  await controller.deactivate();
});

test("resource query stays read-only and requests no mutation surface", () => {
  const request = resourceQuery(context);
  assert.deepEqual(Object.keys(request).sort(), [
    "as_of", "cursor", "family", "frontier_id", "generation", "limit", "mode",
    "record_id", "reference", "run_id", "schema", "schema_version",
  ].sort());
  const markup = renderFixture();
  assert.doesNotMatch(markup, /start training|change batch|apply budget|scale hardware/i);
});

test("missing observation time never borrows materialization time", () => {
  const sample = record("resource:time-authority");
  delete sample.meta.observed_at;
  sample.meta.materialized_at = 999;
  const profile = resourceProfileFromPage(page([sample]), context);
  assert.equal(profile.timeline[0].observedAt, null);
  const markup = renderResourceMarkup({ current: profile });
  assert.match(markup, /Time unavailable/);
  assert.doesNotMatch(markup, /data-source-unix-seconds="999"/);
});

test("resource identities route back to the Resources owner surface", () => {
  const operatorView = {
    active_capability_id: "B.EXAMPLE", learner_state: "READY", stage: "ASSESS_MAIN",
    related_record_ids: [], schema_version: "bilqis.bamf.mission-control.operator-view/v1",
    meta: {
      as_of: 1, authority: "DERIVED", coverage: "COMPLETE", evidence_refs: [],
      materialized_at: 1, observed_at: 1, receipt_refs: [], record_id: "operator-view:test",
      source_refs: [],
      run: {
        candidate_identity_sha256: "2".repeat(64), factory_release_sha256: "2".repeat(64),
        generation: 1, generation_manifest_sha256: "1".repeat(64), run_id: "run-test",
        run_identity_sha256: "4".repeat(64), semantic_release_sha256: "3".repeat(64),
        topology_sha256: "4".repeat(64),
      },
    },
  };
  const selected = inspect(createShellState(operatorView), { kind: "resource", id: "resource:1" });
  assert.equal(openSelectionOwner(selected).view, "resources");
});
