import { createTranslator } from "../foundation/i18n.mjs";
import { contextHelpMarkup, controlClass } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { decomposition, resourceComparison } from "./resource-model.mjs";
import { RESOURCE_MESSAGES } from "./resource-messages.mjs";
import { esc, stateText, bytes, metricValue, badge, unit } from "./resource-format.mjs";

export const RESOURCE_TABS = Object.freeze(["overview", "compute", "timeline", "comparison"]);

const summaryKeys = ["unifiedMemoryUsed", "unifiedMemoryBudget", "forecastMemoryPeak"];
const computeKeys = ["mlxAllocatedMemory", "mlxCacheMemory", "cpuUtilization", "preparationWorkers", "diskFree", "diskUsed", "diskReserve", "candidateSnapshotFootprint", "acceptedStepsHour", "preparationCompileMs", "mlxWallMs", "monetaryCost"];
const lengthKeys = ["sequenceDensity", "frameDensity", "batchSize", "actualLengthP50", "actualLengthP95", "actualLengthMax"];
const hook = id => `data-test-id="${esc(id)}"`;
const text = (t, key, params) => esc(t(`resource.${key}`, params));

function label(t, type, id) {
  try { return text(t, `${type}.${id}`); }
  catch { return esc(id); }
}

function semantic(metric) {
  return metric?.state === "PRESENT" ? metric.semantic ?? metric.origin ?? "MEASURED" : "UNAVAILABLE";
}

function help(t, id, labelKey, bodyKey) {
  return contextHelpMarkup({
    label: t(`resource.help.${labelKey}.label`),
    description: t(`resource.help.${bodyKey}.body`),
    testId: `resources-help-${id}`,
  });
}

function heading(t, title, helps = [], trailing = "") {
  return `<header class="resource-panel-heading"><h3>${text(t, title)}</h3><div class="resource-panel-tools">${helps.join("")}${trailing}</div></header>`;
}

function metricRows(t, profile, keys, prefix) {
  return keys.map(key => {
    const metric = profile.aggregate[key];
    return `<tr ${hook(`${prefix}-${key}`)}><th scope="row">${label(t, "metric", key)}</th><td>${esc(metricValue(t, metric))}</td><td>${badge(t, semantic(metric), true)}</td><td>${badge(t, metric?.state ?? "UNAVAILABLE")}</td></tr>`;
  }).join("");
}

function table(t, title, rows, id, helps = []) {
  return `<section class="resource-panel" ${hook(id)}>${heading(t, title, helps)}<div class="resource-table-wrap" ${hook(`${id}-scroll`)} tabindex="0" role="region" aria-label="${text(t, title)}"><table class="resource-table"><thead><tr><th ${hook(`${id}-identity`)}>${text(t, "metric")}</th><th>${text(t, "value")}</th><th>${text(t, "semantic")}</th><th>${text(t, "state")}</th></tr></thead><tbody>${rows}</tbody></table></div></section>`;
}

function summary(t, profile) {
  return `<section class="resource-panel" ${hook("resources-summary")}>${heading(t, "summary", [
    help(t, "value-types", "summary", "summary"),
  ], `<span ${hook("resources-page-state")}>${badge(t, profile.pageState ?? "PRESENT")}</span>`)}<div class="resource-summary">${summaryKeys.map(key => {
    const metric = profile.aggregate[key];
    return `<article ${hook(`resources-summary-${key}`)}><span>${label(t, "metric", key)}</span><strong>${esc(metricValue(t, metric))}</strong>${badge(t, semantic(metric), true)}</article>`;
  }).join("")}</div><details ${hook("resources-semantics")}><summary>${text(t, "semantics")}</summary><p>${text(t, "semanticDetail")}</p></details><p class="resource-muted">${text(t, "truth")}</p></section>`;
}

