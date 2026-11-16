import test from "node:test";
import assert from "node:assert/strict";

import { createBootstrapController } from "../renderer/foundation/bootstrap-controller.mjs";

function storageFixture() {
  return {
    getItem() { return null; },
    setItem() {},
    removeItem() {},
  };
}

test("disconnected bootstrap schedules automatic reconnect without operator clicks", async () => {
  let connectCalls = 0;
  const scheduled = [];
  const api = {
    async connect() {
      connectCalls += 1;
      return {
        state: "disconnected",
        serviceLive: false,
        serviceReady: false,
        learnerReady: false,
      };
    },
    async querySnapshot() {
      throw new Error("CONTROL_PLANE_NOT_CONNECTED");
    },
  };
  const controller = createBootstrapController({
    api,
    storage: storageFixture(),
    getState: () => null,
    setState() {},
    setDefense() {},
    setBootstrap() {},
    setVerifiedLiveContext() {},
    resetFrameShell() {},
    render() {},
    announce() {},
    currentHash: () => "",
    scheduleReconnect: (callback, _delay) => {
      scheduled.push(callback);
      return scheduled.length;
    },
    cancelReconnect() {},
    reconnectDelayMs: 25,
  });

  await controller.establishSnapshot();
  assert.equal(connectCalls, 1);
  assert.equal(scheduled.length, 1);

  await scheduled.shift()();
  assert.equal(connectCalls, 2);
});
