export const SALIENCE_AXES = Object.freeze(["impact", "exigency", "novelty"]);

const axis = (ordinal, {
  state = "PRESENT",
  origin = "DERIVED",
  observationState = "OBSERVED",
  sourceRef,
  ruleId,
  basisRefs,
} = {}) => Object.freeze({
  state,
  ordinal,
  origin,
  observationState,
  sourceRef,
  ruleId,
  basisRefs: Object.freeze(basisRefs ?? []),
});

const event = (value) => Object.freeze({
  schema: "bilqis.bamf.mission-control.salience-event/v1",
  ...value,
  policy: Object.freeze(value.policy),
  axes: Object.freeze(value.axes),
  evidenceRefs: Object.freeze(value.evidenceRefs),
  receiptRefs: Object.freeze(value.receiptRefs),
});

export const FOUNDATION_POLICY = Object.freeze({
  policyId: "bamf-foundation",
  version: "v1",
  sourceOwner: "fixture:salience-owner",
  policyDigest: "1111111111111111111111111111111111111111111111111111111111111111",
  windowPolicyId: "bamf-foundation-window",
  windowPolicyVersion: "v1",
  windowSize: 20,
  aggregationRule: "COMPLETED_WINDOW_UNION_UNIQUE_LINEAGES/v1",
});

const fact = (capability, metric, suffix = "") => "salience-fact:" + capability + ":" + metric + suffix;

export const CURRENT_SALIENCE_EVENTS = Object.freeze([
  event({
    recordId: "salience-record:fixture:unlock",
    salienceId: "salience:fixture:unlock",
    capabilityId: "B.AND",
    associatedObjectRef: "attention-option:fixture:B.AND",
    actionKind: "TEACHING",
    observedAt: 44239010,
    effectiveAt: 44239010,
    scope: "capability:B.AND",
    sourceFamily: "factory:boolean-ast",
    policy: FOUNDATION_POLICY,
    lineageId: "lineage:fixture:a",
    structureRef: "structure:fixture:boolean-a",
    defectRef: null,
    defectPresent: false,
    axes: {
      impact: axis("HIGH", {
        origin: "SOURCE_AUTHORITATIVE",
        sourceRef: fact("B.AND", "impact.declared"),
        ruleId: "bamf/foundation/declared/v1",
        basisRefs: ["source:curriculum:B.AND", "receipt:impact:B.AND"],
      }),
      exigency: axis("LOW", {
        sourceRef: fact("B.AND", "exigency.blocked"),
        ruleId: "bamf/foundation/exigency.blocked/v1",
        basisRefs: ["source:frontier:B.AND", "receipt:blocking:B.AND"],
      }),
      novelty: axis("MODERATE", {
        sourceRef: fact("B.AND", "novelty.comparison"),
        ruleId: "bamf-foundation/v1:novelty:STRUCTURE_CHANGED",
        basisRefs: ["expectation:boolean-structure:v4", "receipt:observation:44239010"],
      }),
    },
    evidenceRefs: ["evidence:salience:unlock"],
    receiptRefs: ["receipt:salience:unlock"],
  }),
  event({
    recordId: "salience-record:fixture:urgent",
    salienceId: "salience:fixture:urgent",
    capabilityId: "B.IFF",
    associatedObjectRef: "attention-option:fixture:B.IFF",
    actionKind: "TEACHING",
    observedAt: 44239020,
    effectiveAt: 44239020,
    scope: "capability:B.IFF",
    sourceFamily: "factory:boolean-ast",
    policy: FOUNDATION_POLICY,
    lineageId: "lineage:fixture:b",
    structureRef: "structure:fixture:boolean-b",
    defectRef: null,
    defectPresent: false,
    axes: {
      impact: axis("MODERATE", {
        sourceRef: fact("B.IFF", "impact.declared"),
        ruleId: "bamf/foundation/declared/v1",
        basisRefs: ["source:curriculum:B.IFF"],
      }),
      exigency: axis("HIGH", {
        sourceRef: fact("B.IFF", "exigency.blocked"),
        ruleId: "bamf/foundation/exigency.blocked/v1",
        basisRefs: ["source:frontier:B.IFF", "receipt:blocking:B.IFF"],
      }),
      novelty: axis("UNKNOWN", {
        state: "UNKNOWN",
        origin: null,
        observationState: "NOT_REPORTED",
        sourceRef: fact("B.IFF", "novelty.unknown"),
        ruleId: "bilqis.c06.explicit-unknown/v1",
        basisRefs: ["source:novelty:B.IFF"],
      }),
    },
    evidenceRefs: ["evidence:salience:urgent"],
    receiptRefs: ["receipt:salience:urgent"],
  }),
  event({
    recordId: "salience-record:fixture:expected-missing",
    salienceId: "salience:fixture:expected-missing",
    capabilityId: "C.MISSING",
    associatedObjectRef: "expectation:semantic-event:window-17",
    actionKind: "EXPLORATION",
    observedAt: 44239030,
    effectiveAt: 44239030,
    scope: "capability:C.MISSING",
    sourceFamily: "factory:semantic",
    policy: FOUNDATION_POLICY,
    lineageId: "lineage:fixture:c",
    structureRef: "structure:fixture:semantic-missing",
    defectRef: null,
    defectPresent: false,
    axes: {
      impact: axis("LOW", {
        sourceRef: fact("C.MISSING", "impact.declared"),
        ruleId: "bamf/foundation/declared/v1",
        basisRefs: ["source:curriculum:C.MISSING"],
      }),
      exigency: axis("MODERATE", {
        sourceRef: fact("C.MISSING", "exigency.blocked"),
        ruleId: "bamf/foundation/exigency.blocked/v1",
        basisRefs: ["source:frontier:C.MISSING"],
      }),
      novelty: axis("CRITICAL", {
        observationState: "EXPECTED_MISSING",
        sourceRef: fact("C.MISSING", "novelty.comparison"),
        ruleId: "bamf-foundation/v1:novelty:EXPECTED_MISSING",
        basisRefs: ["expectation:semantic-event:window-17", "receipt:expectation-window:17"],
      }),
    },
    evidenceRefs: ["evidence:salience:expected-missing"],
    receiptRefs: ["receipt:salience:expected-missing"],
  }),
  ...[
    ["negative", "C.REPEAT", "lineage:fixture:d", 44239040, "REPORTED_NEGATIVE", "LOW"],
    ["repeat-w20", "C.REPEAT", "lineage:fixture:e", 44239045, "OBSERVED", "MODERATE"],
    ["repeat-w40-a", "C.REPEAT", "lineage:fixture:f", 44239110, "OBSERVED", "LOW"],
    ["repeat-w40-b", "C.REPEAT", "lineage:fixture:g", 44239120, "OBSERVED", "MODERATE"],
  ].map(([suffix, capabilityId, lineageId, observedAt, observationState, novelty]) => event({
    recordId: "salience-record:fixture:" + suffix,
    salienceId: "salience:fixture:" + suffix,
    capabilityId,
    associatedObjectRef: "episode:fixture:" + suffix,
    actionKind: "OBSERVATION",
    observedAt,
    effectiveAt: observedAt,
    scope: "capability:" + capabilityId,
    sourceFamily: "factory:boolean-ast",
    policy: FOUNDATION_POLICY,
    lineageId,
    structureRef: "structure:fixture:boolean-defect",
    defectRef: "defect:fixture:boolean-defect",
    defectPresent: true,
    axes: {
      impact: axis("LOW", {
        sourceRef: fact(capabilityId, "impact.declared"),
        ruleId: "bamf/foundation/declared/v1",
        basisRefs: ["source:curriculum:" + capabilityId],
      }),
      exigency: axis("LOW", {
        sourceRef: fact(capabilityId, "exigency.blocked"),
        ruleId: "bamf/foundation/exigency.blocked/v1",
        basisRefs: ["source:frontier:" + capabilityId],
      }),
      novelty: axis(novelty, {
        observationState,
        sourceRef: fact(capabilityId, "novelty.comparison"),
        ruleId: "bamf-foundation/v1:novelty:" +
          (observationState === "REPORTED_NEGATIVE" ? "REPORTED_NEGATIVE" :
            novelty === "MODERATE" ? "STRUCTURE_CHANGED" : "MATCHED"),
        basisRefs: ["expectation:boolean-defect:" + suffix, "receipt:observation:" + observedAt],
      }),
    },
    evidenceRefs: ["evidence:salience:" + suffix],
    receiptRefs: ["receipt:salience:" + suffix],
  })),
]);

