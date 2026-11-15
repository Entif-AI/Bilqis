import assert from "node:assert/strict";
import test from "node:test";
import { projectionFromPages } from "../../renderer/home/home-model.mjs";
import { renderHomeMarkup } from "../../renderer/home/home-view.mjs";
import { createHomeController } from "../../renderer/home/home-controller.mjs";

const context = { runId: "trainer-run", generation: 0, mode: "LIVE", operatorActive: true };
function observation(changes = {}) {
  return { schema_version: "bilqis.bamf.mission-control.trainer-observation/v1",
    meta: { run: { run_id: "trainer-run", generation: 0 }, observed_at: 1000 },
    observation_id: "visit-1", revision: 3, visit_index: 1, posture: "OBSERVED",
    phase: "RETENTION", outcome: "RUNNING", connection_state: "LIVE", capability_id: "A.IDENTITY",
    candidate_step: 1, candidate_horizon: 1, candidate_optimizer_step: 1,
    retention_completed: 1, retention_total: 4, retention_subject: "A.IDENTITY", retention_role: "parent",
    elapsed_ms: 1500, cpu_seconds: 0.4, peak_rss_bytes: 1048576, disk_free_bytes: 1073741824,
    ...changes };
}
function runPage(row = observation(), generation = 0) {
  return { accepted: true, state: "PARTIAL", records: [
    { schema_version: "bilqis.bamf.mission-control.run-context/v1",
      meta: { run: { run_id: "trainer-run", generation, generation_manifest_sha256: `manifest-${generation}` } },
      optimizer_step: generation, stage: "FOUNDATION" }, row,
  ] };
}
const host = () => ({ innerHTML: "", querySelectorAll: () => [] });

function disclosureHost() {
  let markup = "";
  let details = new Map();
  return {
    hidden: false,
    get innerHTML() { return markup; },
    set innerHTML(value) {
      markup = value;
      details = new Map([...value.matchAll(/<details\b([^>]*)data-test-id="([^"]+)"([^>]*)>/g)].map((match) => [
        match[2], { dataset: { testId: match[2] }, open: /\bopen\b/.test(`${match[1]} ${match[3]}`) },
      ]));
    },
    querySelectorAll(selector) {
      if (selector === "details[data-test-id][open]") return [...details.values()].filter((item) => item.open);
      return [];
    },
    querySelector(selector) {
      const match = selector.match(/^\[data-test-id="([^"]+)"\]$/);
      return match ? details.get(match[1]) ?? null : null;
    },
    disclosure(id) { return details.get(id) ?? null; },
  };
}

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

