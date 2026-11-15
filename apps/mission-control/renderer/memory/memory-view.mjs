import {
  MEMORY_GENERATIONS,
  REJECTED_MEMORY_CANDIDATE,
} from "./memory-fixture.mjs";
import {
  capabilityInterpretation,
  currentMemoryGeneration,
  memoryGeneration,
  memoryCompare,
  pageSummaries,
  priorMemoryGeneration,
  receiptTotals,
  rejectedCandidateInvariant,
  slotAddress,
  slotByIdentity,
  slotGateUseRate,
  slotHitRate,
  slotsForPage,
  stableMemoryIdentity,
} from "./memory-model.mjs";
import { buildDeepLink } from "../deep-link.mjs";
import { objectDomAttributes } from "../interactions/dom-ref.mjs";
import { createTranslator } from "../foundation/i18n.mjs";
import { contextHelpMarkup, controlClass } from "../foundation/primitives.mjs";
import { MEMORY_MESSAGES } from "./memory-messages.mjs";

const t = createTranslator({ messages: Object.freeze({
  "en-US": Object.freeze({
    ...MEMORY_MESSAGES,
    "memory.fixture.label": "REFERENCE MEMORY DATA",
    "memory.fixture.detail": "This launch uses checked-in retained-memory reference records for development and visual verification.",
  }),
}) });

export const MEMORY_TABS = Object.freeze(["overview", "atlas", "dossier", "comparison"]);

const ui = {
  compareGeneration: priorMemoryGeneration().generation,
  selectedPage: 0,
  selectedIdentity: stableMemoryIdentity(currentMemoryGeneration().slots[0]),
  activeTab: "overview",
};

function help(id, key) {
  return contextHelpMarkup({
    label: t(`memory.help.${key}.label`),
    description: t(`memory.help.${key}.body`),
    testId: `memory-help-${id}`,
  });
}

const STATE_KEYS = Object.freeze({
  PRESENT: "memory.state.present",
  ACTIVE: "memory.state.active",
  HELD: "memory.state.held",
  REJECTED: "memory.state.rejected",
  MISSING: "memory.state.missing",
  DIFF: "memory.state.diff",
});

