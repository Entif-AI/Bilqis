import test from "node:test";
import assert from "node:assert/strict";
import {
  HOME_FAMILIES,
  classifyLearning,
  familyForEvent,
  homeStatus,
  projectionFromPages,
  queryRequest,
} from "../../renderer/home/home-model.mjs";
import { referenceHomeProjection } from "../../renderer/home/home-fixture.mjs";
import { createHomeController } from "../../renderer/home/home-controller.mjs";
import { renderHomeMarkup } from "../../renderer/home/home-view.mjs";
import { collectTestIds } from "../../renderer/foundation/test-hooks.mjs";

const context = Object.freeze({ runId: "fixture-run", generation: 7, mode: "LIVE" });

function emptyPage(family, state = "EMPTY") {
  return { accepted: true, family, mode: "current", state, coverage: "COMPLETE", records: [] };
}

function fakeHost() {
  return { hidden: false, innerHTML: "", querySelectorAll: () => [] };
}

function runPage({ generation = 0, optimizerStep = 0, stage = "UNKNOWN" } = {}) {
  return {
    accepted: true, family: "run", mode: "current", state: "PRESENT", coverage: "COMPLETE",
    records: [{
      schema_version: "bilqis.bamf.mission-control.run-context/v1",
      meta: { run: { generation } },
      run_state: "ACCEPTED", optimizer_step: optimizerStep, stage,
    }],
  };
}

test("Home uses the governed five-state band and target overview regions", () => {
  const model = referenceHomeProjection();
  const markup = renderHomeMarkup(model);
  for (const id of ["running", "learning", "regression", "blocked", "invalidity"]) {
    assert.match(markup, new RegExp(`data-test-id="home-status-${id}"`));
  }
  assert.doesNotMatch(markup, /home-status-work/);
  for (const id of ["home-current-work", "home-attention", "home-pulse", "home-school", "home-health-details"]) {
    assert.match(markup, new RegExp(`data-test-id="${id}"`));
  }
  assert.match(markup, /Fixture evidence/);
  assert.match(markup, /School Snapshot/);
  assert.equal(model.learningStatus, "IMPROVING");
});

test("Home health is collapsed detail and operator-significant work values remain complete", () => {
  const markup = renderHomeMarkup(referenceHomeProjection());
  assert.match(markup, /<details class="home-health" data-test-id="home-health-details">/);
  assert.doesNotMatch(markup, /home-metric-card|home-health-strip/);
  assert.match(markup, /paired-screen:source\+prereq/);
  assert.match(markup, /AWAITING_RECONCILIATION/);
});

test("serious attention leads the operational row while healthy attention stays secondary", () => {
  const fixture = referenceHomeProjection();
  const fixtureMarkup = renderHomeMarkup(fixture);
  assert.equal(homeStatus(fixture).attentionPriority, "primary");
  assert.ok(fixtureMarkup.indexOf('data-test-id="home-attention"') < fixtureMarkup.indexOf('data-test-id="home-current-work"'));
  const healthy = { ...fixture, pulse: Object.freeze([]), attention: Object.freeze([]), learningStatus: "IMPROVING" };
  const healthyMarkup = renderHomeMarkup(healthy);
  assert.equal(homeStatus(healthy).attentionPriority, "secondary");
  assert.ok(healthyMarkup.indexOf('data-test-id="home-current-work"') < healthyMarkup.indexOf('data-test-id="home-attention"'));
});

test("Home markup exposes unique stable home test hooks", () => {
  const ids = collectTestIds(renderHomeMarkup(referenceHomeProjection()));
  assert.equal(new Set(ids).size, ids.length);
  assert.ok(ids.length > 20);
  assert.ok(ids.every((id) => id.startsWith("home-")));
});

test("ten retained no-growth events remain throughput and never become learned success", () => {
  assert.equal(classifyLearning({ retained: 10, freshRetainedImprovements: 0 }), "THROUGHPUT_ONLY");
  const markup = renderHomeMarkup({ ...referenceHomeProjection(), learningStatus: "THROUGHPUT_ONLY" });
  assert.match(markup, /Throughput is present, but no fresh retained improvement is evidenced/);
  assert.doesNotMatch(markup, /Fresh retained improvement is evidenced/);
});

test("fresh retained improvement is distinct and exact regression event retains drill-through identity", () => {
  const model = referenceHomeProjection();
  assert.equal(classifyLearning({ retained: 1, freshRetainedImprovements: 1 }), "IMPROVING");
  const regression = model.pulse.find((event) => event.kind === "regress");
  assert.deepEqual(regression.target, { kind: "capability", id: "A.PARENT" });
  const gain = model.pulse.find((event) => event.kind === "gain");
  assert.equal(gain.target.kind, "episode");
  assert.match(gain.target.id, /^episode-record:/);
});

test("reference Home events do not treat generation coordinates as wall-clock time", () => {
  const model = referenceHomeProjection();
  for (const event of model.pulse) {
    assert.equal(event.observedAt, null);
    assert.equal(event.materializedAt, null);
  }
});

