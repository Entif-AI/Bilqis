"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const { CHANNELS } = require("../channels.cjs");
const { loadSandboxedPreload } = require("./_preload-fixture.cjs");

const GLOBAL_NAME = "bamfMissionControl";

function fakeRenderer() {
  const invoked = [];
  const listeners = new Map();
  return {
    invoked,
    listeners,
    invoke(channel, ...args) {
      invoked.push([channel, ...args]);
      return Promise.resolve({ channel });
    },
    on(channel, listener) {
      listeners.set(channel, listener);
    },
    removeListener(channel, listener) {
      if (listeners.get(channel) === listener) {
        listeners.delete(channel);
      }
    },
  };
}

test("preload exposes only the enumerated Mission Control capability surface", () => {
  const renderer = fakeRenderer();
  const exposed = loadSandboxedPreload(renderer);
  const api = exposed.api;

  assert.equal(exposed.name, GLOBAL_NAME);
  assert.deepEqual(Object.keys(api).sort(), [
    "connect",
    "fetchReceipt",
    "launchMode",
    "query",
    "querySnapshot",
    "requestCommand",
    "requestDryRun",
    "status",
    "subscribeEvents",
  ]);
  assert.equal(Object.isFrozen(api), true);
  assert.equal(api.launchMode, "production");
  assert.equal(api.invoke, undefined);
  assert.equal(api.send, undefined);
  assert.equal(api.readFile, undefined);
  assert.equal(api.shell, undefined);
  assert.equal(api.spawn, undefined);
});

test("preload exposes fixture mode only from the fixed launch argument", () => {
  const renderer = fakeRenderer();
  const api = loadSandboxedPreload(renderer, ["electron", "--bamf-mc-mode=fixtures"]).api;
  assert.equal(api.launchMode, "fixtures");
  assert.throws(
    () => loadSandboxedPreload(renderer, ["electron", "--bamf-mc-mode=demo"]),
    /BAMF_MISSION_CONTROL_MODE_INVALID/,
  );
});

test("preload rejects credential injection and malformed requests before IPC", async () => {
  const renderer = fakeRenderer();
  const api = loadSandboxedPreload(renderer).api;

  assert.throws(
    () => api.querySnapshot({ sessionToken: "stolen" }),
    /BAMF_GUI20_IPC_ARGUMENT_INVALID:FORBIDDEN_KEY:sessionToken/,
  );
  assert.throws(
    () => api.requestCommand("python3 -m bilqis_mlx.cli train"),
    /BAMF_GUI20_IPC_ARGUMENT_INVALID:REQUEST_OBJECT_REQUIRED/,
  );
  assert.throws(
    () => api.requestDryRun({ credential: "stolen" }),
    /BAMF_GUI20_IPC_ARGUMENT_INVALID:FORBIDDEN_KEY:credential/,
  );
  assert.throws(
    () => api.fetchReceipt(null),
    /BAMF_GUI20_IPC_ARGUMENT_INVALID:STABLE_REF_REQUIRED/,
  );
  assert.deepEqual(renderer.invoked, []);
});

test("preload invokes only fixed channels and unsubscribes its fixed event listener", async () => {
  const renderer = fakeRenderer();
  const api = loadSandboxedPreload(renderer).api;

  await api.connect();
  await api.status();
  await api.querySnapshot({
    schemaVersion: "cp02.snapshot.fixture/v1",
    objectRef: "run:one",
  });
  await api.query({ schema: "cp03.query.fixture/v1", family: "semantic" });
  await api.requestDryRun({
    schemaVersion: "cp02.dry-run.fixture/v1",
    requestId: "dry-1",
    action: "preflight",
  });
  await api.requestCommand({
    schemaVersion: "cp02.command.fixture/v1",
    requestId: "command-1",
    action: "owner-action",
  });
  await api.fetchReceipt("receipt:abc-123");

  const events = [];
  const unsubscribe = api.subscribeEvents((value) => events.push(value));
  await new Promise((resolve) => setImmediate(resolve));
  renderer.listeners.get(CHANNELS.event)?.({}, { cursor: "event:1" });
  await unsubscribe();

  assert.deepEqual(events, [{ cursor: "event:1" }]);
  assert.equal(renderer.listeners.has(CHANNELS.event), false);
  assert.deepEqual(renderer.invoked.map(([channel]) => channel), [
    CHANNELS.connect,
    CHANNELS.status,
    CHANNELS.snapshot,
    CHANNELS.query,
    CHANNELS.dryRun,
    CHANNELS.command,
    CHANNELS.receipt,
    CHANNELS.eventsSubscribe,
    CHANNELS.eventsUnsubscribe,
  ]);
});