function e(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function pct(value) {
  return value === null ? t("memory.value.unavailable") : `${(100 * value).toFixed(1)}%`;
}

function bytes(value) {
  return `${(value / (1024 * 1024)).toFixed(1)} MiB`;
}

function signed(value) {
  return `${value >= 0 ? "+" : ""}${value}`;
}

function stateBadge(state) {
  const normalized = String(state).toLowerCase().replaceAll("_", "-");
  const label = t(STATE_KEYS[state] ?? "memory.state.present");
  return `<span class="memory-state" data-memory-state="${e(normalized)}">${e(label)}</span>`;
}

function normalizedRouteContext(context) {
  if (!context?.runId || !Number.isSafeInteger(context.generation)) return null;
  return {
    ...context,
    historicalPinned: context.mode === "HISTORICAL",
  };
}

function relationHref(view, kind, id, context) {
  return buildDeepLink({
    view,
    selected: { kind, id },
    ...(normalizedRouteContext(context) ? { context: normalizedRouteContext(context) } : {}),
  });
}

function summaryPanel(snapshot) {
  const totals = receiptTotals(snapshot);
  return `<section class="memory-surface memory-summary" data-test-id="memory-summary">
    <header class="memory-section-heading">
      <div><span class="eyebrow">${t("memory.summary.eyebrow")}</span><h3>${t("memory.summary.title")}</h3></div>
      <div class="memory-heading-tools">${help("metrics", "metrics")}${help("time", "time")}</div>
      ${stateBadge("PRESENT")}
    </header>
    <dl class="memory-metric-band">
      <div data-test-id="memory-summary-allocation"><dt>${t("memory.summary.allocatedCapacity")}</dt><dd>${snapshot.allocatedSlots} / ${snapshot.capacitySlots}</dd></div>
      <div><dt>${t("memory.summary.eligibleHits")}</dt><dd>${totals.hits}<small>${t("memory.summary.hitBreakdown", { exact: totals.exact, structural: totals.structural })}</small></dd></div>
      <div><dt>${t("memory.summary.misses")}</dt><dd>${totals.misses}<small>${t("memory.summary.missDetail")}</small></dd></div>
      <div><dt>${t("memory.summary.hitRate")}</dt><dd>${pct(totals.hitRate)}<small>${t("memory.summary.hitRateDetail")}</small></dd></div>
      <div><dt>${t("memory.summary.gateRate")}</dt><dd>${pct(totals.gateUseRate)}<small>${t("memory.summary.gateRateDetail", { used: totals.gateUses, eligible: totals.gateEligibleHits })}</small></dd></div>
      <div><dt>${t("memory.summary.footprint")}</dt><dd>${bytes(snapshot.memoryFootprint.stateBytes)}<small>${t("memory.summary.footprintDetail", { parameters: bytes(snapshot.memoryFootprint.parameterBytes), optimizer: bytes(snapshot.memoryFootprint.optimizerBytes) })}</small></dd></div>
    </dl>
    <details class="memory-receipts" data-test-id="memory-read-site-receipts">
      <summary>${t("memory.summary.receipts", { count: snapshot.readReceipts.length })}</summary>
      <div class="memory-receipt-list">
        ${snapshot.readReceipts.map((receipt, index) => `<div data-test-id="memory-read-site-${index}">
          <strong>${t("memory.summary.readSite", { site: receipt.siteIndex })}</strong>
          <span>${t("memory.summary.readSiteCounts", { exact: receipt.exactCount, structural: receipt.structuralCount, misses: receipt.missCount })}</span>
          <code>${e(receipt.receiptId)}</code>
        </div>`).join("")}
      </div>
    </details>
    <p class="memory-boundary"><strong>${t("memory.summary.boundary")}:</strong> ${t("memory.summary.boundaryDetail")}</p>
  </section>`;
}

function memoryRelations(slot) {
  return [
    ...slot.capabilities.map((id) => ({ kind: "capability", id, relation: "capability" })),
    ...slot.episodes.map((id) => ({ kind: "episode", id, relation: "episode" })),
  ];
}

function atlasPanel(snapshot) {
  const pages = pageSummaries(snapshot);
  const pageSlots = slotsForPage(snapshot, ui.selectedPage);
  const currentPosition = Math.max(0, pages.findIndex((page) => page.pageIndex === ui.selectedPage));
  return `<section class="memory-surface memory-atlas" data-test-id="memory-atlas">
    <header class="memory-section-heading">
      <div><span class="eyebrow">${t("memory.atlas.eyebrow")}</span><h3>${t("memory.atlas.title")}</h3><p>${t("memory.atlas.summary")}</p></div>
      <div class="memory-heading-tools">${help("identity", "identity")}${help("allocation", "allocation")}</div>
    </header>
    <nav class="memory-page-nav" aria-label="${e(t("memory.atlas.eyebrow"))}" data-test-id="memory-page-navigation">
      <button type="button" data-memory-page-step="-1" data-test-id="memory-page-previous" ${currentPosition === 0 ? "disabled" : ""}>${t("memory.atlas.previous")}</button>
      <strong data-test-id="memory-page-position">${t("memory.atlas.page", { current: currentPosition + 1, total: pages.length })}</strong>
      <button type="button" data-memory-page-step="1" data-test-id="memory-page-next" ${currentPosition >= pages.length - 1 ? "disabled" : ""}>${t("memory.atlas.next")}</button>
    </nav>
    <div class="memory-table-wrap" tabindex="0" role="region" aria-label="${e(t("memory.atlas.title"))}" data-test-id="memory-atlas-table-wrap">
      <table class="memory-slot-table">
        <thead><tr>
          <th scope="col">${t("memory.atlas.address")}</th>
          <th scope="col">${t("memory.atlas.identity")}</th>
          <th scope="col">${t("memory.atlas.frameSchema")}</th>
          <th scope="col">${t("memory.atlas.state")}</th>
          <th scope="col">${t("memory.atlas.relations")}</th>
        </tr></thead>
        <tbody>${pageSlots.length ? pageSlots.map((slot) => {
          const identity = stableMemoryIdentity(slot);
          const selected = identity === ui.selectedIdentity;
          return `<tr data-memory-allocation-state="${e(slot.allocationState.toLowerCase())}" data-selected="${selected}" data-test-id="memory-slot-row-${slot.pageIndex}-${slot.rowIndex}">
            <td><code>${e(slotAddress(slot))}</code></td>
            <td><button type="button" class="memory-slot-action" data-memory-slot="${e(identity)}" data-test-id="memory-slot-select-${slot.pageIndex}-${slot.rowIndex}" ${objectDomAttributes({
              kind: "memory", id: identity, relations: memoryRelations(slot),
            })} aria-pressed="${selected}" aria-label="${e(t("memory.atlas.select", { identity }))}"><code>${e(identity)}</code></button></td>
            <td><code>${e(slot.frameSchemaId)}</code></td>
            <td>${stateBadge(slot.allocationState)}</td>
            <td>${t("memory.atlas.relationCounts", { capabilities: slot.capabilities.length, episodes: slot.episodes.length })}</td>
          </tr>`;
        }).join("") : `<tr><td colspan="5" class="memory-muted">${t("memory.atlas.empty")}</td></tr>`}</tbody>
      </table>
    </div>
  </section>`;
}

function refList(items) {
  return items.length
    ? `<ul class="memory-ref-list">${items.map((item) => `<li><code>${e(item)}</code></li>`).join("")}</ul>`
    : `<span class="memory-muted">${t("memory.value.none")}</span>`;
}

function relationList(items, view, kind, messageKey, context) {
  return items.length
    ? `<ul class="memory-action-list">${items.map((id, index) => `<li><a href="${e(relationHref(view, kind, id, context))}" data-test-id="memory-related-${kind}-${index}">${e(t(messageKey, { id }))}</a></li>`).join("")}</ul>`
    : `<span class="memory-muted">${t("memory.value.none")}</span>`;
}

function evidenceList(slot, context) {
  return slot.evidenceRefs.length
    ? `<ul class="memory-action-list">${slot.evidenceRefs.map((id, index) => `<li><code>${e(id)}</code><a href="${e(relationHref("evidence", "evidence", id, context))}" data-test-id="memory-related-evidence-${index}">${e(t("memory.dossier.openEvidence", { id }))}</a></li>`).join("")}</ul>`
    : `<span class="memory-muted">${t("memory.value.none")}</span>`;
}

function slotPanel(snapshot, context) {
  const slot = slotByIdentity(snapshot, ui.selectedIdentity);
  if (!slot) {
    return `<section class="memory-surface memory-dossier" data-test-id="memory-dossier">
      <header class="memory-section-heading"><div><span class="eyebrow">${t("memory.dossier.eyebrow")}</span><h3>${t("memory.dossier.missingTitle")}</h3></div>${stateBadge("MISSING")}</header>
    </section>`;
  }
  const interpretation = capabilityInterpretation(slot);
  return `<section class="memory-surface memory-dossier" data-test-id="memory-dossier">
    <header class="memory-section-heading">
      <div><span class="eyebrow">${t("memory.dossier.eyebrow")}</span><h3>${t("memory.dossier.title")}</h3><code class="memory-primary-identity">${e(stableMemoryIdentity(slot))}</code></div>
      <div class="memory-heading-tools">${help("optimizer", "optimizer")}${help("relations", "relations")}${help("correction", "correction")}</div>
      ${stateBadge(slot.allocationState)}
    </header>
    <div class="memory-dossier-grid">
      <section><h4>${t("memory.dossier.identitySection")}</h4><dl>
        <div><dt>${t("memory.dossier.identityContract")}</dt><dd><code>${e(slot.schema)}</code></dd></div>
        <div><dt>${t("memory.dossier.keyDigest")}</dt><dd><code>${e(slot.keyDigest)}</code></dd></div>
        <div><dt>${t("memory.dossier.semanticRelease")}</dt><dd><code>${e(slot.semanticRelease)}</code></dd></div>
        <div><dt>${t("memory.dossier.exactAddress")}</dt><dd>${e(t("memory.dossier.exactAddressValue", { address: slotAddress(slot), slot: slot.slotId }))}</dd></div>
      </dl></section>
      <section><h4>${t("memory.dossier.useSection")}</h4><dl>
        <div><dt>${t("memory.dossier.sourceEligibility")}</dt><dd>${e(slot.sourceEligibility)}${slot.heldReason ? ` · ${e(slot.heldReason)}` : ""}</dd></div>
        <div><dt>${t("memory.dossier.created")}</dt><dd>${t("memory.dossier.createdValue", { generation: slot.createdGeneration })}</dd></div>
        <div><dt>${t("memory.dossier.lastUse")}</dt><dd>${e(t("memory.dossier.lastUseValue", { generation: slot.lastUse.generation, step: slot.lastUse.optimizerStep, receipt: slot.lastUse.receiptId }))}</dd></div>
        <div><dt>${t("memory.dossier.lifetimeHits")}</dt><dd>${t("memory.dossier.lifetimeHitsValue", { hits: slot.hitCount, eligible: slot.eligibleReadCount, rate: pct(slotHitRate(slot)) })}</dd></div>
        <div><dt>${t("memory.dossier.gateActivity")}</dt><dd>${t("memory.dossier.gateActivityValue", { uses: slot.gateUseCount, rate: pct(slotGateUseRate(slot)) })}</dd></div>
      </dl></section>
      <section><h4>${t("memory.dossier.stateSection")}</h4><dl>
        <div><dt>${t("memory.dossier.parameterBank")}</dt><dd>${e(slot.parameterBank)} · ${e(slot.allocationExtent)}</dd></div>
        <div><dt>${t("memory.dossier.optimizer")}</dt><dd>${slot.optimizerParticipated ? t("memory.dossier.optimizerYes", { updates: slot.optimizerUpdateCount }) : t("memory.dossier.optimizerNo")}</dd></div>
        <div><dt>${t("memory.dossier.correction")}</dt><dd>${e(slot.correctionState)}${slot.correctionRef ? ` · ${e(slot.correctionRef)}` : ""}</dd></div>
      </dl></section>
    </div>
    <p class="memory-capability-boundary"><strong>${t("memory.dossier.capabilityBoundary")}:</strong> ${t(interpretation.messageKey)}</p>
    <details class="memory-provenance" data-test-id="memory-dossier-provenance">
      <summary>${t("memory.dossier.provenance")}</summary>
      <div class="memory-provenance-grid">
        <section><h4>${t("memory.dossier.sourceRefs")}</h4>${refList(slot.sourceRefs)}</section>
        <section><h4>${t("memory.dossier.evidenceRefs")}</h4>${evidenceList(slot, context)}</section>
        <section><h4>${t("memory.dossier.relatedCapabilities")}</h4>${relationList(slot.capabilities, "capability", "capability", "memory.dossier.openCapability", context)}</section>
        <section><h4>${t("memory.dossier.relatedEpisodes")}</h4>${relationList(slot.episodes, "learning", "episode", "memory.dossier.openEpisode", context)}</section>
      </div>
    </details>
  </section>`;
}

function comparePanel(snapshot) {
  const candidates = MEMORY_GENERATIONS.filter((item) => item.generation !== snapshot.generation);
  const before = candidates.find((item) => item.generation === ui.compareGeneration) ?? candidates[0] ?? snapshot;
  const delta = memoryCompare(before, snapshot);
  const rows = [
    ["created", "memory.compare.created", delta.created],
    ["removed", "memory.compare.removed", delta.removed],
    ["held", "memory.compare.held", delta.held],
    ["requalified", "memory.compare.requalified", delta.requalified],
  ];
  return `<section class="memory-surface memory-compare" data-test-id="memory-generation-comparison">
    <header class="memory-section-heading"><div><span class="eyebrow">${t("memory.compare.eyebrow")}</span><h3>${t("memory.compare.title")}</h3></div><div class="memory-heading-tools">${help("comparison", "comparison")}</div>${stateBadge("DIFF")}</header>
    <label class="memory-compare-control">${t("memory.compare.from")}
      <select data-memory-compare data-test-id="memory-compare-generation">${candidates.map((item) => `<option value="${item.generation}" ${item.generation === before.generation ? "selected" : ""}>${t("memory.compare.option", { generation: item.generation })}</option>`).join("")}</select>
    </label>
    <div class="memory-table-wrap" tabindex="0" role="region"
         aria-label="${e(t("memory.compare.title"))}" data-test-id="memory-compare-table-wrap">
      <table class="memory-delta-table"><thead><tr><th>${t("memory.compare.dimension")}</th><th>${t("memory.compare.count")}</th><th>${t("memory.compare.identities")}</th></tr></thead>
        <tbody>${rows.map(([kind, key, identities]) => `<tr data-delta-kind="${kind}" data-test-id="memory-compare-${kind}"><th scope="row">${t(key)}</th><td>${identities.length}</td><td>${identities.length ? identities.map((identity) => `<code>${e(identity)}</code>`).join("<br>") : t("memory.value.none")}</td></tr>`).join("")}</tbody>
      </table>
    </div>
    <h4>${t("memory.compare.metrics")}</h4>
    <dl class="memory-compare-metrics">
      <div><dt>${t("memory.compare.allocation")}</dt><dd>${signed(delta.allocationDelta)}</dd></div>
      <div><dt>${t("memory.compare.capacity")}</dt><dd>${signed(delta.capacityDelta)}</dd></div>
      <div><dt>${t("memory.compare.hits")}</dt><dd>${signed(delta.hitDelta)}</dd></div>
      <div><dt>${t("memory.compare.misses")}</dt><dd>${signed(delta.missDelta)}</dd></div>
      <div><dt>${t("memory.compare.gate")}</dt><dd>${signed(delta.gateUseDelta)}</dd></div>
    </dl>
    <p class="memory-boundary">${t("memory.compare.boundary")}</p>
  </section>`;
}

function rejectedCandidatePanel(snapshot) {
  const invariant = rejectedCandidateInvariant(REJECTED_MEMORY_CANDIDATE, snapshot);
  return `<section class="memory-rejected" data-test-id="memory-rejected-boundary">
    <header class="memory-section-heading"><div><span class="eyebrow">${t("memory.rejected.eyebrow")}</span><h3>${t("memory.rejected.title")}</h3></div>${stateBadge("REJECTED")}</header>
    <dl class="memory-rejected-proof">
      <div><dt>${t("memory.rejected.candidate")}</dt><dd><code>${e(REJECTED_MEMORY_CANDIDATE.candidateId)}</code></dd></div>
      <div><dt>${t("memory.rejected.proposed")}</dt><dd><code>${e(invariant.proposedIdentity)}</code></dd></div>
      <div><dt>${t("memory.rejected.parent")}</dt><dd>${invariant.parentAllocationPreserved ? t("memory.value.yes") : t("memory.value.no")}</dd></div>
      <div><dt>${t("memory.rejected.committed")}</dt><dd>${invariant.noCommittedGeneration ? t("memory.value.none") : REJECTED_MEMORY_CANDIDATE.committedGeneration}</dd></div>
      <div><dt>${t("memory.rejected.slot")}</dt><dd>${invariant.proposedSlotAbsent ? t("memory.value.absent") : t("memory.value.presentInvalid")}</dd></div>
      <div><dt>${t("memory.rejected.reason")}</dt><dd><code>${e(REJECTED_MEMORY_CANDIDATE.reasonCode)}</code></dd></div>
    </dl>
    <p class="memory-boundary">${t("memory.rejected.boundary")}</p>
  </section>`;
}

function historicalUnavailable(generation) {
  return `<div class="memory-view" data-test-id="memory-workspace">
    <section class="memory-historical-unavailable" data-test-id="memory-historical-unavailable">
      <header class="memory-section-heading"><div><span class="eyebrow">${t("memory.historical.eyebrow")}</span><h2>${t("memory.historical.title")}</h2></div>${stateBadge("MISSING")}</header>
      <p>${t("memory.historical.detail", { generation })}</p>
    </section>
  </div>`;
}

function tabsMarkup() {
  return MEMORY_TABS.map((id) => `<button type="button" role="tab" class="${controlClass("peer-tab")}" id="memory-tab-${id}" data-memory-tab="${id}" aria-controls="memory-panel-${id}" aria-selected="${String(id === ui.activeTab)}" tabindex="${id === ui.activeTab ? "0" : "-1"}" data-test-id="memory-tab-${id}">${t(`memory.tab.${id}`)}</button>`).join("");
}

function tabPanel(id, body) {
  return `<section class="memory-tabpanel" role="tabpanel" id="memory-panel-${id}" aria-labelledby="memory-tab-${id}" data-memory-panel="${id}" ${id === ui.activeTab ? "" : "hidden "}data-test-id="memory-panel-${id}">${body}</section>`;
}

function bindTabs(container) {
  const tabs = [...container.querySelectorAll("[data-memory-tab]")];
  const panels = [...container.querySelectorAll("[data-memory-panel]")];
  const activate = (id, focus = false) => {
    if (!MEMORY_TABS.includes(id)) return;
    ui.activeTab = id;
    tabs.forEach(tab => {
      const selected = tab.dataset.memoryTab === id;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      if (selected && focus) tab.focus?.({ preventScroll: true });
    });
    panels.forEach(panel => { panel.hidden = panel.dataset.memoryPanel !== id; });
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activate(tab.dataset.memoryTab));
    tab.addEventListener("keydown", event => {
      const next = event.key === "ArrowRight" ? (index + 1) % tabs.length
        : event.key === "ArrowLeft" ? (index - 1 + tabs.length) % tabs.length
        : event.key === "Home" ? 0
        : event.key === "End" ? tabs.length - 1
        : null;
      if (next === null) return;
      event.preventDefault();
      activate(tabs[next].dataset.memoryTab, true);
    });
  });
}

