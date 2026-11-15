"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const { CHANNELS, HANDLER_CHANNELS } = require("../channels.cjs");
const { ControlPlaneBridge } = require("../control-plane-bridge.cjs");
const { registerMissionControlIpc } = require("../main-ipc.cjs");
const { RENDERER_ENTRY_URL, RENDERER_ORIGIN } = require("../shell/renderer-location.cjs");
const { FIXTURE_VALIDATORS } = require("./_contract-fixture.cjs");

function ipcMainFixture() {
  const handlers = new Map();
  return {
    handlers,
    handle(channel, handler) {
      if (handlers.has(channel)) {
        throw new Error(`duplicate:${channel}`);
      }
      handlers.set(channel, handler);
    },
    removeHandler(channel) {
      handlers.delete(channel);
    },
  };
}

function senderFixture(url = RENDERER_ENTRY_URL) {
  const sent = [];
  const onceHandlers = new Map();
  const frame = { url, origin: RENDERER_ORIGIN };
  frame.top = frame;
  const sender = {
    id: 17,
    mainFrame: frame,
    send(channel, payload) { sent.push([channel, payload]); },
    isDestroyed() { return false; },
    once(name, handler) { onceHandlers.set(name, handler); },
  };
  return {
    event: {
      senderFrame: frame,
      sender,
    },
    sender,
    sent,
    onceHandlers,
  };
}

function adapterFixture() {
  let listener;
  return {
    async connect() {
      return {
        session: { token: "main-only" },
        publicStatus: {
          schemaVersion: "cp01.public-status.fixture/v1",
          state: "HEALTHY",
          protocolVersion: "cp01/v1",
        },
      };
    },
    async status() {
      return { schemaVersion: "cp01.status.fixture/v1", state: "HEALTHY" };
    },
    async snapshot(_session, request) {
      return {
        schemaVersion: "cp02.snapshot.result.fixture/v1",
        objectRef: request.objectRef,
      };
    },
    async dryRun(_session, request) {
      return {
        schemaVersion: "cp02.dry-run.result.fixture/v1",
        state: "READY",
        requestId: request.requestId,
      };
    },
    async command(_session, request) {
      return {
        schemaVersion: "cp02.command.result.fixture/v1",
        state: "ACCEPTED",
        requestId: request.requestId,
      };
    },
    async receipt(_session, ref) {
      return { schemaVersion: "cp02.receipt.fixture/v1", ref };
    },
    async subscribe(_session, next) {
      listener = next;
      return () => { listener = null; };
    },
    emit(payload) { listener?.(payload); },
  };
}

test("main registers only the enumerated request channels", () => {
  const ipcMain = ipcMainFixture();
  const bridge = new ControlPlaneBridge(adapterFixture(), FIXTURE_VALIDATORS);
  const sender = senderFixture();
  const dispose = registerMissionControlIpc({
    ipcMain,
    bridge,
    trustedWebContents: sender.sender,
  });

  assert.deepEqual([...ipcMain.handlers.keys()], [...HANDLER_CHANNELS]);
  assert.equal(ipcMain.handlers.has("shell:exec"), false);
  assert.equal(ipcMain.handlers.has("fs:read"), false);
  assert.equal(ipcMain.handlers.has("ipc:invoke"), false);

  dispose();
  assert.equal(ipcMain.handlers.size, 0);
});

test("untrusted renderer origins cannot invoke even valid channels", async () => {
  const ipcMain = ipcMainFixture();
  const bridge = new ControlPlaneBridge(adapterFixture(), FIXTURE_VALIDATORS);
  const trusted = senderFixture();
  registerMissionControlIpc({ ipcMain, bridge, trustedWebContents: trusted.sender });
  const { event } = senderFixture("https://evil.example/index.html");

  await assert.rejects(
    ipcMain.handlers.get(CHANNELS.connect)(event),
    /BAMF_GUI20_UNTRUSTED_IPC_SENDER/,
  );
});

test("same WebContents cannot invoke from a child or wrong-origin frame", async () => {
  const ipcMain = ipcMainFixture();
  const bridge = new ControlPlaneBridge(adapterFixture(), FIXTURE_VALIDATORS);
  const trusted = senderFixture();
  registerMissionControlIpc({ ipcMain, bridge, trustedWebContents: trusted.sender });

  const child = {
    url: RENDERER_ENTRY_URL,
    origin: RENDERER_ORIGIN,
    top: trusted.sender.mainFrame,
  };
  await assert.rejects(
    ipcMain.handlers.get(CHANNELS.connect)({ sender: trusted.sender, senderFrame: child }),
    /BAMF_GUI20_UNTRUSTED_IPC_SENDER/,
  );

  trusted.sender.mainFrame.origin = "https://evil.example";
  await assert.rejects(
    ipcMain.handlers.get(CHANNELS.connect)(trusted.event),
    /BAMF_GUI20_UNTRUSTED_IPC_SENDER/,
  );
});

