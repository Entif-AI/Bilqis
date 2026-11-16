import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { MEMORY_FIXTURE_CONTRACT, MEMORY_GENERATIONS, REJECTED_MEMORY_CANDIDATE } from "../../renderer/memory/memory-fixture.mjs";
import {
  capabilityInterpretation,
  currentMemoryGeneration,
  memoryCompare,
  memoryDeepLink,
  pageSummaries,
  priorMemoryGeneration,
  receiptTotals,
  rejectedCandidateInvariant,
  slotAddress,
  slotHitRate,
  stableMemoryIdentity,
} from "../../renderer/memory/memory-model.mjs";
import { renderMemoryView } from "../../renderer/memory/memory-view.mjs";
import {
  historicalMemoryQuery,
  memoryProfileFromPage,
  memoryQuery,
} from "../../renderer/memory/production-model.mjs";
import { productionMemoryMarkup } from "../../renderer/memory/production-view.mjs";
import { t } from "../../renderer/foundation/i18n.mjs";
import { parseDeepLink } from "../../renderer/deep-link.mjs";
import { INSPECTOR_OWNERS } from "../../renderer/shell-state.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../../..");
const rendererRoot = path.resolve(here, "../../renderer");
const fakeContainer = () => ({ innerHTML: "", querySelectorAll: () => [], querySelector: () => null });

test("summary reconciles literal hit miss and gate counts from fixture receipts", () => {
  const current = currentMemoryGeneration();
  const totals = receiptTotals(current);
  assert.deepEqual(totals, {
    exact: 14,
    structural: 6,
    misses: 5,
    hits: 20,
    reads: 25,
    hitRate: 0.8,
    gateEligibleHits: 20,
    gateUses: 13,
    gateUseRate: 0.65,
  });
  assert.equal(current.readReceipts.reduce((n, row) => n + row.exactCount + row.structuralCount, 0), totals.hits);
  assert.equal(current.gateReceipts.reduce((n, row) => n + row.usedHits, 0), totals.gateUses);
});

test("fixture geometry matches executable motif page and telemetry contracts", () => {
  const identitySource = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_engram/atlas_engram_identity.py"), "utf8",
  );
  const reportSource = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/atlas_engram.py"), "utf8",
  );
  assert.equal(MEMORY_FIXTURE_CONTRACT.pageRows, 16_384);
  assert.equal(MEMORY_FIXTURE_CONTRACT.vectorWidth, 128);
  assert.equal(MEMORY_FIXTURE_CONTRACT.stateBytesPerPage, 25_165_824);
  assert.match(identitySource, /INITIAL_MOTIF_CAPACITY, MOTIF_VECTOR_WIDTH = MOTIF_PAGE_SHAPE/);
  assert.match(identitySource, /MOTIF_PAGE_STATE_BYTES = INITIAL_MOTIF_CAPACITY \* MOTIF_VECTOR_WIDTH \* 4 \* 3/);
  assert.match(reportSource, /class MotifReadReport/);
  assert.match(reportSource, /HELD, foreign-release, and quarantined outcomes are non-reads/);
});

test("atlas aggregates by page but drill-down resolves exact stable BAMF memory identity", () => {
  const current = currentMemoryGeneration();
  const pages = pageSummaries(current);
  assert.deepEqual(pages, [{ pageIndex: 0, capacity: 16_384, allocated: 5, active: 4, held: 1, optimizerParticipating: 4 }]);
  const slot = current.slots[0];
  const identity = stableMemoryIdentity(slot);
  assert.equal(identity, slot.keyDigest);
  assert.equal(slotAddress(slot), "motif.page.0[0]");
  assert.equal(identity.includes("motif.page.0"), false);
  assert.equal(identity.includes("row"), false);
  assert.equal(identity.includes("provider"), false);
});

