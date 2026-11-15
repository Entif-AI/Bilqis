"use strict";

const { CHANNELS, HANDLER_CHANNELS } = require("./channels.cjs");
const { createTrustedSender, requireTrustedSender } = require("./shell/sender-trust.cjs");

function safeBoundaryError(_error) {
  const safe = new Error("BAMF_GUI20_CONTROL_PLANE_REQUEST_FAILED");
  safe.code = "BAMF_GUI20_CONTROL_PLANE_REQUEST_FAILED";
  return safe;
}

function registerMissionControlIpc({ ipcMain, bridge, trustedWebContents }) {
  if (!ipcMain || typeof ipcMain.handle !== "function" ||
      typeof ipcMain.removeHandler !== "function") {
    throw new TypeError("BAMF_GUI20_IPC_MAIN_REQUIRED");
  }
  if (!bridge) {
    throw new TypeError("BAMF_GUI20_CONTROL_PLANE_BRIDGE_REQUIRED");
  }
  const isTrustedSender = createTrustedSender(trustedWebContents);
  const subscriptions = new Map();

  function senderId(event) {
    if (!Number.isInteger(event?.sender?.id)) {
      throw new TypeError("BAMF_GUI20_IPC_SENDER_ID_REQUIRED");
    }
    return event.sender.id;
  }

  function clearSubscription(id) {
    const unsubscribe = subscriptions.get(id);
    if (unsubscribe) {
      subscriptions.delete(id);
      unsubscribe();
    }
  }

  function trusted(handler) {
    return async (event, ...args) => {
      requireTrustedSender(isTrustedSender, event);
      try {
        return await handler(event, ...args);
      } catch (error) {
        throw safeBoundaryError(error);
      }
    };
  }

  ipcMain.handle(CHANNELS.connect, trusted(async (event) => {
    clearSubscription(senderId(event));
    return bridge.connect();
  }));
  ipcMain.handle(CHANNELS.status, trusted(() => bridge.status()));
  ipcMain.handle(CHANNELS.snapshot, trusted((_event, request) => bridge.snapshot(request)));
  ipcMain.handle(CHANNELS.query, trusted((_event, request) => bridge.query(request)));
  ipcMain.handle(CHANNELS.dryRun, trusted((_event, request) => bridge.dryRun(request)));
  ipcMain.handle(CHANNELS.command, trusted((_event, request) => bridge.command(request)));
  ipcMain.handle(CHANNELS.receipt, trusted((_event, ref) => bridge.receipt(ref)));
  ipcMain.handle(CHANNELS.eventsSubscribe, trusted(async (event) => {
    const id = senderId(event);
    clearSubscription(id);
    const unsubscribe = await bridge.subscribe((payload) => {
      if (!event.sender.isDestroyed?.()) {
        event.sender.send(CHANNELS.event, payload);
      }
    });
    subscriptions.set(id, unsubscribe);
    event.sender.once?.("destroyed", () => clearSubscription(id));
    return Object.freeze({ subscribed: true });
  }));
  ipcMain.handle(CHANNELS.eventsUnsubscribe, trusted((event) => {
    clearSubscription(senderId(event));
    return Object.freeze({ subscribed: false });
  }));

  return () => {
    for (const id of [...subscriptions.keys()]) {
      clearSubscription(id);
    }
    for (const channel of HANDLER_CHANNELS) {
      ipcMain.removeHandler(channel);
    }
  };
}

module.exports = { registerMissionControlIpc, safeBoundaryError };
