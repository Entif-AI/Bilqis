const SEMANTIC_RELEASE = "7".repeat(64);
const PRIOR_ALLOCATION = "1".repeat(64);
const CURRENT_ALLOCATION = "2".repeat(64);
const PRIOR_MANIFEST = "3".repeat(64);
const CURRENT_MANIFEST = "4".repeat(64);

const KEY = Object.freeze({
  booleanAnd: "a".repeat(64),
  implication: "b".repeat(64),
  numericSuccessor: "c".repeat(64),
  quantifierScope: "d".repeat(64),
  retainedNew: "e".repeat(64),
  rejectedOnly: "f".repeat(64),
});

const PAGE_ROWS = 16_384;
const VECTOR_WIDTH = 128;
const PARAMETER_BYTES_PER_PAGE = PAGE_ROWS * VECTOR_WIDTH * 4;
const OPTIMIZER_BYTES_PER_PAGE = PARAMETER_BYTES_PER_PAGE * 2;
const STATE_BYTES_PER_PAGE = PARAMETER_BYTES_PER_PAGE + OPTIMIZER_BYTES_PER_PAGE;

function slot({
  keyDigest,
  slotId,
  keyKind = "EXACT",
  frameSchemaId,
  createdGeneration,
  allocationState = "ACTIVE",
  sourceEligibility = "ELIGIBLE",
  correctionState = "QUALIFIED",
  correctionRef = null,
  heldReason = null,
  eligibleReadCount,
  hitCount,
  gateUseCount,
  optimizerUpdateCount,
  capabilities,
  episodes,
  capabilityEvidence = "INDEPENDENT_EVIDENCE_UNAVAILABLE",
}) {
  const pageIndex = Math.floor(slotId / PAGE_ROWS);
  const rowIndex = slotId % PAGE_ROWS;
  return Object.freeze({
    schema: "bilqis.motif-key/v1",
    semanticRelease: SEMANTIC_RELEASE,
    keyDigest,
    keyKind,
    frameSchemaId,
    frameSchemaRevision: 1,
    scope: "PUBLIC_FORMAL",
    slotId,
    pageIndex,
    rowIndex,
    allocationState,
    sourceEligibility,
    sourceRefs: Object.freeze([
      `semantic-release:${SEMANTIC_RELEASE}`,
      `frame-schema:${frameSchemaId}:1`,
    ]),
    evidenceRefs: Object.freeze([
      `motif-key:${keyDigest}`,
      `allocation-slot:${slotId}`,
    ]),
    createdGeneration,
    lastUse: Object.freeze({
      generation: 44_239,
      optimizerStep: 8_112,
      receiptId: `motif-read:fixture:${keyDigest.slice(0, 8)}`,
    }),
    eligibleReadCount,
    hitCount,
    gateUseCount,
    optimizerParticipated: optimizerUpdateCount > 0,
    optimizerUpdateCount,
    parameterBank: `motif.page.${pageIndex}`,
    allocationExtent: `row ${rowIndex} of ${PAGE_ROWS} × ${VECTOR_WIDTH}`,
    correctionState,
    correctionRef,
    heldReason,
    capabilities: Object.freeze(capabilities),
    episodes: Object.freeze(episodes),
    capabilityEvidence,
  });
}