test("trusted renderer uses typed handlers and cannot inject credential material", async () => {
  const ipcMain = ipcMainFixture();
  const adapter = adapterFixture();
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS);
  const sender = senderFixture();
  registerMissionControlIpc({ ipcMain, bridge, trustedWebContents: sender.sender });
  const { event } = sender;

  await ipcMain.handlers.get(CHANNELS.connect)(event);
  assert.deepEqual(await ipcMain.handlers.get(CHANNELS.status)(event), {
    schemaVersion: "cp01.status.fixture/v1",
    state: "HEALTHY",
  });
  await assert.rejects(
    ipcMain.handlers.get(CHANNELS.snapshot)(event, { sessionCapability: "forged" }),
    /BAMF_GUI20_CONTROL_PLANE_REQUEST_FAILED/,
  );
  await assert.rejects(
    ipcMain.handlers.get(CHANNELS.command)(event, "open -a Terminal"),
    /BAMF_GUI20_CONTROL_PLANE_REQUEST_FAILED/,
  );
});

test("event subscription only forwards renderer-safe control-plane events", async () => {
  const ipcMain = ipcMainFixture();
  const adapter = adapterFixture();
  const violations = [];
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS, {
    onSecurityViolation: (code) => violations.push(code),
  });
  const sender = senderFixture();
  registerMissionControlIpc({ ipcMain, bridge, trustedWebContents: sender.sender });

  await ipcMain.handlers.get(CHANNELS.connect)(sender.event);
  await ipcMain.handlers.get(CHANNELS.eventsSubscribe)(sender.event);
  adapter.emit({
    schemaVersion: "cp02.event.fixture/v1",
    cursor: "event:1",
    state: "RUNNING",
  });
  assert.deepEqual(sender.sent, [[CHANNELS.event, {
    schemaVersion: "cp02.event.fixture/v1",
    cursor: "event:1",
    state: "RUNNING",
  }]]);

  assert.doesNotThrow(() => adapter.emit({
    schemaVersion: "cp02.event.fixture/v1",
    cursor: "event:2",
    sessionToken: "leak",
  }));
  assert.deepEqual(violations, ["BAMF_GUI20_RENDERER_PAYLOAD_UNSAFE"]);
  await ipcMain.handlers.get(CHANNELS.eventsUnsubscribe)(sender.event);
  adapter.emit({ schemaVersion: "cp02.event.fixture/v1", cursor: "event:3" });
  assert.equal(sender.sent.length, 1);
});

test("adapter exception messages are not exposed to the renderer", async () => {
  const ipcMain = ipcMainFixture();
  const adapter = adapterFixture();
  adapter.status = async () => {
    const error = new Error("token=super-secret /Users/operator/private-run");
    error.code = "BAMF_GUI20_FAKE_ADAPTER_ERROR";
    throw error;
  };
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS);
  const sender = senderFixture();
  registerMissionControlIpc({ ipcMain, bridge, trustedWebContents: sender.sender });
  await ipcMain.handlers.get(CHANNELS.connect)(sender.event);

  await assert.rejects(
    ipcMain.handlers.get(CHANNELS.status)(sender.event),
    (error) => {
      assert.equal(error.code, "BAMF_GUI20_CONTROL_PLANE_REQUEST_FAILED");
      assert.equal(error.message, "BAMF_GUI20_CONTROL_PLANE_REQUEST_FAILED");
      return true;
    },
  );
});

test("main logs only operation and sanitized cause code for rejected IPC requests", async () => {
  const ipcMain = ipcMainFixture();
  const adapter = adapterFixture();
  adapter.status = async () => {
    const error = new Error("token=super-secret /Users/operator/private-run");
    error.code = "BAMF_GUI20_CP01_UNAVAILABLE";
    throw error;
  };
  const bridge = new ControlPlaneBridge(adapter, FIXTURE_VALIDATORS);
  const sender = senderFixture();
  const diagnostics = [];
  registerMissionControlIpc({
    ipcMain,
    bridge,
    trustedWebContents: sender.sender,
    onRequestFailure: (diagnostic) => diagnostics.push(diagnostic),
  });
  await ipcMain.handlers.get(CHANNELS.connect)(sender.event);

  await assert.rejects(ipcMain.handlers.get(CHANNELS.status)(sender.event));
  assert.deepEqual(diagnostics, [{
    operation: "status",
    causeCode: "BAMF_GUI20_CP01_UNAVAILABLE",
  }]);
  const serialized = JSON.stringify(diagnostics);
  assert.equal(serialized.includes("super-secret"), false);
  assert.equal(serialized.includes("/Users/operator/private-run"), false);
});