function bind(container, inspectMemory, snapshot, context) {
  bindTabs(container);
  container.querySelectorAll("[data-memory-page-step]").forEach((button) => button.addEventListener("click", () => {
    const pages = pageSummaries(snapshot);
    const current = pages.findIndex((page) => page.pageIndex === ui.selectedPage);
    const next = pages[current + Number(button.dataset.memoryPageStep)];
    if (!next) return;
    ui.selectedPage = next.pageIndex;
    const first = slotsForPage(snapshot, ui.selectedPage)[0];
    if (first) ui.selectedIdentity = stableMemoryIdentity(first);
    renderMemoryView(container, inspectMemory, ui.selectedIdentity, context);
  }));
  container.querySelectorAll("[data-memory-slot]").forEach((button) => button.addEventListener("click", () => {
    ui.selectedIdentity = button.dataset.memorySlot;
    renderMemoryView(container, inspectMemory, ui.selectedIdentity, context);
    const slot = slotByIdentity(snapshot, ui.selectedIdentity);
    if (slot) inspectMemory(ui.selectedIdentity, slot);
  }));
  container.querySelector("[data-memory-compare]")?.addEventListener("change", (event) => {
    ui.compareGeneration = Number(event.currentTarget.value);
    renderMemoryView(container, inspectMemory, ui.selectedIdentity, context);
  });
}

