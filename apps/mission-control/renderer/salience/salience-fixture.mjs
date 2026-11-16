import {
  CURRENT_SALIENCE_EVENTS,
  FOUNDATION_POLICY,
  HISTORICAL_SALIENCE_EVENTS,
  SALIENCE_AXES,
} from "./salience-events-fixture.mjs";

export { SALIENCE_AXES };

export const SALIENCE_SNAPSHOTS = Object.freeze([
  Object.freeze({
    id: "current",
    label: "Current fixture · generation 44239",
    mode: "CURRENT",
    generation: 44239,
    asOf: 44239130,
    policy: FOUNDATION_POLICY,
    events: CURRENT_SALIENCE_EVENTS,
    aggregationState: "PRESENT",
    routingState: "PRESENT",
  }),
  Object.freeze({
    id: "historical",
    label: "Historical fixture · generation 44237",
    mode: "HISTORICAL",
    generation: 44237,
    asOf: 44237050,
    policy: FOUNDATION_POLICY,
    events: HISTORICAL_SALIENCE_EVENTS,
    aggregationState: "UNAVAILABLE",
    routingState: "UNAVAILABLE",
  }),
]);

const cluster = (id, windowId, eventIds, lineageIds) => Object.freeze({
  id,
  windowId,
  capabilityId: "C.REPEAT",
  partition: "capability-epoch + scope + semantic-release + source-binding + source-family + rights/correction frontier",
  structureRef: "structure:fixture:boolean-defect",
  defectRef: "defect:fixture:boolean-defect",
  eventIds: Object.freeze(eventIds),
  lineageIds: Object.freeze(lineageIds),
  ruleId: "COMPLETED_WINDOW_UNION_UNIQUE_LINEAGES/v1",
});

export const SALIENCE_AGGREGATION = Object.freeze({
  schema: "bilqis.c06.salience-aggregation/v1",
  policyDigest: "2222222222222222222222222222222222222222222222222222222222222222",
  windows: Object.freeze([
    Object.freeze({
      id: "window:fixture:20:boolean",
      size: 20,
      acceptedAppendCount: 20,
      observedBounds: Object.freeze([44238900, 44239045]),
      lateObservations: 1,
    }),
    Object.freeze({
      id: "window:fixture:40:boolean",
      size: 20,
      acceptedAppendCount: 20,
      observedBounds: Object.freeze([44239050, 44239120]),
      lateObservations: 0,
    }),
  ]),
  clusters: Object.freeze([
    cluster(
      "cluster:fixture:boolean-defect:w20",
      "window:fixture:20:boolean",
      Object.freeze([
        "salience-record:fixture:negative",
        "salience-record:fixture:repeat-w20",
      ]),
      Object.freeze(["lineage:fixture:d", "lineage:fixture:e"]),
    ),
    cluster(
      "cluster:fixture:boolean-defect:w40",
      "window:fixture:40:boolean",
      Object.freeze([
        "salience-record:fixture:repeat-w40-a",
        "salience-record:fixture:repeat-w40-b",
      ]),
      Object.freeze(["lineage:fixture:f", "lineage:fixture:g"]),
    ),
  ]),
  pattern: Object.freeze({
    id: "pattern:fixture:boolean-defect",
    ruleId: "COMPLETED_WINDOW_UNION_UNIQUE_LINEAGES/v1",
    clusterIds: Object.freeze([
      "cluster:fixture:boolean-defect:w20",
      "cluster:fixture:boolean-defect:w40",
    ]),
    eventIds: Object.freeze([
      "salience-record:fixture:negative",
      "salience-record:fixture:repeat-w20",
      "salience-record:fixture:repeat-w40-a",
      "salience-record:fixture:repeat-w40-b",
    ]),
    independentLineages: 4,
    status: "CONJECTURE",
    sourceGold: false,
    qualifiedForTeaching: false,
    nomination: "PROCEDURE_REPAIR_INVESTIGATION",
  }),
  trend: Object.freeze({
    id: "trend:fixture:boolean-defect",
    patternId: "pattern:fixture:boolean-defect",
    ruleId: "COMPLETED_WINDOW_UNION_UNIQUE_LINEAGES/v1",
    supported: true,
    points: Object.freeze([
      Object.freeze({ windowId: "window:fixture:20:boolean", newLineages: 2, cumulativeLineages: 2 }),
      Object.freeze({ windowId: "window:fixture:40:boolean", newLineages: 2, cumulativeLineages: 4 }),
    ]),
  }),
});

export const ROUTING_FIXTURES = Object.freeze([
  Object.freeze({
    id: "routing:fixture:urgent-relevant",
    optionId: "attention-option:fixture:B.IFF",
    citedObservationIds: Object.freeze(["salience-record:fixture:urgent"]),
    tier: "URGENT_RELEVANT",
    rule: "relevant && exigency >= HIGH",
    ordering: Object.freeze(["dispatch-tier", "eligible-since", "stable-id"]),
    policyVisibility: "ADMITTED_EVIDENCE_ONLY",
    hiddenWeighting: "NOT_EXPOSED_OR_INFERRED",
  }),
]);

export const SALIENCE_PROJECTION = Object.freeze({
  schema: "bilqis.bamf.mission-control.salience-event/v1",
  fields: Object.freeze([
    "meta", "salience_id", "capability_id", "impact", "exigency", "novelty", "action_kind",
  ]),
  richRecursiveProjection: false,
  policyVersionProjected: false,
  aggregationProjected: false,
  routingRationaleProjected: false,
});
