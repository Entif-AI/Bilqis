"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const { ControlPlaneBridge } = require("../control-plane-bridge.cjs");
const { FIXTURE_VALIDATORS } = require("./_contract-fixture.cjs");

function adapterFixture() {
  const calls = [];
  let listener;
  let sessionNumber = 0;
  return {
    calls,
    get listener() {
      return listener;
    },
    async connect() {
      sessionNumber += 1;
      const session = { token: `secret-${sessionNumber}`, id: sessionNumber };
      calls.push(["connect", session]);
      return {
        session,
        publicStatus: {
          schemaVersion: "cp01.public-status.fixture/v1",
          state: "HEALTHY",
          protocolVersion: "cp01/v1",
          runId: "run-1",
        },
      };
    },
    async disconnect(session) {
      calls.push(["disconnect", session]);
    },
    async status(session) {
      calls.push(["status", session]);
      return {
        schemaVersion: "cp01.status.fixture/v1",
        state: "HEALTHY",
        runId: "run-1",
      };
    },
    async snapshot(session, request) {
      calls.push(["snapshot", session, request]);
      return {
        schemaVersion: "cp02.snapshot.result.fixture/v1",
        objectRef: request.objectRef,
      };
    },
    async dryRun(session, request) {
      calls.push(["dryRun", session, request]);
      return {
        schemaVersion: "cp02.dry-run.result.fixture/v1",
        state: "READY",
        requestId: request.requestId,
      };
    },
    async command(session, request) {
      calls.push(["command", session, request]);
      return {
        schemaVersion: "cp02.command.result.fixture/v1",
        state: "ACCEPTED",
        requestId: request.requestId,
      };
    },
    async receipt(session, ref) {
      calls.push(["receipt", session, ref]);
      return { schemaVersion: "cp02.receipt.fixture/v1", ref, verified: true };
    },
    async subscribe(session, next) {
      calls.push(["subscribe", session]);
      listener = next;
      return () => {
        calls.push(["unsubscribe", session]);
        listener = null;
      };
    },
  };
}

test("connection session and credential material remain main-process only", async () => {
  const adapter = adapterFixture();
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS);

  const publicStatus = await bridge.connect();

  assert.deepEqual(publicStatus, {
    schemaVersion: "cp01.public-status.fixture/v1",
    state: "HEALTHY",
    protocolVersion: "cp01/v1",
    runId: "run-1",
    connectionEpoch: 1,
  });
  assert.equal(JSON.stringify(publicStatus).includes("secret-1"), false);
  await bridge.status();
  assert.equal(adapter.calls.at(-1)[1].token, "secret-1");
});

test("unsafe service output is rejected before it reaches the renderer", async () => {
  const adapter = adapterFixture();
  adapter.status = async () => ({ state: "HEALTHY", sessionToken: "leak" });
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS);
  await bridge.connect();

  await assert.rejects(
    bridge.status(),
    /BAMF_GUI20_RENDERER_PAYLOAD_UNSAFE:FORBIDDEN_KEY:sessionToken/,
  );
});

test("unsafe handshake payload is rejected and its fresh session is disconnected", async () => {
  const adapter = adapterFixture();
  adapter.connect = async () => ({
    session: { token: "secret" },
    publicStatus: { state: "HEALTHY", credential: "leak" },
  });
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS);

  await assert.rejects(
    bridge.connect(),
    /BAMF_GUI20_RENDERER_PAYLOAD_UNSAFE:FORBIDDEN_KEY:credential/,
  );
  assert.equal(adapter.calls.some(([name]) => name === "disconnect"), true);
  await assert.rejects(bridge.status(), /BAMF_GUI20_CONTROL_PLANE_NOT_CONNECTED/);
});