test("attention queue contains actionable conditions rather than ordinary healthy telemetry", () => {
  const model = referenceHomeProjection();
  assert.deepEqual(model.attention.map((item) => item.kind), ["stalled", "held", "recovery"]);
  assert.equal(model.attention.some((item) => item.label !== undefined || item.detail !== undefined), false);
});

test("stale and partial query states remain explicit instead of becoming healthy zeroes", () => {
  const pages = Object.fromEntries(HOME_FAMILIES.map((family) => [family, emptyPage(family)]));
  pages.capability = emptyPage("capability", "STALE");
  pages.resource = emptyPage("resource", "PARTIAL");
  const model = projectionFromPages(pages, context);
  assert.equal(model.state.capability, "STALE");
  assert.equal(model.state.resource, "PARTIAL");
  assert.equal(model.learning.latestSchoolScore, null);
  assert.equal(model.system.memoryPressure, null);
  const markup = renderHomeMarkup(model);
  assert.match(markup, /data-state="STALE"/);
  assert.match(markup, /data-state="PARTIAL"/);
  assert.match(markup, /Unavailable/);
});

test("RUNNING reflects the live learner-active handshake instead of mere run-record presence", () => {
  const pages = Object.fromEntries(HOME_FAMILIES.map((family) => [family, emptyPage(family)]));
  const stopped = projectionFromPages(pages, { ...context, operatorActive: false });
  const running = projectionFromPages(pages, { ...context, operatorActive: true });
  assert.equal(homeStatus(stopped).running, false);
  assert.equal(homeStatus(running).running, true);
  assert.match(renderHomeMarkup(stopped), /<dt>Running<\/dt><dd>No<\/dd>/);
  assert.match(renderHomeMarkup(running), /<dt>Running<\/dt><dd>Yes<\/dd>/);
});

test("accepted generation zero renders a setup state instead of a wall of unavailable metrics", () => {
  const pages = Object.fromEntries(HOME_FAMILIES.map((family) => [family, emptyPage(family)]));
  pages.run = runPage();
  const model = projectionFromPages(pages, { ...context, runId: "aspirant", generation: 0, operatorActive: false });
  const markup = renderHomeMarkup(model);
  assert.equal(model.startup.state, "GENERATION_ZERO_READY");
  assert.match(markup, /Generation 0 is accepted and ready/);
  assert.match(markup, /Optimizer step<\/dt><dd>0/);
  assert.match(markup, /Trainer<\/dt><dd>Stopped/);
  assert.match(markup, /No training events yet/);
  assert.match(markup, /data-test-id="home-startup-operate"/);
  assert.doesNotMatch(markup, /Unavailable/);
  assert.doesNotMatch(markup, /Latest school score|Whole-school growth|Peak memory/);
});

test("historical home queries bind the explicit prior generation", () => {
  const request = queryRequest("capability", { runId: "run-7", generation: 6, mode: "HISTORICAL" });
  assert.equal(request.mode, "historical");
  assert.equal(request.run_id, "run-7");
  assert.equal(request.generation, 6);
});

test("CP04 event families refresh only their owning CP03 family", () => {
  assert.equal(familyForEvent({ event_family: "candidate.retained" }), "episode");
  assert.equal(familyForEvent({ event_family: "capability.changed" }), "capability");
  assert.equal(familyForEvent({ event_family: "resource.health.sample" }), "resource");
  assert.equal(familyForEvent({ event_family: "warning.failure" }), null);
});

test("live home uses one family query per CP04 event rather than polling the full view", async () => {
  const calls = [];
  let active = true;
  let listener = null;
  const api = {
    async status() { return { learnerActive: active }; },
    async query(request) {
      calls.push(request.family);
      return emptyPage(request.family);
    },
    subscribeEvents(next) {
      listener = next;
      return async () => { listener = null; };
    },
  };
  const controller = createHomeController(api);
  await controller.activate(context, { host: fakeHost(), onInspect: () => {}, defense: { historical: false } });
  assert.deepEqual(new Set(calls), new Set(HOME_FAMILIES));
  assert.equal(controller.currentModel().runtime.running, true);
  const baseline = calls.length;
  active = false;
  await listener({ event_family: "operator.action.state" });
  assert.equal(controller.currentModel().runtime.running, false);
  assert.equal(calls.length, baseline);
  await listener({ event_family: "capability.changed" });
  assert.equal(calls.length, baseline + 1);
  assert.equal(calls.at(-1), "capability");
  await controller.deactivate();
});

test("historical home never opens a live CP04 subscription", async () => {
  let subscriptions = 0;
  const api = {
    async query(request) { return { ...emptyPage(request.family), mode: "historical" }; },
    subscribeEvents() { subscriptions += 1; return async () => {}; },
  };
  const controller = createHomeController(api);
  await controller.activate({ ...context, mode: "HISTORICAL" }, {
    host: fakeHost(), onInspect: () => {}, defense: { historical: true },
  });
  assert.equal(subscriptions, 0);
});