export const HISTORICAL_SALIENCE_EVENTS = Object.freeze([
  event({
    recordId: "salience-record:fixture:unlock:g44237",
    salienceId: "salience:fixture:unlock:g44237",
    capabilityId: "B.AND",
    associatedObjectRef: "attention-option:fixture:B.AND:g44237",
    actionKind: "TEACHING",
    observedAt: 44237010,
    effectiveAt: 44237010,
    scope: "capability:B.AND",
    sourceFamily: "factory:boolean-ast",
    policy: FOUNDATION_POLICY,
    lineageId: "lineage:fixture:a",
    structureRef: "structure:fixture:boolean-a:g44237",
    defectRef: null,
    defectPresent: false,
    axes: {
      impact: axis("MODERATE", {
        sourceRef: fact("B.AND", "impact.declared", ":g44237"),
        ruleId: "bamf/foundation/declared/v1",
        basisRefs: ["source:curriculum:B.AND:g44237"],
      }),
      exigency: axis("LOW", {
        sourceRef: fact("B.AND", "exigency.blocked", ":g44237"),
        ruleId: "bamf/foundation/exigency.blocked/v1",
        basisRefs: ["source:frontier:B.AND:g44237"],
      }),
      novelty: axis("LOW", {
        sourceRef: fact("B.AND", "novelty.comparison", ":g44237"),
        ruleId: "bamf-foundation/v1:novelty:MATCHED",
        basisRefs: ["expectation:boolean-structure:v3"],
      }),
    },
    evidenceRefs: ["evidence:salience:unlock:g44237"],
    receiptRefs: ["receipt:salience:unlock:g44237"],
  }),
]);