test("reconnect invalidates old subscriptions and obsolete session state", async () => {
  const adapter = adapterFixture();
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS);
  const observed = [];

  await bridge.connect();
  await bridge.subscribe((event) => observed.push(event));
  const staleListener = adapter.listener;
  staleListener({ schemaVersion: "cp02.event.fixture/v1", cursor: "event:1" });

  const second = await bridge.connect();
  staleListener({ schemaVersion: "cp02.event.fixture/v1", cursor: "event:stale" });

  assert.equal(second.connectionEpoch, 2);
  assert.deepEqual(observed, [{
    schemaVersion: "cp02.event.fixture/v1",
    cursor: "event:1",
  }]);
  assert.equal(adapter.calls.filter(([name]) => name === "unsubscribe").length, 1);
  assert.equal(adapter.calls.filter(([name]) => name === "disconnect").length, 1);
});

test("bridge forwards opaque CP02-shaped data while enforcing transport safety", async () => {
  const adapter = adapterFixture();
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS);
  await bridge.connect();

  assert.deepEqual(
    await bridge.snapshot({
      schemaVersion: "cp02.snapshot.fixture/v1",
      objectRef: "capability:A.ADD",
    }),
    {
      schemaVersion: "cp02.snapshot.result.fixture/v1",
      objectRef: "capability:A.ADD",
    },
  );
  assert.deepEqual(
    await bridge.dryRun({
      schemaVersion: "cp02.dry-run.fixture/v1",
      requestId: "r1",
      action: "preflight",
    }),
    {
      schemaVersion: "cp02.dry-run.result.fixture/v1",
      state: "READY",
      requestId: "r1",
    },
  );
  assert.deepEqual(
    await bridge.command({
      schemaVersion: "cp02.command.fixture/v1",
      requestId: "r2",
      action: "owner-action",
    }),
    {
      schemaVersion: "cp02.command.result.fixture/v1",
      state: "ACCEPTED",
      requestId: "r2",
    },
  );
  assert.deepEqual(await bridge.receipt("receipt:abc"), {
    schemaVersion: "cp02.receipt.fixture/v1",
    ref: "receipt:abc",
    verified: true,
  });

  await assert.rejects(
    bridge.command(["not", "a", "typed", "record"]),
    /BAMF_GUI20_IPC_ARGUMENT_INVALID:REQUEST_OBJECT_REQUIRED/,
  );
  await assert.rejects(
    bridge.snapshot({ sessionToken: "renderer-must-not-supply-this" }),
    /BAMF_GUI20_IPC_ARGUMENT_INVALID:FORBIDDEN_KEY:sessionToken/,
  );
  await assert.rejects(
    bridge.receipt(null),
    /BAMF_GUI20_IPC_ARGUMENT_INVALID:STABLE_REF_REQUIRED/,
  );
});

test("CP02 validators reject semantically invalid records before adapter invocation", async () => {
  const adapter = adapterFixture();
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS);
  await bridge.connect();
  const before = adapter.calls.length;

  await assert.rejects(
    bridge.command({ requestId: "missing-schema" }),
    /FIXTURE_CP02_RECORD_INVALID/,
  );
  await assert.rejects(
    bridge.receipt("not-a-receipt-ref"),
    /FIXTURE_CP02_RECEIPT_REF_INVALID/,
  );
  assert.equal(adapter.calls.length, before);
});

test("response validators reject structurally safe but contract-invalid service data", async () => {
  const adapter = adapterFixture();
  adapter.status = async () => ({ schemaVersion: "wrong/v1", state: "HEALTHY" });
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS);
  await bridge.connect();

  await assert.rejects(bridge.status(), /FIXTURE_CP02_RECORD_INVALID/);
});

test("unsafe service event is dropped without throwing through the main event loop", async () => {
  const adapter = adapterFixture();
  const violations = [];
  const observed = [];
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS, {
    onSecurityViolation: (code) => violations.push(code),
  });
  await bridge.connect();
  await bridge.subscribe((value) => observed.push(value));

  assert.doesNotThrow(() => adapter.listener({
    schemaVersion: "cp02.event.fixture/v1",
    cursor: "event:1",
    sessionToken: "leak",
  }));
  assert.deepEqual(observed, []);
  assert.deepEqual(violations, ["BAMF_GUI20_RENDERER_PAYLOAD_UNSAFE"]);
});
