"use strict";

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

const HANDLER_CHANNELS = Object.freeze([
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

module.exports = { CHANNELS, HANDLER_CHANNELS };
