import {
  MEMORY_GENERATIONS,
  REJECTED_MEMORY_CANDIDATE,
} from "./memory-fixture.mjs";

export function stableMemoryIdentity(slot) {
  return slot.keyDigest;
}

export function slotAddress(slot) {
  return `motif.page.${slot.pageIndex}[${slot.rowIndex}]`;
}

export function memoryGeneration(generation) {
  const found = MEMORY_GENERATIONS.find((item) => item.generation === generation);
  if (!found) throw new RangeError(`MEMORY_GENERATION_UNKNOWN:${generation}`);
  return found;
}

export function currentMemoryGeneration() {
  return MEMORY_GENERATIONS.at(-1);
}

export function priorMemoryGeneration() {
  return MEMORY_GENERATIONS.at(-2);
}

export function receiptTotals(snapshot) {
  const totals = snapshot.readReceipts.reduce((acc, item) => {
    acc.exact += item.exactCount;
    acc.structural += item.structuralCount;
    acc.misses += item.missCount;
    acc.hits += item.exactCount + item.structuralCount;
    acc.reads += item.exactCount + item.structuralCount + item.missCount;
    return acc;
  }, { exact: 0, structural: 0, misses: 0, hits: 0, reads: 0 });
  const gate = snapshot.gateReceipts.reduce((acc, item) => {
    acc.eligible += item.eligibleHits;
    acc.used += item.usedHits;
    return acc;
  }, { eligible: 0, used: 0 });
  return Object.freeze({
    ...totals,
    hitRate: totals.reads ? totals.hits / totals.reads : null,
    gateEligibleHits: gate.eligible,
    gateUses: gate.used,
    gateUseRate: gate.eligible ? gate.used / gate.eligible : null,
  });
}

export function pageSummaries(snapshot) {
  const pages = new Map();
  for (let page = 0; page < snapshot.pageCount; page += 1) {
    pages.set(page, {
      pageIndex: page,
      capacity: snapshot.pageRows,
      allocated: 0,
      active: 0,
      held: 0,
      optimizerParticipating: 0,
    });
  }
  for (const slot of snapshot.slots) {
    const row = pages.get(slot.pageIndex);
    if (!row) throw new RangeError(`MEMORY_PAGE_UNKNOWN:${slot.pageIndex}`);
    row.allocated += 1;
    row[slot.allocationState === "HELD" ? "held" : "active"] += 1;
    if (slot.optimizerParticipated && slot.allocationState !== "HELD") {
      row.optimizerParticipating += 1;
    }
  }
  return Object.freeze([...pages.values()].map(Object.freeze));
}

export function slotByIdentity(snapshot, identity) {
  return snapshot.slots.find((slot) => stableMemoryIdentity(slot) === identity) ?? null;
}

export function slotsForPage(snapshot, pageIndex) {
  return Object.freeze(snapshot.slots.filter((slot) => slot.pageIndex === pageIndex));
}

export function slotHitRate(slot) {
  return slot.eligibleReadCount ? slot.hitCount / slot.eligibleReadCount : null;
}

export function slotGateUseRate(slot) {
  return slot.hitCount ? slot.gateUseCount / slot.hitCount : null;
}

export function memoryCompare(before, after) {
  const beforeByIdentity = new Map(before.slots.map((slot) => [stableMemoryIdentity(slot), slot]));
  const afterByIdentity = new Map(after.slots.map((slot) => [stableMemoryIdentity(slot), slot]));
  const created = [];
  const removed = [];
  const held = [];
  const requalified = [];
  const changed = [];
  for (const [identity, slot] of afterByIdentity) {
    const prior = beforeByIdentity.get(identity);
    if (!prior) {
      created.push(identity);
      continue;
    }
    if (prior.allocationState !== "HELD" && slot.allocationState === "HELD") held.push(identity);
    if (prior.correctionState !== "QUALIFIED" && slot.correctionState === "QUALIFIED") {
      requalified.push(identity);
    }
    if (
      prior.hitCount !== slot.hitCount ||
      prior.gateUseCount !== slot.gateUseCount ||
      prior.optimizerUpdateCount !== slot.optimizerUpdateCount ||
      prior.allocationState !== slot.allocationState ||
      prior.correctionState !== slot.correctionState
    ) changed.push(identity);
  }
  for (const identity of beforeByIdentity.keys()) {
    if (!afterByIdentity.has(identity)) removed.push(identity);
  }
  const beforeTotals = receiptTotals(before);
  const afterTotals = receiptTotals(after);
  return Object.freeze({
    fromGeneration: before.generation,
    toGeneration: after.generation,
    created: Object.freeze(created),
    removed: Object.freeze(removed),
    held: Object.freeze(held),
    requalified: Object.freeze(requalified),
    changed: Object.freeze(changed),
    capacityDelta: after.capacitySlots - before.capacitySlots,
    allocationDelta: after.allocatedSlots - before.allocatedSlots,
    hitDelta: afterTotals.hits - beforeTotals.hits,
    missDelta: afterTotals.misses - beforeTotals.misses,
    gateUseDelta: afterTotals.gateUses - beforeTotals.gateUses,
  });
}

export function rejectedCandidateInvariant(candidate = REJECTED_MEMORY_CANDIDATE, committed = currentMemoryGeneration()) {
  const proposedIdentity = stableMemoryIdentity(candidate.proposedSlot);
  return Object.freeze({
    parentAllocationPreserved: candidate.parentAllocationBefore === candidate.committedAllocationAfter,
    noCommittedGeneration: candidate.committedGeneration === null,
    proposedSlotAbsent: !committed.slots.some((slot) => stableMemoryIdentity(slot) === proposedIdentity),
    proposedIdentity,
  });
}

export function capabilityInterpretation(slot) {
  return Object.freeze({
    retrievalHitRate: slotHitRate(slot),
    capabilityEvidence: slot.capabilityEvidence,
    learnedSuccess: false,
    messageKey: slot.capabilityEvidence === "INDEPENDENT_EVIDENCE_UNAVAILABLE"
      ? "memory.dossier.capabilityUnavailable"
      : "memory.dossier.capabilityRequired",
  });
}

export function memoryDeepLink(identity) {
  const params = new URLSearchParams({ kind: "memory", id: identity });
  return `#/view/memory?${params.toString()}`;
}