test("selected slot exposes creation provenance custody correction and related refs", () => {
  const slot = currentMemoryGeneration().slots.find((item) => item.keyDigest === "c".repeat(64));
  assert.ok(slot);
  assert.equal(slot.createdGeneration, 44_238);
  assert.equal(slot.sourceEligibility, "ELIGIBLE");
  assert.equal(slot.correctionState, "QUALIFIED");
  assert.equal(slot.correctionRef, "requalification:fixture:numeric-source-r9");
  assert.equal(slot.optimizerParticipated, true);
  assert.equal(slot.optimizerUpdateCount, 7);
  assert.equal(slot.sourceRefs.length > 0, true);
  assert.equal(slot.evidenceRefs.length > 0, true);
  assert.equal(slot.capabilities.includes("C.SUCCESSOR"), true);
  assert.equal(slot.episodes.includes("episode-record:fixture:retained-44239"), true);
});

test("rejected candidate cannot appear as committed memory allocation", () => {
  const invariant = rejectedCandidateInvariant(REJECTED_MEMORY_CANDIDATE, currentMemoryGeneration());
  assert.deepEqual(invariant, {
    parentAllocationPreserved: true,
    noCommittedGeneration: true,
    proposedSlotAbsent: true,
    proposedIdentity: REJECTED_MEMORY_CANDIDATE.proposedSlot.keyDigest,
  });
});

test("generation compare identifies created held requalified and metric deltas without pretending append-only rows vanished", () => {
  const delta = memoryCompare(priorMemoryGeneration(), currentMemoryGeneration());
  assert.equal(delta.created.length, 1);
  assert.equal(delta.removed.length, 0);
  assert.equal(delta.held.length, 1);
  assert.equal(delta.requalified.length, 1);
  assert.equal(delta.allocationDelta, 1);
  assert.equal(delta.hitDelta, 5);
  assert.equal(delta.gateUseDelta, 4);
  assert.equal(delta.capacityDelta, 0);
});

test("comparison detects physical removal if supplied but default retained manifest remains append-only", () => {
  const before = priorMemoryGeneration();
  const current = currentMemoryGeneration();
  const syntheticAfter = { ...current, slots: current.slots.slice(1), allocatedSlots: current.allocatedSlots - 1 };
  const delta = memoryCompare(before, syntheticAfter);
  assert.equal(delta.removed.length, 1);
  assert.equal(memoryCompare(before, current).removed.length, 0);
});

test("correction and requalification state is independent of retrieval hit rate", () => {
  const held = currentMemoryGeneration().slots.find((slot) => slot.allocationState === "HELD");
  assert.ok(held);
  assert.equal(held.hitCount > 0, true);
  assert.equal(slotHitRate(held) > 0.5, true);
  assert.equal(held.correctionState, "REQUALIFICATION_REQUIRED");
  assert.equal(held.sourceEligibility, "HELD");
});

test("high hit rate retains its literal retrieval interpretation", () => {
  const slot = currentMemoryGeneration().slots[0];
  assert.equal(slotHitRate(slot), 0.95);
  const interpretation = capabilityInterpretation(slot);
  assert.equal(interpretation.learnedSuccess, false);
  assert.equal(interpretation.capabilityEvidence, "INDEPENDENT_EVIDENCE_UNAVAILABLE");
  assert.equal(interpretation.messageKey, "memory.dossier.capabilityUnavailable");
  assert.match(t(interpretation.messageKey), /retrieval activity recorded/i);
});

test("memory deep link uses stable BAMF memory identity and owning view", () => {
  const identity = stableMemoryIdentity(currentMemoryGeneration().slots[0]);
  assert.deepEqual(parseDeepLink(memoryDeepLink(identity)), {
    view: "memory",
    selected: { kind: "memory", id: identity },
  });
  assert.equal(INSPECTOR_OWNERS.memory, "memory");
});

test("GUI10 source avoids memory-policy mutation and unsolicited negative-capability copy", () => {
  const source = [
    "memory-fixture.mjs", "memory-model.mjs", "memory-view.mjs", "memory-messages.mjs",
    "production-model.mjs", "production-view.mjs", "production-controller.mjs",
  ].map((name) => fs.readFileSync(
    path.join(rendererRoot, "memory", name), "utf8",
  )).join("\n").toLowerCase();
  for (const forbidden of [
    "allocate memory now", "edit memory", "promote slot", "learned success", "semantic authority from memory",
    "providerrowid", "database row id",
  ]) assert.equal(source.includes(forbidden), false, forbidden);
  for (const defensive of [
    "does not prove", "does not establish", "does not imply", "does not demonstrate",
    "does not mean", "not evidence of", "no independent capability claim",
  ]) assert.equal(source.includes(defensive), false, defensive);
});

