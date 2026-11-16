import { createTranslator } from "../foundation/i18n.mjs";
import { contextHelpMarkup, controlClass, stateMarkup } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { MEMORY_MESSAGES } from "./memory-messages.mjs";
import { memoryComparison } from "./production-model.mjs";

export const MEMORY_PRODUCTION_TABS = Object.freeze(["overview", "atlas", "dossier", "comparison"]);

const esc = value => String(value ?? "").replace(/[&<>"']/g, character => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[character]);

function translator(locale) {
  return createTranslator({ locale, messages: Object.freeze({ "en-US": MEMORY_MESSAGES }) });
}

function help(t, id, key) {
  return contextHelpMarkup({
    label: t(`memory.help.${key}.label`),
    description: t(`memory.help.${key}.body`),
    testId: `memory-production-help-${id}`,
  });
}

function metricValue(metric) {
  if (metric?.state !== "PRESENT") return metric?.state ?? "UNAVAILABLE";
  const value = metric.value;
  if (metric.units === "bytes" && Number.isFinite(value)) return `${(value / (1024 * 1024)).toFixed(1)} MiB`;
  return `${value}${metric.units ? ` ${metric.units}` : ""}`;
}

function metricRows(t, profile) {
  const labels = {
    used: "used", budget: "budget", hits: "hits", misses: "misses", requalifications: "requalifications",
  };
  return Object.entries(profile.metrics).map(([key, metric]) => `<tr data-test-id="memory-production-metric-${key}"><th scope="row">${esc(t(`memory.production.${labels[key]}`))}</th><td>${esc(metricValue(metric))}</td><td>${esc(metric.state)}</td></tr>`).join("");
}

function overview(t, profile, locale) {
  const observed = profile.observedAt == null
    ? `<span data-test-id="memory-production-time-unavailable">${esc(t("foundation.temporal.unavailable"))}</span>`
    : temporalMarkup({ unixSeconds: profile.observedAt, locale, testId: "memory-production-time" });
  return `<section class="memory-surface" data-test-id="memory-production-overview"><header class="memory-section-heading"><div><span class="eyebrow">${esc(t("memory.summary.eyebrow"))}</span><h3>${esc(t("memory.summary.title"))}</h3></div><div class="memory-heading-tools">${help(t, "metrics", "metrics")}${help(t, "time", "time")}</div></header><dl class="memory-production-context"><div><dt>${esc(t("memory.production.generation"))}</dt><dd>${esc(profile.generation ?? "UNAVAILABLE")}</dd></div><div><dt>${esc(t("memory.production.observed"))}</dt><dd>${observed}</dd></div></dl><div class="memory-table-wrap" tabindex="0" role="region" aria-label="${esc(t("memory.summary.title"))}"><table class="memory-slot-table"><thead><tr><th>${esc(t("memory.production.metric"))}</th><th>${esc(t("memory.production.metricValue"))}</th><th>${esc(t("memory.production.metricState"))}</th></tr></thead><tbody>${metricRows(t, profile)}</tbody></table></div><button type="button" class="${controlClass("inspect")}" data-memory-production-inspect data-test-id="memory-production-inspect">Inspect source record</button></section>`;
}

function atlas(t) {
  return `<section class="memory-surface" data-test-id="memory-production-atlas"><header class="memory-section-heading"><div><span class="eyebrow">${esc(t("memory.atlas.eyebrow"))}</span><h3>${esc(t("memory.atlas.title"))}</h3></div><div class="memory-heading-tools">${help(t, "identity", "identity")}${help(t, "allocation", "allocation")}</div></header>${stateMarkup({ title: t("memory.value.unavailable"), detail: t("memory.production.atlasUnavailable"), testId: "memory-production-atlas-state" })}</section>`;
}

function dossier(t) {
  return `<section class="memory-surface" data-test-id="memory-production-dossier"><header class="memory-section-heading"><div><span class="eyebrow">${esc(t("memory.dossier.eyebrow"))}</span><h3>${esc(t("memory.dossier.title"))}</h3></div><div class="memory-heading-tools">${help(t, "optimizer", "optimizer")}${help(t, "relations", "relations")}${help(t, "correction", "correction")}</div></header>${stateMarkup({ title: t("memory.value.unavailable"), detail: t("memory.production.dossierUnavailable"), testId: "memory-production-dossier-state" })}</section>`;
}

function comparison(t, current, state) {
  const generation = state.comparisonGeneration ?? state.comparison?.generation ?? "";
  const rows = state.comparison ? memoryComparison(state.comparison, current).map(row => `<tr data-test-id="memory-production-comparison-${esc(row.key)}"><th scope="row">${esc(t(`memory.production.${row.key === "used" ? "used" : row.key === "budget" ? "budget" : row.key}`))}</th><td>${esc(metricValue(row.before))}</td><td>${esc(metricValue(row.after))}</td><td>${row.delta == null ? "UNAVAILABLE" : esc(`${row.delta >= 0 ? "+" : ""}${row.delta}`)}</td></tr>`).join("") : "";
  return `<section class="memory-surface" data-test-id="memory-production-comparison"><header class="memory-section-heading"><div><span class="eyebrow">${esc(t("memory.compare.eyebrow"))}</span><h3>${esc(t("memory.compare.title"))}</h3></div><div class="memory-heading-tools">${help(t, "comparison", "comparison")}</div></header><form class="memory-production-compare-form" data-memory-production-compare-form><label>${esc(t("memory.production.compareFrom"))} <input name="generation" data-test-id="memory-production-compare-generation" type="text" inputmode="numeric" pattern="[0-9]+" required value="${esc(generation)}"></label><button class="${controlClass("compare")}" type="submit" data-test-id="memory-production-compare-submit">${esc(t("memory.production.load"))}</button></form><p role="status" data-test-id="memory-production-comparison-status">${state.comparisonGeneration == null ? esc(t("memory.production.compareEmpty")) : esc(t("memory.production.compareRequested", { generation: state.comparisonGeneration, state: state.comparisonState ?? "EMPTY" }))}</p>${rows ? `<div class="memory-table-wrap" tabindex="0"><table class="memory-delta-table"><thead><tr><th>${esc(t("memory.production.metric"))}</th><th>${esc(t("memory.production.before", { generation: state.comparison.generation }))}</th><th>${esc(t("memory.production.current", { generation: current.generation }))}</th><th>${esc(t("memory.production.delta"))}</th></tr></thead><tbody>${rows}</tbody></table></div>` : ""}</section>`;
}

function tabButton(t, id, activeTab) {
  return `<button type="button" role="tab" class="${controlClass("peer-tab")}" id="memory-production-tab-${id}" data-memory-production-tab="${id}" aria-controls="memory-production-panel-${id}" aria-selected="${String(id === activeTab)}" tabindex="${id === activeTab ? "0" : "-1"}" data-test-id="memory-tab-${id}">${esc(t(`memory.tab.${id}`))}</button>`;
}

function panel(id, activeTab, body) {
  return `<section class="memory-tabpanel" role="tabpanel" id="memory-production-panel-${id}" aria-labelledby="memory-production-tab-${id}" data-memory-production-panel="${id}" ${id === activeTab ? "" : "hidden "}data-test-id="memory-panel-${id}">${body}</section>`;
}

export function productionMemoryMarkup(state, { activeTab = "overview", historical = false, locale } = {}) {
  const t = translator(locale);
  const tab = MEMORY_PRODUCTION_TABS.includes(activeTab) ? activeTab : "overview";
  const current = state?.current;
  if (!current) {
    const loading = state?.currentState === "LOADING";
    return `<div class="memory-view" data-test-id="memory-workspace">${stateMarkup({ title: loading ? t("memory.production.loading") : t("memory.production.unavailable"), detail: loading ? "" : t("memory.production.slotUnavailable"), testId: "memory-production-state", kind: loading ? "empty" : "error" })}</div>`;
  }
  return `<div class="memory-view" data-test-id="memory-workspace"><header class="memory-heading"><div><span class="eyebrow">${esc(t("memory.heading.eyebrow"))}</span><h2>${esc(t("memory.heading.title"))}</h2></div><p>${esc(t("memory.heading.summary"))}</p></header><div class="memory-production-posture" data-test-id="memory-production-posture"><strong>${esc(t(historical ? "memory.production.historical" : "memory.production.live"))}</strong><span>${esc(t("memory.production.provenance", { generation: current.generation ?? "UNAVAILABLE" }))}</span></div><div class="memory-tabs" role="tablist" aria-label="${esc(t("memory.tabs.aria"))}" data-test-id="memory-tabs">${MEMORY_PRODUCTION_TABS.map(id => tabButton(t, id, tab)).join("")}</div>${panel("overview", tab, overview(t, current, locale))}${panel("atlas", tab, atlas(t))}${panel("dossier", tab, dossier(t))}${panel("comparison", tab, comparison(t, current, state))}</div>`;
}

export function bindProductionMemory(host, { onTabChange, onCompare, onInspect, state, locale } = {}) {
  const t = translator(locale);
  const tabs = [...host.querySelectorAll("[data-memory-production-tab]")];
  const panels = [...host.querySelectorAll("[data-memory-production-panel]")];
  const activate = (id, focus = false) => {
    if (!MEMORY_PRODUCTION_TABS.includes(id)) return;
    tabs.forEach(tab => {
      const active = tab.dataset.memoryProductionTab === id;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
      if (active && focus) tab.focus?.({ preventScroll: true });
    });
    panels.forEach(panel => { panel.hidden = panel.dataset.memoryProductionPanel !== id; });
    onTabChange?.(id);
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activate(tab.dataset.memoryProductionTab));
    tab.addEventListener("keydown", event => {
      const next = event.key === "ArrowRight" ? (index + 1) % tabs.length : event.key === "ArrowLeft" ? (index - 1 + tabs.length) % tabs.length : event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : null;
      if (next === null) return;
      event.preventDefault();
      activate(tabs[next].dataset.memoryProductionTab, true);
    });
  });
  const form = host.querySelector("[data-memory-production-compare-form]");
  form?.elements?.generation?.addEventListener?.("input", event => event.target.setCustomValidity(""));
  form?.addEventListener("submit", event => {
    event.preventDefault();
    const input = event.currentTarget.elements.generation;
    const raw = input.value.trim();
    const generation = Number(raw);
    if (!/^[0-9]+$/.test(raw) || !Number.isSafeInteger(generation) || generation < 0) {
      input.setCustomValidity(t("memory.production.invalidGeneration"));
      input.reportValidity?.();
      return;
    }
    input.setCustomValidity("");
    onCompare?.(generation);
  });
  host.querySelector("[data-memory-production-inspect]")?.addEventListener("click", () => {
    const profile = state?.current;
    if (!profile) return;
    onInspect?.({ kind: "memory", id: profile.recordId ?? `memory:g${profile.generation}`, details: {
      [t("memory.production.inspector.record")]: profile.recordId ?? "UNAVAILABLE",
      [t("memory.production.inspector.generation")]: profile.generation ?? "UNAVAILABLE",
      [t("memory.production.inspector.observed")]: profile.observedAt ?? "UNAVAILABLE",
      [t("memory.production.inspector.sourceRefs")]: profile.sourceRefs,
      [t("memory.production.inspector.evidenceRefs")]: profile.evidenceRefs,
      [t("memory.production.inspector.receiptRefs")]: profile.receiptRefs,
    } });
  });
}