export function renderMemoryView(container, inspectMemory, selectedIdentity = null, context = null) {
  let snapshot = currentMemoryGeneration();
  if (context?.mode === "HISTORICAL") {
    try {
      snapshot = memoryGeneration(context.generation);
    } catch (_error) {
      container.innerHTML = historicalUnavailable(context.generation);
      return;
    }
  }
  if (selectedIdentity && slotByIdentity(snapshot, selectedIdentity)) ui.selectedIdentity = selectedIdentity;
  if (!slotByIdentity(snapshot, ui.selectedIdentity)) ui.selectedIdentity = stableMemoryIdentity(snapshot.slots[0]);
  const selected = slotByIdentity(snapshot, ui.selectedIdentity);
  if (selected) ui.selectedPage = selected.pageIndex;
  container.innerHTML = `<div class="memory-view" data-test-id="memory-workspace">
    <header class="memory-heading" data-test-id="memory-heading"><div><span class="eyebrow">${t("memory.heading.eyebrow")}</span><h2>${t("memory.heading.title")}</h2></div><p>${t("memory.heading.summary")}</p></header>
    <div class="memory-fixture-notice" role="note" data-test-id="memory-fixture-posture"><strong>${t("memory.fixture.label")}</strong><span>${t("memory.fixture.detail")}</span></div>
    <div class="memory-tabs" role="tablist" aria-label="${e(t("memory.tabs.aria"))}" data-test-id="memory-tabs">${tabsMarkup()}</div>
    ${tabPanel("overview", summaryPanel(snapshot))}
    ${tabPanel("atlas", atlasPanel(snapshot))}
    ${tabPanel("dossier", slotPanel(snapshot, context) + rejectedCandidatePanel(snapshot))}
    ${tabPanel("comparison", comparePanel(snapshot))}
  </div>`;
  bind(container, inspectMemory, snapshot, context);
}
