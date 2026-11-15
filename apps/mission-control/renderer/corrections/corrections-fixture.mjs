import { CORRECTION_MESSAGES } from "./corrections-messages.mjs";

const D = (char) => char.repeat(64);

export const CORRECTION_FIXTURE_MESSAGES = Object.freeze({ "en-US": Object.freeze({
  "corrections.fixture.title": "REFERENCE FIXTURES · correction contract example",
  "corrections.fixture.description": "Checked-in correction data for inspection and interaction verification under the explicit fixture launch.",
  "corrections.posture.live": "REFERENCE FIXTURES · reference correction projection",
  "corrections.posture.historical": "REFERENCE FIXTURES · reference historical projection · generation {generation}",
}) });

export const CORRECTION_FIXTURE_CONTRACT = Object.freeze({
  schema: "bilqis.bamf.gui13.correction-impact-fixture/v1",
  source: "C09 correction/requalification contracts + CP03 CorrectionEvent",
  projection: "FIXTURE_RETAINED_CONTRACT_SHAPE",
});

const nodes = Object.freeze([
  { id: "source:numeric-registry:r9", kind: "source", label: "Numeric registry revision r9", state: "RECOMPUTED", evidenceRefs: ["receipt:source-r9"] },
  { id: "sem:number.successor", kind: "semantic", label: "SUCCESSOR semantic identity", state: "RECOMPUTED", evidenceRefs: ["receipt:semantic-r9"] },
  { id: "frame:number.successor", kind: "frame", label: "SUCCESSOR compiled frame", state: "RECOMPUTED", evidenceRefs: ["receipt:frame-r9"] },
  { id: "generation:44238", kind: "generation", label: "Generation 44238", state: "REQUALIFICATION_REQUIRED", evidenceRefs: ["receipt:g44238-exposure"] },
  { id: "motif:" + D("c"), kind: "memory", label: "Retained SUCCESSOR motif", state: "REQUALIFIED", evidenceRefs: ["requalification:fixture:numeric-source-r9"] },
  { id: "cache:successor:r8", kind: "projection", label: "Derived SUCCESSOR cache", state: "INVALIDATED", evidenceRefs: ["receipt:cache-invalidation-r8"] },
  { id: "capability:C.SUCCESSOR", kind: "capability", label: "C.SUCCESSOR", state: "REQUALIFIED", evidenceRefs: ["receipt:capability-successor-r9"] },
  { id: "neural-influence:untracked:44238", kind: "unknown", label: "Untracked learned influence", state: "UNAVAILABLE_UNKNOWN", evidenceRefs: [] },
]);

const edges = Object.freeze([
  ["source:numeric-registry:r9", "sem:number.successor", "INTERPRETS"],
  ["sem:number.successor", "frame:number.successor", "COMPILES"],
  ["frame:number.successor", "generation:44238", "TRAINING_EXPOSURE"],
  ["generation:44238", "motif:" + D("c"), "MEMORY_SUPPORT"],
  ["generation:44238", "cache:successor:r8", "DERIVED_PROJECTION"],
  ["generation:44238", "capability:C.SUCCESSOR", "EVALUATED_CAPABILITY"],
  ["generation:44238", "neural-influence:untracked:44238", "POTENTIAL_UNTRACKED_INFLUENCE"],
].map(([from, to, relation]) => Object.freeze({ from, to, relation })));

export const CORRECTION_FIXTURE = Object.freeze({
  posture: "live",
  generation: null,
  pageState: "PRESENT",
  correction: Object.freeze({
    id: "correction:fixture:numeric-source-r8-r9",
    correctionGeneration: 12,
    sourceRef: "source:numeric-registry",
    priorRevision: "source:numeric-registry:r8",
    currentRevision: "source:numeric-registry:r9",
    oldDigest: D("8"),
    newDigest: D("9"),
    sourceReceipt: "receipt:source-r9",
    recordedReceipt: "receipt:correction-numeric-r8-r9",
  }),
  nodes,
  edges,
  nonDescendants: Object.freeze([
    "capability:B.AND",
    "motif:" + D("a"),
    "frame:boolean.and",
  ]),
  queue: Object.freeze([
    Object.freeze({
      id: "requal-task:successor-44238",
      generation: 44_238,
      checkpoint: D("3"),
      sourceRevision: "source:numeric-registry:r9",
      implicatedRefs: Object.freeze(["capability:C.SUCCESSOR", "motif:" + D("c"), "cache:successor:r8"]),
      urgency: "HIGH",
      status: "REQUALIFIED",
      owner: "bamf.c09.requalification",
      evidenceRefs: Object.freeze(["receipt:g44238-exposure", "receipt:capability-successor-r9"]),
      receiptRefs: Object.freeze(["receipt:correction-numeric-r8-r9", "requalification:fixture:numeric-source-r9"]),
    }),
    Object.freeze({
      id: "requal-task:latent-44238",
      generation: 44_238,
      checkpoint: D("3"),
      sourceRevision: "source:numeric-registry:r9",
      implicatedRefs: Object.freeze(["neural-influence:untracked:44238"]),
      urgency: "UNKNOWN",
      status: "UNAVAILABLE_UNKNOWN",
      owner: "UNTRACKED",
      evidenceRefs: Object.freeze(["receipt:g44238-exposure"]),
      receiptRefs: Object.freeze([]),
    }),
  ]),
  history: Object.freeze([
    Object.freeze({
      id: "history:correction-recorded",
      phase: "CORRECTION_RECORDED",
      atGeneration: 44_238,
      receipt: "receipt:correction-numeric-r8-r9",
      states: Object.freeze({
        "generation:44238": "KNOWN_EXPOSURE",
        ["motif:" + D("c")]: "HELD",
        "cache:successor:r8": "RECOMPUTE_REQUIRED",
        "capability:C.SUCCESSOR": "REQUALIFICATION_REQUIRED",
      }),
    }),
    Object.freeze({
      id: "history:requalification-complete",
      phase: "REQUALIFICATION_COMPLETE",
      atGeneration: 44_239,
      receipt: "requalification:fixture:numeric-source-r9",
      states: Object.freeze({
        "generation:44238": "REQUALIFICATION_REQUIRED",
        ["motif:" + D("c")]: "REQUALIFIED",
        "cache:successor:r8": "INVALIDATED",
        "capability:C.SUCCESSOR": "REQUALIFIED",
      }),
    }),
  ]),
});

export const CORRECTION_FIXTURE_SUPPORT = Object.freeze({
  projection: CORRECTION_FIXTURE,
  messages: Object.freeze({ "en-US": Object.freeze({
    ...CORRECTION_MESSAGES["en-US"],
    ...CORRECTION_FIXTURE_MESSAGES["en-US"],
  }) }),
  notice: `<aside class="corrections-fixture-notice" data-test-id="corrections-fixture-notice" role="note"><strong>REFERENCE FIXTURES</strong><p>Reference correction data is isolated to this explicit fixture launch.</p></aside>`,
});