const PRIOR_SLOTS = Object.freeze([
  slot({
    keyDigest: KEY.booleanAnd,
    slotId: 0,
    frameSchemaId: "frame:boolean.and",
    createdGeneration: 44_237,
    eligibleReadCount: 160,
    hitCount: 148,
    gateUseCount: 98,
    optimizerUpdateCount: 27,
    capabilities: ["B.AND"],
    episodes: ["episode-record:fixture:retained-44239"],
  }),
  slot({
    keyDigest: KEY.implication,
    slotId: 1,
    frameSchemaId: "frame:boolean.implies",
    createdGeneration: 44_237,
    eligibleReadCount: 83,
    hitCount: 62,
    gateUseCount: 35,
    optimizerUpdateCount: 14,
    capabilities: ["B.IMPLIES"],
    episodes: ["episode-record:fixture:no-gain-reject"],
  }),
  slot({
    keyDigest: KEY.numericSuccessor,
    slotId: 2,
    frameSchemaId: "frame:number.successor",
    createdGeneration: 44_238,
    allocationState: "HELD",
    sourceEligibility: "HELD",
    correctionState: "REQUALIFICATION_REQUIRED",
    correctionRef: "correction:fixture:numeric-source-r8-r9",
    heldReason: "SOURCE_CORRECTION_PENDING",
    eligibleReadCount: 40,
    hitCount: 21,
    gateUseCount: 0,
    optimizerUpdateCount: 0,
    capabilities: ["C.SUCCESSOR"],
    episodes: ["episode-record:fixture:interference-reject"],
  }),
  slot({
    keyDigest: KEY.quantifierScope,
    slotId: 3,
    keyKind: "STRUCTURAL",
    frameSchemaId: "frame:scope.quantifier",
    createdGeneration: 44_238,
    eligibleReadCount: 19,
    hitCount: 8,
    gateUseCount: 5,
    optimizerUpdateCount: 3,
    capabilities: ["D.QUANTIFIER_SCOPE"],
    episodes: [],
  }),
]);

const CURRENT_SLOTS = Object.freeze([
  slot({
    keyDigest: KEY.booleanAnd,
    slotId: 0,
    frameSchemaId: "frame:boolean.and",
    createdGeneration: 44_237,
    eligibleReadCount: 200,
    hitCount: 190,
    gateUseCount: 132,
    optimizerUpdateCount: 34,
    capabilities: ["B.AND"],
    episodes: ["episode-record:fixture:retained-44239"],
  }),
  slot({
    keyDigest: KEY.implication,
    slotId: 1,
    frameSchemaId: "frame:boolean.implies",
    createdGeneration: 44_237,
    allocationState: "HELD",
    sourceEligibility: "HELD",
    correctionState: "REQUALIFICATION_REQUIRED",
    correctionRef: "correction:fixture:boolean-implication-r4-r5",
    heldReason: "SOURCE_CORRECTION_PENDING",
    eligibleReadCount: 91,
    hitCount: 66,
    gateUseCount: 35,
    optimizerUpdateCount: 14,
    capabilities: ["B.IMPLIES"],
    episodes: ["episode-record:fixture:no-gain-reject"],
  }),
  slot({
    keyDigest: KEY.numericSuccessor,
    slotId: 2,
    frameSchemaId: "frame:number.successor",
    createdGeneration: 44_238,
    correctionState: "QUALIFIED",
    correctionRef: "requalification:fixture:numeric-source-r9",
    eligibleReadCount: 61,
    hitCount: 34,
    gateUseCount: 11,
    optimizerUpdateCount: 7,
    capabilities: ["C.SUCCESSOR"],
    episodes: ["episode-record:fixture:retained-44239"],
  }),
  slot({
    keyDigest: KEY.quantifierScope,
    slotId: 3,
    keyKind: "STRUCTURAL",
    frameSchemaId: "frame:scope.quantifier",
    createdGeneration: 44_238,
    eligibleReadCount: 24,
    hitCount: 11,
    gateUseCount: 7,
    optimizerUpdateCount: 5,
    capabilities: ["D.QUANTIFIER_SCOPE"],
    episodes: [],
  }),
  slot({
    keyDigest: KEY.retainedNew,
    slotId: 4,
    frameSchemaId: "frame:boolean.iff",
    createdGeneration: 44_239,
    eligibleReadCount: 6,
    hitCount: 4,
    gateUseCount: 2,
    optimizerUpdateCount: 2,
    capabilities: ["B.IFF"],
    episodes: ["episode-record:fixture:retained-44239"],
  }),
]);

