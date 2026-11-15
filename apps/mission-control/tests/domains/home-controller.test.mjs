import test from "node:test";
import assert from "node:assert/strict";
import {
  HOME_FAMILIES,
  familyForEvent,
  queryRequest,
} from "../../renderer/home/home-model.mjs";
import { createHomeController } from "../../renderer/home/home-controller.mjs";

const context = Object.freeze({ runId: "fixture-run", generation: 7, mode: "LIVE" });

function emptyPage(family, state = "EMPTY") {
  return { accepted: true, family, mode: "current", state, coverage: "COMPLETE", records: [] };
}

function fakeHost() {
  return { hidden: false, innerHTML: "", querySelectorAll: () => [] };
}

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

test("same-context home reactivation does not restart the CP01 query and subscription lifecycle", async () => {
  const calls = [];
  let subscriptions = 0;
  let unsubscriptions = 0;
  const api = {
    async status() { return { learnerActive: true }; },
    async query(request) {
      calls.push(request.family);
      return emptyPage(request.family);
    },
    subscribeEvents() {
      subscriptions += 1;
      return async () => { unsubscriptions += 1; };
    },
  };
  const controller = createHomeController(api, { schedule: () => 1, cancel: () => {} });
  const firstHost = fakeHost();
  await controller.activate(context, { host: firstHost, onInspect: () => {}, defense: { historical: false } });
  const baselineCalls = calls.length;
  assert.equal(subscriptions, 1);

  const secondHost = fakeHost();
  await controller.activate(context, { host: secondHost, onInspect: () => {}, defense: { historical: false } });

  assert.equal(calls.length, baselineCalls);
  assert.equal(subscriptions, 1);
  assert.equal(unsubscriptions, 0);
  assert.match(secondHost.innerHTML, /Mission Control|Generation|No training|Unavailable|Current Work/i);

  await controller.activate({ ...context, generation: context.generation + 1 }, {
    host: fakeHost(), onInspect: () => {}, defense: { historical: false },
  });

  assert.equal(calls.length, baselineCalls * 2);
  assert.equal(subscriptions, 2);
  assert.equal(unsubscriptions, 1);
  await controller.deactivate();
});

test("failed unsubscribe does not make a changed context look successfully activated", async () => {
  const calls = [];
  let subscriptions = 0;
  let failNextUnsubscribe = true;
  const api = {
    async status() { return { learnerActive: true }; },
    async query(request) {
      calls.push(request.family);
      return emptyPage(request.family);
    },
    subscribeEvents() {
      subscriptions += 1;
      return async () => {
        if (failNextUnsubscribe) {
          failNextUnsubscribe = false;
          throw new Error("TRANSIENT_UNSUBSCRIBE_FAILURE");
        }
      };
    },
  };
  const controller = createHomeController(api, { schedule: () => 1, cancel: () => {} });
  await controller.activate(context, {
    host: fakeHost(), onInspect: () => {}, defense: { historical: false },
  });
  assert.equal(calls.length, 9);
  assert.equal(subscriptions, 1);

  const changed = { ...context, generation: context.generation + 1 };
  await assert.rejects(controller.activate(changed, {
    host: fakeHost(), onInspect: () => {}, defense: { historical: false },
  }), /TRANSIENT_UNSUBSCRIBE_FAILURE/);

  await controller.activate(changed, {
    host: fakeHost(), onInspect: () => {}, defense: { historical: false },
  });
  assert.equal(calls.length, 18);
  assert.equal(subscriptions, 2);
  await controller.deactivate();
});

test("concurrent changed-context activation waits for failed teardown and retries it", async () => {
  const calls = [];
  let subscriptions = 0;
  let stopCalls = 0;
  let rejectFirstStop;
  const api = {
    async status() { return { learnerActive: true }; },
    async query(request) {
      calls.push(request.family);
      return emptyPage(request.family);
    },
    subscribeEvents() {
      subscriptions += 1;
      return async () => {
        stopCalls += 1;
        if (stopCalls === 1) {
          await new Promise((resolve, reject) => {
            rejectFirstStop = reject;
          });
        }
      };
    },
  };
  const controller = createHomeController(api, { schedule: () => 1, cancel: () => {} });
  await controller.activate(context, {
    host: fakeHost(), onInspect: () => {}, defense: { historical: false },
  });
  assert.equal(calls.length, 9);
  assert.equal(subscriptions, 1);

  const changed = { ...context, generation: context.generation + 1 };
  const first = controller.activate(changed, {
    host: fakeHost(), onInspect: () => {}, defense: { historical: false },
  });
  const rejected = assert.rejects(first, /TRANSIENT_UNSUBSCRIBE_FAILURE/);
  await new Promise((resolve) => setImmediate(resolve));
  const second = controller.activate(changed, {
    host: fakeHost(), onInspect: () => {}, defense: { historical: false },
  });
  await new Promise((resolve) => setImmediate(resolve));
  rejectFirstStop(new Error("TRANSIENT_UNSUBSCRIBE_FAILURE"));

  await rejected;
  await second;
  assert.equal(stopCalls, 2);
  assert.equal(calls.length, 18);
  assert.equal(subscriptions, 2);
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
