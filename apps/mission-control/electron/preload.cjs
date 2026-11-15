"use strict";

const { contextBridge, ipcRenderer } = require("electron");

const LAUNCH_MODE_ARGUMENT = "--bamf-mc-mode=";

function launchMode() {
  const values = (globalThis.process?.argv ?? [])
    .filter((value) => typeof value === "string" && value.startsWith(LAUNCH_MODE_ARGUMENT))
    .map((value) => value.slice(LAUNCH_MODE_ARGUMENT.length));
  if (values.length === 0) return "production";
  if (values.length !== 1 || !["production", "fixtures"].includes(values[0])) {
    throw new TypeError("BAMF_MISSION_CONTROL_MODE_INVALID");
  }
  return values[0];
}

// Electron's sandboxed preload environment cannot load this repository's local
// CommonJS module graph. Keep this entrypoint self-contained; contract tests bind
// these literals back to the main-process channel registry to prevent drift.
const CHANNELS = Object.freeze({
  connect: "bamf:mission-control:connect",
  status: "bamf:mission-control:status",
  snapshot: "bamf:mission-control:snapshot",
  query: "bamf:mission-control:query",
  dryRun: "bamf:mission-control:dry-run",
  command: "bamf:mission-control:command",
  receipt: "bamf:mission-control:receipt",
  eventsSubscribe: "bamf:mission-control:events:subscribe",
  eventsUnsubscribe: "bamf:mission-control:events:unsubscribe",
  event: "bamf:mission-control:event",
});

const FORBIDDEN_KEYS = new Set([
  "accesstoken", "authorization", "authtoken", "bearertoken", "credential",
  "credentials", "privatekey", "secret", "sessioncapability", "sessiontoken",
]);

function invalid(reason) {
  throw new TypeError(`BAMF_GUI20_IPC_ARGUMENT_INVALID:${reason}`);
}

function normalizedKey(key) {
  return key.replace(/[-_]/g, "").toLowerCase();
}

function assertRequest(value, depth = 0, seen = new Set()) {
  if (depth > 12) invalid("MAX_DEPTH");
  if (value === null || typeof value === "boolean") return value;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) invalid("NON_FINITE_NUMBER");
    return value;
  }
  if (typeof value === "string") {
    if (value.length > 64 * 1024) invalid("STRING_TOO_LARGE");
    return value;
  }
  if (typeof value !== "object") invalid("NON_JSON_VALUE");
  if (seen.has(value)) invalid("CYCLIC_VALUE");
  seen.add(value);
  try {
    if (Array.isArray(value)) {
      if (value.length > 4096) invalid("ARRAY_TOO_LARGE");
      for (const item of value) assertRequest(item, depth + 1, seen);
      return value;
    }
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== null && Object.prototype.toString.call(value) !== "[object Object]") {
      invalid("NON_PLAIN_OBJECT");
    }
    const entries = Object.entries(value);
    if (entries.length > 256) invalid("OBJECT_TOO_LARGE");
    for (const [key, child] of entries) {
      if (FORBIDDEN_KEYS.has(normalizedKey(key))) invalid(`FORBIDDEN_KEY:${key}`);
      assertRequest(child, depth + 1, seen);
    }
    return value;
  } finally {
    seen.delete(value);
  }
}

function assertRequestObject(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    invalid("REQUEST_OBJECT_REQUIRED");
  }
  return assertRequest(value);
}

function assertStableRef(value) {
  if (typeof value !== "string" || value.length === 0 || value.length > 64 * 1024) {
    invalid("STABLE_REF_REQUIRED");
  }
  return value;
}

const api = Object.freeze({
  launchMode: launchMode(),
  connect: () => ipcRenderer.invoke(CHANNELS.connect),
  status: () => ipcRenderer.invoke(CHANNELS.status),
  querySnapshot: (request) => ipcRenderer.invoke(CHANNELS.snapshot, assertRequestObject(request)),
  query: (request) => ipcRenderer.invoke(CHANNELS.query, assertRequestObject(request)),
  requestDryRun: (request) => ipcRenderer.invoke(CHANNELS.dryRun, assertRequestObject(request)),
  requestCommand: (request) => ipcRenderer.invoke(CHANNELS.command, assertRequestObject(request)),
  fetchReceipt: (ref) => ipcRenderer.invoke(CHANNELS.receipt, assertStableRef(ref)),
  subscribeEvents: (listener) => {
    if (typeof listener !== "function") throw new TypeError("BAMF_GUI20_EVENT_LISTENER_REQUIRED");
    const wrapped = (_event, payload) => listener(payload);
    ipcRenderer.on(CHANNELS.event, wrapped);
    const started = ipcRenderer.invoke(CHANNELS.eventsSubscribe).catch((error) => {
      ipcRenderer.removeListener(CHANNELS.event, wrapped);
      throw error;
    });
    let active = true;
    return async () => {
      if (!active) return started;
      active = false;
      ipcRenderer.removeListener(CHANNELS.event, wrapped);
      await started;
      return ipcRenderer.invoke(CHANNELS.eventsUnsubscribe);
    };
  },
});

contextBridge.exposeInMainWorld("bamfMissionControl", api);