function decompositionPanel(t, profile) {
  const totals = decomposition(profile);
  const state = totals.reconciliationState ?? (totals.aggregate === null ? "UNAVAILABLE" : totals.complete ? "COMPLETE" : "PARTIAL");
  const rows = profile.memoryDecomposition.map((item, index) => `<tr ${hook(`resources-category-${index}`)} data-resource-category="${esc(item.id)}"><th scope="row">${label(t, "category", item.id)}</th><td>${esc(item.state === "PRESENT" ? bytes(t, item.value) : stateText(t, "UNAVAILABLE"))}</td><td>${badge(t, item.state)}</td></tr>`).join("");
  const remainderLabel = totals.remainder < 0 ? "overage" : "remainder";
  return `<section class="resource-panel" ${hook("resources-decomposition")}>${heading(t, "decomposition", [
    help(t, "decomposition", "decomposition", "decomposition"),
  ], badge(t, state))}<div class="resource-table-wrap" ${hook("resources-decomposition-scroll")} tabindex="0" role="region" aria-label="${text(t, "decomposition")}"><table class="resource-table"><thead><tr><th ${hook("resources-decomposition-identity")}>${text(t, "category")}</th><th>${text(t, "value")}</th><th>${text(t, "state")}</th></tr></thead><tbody>${rows}<tr ${hook("resources-remainder")}><th scope="row">${text(t, remainderLabel)}</th><td>${esc(bytes(t, totals.remainder))}</td><td>${badge(t, totals.remainder === null ? "UNAVAILABLE" : totals.complete ? "RECONCILED" : "EXPLICIT_REMAINDER")}</td></tr></tbody></table></div><p class="resource-muted">${text(t, "reconciliation", { sum: bytes(t, totals.allocated), aggregate: bytes(t, totals.aggregate) })}</p></section>`;
}

