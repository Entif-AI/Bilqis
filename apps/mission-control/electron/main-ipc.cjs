"use strict";

const { CHANNELS, HANDLER_CHANNELS } = require("./channels.cjs");
const { createTrustedSender, requireTrustedSender } = require("./shell/sender-trust.cjs");

function safeBoundaryError(_error) {
  const safe = new Error("BAMF_GUI20_CONTROL_PLANE_REQUEST_FAILED");
  safe.code = "BAMF_GUI20_CONTROL_PLANE_REQUEST_FAILED";
  return safe;
}

function safeCauseCode(error) {
  const code = typeof error?.code === "string" ? error.code : "";
  return /^(?:BAMF|GUI)[A-Z0-9_:-]{1,127}$/.test(code)
    ? code
    : "BAMF_GUI20_UNCLASSIFIED_FAILURE";
}

function registerMissionControlIpc({
  ipcMain,
  bridge,
  trustedWebContents,
  onRequestFailure = ({ operation, causeCode }) => {
    console.error(`[Mission Control IPC] ${operation} failed (${causeCode})`);
  },
}) {
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

  function trusted(operation, handler) {
    return async (event, ...args) => {
      requireTrustedSender(isTrustedSender, event);
      try {
        return await handler(event, ...args);
      } catch (error) {
        try {
          onRequestFailure?.(Object.freeze({
            operation,
            causeCode: safeCauseCode(error),
          }));
        } catch (_diagnosticError) {
          // Diagnostics must never replace the fail-closed renderer boundary.
        }
        throw safeBoundaryError(error);
      }
    };
  }

  ipcMain.handle(CHANNELS.connect, trusted("connect", async (event) => {
    clearSubscription(senderId(event));
    return bridge.connect();
  }));
  ipcMain.handle(CHANNELS.status, trusted("status", () => bridge.status()));
  ipcMain.handle(CHANNELS.snapshot, trusted("snapshot", (_event, request) => bridge.snapshot(request)));
  ipcMain.handle(CHANNELS.query, trusted("query", (_event, request) => bridge.query(request)));
  ipcMain.handle(CHANNELS.dryRun, trusted("dry-run", (_event, request) => bridge.dryRun(request)));
  ipcMain.handle(CHANNELS.command, trusted("command", (_event, request) => bridge.command(request)));
  ipcMain.handle(CHANNELS.receipt, trusted("receipt", (_event, ref) => bridge.receipt(ref)));
  ipcMain.handle(CHANNELS.eventsSubscribe, trusted("events-subscribe", async (event) => {
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
  ipcMain.handle(CHANNELS.eventsUnsubscribe, trusted("events-unsubscribe", (event) => {
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