function generation({ generation, checkpointId, allocationDigest, manifestDigest, slots, reads, gates }) {
  return Object.freeze({
    schema: "bilqis.motif-allocation-snapshot/v1",
    generation,
    checkpointId,
    semanticRelease: SEMANTIC_RELEASE,
    allocationDigest,
    manifestDigest,
    pageRows: PAGE_ROWS,
    vectorWidth: VECTOR_WIDTH,
    pageCount: 1,
    capacitySlots: PAGE_ROWS,
    allocatedSlots: slots.length,
    memoryFootprint: Object.freeze({
      parameterBytes: PARAMETER_BYTES_PER_PAGE,
      optimizerBytes: OPTIMIZER_BYTES_PER_PAGE,
      stateBytes: STATE_BYTES_PER_PAGE,
      budgetBytes: STATE_BYTES_PER_PAGE * 2,
    }),
    readReceipts: Object.freeze(reads.map(Object.freeze)),
    gateReceipts: Object.freeze(gates.map(Object.freeze)),
    slots,
  });
}

export const MEMORY_GENERATIONS = Object.freeze([
  generation({
    generation: 44_238,
    checkpointId: "checkpoint:fixture:g44238",
    allocationDigest: PRIOR_ALLOCATION,
    manifestDigest: PRIOR_MANIFEST,
    slots: PRIOR_SLOTS,
    reads: [
      { schema: "bilqis.mlx.motif-read-report/v1", receiptId: "motif-read:fixture:g44238:s0", siteIndex: 0, exactCount: 6, structuralCount: 2, missCount: 2, participatingSlots: [0, 1, 3] },
      { schema: "bilqis.mlx.motif-read-report/v1", receiptId: "motif-read:fixture:g44238:s1", siteIndex: 1, exactCount: 4, structuralCount: 3, missCount: 3, participatingSlots: [0, 2] },
    ],
    gates: [
      { receiptId: "motif-gate:fixture:g44238:s0", siteIndex: 0, eligibleHits: 8, usedHits: 5, authority: "MEASURED" },
      { receiptId: "motif-gate:fixture:g44238:s1", siteIndex: 1, eligibleHits: 7, usedHits: 4, authority: "MEASURED" },
    ],
  }),
  generation({
    generation: 44_239,
    checkpointId: "checkpoint:fixture:g44239",
    allocationDigest: CURRENT_ALLOCATION,
    manifestDigest: CURRENT_MANIFEST,
    slots: CURRENT_SLOTS,
    reads: [
      { schema: "bilqis.mlx.motif-read-report/v1", receiptId: "motif-read:fixture:g44239:s0", siteIndex: 0, exactCount: 8, structuralCount: 3, missCount: 2, participatingSlots: [0, 2, 3, 4] },
      { schema: "bilqis.mlx.motif-read-report/v1", receiptId: "motif-read:fixture:g44239:s1", siteIndex: 1, exactCount: 6, structuralCount: 3, missCount: 3, participatingSlots: [0, 2, 4] },
    ],
    gates: [
      { receiptId: "motif-gate:fixture:g44239:s0", siteIndex: 0, eligibleHits: 11, usedHits: 7, authority: "MEASURED" },
      { receiptId: "motif-gate:fixture:g44239:s1", siteIndex: 1, eligibleHits: 9, usedHits: 6, authority: "MEASURED" },
    ],
  }),
]);

export const REJECTED_MEMORY_CANDIDATE = Object.freeze({
  candidateId: "candidate:fixture:memory-allocation-reject",
  episodeId: "episode-record:fixture:interference-reject",
  parentGeneration: 44_239,
  proposedGeneration: 44_240,
  outcome: "REJECTED",
  reasonCode: "PROTECTED_CAPABILITY_REGRESSION",
  parentAllocationBefore: CURRENT_ALLOCATION,
  committedAllocationAfter: CURRENT_ALLOCATION,
  proposedSlot: Object.freeze({
    semanticRelease: SEMANTIC_RELEASE,
    keyDigest: KEY.rejectedOnly,
    slotId: 5,
    pageIndex: 0,
    rowIndex: 5,
  }),
  committedGeneration: null,
});

export const MEMORY_FIXTURE_CONTRACT = Object.freeze({
  semanticRelease: SEMANTIC_RELEASE,
  pageRows: PAGE_ROWS,
  vectorWidth: VECTOR_WIDTH,
  stateBytesPerPage: STATE_BYTES_PER_PAGE,
  parameterBytesPerPage: PARAMETER_BYTES_PER_PAGE,
  optimizerBytesPerPage: OPTIMIZER_BYTES_PER_PAGE,
});
