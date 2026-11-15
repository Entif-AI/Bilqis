import assert from "node:assert/strict";
import test from "node:test";
import { createHomeController } from "../../../renderer/home/home-controller.mjs";
import { context, disclosureHost, host, observation, runPage } from "./home-observed-fixtures.mjs";

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

test("an open step timing disclosure stays open across live heartbeat refresh", async () => {
  let listener;
  const completed = {
    candidate_step: 1, candidate_optimizer_step: 8, candidate_step_wall_seconds: 1.5,
    pre_neural_source_compile_wall_seconds: 0.2, currentness_binding_wall_seconds: 0.05,
    b11_preflight_wall_seconds: 0.3, b11_autodiff_wall_seconds: 0.6,
    optimizer_admission_wall_seconds: 0.2, motif_staging_wall_seconds: 0.0,
    evidence_capture_wall_seconds: 0.01, candidate_terminal_step: false,
    c08_gradient_launches: 2, c08_vectorized_microbatches: 1,
    c08_materialization_barriers: 1, c08_scalar_fallback_rows: 0,
    c08_logical_batch_wall_seconds: 0.9, c08_rows_per_gradient_launch: 4,
    b11_provider_draw_count: 32, b11_atlas_reload_count: 8, logical_rows: 8, compiled_positions: 64,
  };
  let page = runPage(observation({
    schema_version: "bilqis.bamf.mission-control.trainer-observation/v3",
    phase: "TRAINING", candidate_step: 2, candidate_horizon: 4, candidate_optimizer_step: 9,
    candidate_step_wall_seconds: 2.0, candidate_steps: [completed],
  }));
  const renderHost = disclosureHost();
  const controller = createHomeController({
    query: async ({ family }) => family === "run"
      ? page : { accepted: true, state: "EMPTY", records: [] },
    status: async () => ({ learnerActive: true }),
    subscribeEvents(next) { listener = next; return () => {}; },
  }, { schedule: () => 1, cancel: () => {} });
  await controller.activate(context, { host: renderHost });
  const step = renderHost.disclosure("home-observed-step-2");
  assert.ok(step);
  step.open = true;
  page = runPage(observation({
    schema_version: "bilqis.bamf.mission-control.trainer-observation/v3", revision: 4,
    phase: "TRAINING", candidate_step: 2, candidate_horizon: 4, candidate_optimizer_step: 9,
    candidate_step_wall_seconds: 3.0, candidate_steps: [completed],
    meta: { run: { run_id: "trainer-run", generation: 0 }, observed_at: 1001 },
  }));
  await listener({ event_family: "run.trainer.observed" });
  assert.equal(renderHost.disclosure("home-observed-step-2")?.open, true);
  assert.match(renderHost.innerHTML, /Step 2 · running · 3 s/);
  assert.match(renderHost.innerHTML, /Step wall time<\/th><td>3 s/);
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