function timeline(t, profile, locale) {
  const rows = profile.timeline.map((row, index) => `<tr ${hook(`resources-timeline-row-${index}`)}><td><button type="button" class="${controlClass("inspect")}" ${hook(`resources-inspect-${index}`)} data-resource-inspect="${esc(row.id)}">${esc(row.id)}</button><small>${temporalMarkup({ unixSeconds: row.observedAt, locale, testId: `resources-time-${index}` })}</small></td><td>${esc(bytes(t, row.unifiedMemoryUsed))}</td><td>${esc(bytes(t, row.mlxAllocated))}</td><td>${esc(row.batchSize ?? stateText(t, "UNAVAILABLE"))}</td><td>${esc(Number.isFinite(row.sequenceDensity) ? t("resource.format.percent", { value: (row.sequenceDensity * 100).toFixed(1) }) : stateText(t, "UNAVAILABLE"))}</td><td>${esc(row.acceptedStepsHour ?? stateText(t, "UNAVAILABLE"))}</td><td>${esc(row.expansionCount ?? stateText(t, "UNAVAILABLE"))}</td></tr>`).join("");
  return `<section class="resource-panel" ${hook("resources-timeline")}>${heading(t, "timeline", [
    help(t, "timeline", "timeline", "timeline"),
  ])}<p class="resource-muted">${text(t, "timelineNote")}</p>${rows ? `<div class="resource-table-wrap" ${hook("resources-timeline-scroll")} tabindex="0" role="region" aria-label="${text(t, "timeline")}"><table class="resource-table"><thead><tr>${["sample", "memory", "mlx", "batch", "density", "steps", "expansion"].map(key => `<th ${key === "sample" ? hook("resources-timeline-identity") : ""}>${text(t, key)}${key === "sample" ? `<small>${text(t, "timestamp")}</small>` : ""}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table></div>` : `<p>${text(t, "noSamples")}</p>`}</section>`;
}

function comparison(t, current, state) {
  const comparison = state.comparison;
  const generation = state.comparisonGeneration ?? comparison?.generation;
  const status = state.comparisonState ?? "EMPTY";
  const rows = comparison ? resourceComparison(comparison, current).map((row, index) => `<tr ${hook(`resources-comparison-row-${index}`)}><th scope="row">${label(t, "metric", row.key)}</th><td>${esc(metricValue(t, row.before))}</td><td>${esc(metricValue(t, row.after))}</td><td>${row.delta === null ? esc(stateText(t, "UNAVAILABLE")) : esc(t("resource.format.delta", { sign: row.delta >= 0 ? "+" : "", value: Number(row.delta).toFixed(row.after.units === "fraction" ? 3 : 1), unit: unit(t, row.after.units) }))}</td></tr>`).join("") : "";
  return `<section class="resource-panel" ${hook("resources-comparison")}>${heading(t, "compare", [
    help(t, "comparison", "comparison", "comparison"),
  ], badge(t, status))}<form class="resource-compare-form" data-resource-compare-form ${hook("resources-compare-form")}><label>${text(t, "generation")} <input class="resource-compare-input" ${hook("resources-compare-generation")} name="generation" type="text" pattern="[0-9]+" required value="${esc(generation ?? "")}" inputmode="numeric"></label><button class="${controlClass("compare")}" ${hook("resources-compare-submit")} type="submit">${text(t, "load")}</button><span>${text(t, "queryNote")}</span></form><p role="status" ${hook("resources-comparison-status")}>${generation == null ? text(t, "emptyComparison") : text(t, "requested", { generation, state: stateText(t, status) })}</p>${comparison ? `<div class="resource-table-wrap" ${hook("resources-comparison-scroll")} tabindex="0" role="region" aria-label="${text(t, "compare")}"><table class="resource-table"><thead><tr><th ${hook("resources-comparison-identity")}>${text(t, "metric")}</th><th>${text(t, "columnGeneration", { generation: comparison.generation })}</th><th>${text(t, "columnGeneration", { generation: current.generation ?? stateText(t, "UNKNOWN") })}</th><th>${text(t, "delta")}</th></tr></thead><tbody>${rows}</tbody></table></div>` : ""}</section>`;
}

function tabsMarkup(t, activeTab) {
  return RESOURCE_TABS.map(id => `<button type="button" role="tab" class="${controlClass("peer-tab")}" id="resources-tab-${id}" data-resource-tab="${id}" aria-controls="resources-panel-${id}" aria-selected="${String(id === activeTab)}" tabindex="${id === activeTab ? "0" : "-1"}" ${hook(`resources-tab-${id}`)}>${text(t, `tab.${id}`)}</button>`).join("");
}

function tabPanel(id, activeTab, body) {
  return `<section class="resource-tabpanel" role="tabpanel" id="resources-panel-${id}" aria-labelledby="resources-tab-${id}" data-resource-panel="${id}" ${id === activeTab ? "" : "hidden "}${hook(`resources-panel-${id}`)}>${body}</section>`;
}

export function renderResourceMarkup(state, { historical = false, locale, messages = RESOURCE_MESSAGES, activeTab = "overview" } = {}) {
  const t = createTranslator({ locale, messages });
  const current = state?.current;
  const tab = RESOURCE_TABS.includes(activeTab) ? activeTab : "overview";
  if (!current) return `<div class="resource-view" ${hook("resources-view")}><section class="resource-panel"><h2>${text(t, state?.currentState === "LOADING" ? "loading" : "unavailable")}</h2>${badge(t, state?.currentState ?? "UNAVAILABLE")}<p>${text(t, state?.currentState === "LOADING" ? "loadingDetail" : "missing")}</p></section></div>`;
  const provenance = current.provenance === "FIXTURE" ? "fixture" : historical ? "historical" : "live";
  const panels = {
    overview: summary(t, current) + decompositionPanel(t, current),
    compute: table(t, "compute", metricRows(t, current, computeKeys, "resources-compute"), "resources-compute", [
      help(t, "compute", "compute", "compute"),
      help(t, "reserve", "reserve", "reserve"),
    ]) + table(t, "length", metricRows(t, current, lengthKeys, "resources-length"), "resources-length", [
      help(t, "length", "length", "length"),
    ]),
    timeline: timeline(t, current, locale),
    comparison: comparison(t, current, state),
  };
  return `<div class="resource-view" ${hook("resources-view")}><header class="resource-heading"><div><span class="eyebrow">${text(t, "eyebrow")}</span><h2>${text(t, "title")}</h2></div></header><div class="resource-provenance" data-provenance="${esc(current.provenance.toLowerCase())}" ${hook("resources-provenance")}><strong>${text(t, provenance)}</strong><span>${text(t, "provenance", { generation: current.generation ?? stateText(t, "UNKNOWN"), window: current.window === "accepted CP03 resource page" ? t("resource.acceptedWindow") : current.window })}</span></div><div class="resource-tabs" role="tablist" aria-label="${text(t, "tabs.aria")}" ${hook("resources-tabs")}>${tabsMarkup(t, tab)}</div>${RESOURCE_TABS.map(id => tabPanel(id, tab, panels[id])).join("")}</div>`;
}

function bindResourceTabs(host, onTabChange) {
  const tabs = [...host.querySelectorAll("[data-resource-tab]")].filter(tab => tab?.dataset?.resourceTab);
  const panels = [...host.querySelectorAll("[data-resource-panel]")].filter(panel => panel?.dataset?.resourcePanel);
  const activate = (id, focus = false) => {
    if (!RESOURCE_TABS.includes(id)) return;
    tabs.forEach(tab => {
      const selected = tab.dataset.resourceTab === id;
      tab.setAttribute?.("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      if (selected && focus) tab.focus?.({ preventScroll: true });
    });
    panels.forEach(panel => { panel.hidden = panel.dataset.resourcePanel !== id; });
    onTabChange?.(id);
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activate(tab.dataset.resourceTab));
    tab.addEventListener("keydown", event => {
      const key = event.key;
      let next = null;
      if (key === "ArrowRight") next = (index + 1) % tabs.length;
      if (key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
      if (key === "Home") next = 0;
      if (key === "End") next = tabs.length - 1;
      if (next === null) return;
      event.preventDefault();
      activate(tabs[next].dataset.resourceTab, true);
    });
  });
}

export function bindResourceInteractions(host, { onInspect, onCompare, onTabChange, locale, messages = RESOURCE_MESSAGES }) {
  const t = createTranslator({ locale, messages });
  bindResourceTabs(host, onTabChange);
  host.querySelectorAll("[data-resource-inspect]").forEach(button => button.addEventListener("click", () => {
    const sample = host.__resourceState?.current?.timeline?.find(row => row.id === button.dataset.resourceInspect);
    if (!sample) return;
    const pairs = [["episode", sample.episodeId], ["batch", sample.batchId], ["sample", sample.id], ["checkpoint", sample.checkpointId], ["source", sample.sourceWorkload], ["expansion", sample.expansionCount]];
    const details = Object.fromEntries(pairs.filter(([, value]) => value != null).map(([key, value]) => [t(`resource.inspector.${key}`), value]));
    const groups = sample.exactRefGroups ?? { accepted: sample.exactRefs ?? [] };
    for (const [kind, refs] of Object.entries(groups)) refs.forEach((ref, index) => {
      details[t(`resource.inspector.${kind}Ref`, { index: index + 1 })] = ref;
    });
    onInspect?.({ kind: "resource", id: sample.id, details });
  }));
  const form = host.querySelector("[data-resource-compare-form]");
  form?.elements?.generation?.addEventListener?.("input", event => event.target.setCustomValidity(""));
  form?.addEventListener("submit", event => {
    event.preventDefault();
    const input = event.currentTarget.elements.generation;
    const raw = input.value.trim();
    const generation = Number(raw);
    if (!/^[0-9]+$/.test(raw) || !Number.isSafeInteger(generation) || generation < 0) {
      input.setCustomValidity?.(t("resource.invalidGeneration"));
      input.reportValidity?.();
      return;
    }
    input.setCustomValidity?.("");
    onCompare?.(generation);
  });
}