test("Memory target markup is analytical, progressively disclosed, localized, and hook-stable", () => {
  const container = fakeContainer();
  renderMemoryView(container, () => {});
  const html = container.innerHTML;
  for (const id of [
    "memory-workspace",
    "memory-fixture-posture",
    "memory-tabs",
    "memory-tab-overview",
    "memory-tab-atlas",
    "memory-tab-dossier",
    "memory-tab-comparison",
    "memory-summary",
    "memory-page-navigation",
    "memory-atlas",
    "memory-dossier",
    "memory-dossier-provenance",
    "memory-generation-comparison",
    "memory-compare-generation",
    "memory-rejected-boundary",
  ]) assert.match(html, new RegExp(`data-test-id="${id}"`), id);
  assert.equal((html.match(/role="tablist"/g) ?? []).length, 1);
  assert.equal((html.match(/role="tab"/g) ?? []).length, 4);
  assert.equal((html.match(/data-test-id="memory-help-[^"]+-trigger"/g) ?? []).length >= 8, true);
  assert.match(html, /<table class="memory-slot-table">/);
  assert.match(html, /<table class="memory-delta-table">/);
  assert.match(html, /<details class="memory-receipts"/);
  assert.match(html, /<details class="memory-provenance"/);
  assert.doesNotMatch(html, /class="memory-panel"/);
  const ids = [...html.matchAll(/data-test-id="([^"]+)"/g)].map((match) => match[1]);
  assert.equal(ids.length, new Set(ids).size);
});

test("historical memory absence replaces current content instead of blending it", () => {
  const container = fakeContainer();
  renderMemoryView(container, () => {}, null, {
    runId: "fixture-run",
    generation: 1,
    mode: "HISTORICAL",
  });
  assert.match(container.innerHTML, /data-test-id="memory-historical-unavailable"/);
  assert.match(container.innerHTML, /Exact memory reference unavailable/);
  assert.doesNotMatch(container.innerHTML, /data-test-id="memory-summary"/);
  assert.doesNotMatch(container.innerHTML, /data-test-id="memory-atlas"/);
});

test("production Memory builds exact current and historical CP03 queries", () => {
  const context = { runId: "run-1188", generation: 9, mode: "LIVE" };
  assert.deepEqual(memoryQuery(context), {
    schema: "bilqis.bamf.control-plane.query/v1",
    family: "memory",
    mode: "current",
    run_id: "run-1188",
    record_id: null,
    schema_version: "bilqis.bamf.mission-control.memory-snapshot/v1",
    generation: null,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor: null,
    limit: 64,
  });
  assert.equal(historicalMemoryQuery(context, 8).mode, "historical");
  assert.equal(historicalMemoryQuery(context, 8).generation, 8);
  assert.throws(() => historicalMemoryQuery(context, -1), /GUI10_HISTORICAL_GENERATION_REQUIRED/);
});

test("production Memory consumes summary-only MemorySnapshot without inventing slots", () => {
  const profile = memoryProfileFromPage({ accepted: true, state: "PRESENT", records: [{
    schema_version: "bilqis.bamf.mission-control.memory-snapshot/v1",
    meta: {
      record_id: "memory:run-1188:g9",
      run: { run_id: "run-1188", generation: 9 },
      observed_at: 1790000118,
      source_refs: ["source:memory"],
      evidence_refs: ["evidence:memory"],
      receipt_refs: ["receipt:memory"],
    },
    used_bytes: { state: "PRESENT", value: 1024, units: "bytes", origin: "MEASURED" },
    budget_bytes: { state: "PRESENT", value: 4096, units: "bytes", origin: "CONFIGURED_LIMIT" },
    hits: { state: "PRESENT", value: 10, units: "count", origin: "MEASURED" },
    misses: { state: "PRESENT", value: 2, units: "count", origin: "MEASURED" },
    requalifications: { state: "PRESENT", value: 1, units: "count", origin: "MEASURED" },
  }] }, { runId: "run-1188", generation: 9, mode: "LIVE" });
  assert.equal(profile.generation, 9);
  assert.equal(profile.observedAt, 1790000118);
  assert.equal(profile.metrics.hits.value, 10);
  assert.equal(Object.hasOwn(profile, "slots"), false);
});

test("production Memory renders one peer-tab layer and truthful slot-detail absence", () => {
  const current = {
    provenance: "LIVE_QUERY", pageState: "PRESENT", generation: 9,
    recordId: "memory:run-1188:g9", observedAt: 1790000118,
    sourceRefs: [], evidenceRefs: [], receiptRefs: [],
    metrics: {
      used: { state: "PRESENT", value: 1024, units: "bytes" },
      budget: { state: "PRESENT", value: 4096, units: "bytes" },
      hits: { state: "PRESENT", value: 10, units: "count" },
      misses: { state: "PRESENT", value: 2, units: "count" },
      requalifications: { state: "PRESENT", value: 1, units: "count" },
    },
  };
  const html = productionMemoryMarkup({ current, comparison: null, comparisonState: "EMPTY", comparisonGeneration: null });
  assert.equal((html.match(/role="tablist"/g) ?? []).length, 1);
  assert.equal((html.match(/role="tab"/g) ?? []).length, 4);
  assert.match(html, /data-test-id="memory-production-atlas-state"/);
  assert.match(html, /aggregate memory state only/i);
  assert.match(html, /data-source-unix-seconds="1790000118"/);
  assert.doesNotMatch(html, /REFERENCE MEMORY DATA|44239|candidate:fixture/);
});

test("production Memory dependency graph contains no fixture module", () => {
  const sources = ["production-controller.mjs", "production-model.mjs", "production-view.mjs"]
    .map(name => fs.readFileSync(path.join(rendererRoot, "memory", name), "utf8"))
    .join("\n");
  assert.doesNotMatch(sources, /memory-fixture|REFERENCE MEMORY DATA|fixture:/);
});

test("owned Memory human copy is routed through the Memory message catalog", () => {
  const source = ["memory-view.mjs", "memory-fixture-panels.mjs"]
    .map(name => fs.readFileSync(path.join(rendererRoot, "memory", name), "utf8"))
    .join("\n");
  for (const legacyLiteral of ["Engram memory summary", "Aggregate → page → stable motif", "Motif inspector", "Rejected candidate boundary", "Historical memory"]) {
    assert.equal(source.includes(legacyLiteral), false, legacyLiteral);
  }
  assert.match(source, /t\("memory\.heading\.title"\)/);
  assert.match(source, /t\("memory\.compare\.title"\)/);
  assert.match(source, /t\("memory\.rejected\.title"\)/);
});

test("CSS gives held rejected and requalified states non-color structural cues", () => {
  const css = ["memory-core.css", "memory-atlas.css", "memory-evidence.css"]
    .map((name) => fs.readFileSync(path.join(rendererRoot, "memory", name), "utf8")).join("\n");
  assert.match(css, /data-memory-state="held"/);
  assert.match(css, /border-style:\s*dashed/);
  assert.match(css, /data-memory-state="rejected"/);
  assert.match(css, /data-delta-kind="requalified"/);
});

test("Memory stylesheet modules stay below the structural interruption threshold", () => {
  for (const name of ["memory-core.css", "memory-atlas.css", "memory-evidence.css"]) {
    const lines = fs.readFileSync(path.join(rendererRoot, "memory", name), "utf8").split("\n").length - 1;
    assert.ok(lines < 240, `${name} has ${lines} lines`);
  }
});

test("fixture generation sequence is ordered and immutable enough for compare", () => {
  assert.deepEqual(MEMORY_GENERATIONS.map((item) => item.generation), [44_238, 44_239]);
  assert.equal(MEMORY_GENERATIONS.every((item) => Object.isFrozen(item)), true);
});
