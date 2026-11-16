import {
  ROUTING_FIXTURES,
  SALIENCE_AGGREGATION,
  SALIENCE_AXES,
  SALIENCE_PROJECTION,
  SALIENCE_SNAPSHOTS,
} from "./salience-fixture.mjs";

export function snapshotById(id) {
  return SALIENCE_SNAPSHOTS.find((snapshot) => snapshot.id === id) ?? SALIENCE_SNAPSHOTS[0];
}

export function salienceEventById(id, snapshotId = "current") {
  return snapshotById(snapshotId).events.find((event) =>
    event.recordId === id || event.salienceId === id,
  ) ?? null;
}

export function axisEvidence(event, axis) {
  if (!SALIENCE_AXES.includes(axis)) throw new TypeError("GUI12_SALIENCE_AXIS_INVALID");
  return event?.axes?.[axis] ?? null;
}

export function axisPosture(value) {
  if (!value) return "MISSING";
  if (value.state !== "PRESENT") return value.state;
  if (value.observationState === "EXPECTED_MISSING") return "EXPECTED_MISSING";
  if (value.observationState === "REPORTED_NEGATIVE") return "REPORTED_NEGATIVE";
  return value.ordinal;
}

export function aggregationPathForEvent(eventId) {
  const { clusters, pattern, trend, windows } = SALIENCE_AGGREGATION;
  const cluster = clusters.find((item) => item.eventIds.includes(eventId));
  if (!cluster) return null;
  const window = windows.find((item) => item.id === cluster.windowId) ?? null;
  return Object.freeze({ observation: eventId, cluster, pattern, trend, window });
}

export function constituentObservationIds(kind, id) {
  const { clusters, pattern, trend } = SALIENCE_AGGREGATION;
  if (kind === "cluster") return clusters.find((item) => item.id === id)?.eventIds ?? Object.freeze([]);
  if (kind === "pattern" && id === pattern.id) return pattern.eventIds;
  if (kind === "trend" && id === trend.id) return pattern.eventIds;
  return Object.freeze([]);
}

export function routingById(id) {
  return ROUTING_FIXTURES.find((route) => route.id === id) ?? null;
}

export function aggregationForSnapshot(snapshot) {
  return snapshot?.aggregationState === "PRESENT" ? SALIENCE_AGGREGATION : null;
}

export function routingForSnapshot(snapshot) {
  return snapshot?.routingState === "PRESENT" ? ROUTING_FIXTURES : Object.freeze([]);
}

export function projectionBoundary() {
  return SALIENCE_PROJECTION;
}

export function salienceDeepLink(recordId) {
  const params = new URLSearchParams({ kind: "salience-observation", id: recordId });
  return "#/view/salience?" + params.toString();
}