test("observed elapsed and CPU values render human durations across seconds minutes hours days and fractions", () => {
  const cases = [
    { elapsed_ms: 4_000, cpu_seconds: 0.4, expected: ["4 seconds", "0.4 seconds"] },
    { elapsed_ms: 64_000, cpu_seconds: 61.25, expected: ["1 minute and 4 seconds", "1 minute and 1.25 seconds"] },
    { elapsed_ms: 3_664_000, cpu_seconds: 3_661.5, expected: ["1 hour, 1 minute, and 4 seconds", "1 hour, 1 minute, and 1.5 seconds"] },
    { elapsed_ms: 93_784_500, cpu_seconds: 90_061.02, expected: ["1 day, 2 hours, 3 minutes, and 4.5 seconds", "1 day, 1 hour, 1 minute, and 1.02 seconds"] },
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

test("a recovery tick restores a missed terminal event without navigation or another event", async () => {
  let page = runPage();
  let tick;
  const controller = createHomeController({ query: async () => page,
    status: async () => ({ learnerActive: true }), subscribeEvents: () => () => {} },
  { schedule: (callback) => { tick = callback; return 1; }, cancel: () => {} });
  await controller.activate(context, { host: host() });
  page = runPage(observation({ phase: "COMPLETED", outcome: "ACCEPTED", connection_state: "FINISHED" }), 1);
  await tick();
  assert.equal(controller.currentModel().observed.current.outcome, "ACCEPTED");
  assert.equal(controller.currentModel().observed.acceptedGeneration, 1);
  await controller.deactivate();
});

test("observed history stays open across a live trainer update", async () => {
  let listener;
  let page = runPage();
  const renderHost = disclosureHost();
  const controller = createHomeController({
    query: async ({ family }) => family === "run"
      ? page : { accepted: true, state: "EMPTY", records: [] },
    status: async () => ({ learnerActive: true }),
    subscribeEvents(next) { listener = next; return () => {}; },
  }, { schedule: () => 1, cancel: () => {} });
  await controller.activate(context, { host: renderHost });
  const history = renderHost.disclosure("home-observed-history");
  assert.ok(history);
  history.open = true;
  page = runPage(observation({ revision: 4, meta: { run: { run_id: "trainer-run", generation: 0 }, observed_at: 1001 } }));
  await listener({ event_family: "run.trainer.observed" });
  assert.equal(renderHost.disclosure("home-observed-history")?.open, true);
  await controller.deactivate();
});

test("late live queries cannot populate historical navigation", async () => {
  let release;
  let first = true;
  const controller = createHomeController({ query: async (request) => {
    if (first) { first = false; await new Promise((resolve) => { release = resolve; }); }
    return request.mode === "historical" ? { accepted: true, state: "EMPTY", records: [] } : runPage();
  }, subscribeEvents: () => () => {} }, { schedule: () => 1, cancel: () => {} });
  const live = controller.activate(context, { host: host() });
  await new Promise((resolve) => setImmediate(resolve));
  await controller.activate({ ...context, mode: "HISTORICAL" }, { host: host() });
  release();
  await live;
  assert.equal(controller.currentModel().observed.current, null);
  await controller.deactivate();
});

test("transport failure keeps last observation disconnected and reconnect reloads it", async () => {
  let tick, fail = false, connects = 0, subscriptions = 0;
  let page = runPage();
  const controller = createHomeController({
    query: async () => { if (fail) throw new Error("offline"); return page; },
    connect: async () => { connects++; fail = false; },
    subscribeEvents: () => { subscriptions++; return () => {}; },
  }, { schedule: (callback) => { tick = callback; return 1; }, cancel: () => {} });
  await controller.activate(context, { host: host() });
  fail = true;
  await tick();
  assert.equal(controller.currentModel().observed.current.connection_state, "DISCONNECTED");
  page = runPage(observation({ phase: "COMPLETED", outcome: "REJECTED", connection_state: "FINISHED" }));
  await tick();
  assert.equal(connects, 1);
  assert.equal(subscriptions, 2);
  assert.equal(controller.currentModel().observed.current.outcome, "REJECTED");
  await controller.deactivate();
});

test("a subscription resolving after navigation is immediately closed", async () => {
  let release, stopped = 0;
  const controller = createHomeController({
    query: async () => ({ accepted: true, state: "EMPTY", records: [] }),
    subscribeEvents: () => new Promise((resolve) => { release = () => resolve(() => { stopped++; }); }),
  }, { schedule: () => 1, cancel: () => {} });
  const live = controller.activate(context, { host: host() });
  await new Promise((resolve) => setImmediate(resolve));
  await controller.activate({ ...context, mode: "HISTORICAL" }, { host: host() });
  release();
  await live;
  assert.equal(stopped, 1);
  await controller.deactivate();
});

test("rejected transport pages trigger reconnect instead of clearing current posture", async () => {
  let tick, unavailable = false, connects = 0;
  const controller = createHomeController({
    query: async () => unavailable ? { accepted: false, reason: "CONTROL_PLANE_NOT_CONNECTED" } : runPage(),
    connect: async () => { connects += 1; unavailable = false; },
    subscribeEvents: () => () => {},
  }, { schedule: (callback) => { tick = callback; return 1; }, cancel: () => {} });
  await controller.activate(context, { host: host() });
  unavailable = true;
  await tick();
  assert.equal(controller.currentModel().observed.current.connection_state, "DISCONNECTED");
  await tick();
  assert.equal(connects, 1);
  assert.equal(controller.currentModel().observed.current.connection_state, "LIVE");
  await controller.deactivate();
});

test("defensive historical posture forces historical queries and suppresses observations", async () => {
  const requests = [];
  const controller = createHomeController({ query: async (request) => {
    requests.push(request); return runPage();
  }, subscribeEvents: () => { throw new Error("must not subscribe"); } },
  { schedule: () => { throw new Error("must not schedule"); }, cancel: () => {} });
  await controller.activate(context, { host: host(), defense: { historical: true } });
  assert.ok(requests.every((request) => request.mode === "historical"));
  assert.equal(controller.currentModel().observed.current, null);
  await controller.deactivate();
});

test("snapshot recovery still loads when event subscription is unavailable", async () => {
  const controller = createHomeController({ query: async () => runPage(),
    subscribeEvents: () => { throw new Error("unavailable stream"); } },
  { schedule: () => 1, cancel: () => {} });
  await controller.activate(context, { host: host() });
  assert.equal(controller.currentModel().observed.current.phase, "RETENTION");
  await controller.deactivate();
});

test("snapshot requests cannot retain pre-publication families behind a successor RUN", async () => {
  let runObserved = false, tick;
  const controller = createHomeController({ query: async ({ family }) => {
    if (family === "run") {
      await Promise.resolve();
      runObserved = true;
      return runPage(observation({ phase: "COMPLETED", outcome: "ACCEPTED", connection_state: "FINISHED" }), 1);
    }
    const records = family === "episode" && runObserved ? [{
      schema_version: "bilqis.bamf.mission-control.candidate-decision/v1",
      outcome: "ACCEPTED", capability_id: "A.IDENTITY", reason_code: "RETAINED",
      meta: { run: { run_id: context.runId, generation: 1 } },
    }] : [];
    return { accepted: true, state: records.length ? "PRESENT" : "EMPTY", records };
  }, subscribeEvents: () => () => {} },
  { schedule: (callback) => { tick = callback; return 1; }, cancel: () => {} });
  await controller.activate(context, { host: host() });
  await tick();
  assert.equal(controller.currentModel().observed.acceptedGeneration, 1);
  assert.equal(controller.currentModel().runtime.retainedCandidates, 1);
  await controller.deactivate();
});

test("publication between snapshot anchors retries on the next bounded tick", async () => {
  let runReads = 0, tick;
  const controller = createHomeController({ query: async ({ family }) => {
    if (family === "run") { runReads += 1; return runPage(observation(), runReads === 1 ? 0 : 1); }
    const records = family === "episode" && runReads > 2 ? [{
      schema_version: "bilqis.bamf.mission-control.candidate-decision/v1",
      outcome: "ACCEPTED", capability_id: "A.IDENTITY", reason_code: "RETAINED",
      meta: { run: { run_id: context.runId, generation: 1 } },
    }] : [];
    return { accepted: true, state: records.length ? "PRESENT" : "EMPTY", records };
  }, subscribeEvents: () => () => {} },
  { schedule: (callback) => { tick = callback; return 1; }, cancel: () => {} });
  await controller.activate(context, { host: host() });
  assert.equal(controller.currentModel()?.observed?.acceptedGeneration ?? null, null);
  await tick();
  assert.equal(controller.currentModel().observed.acceptedGeneration, 1);
  assert.equal(controller.currentModel().runtime.retainedCandidates, 1);
  await controller.deactivate();
});
