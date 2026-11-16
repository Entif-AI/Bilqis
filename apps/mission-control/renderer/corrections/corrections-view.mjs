import { createTranslator } from "../foundation/i18n.mjs";
import { contextHelpMarkup, controlClass } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { escapeText as esc } from "../frames/frame-model.mjs";
import {
  assertReceiptBackedTerminalStates, evidencedDescendants, impactRows,
  requalificationQueue, unknownInfluenceRows,
} from "./corrections-model.mjs";
import { CORRECTION_MESSAGES } from "./corrections-messages.mjs";

export const CORRECTION_TABS = Object.freeze(["context", "impact", "queue", "history"]);

function hook(scope, identity = "") {
  const suffix = identity === "" ? "" : `-${Array.from(String(identity), char => char.codePointAt(0).toString(16)).join("-")}`;
  return `corrections-${scope}${suffix}`;
}

function help(t, id, key) {
  return contextHelpMarkup({ label: t(`corrections.help.${key}.label`), description: t(`corrections.help.${key}.body`), testId: `corrections-help-${id}` });
}

function stateBadge(state, t) {
  const key = `corrections.state.${state}`;
  let label;
  try { label = t(key); } catch (error) { if (!(error instanceof RangeError)) throw error; label = t("corrections.state.unknown", { state }); }
  return `<span class="correction-state" data-correction-state="${esc(state)}">${esc(label)}</span>`;
}

function inspectNode(node, scope) {
  const id = hook(scope, node.id);
  return `<button type="button" class="${controlClass("link")} correction-artifact" data-test-id="${id}" data-focus-key="${id}" data-correction-node="${esc(node.id)}"><code>${esc(node.id)}</code></button>`;
}

function references(values, scope, t, kind = "reference", owner = "") {
  if (!values?.length) return `<span class="correction-untracked">${esc(t("corrections.evidence.none"))}</span>`;
  return `<ul class="correction-refs">${values.map((ref, index) => `<li><button type="button" class="${controlClass("link")}" data-test-id="${hook(scope, `${owner}:${index}:${ref}`)}" data-focus-key="${hook(scope, `${owner}:${index}:${ref}`)}" data-correction-ref="${esc(ref)}" data-correction-ref-kind="${kind}"><span>${esc(t(`corrections.inspect.${kind}`))}</span><code>${esc(ref)}</code></button></li>`).join("")}</ul>`;
}

function tableWrap(id, caption, head, rows, t) {
  return `<div class="correction-table-wrap" data-test-id="${id}-scroll" tabindex="0" role="region" aria-label="${esc(caption)}"><table data-test-id="${id}"><caption>${esc(caption)}</caption><thead><tr>${head.map(label => `<th scope="col">${esc(label)}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table></div><p class="correction-scroll-hint">${esc(t("corrections.table.scroll"))}</p>`;
}

function graphMarkup(t, projection) {
  const nodes = new Map(evidencedDescendants(projection).map(node => [node.id, node]));
  const edges = projection.edges ?? [];
  if (!edges.length) return `<p class="correction-muted">${esc(t("corrections.impact.unavailable"))}</p>`;
  const endpoint = (id, scope) => {
    const node = nodes.get(id) ?? projection.nodes.find(item => item.id === id);
    if (!node) return `<code>${esc(id)}</code>`;
    return `<article class="correction-endpoint" data-test-id="${hook("graph-endpoint", `${scope}:${node.id}`)}"><span>${esc(node.kind)}</span><span>${esc(node.label)}</span>${inspectNode(node, scope)}${stateBadge(node.state, t)}<span>${esc(t("corrections.evidence.count", { count: node.evidenceRefs.length }))}</span></article>`;
  };
  return `<details class="correction-graph-disclosure" data-test-id="corrections-graph"><summary data-test-id="corrections-graph-toggle">${esc(t("corrections.graph.toggle", { count: edges.length }))}</summary>${help(t, "graph", "graph")}<ol class="correction-graph" aria-label="${esc(t("corrections.graph.label"))}" data-test-id="corrections-graph-edges">${edges.map((edge, index) => `<li data-test-id="${hook("graph-edge", `${index}:${edge.from}:${edge.to}`)}"><div><span class="correction-endpoint-label">${esc(t("corrections.graph.from"))}</span>${endpoint(edge.from, `graph-from-${index}`)}</div><div class="correction-relation"><span aria-hidden="true">→</span><code>${esc(edge.relation)}</code><span aria-hidden="true">→</span></div><div><span class="correction-endpoint-label">${esc(t("corrections.graph.to"))}</span>${endpoint(edge.to, `graph-to-${index}`)}</div></li>`).join("")}</ol>${tableWrap("corrections-edge-table", t("corrections.graph.edgeTable"), [t("corrections.graph.from"), t("corrections.graph.relation"), t("corrections.graph.to")], edges.map(edge => `<tr><td><code>${esc(edge.from)}</code></td><td><code>${esc(edge.relation)}</code></td><td><code>${esc(edge.to)}</code></td></tr>`).join(""), t)}</details>`;
}

function contextMarkup(t, projection, locale) {
  const correction = projection.correction;
  if (!correction) return `<section class="correction-panel"><h3>${esc(t("corrections.state.unavailableTitle"))}</h3><p>${esc(t("corrections.state.unavailableBody"))}</p></section>`;
  const rows = [
    ["id", correction.id, null], ["before", correction.priorRevision, help(t, "prior", "prior")],
    ["after", correction.currentRevision, help(t, "current", "current")],
    ["generation", correction.correctionGeneration, help(t, "generation", "generation")],
    ["unknown", t("corrections.context.unknownCount", { count: unknownInfluenceRows(projection).length }), help(t, "unknown", "unknown")],
  ];
  const time = correction.observedAt == null ? "" : `<div class="correction-observed"><span>${esc(t("corrections.history.observed"))}</span>${temporalMarkup({ unixSeconds: correction.observedAt, locale, testId: "corrections-context-time" })}</div>`;
  const sourceRefs = [correction.sourceReference].filter(Boolean);
  const receipts = [correction.sourceReceipt, correction.recordedReceipt].filter(Boolean);
  return `<section class="correction-context" data-test-id="corrections-context"><header><h3>${esc(t("corrections.context.title"))}</h3>${help(t, "provenance", "provenance")}</header><dl>${rows.map(([key, value, helper]) => `<dt>${esc(t(`corrections.context.${key}`))}${helper ?? ""}</dt><dd>${typeof value === "number" ? esc(value) : `<code>${esc(value)}</code>`}</dd>`).join("")}</dl>${time}<details data-test-id="corrections-context-receipts"><summary data-test-id="corrections-context-receipts-toggle">${esc(t("corrections.context.receipts"))}</summary>${help(t, "references-context", "references")}${references(sourceRefs, "context-source", t, "reference", correction.id)}${references(receipts, "context-receipt", t, "receipt", correction.id)}</details></section>`;
}

function impactMarkup(t, projection) {
  const nodes = evidencedDescendants(projection);
  const rows = impactRows(projection).map(row => `<tr data-test-id="${hook("impact-row", row.id)}"><th scope="row">${inspectNode(row, "artifact")}</th><td>${esc(row.kind)}</td><td>${stateBadge(row.state, t)}</td><td>${references(row.evidenceRefs, "artifact-ref", t, "reference", row.id)}</td></tr>`).join("");
  return `<section class="correction-impact" data-test-id="corrections-impact"><header><h3>${esc(t("corrections.impact.title"))}</h3><div class="correction-panel-tools">${help(t, "impact", "impact")}<p>${esc(t("corrections.impact.summary", { artifacts: nodes.length, edges: projection.edges?.length ?? 0 }))}</p></div></header><p>${esc(t("corrections.impact.boundary"))}</p>${graphMarkup(t, projection)}${rows ? tableWrap("corrections-impact-table", t("corrections.table.caption"), ["identity", "class", "state", "evidence"].map(key => t(`corrections.table.${key}`)), rows, t) : ""}</section>`;
}

function queueMarkup(t, projection) {
  const tasks = requalificationQueue(projection);
  const rows = tasks.map(task => `<tr data-test-id="${hook("task", task.id)}"><th scope="row"><code>${esc(task.id)}</code></th><td>${esc(t(`corrections.urgency.${task.urgency}`))}</td><td>${task.owner === "UNTRACKED" ? esc(t("corrections.owner.untracked")) : `<code>${esc(task.owner)}</code>`}</td><td>${stateBadge(task.status, t)}</td><td><span>${esc(t("corrections.queue.generation", { generation: task.generation }))}</span><details data-test-id="${hook("custody", task.id)}"><summary data-test-id="${hook("custody-toggle", task.id)}">${esc(t("corrections.queue.details"))}</summary><dl><dt>${esc(t("corrections.queue.checkpoint"))}</dt><dd><code>${esc(task.checkpoint)}</code></dd><dt>${esc(t("corrections.queue.revision"))}</dt><dd><code>${esc(task.sourceRevision)}</code></dd><dt>${esc(t("corrections.queue.implicated"))}</dt><dd>${task.implicatedRefs.map(ref => `<code>${esc(ref)}</code>`).join("<br>")}</dd></dl></details></td><td>${references(task.evidenceRefs, "task-evidence", t, "reference", task.id)}${task.receiptRefs.length ? references(task.receiptRefs, "task-receipt", t, "receipt", task.id) : `<p class="correction-untracked">${esc(t("corrections.queue.noReceipt"))}</p>`}</td></tr>`).join("");
  return `<section class="correction-queue" data-test-id="corrections-queue"><header><h3>${esc(t("corrections.queue.title"))}</h3>${help(t, "queue", "queue")}</header><p>${esc(t("corrections.queue.summary"))}</p>${rows ? tableWrap("corrections-queue-table", t("corrections.queue.caption"), [t("corrections.queue.task"), t("corrections.queue.urgency"), t("corrections.queue.owner"), t("corrections.table.state"), t("corrections.queue.custody"), t("corrections.queue.evidence")], rows, t) : `<p class="correction-muted">${esc(t("corrections.queue.unavailable"))}</p>`}</section>`;
}

function historyMarkup(t, projection, locale) {
  const events = projection.history ?? [];
  return `<section class="correction-history-section" data-test-id="corrections-history"><h3>${esc(t("corrections.history.title"))}</h3><p>${esc(t("corrections.history.summary"))}</p><ol class="correction-history">${events.map(entry => `<li data-test-id="${hook("history", entry.id)}"><header><h4>${esc(t(`corrections.phase.${entry.phase}`))}</h4>${entry.atGeneration == null ? "" : `<span>${esc(t("corrections.history.generation", { generation: entry.atGeneration }))}</span>`}${entry.observedAt == null ? "" : temporalMarkup({ unixSeconds: entry.observedAt, locale, testId: hook("history-time", entry.id) })}</header><code>${esc(entry.id)}</code>${references(entry.receipt ? [entry.receipt] : [], "history-receipt", t, "receipt", entry.id)}<dl aria-label="${esc(t("corrections.history.states"))}">${Object.entries(entry.states).map(([id, state]) => `<dt><code>${esc(id)}</code></dt><dd>${stateBadge(state, t)}</dd>`).join("")}</dl></li>`).join("") || `<li>${esc(t("corrections.history.empty"))}</li>`}</ol></section>`;
}

function tabPanel(id, active, body) {
  return `<section class="correction-tabpanel" role="tabpanel" id="corrections-panel-${id}" aria-labelledby="corrections-tab-${id}" data-correction-panel="${id}" ${id === active ? "" : "hidden "}data-test-id="corrections-panel-${id}">${body}</section>`;
}

export function renderCorrectionsMarkup(projection, { locale, messages = CORRECTION_MESSAGES, activeTab = "context", fixtureNotice = null } = {}) {
  const t = createTranslator({ locale, messages });
  const tab = CORRECTION_TABS.includes(activeTab) ? activeTab : "context";
  assertReceiptBackedTerminalStates(projection);
  const panels = { context: contextMarkup(t, projection, locale), impact: impactMarkup(t, projection), queue: queueMarkup(t, projection), history: historyMarkup(t, projection, locale) };
  const postureKey = projection.posture === "historical" ? "historical" : "live";
  return `<div class="corrections-view" data-test-id="corrections-workspace"><header class="corrections-heading"><div><h2>${esc(t("corrections.title"))}</h2><p data-test-id="corrections-provenance">${esc(t(`corrections.posture.${postureKey}`, { generation: projection.generation ?? "" }))}</p></div>${help(t, "route-provenance", "provenance")}</header>${fixtureNotice ?? ""}<div class="correction-tabs" role="tablist" aria-label="${esc(t("corrections.tabs.aria"))}" data-test-id="corrections-tabs">${CORRECTION_TABS.map(id => `<button type="button" role="tab" class="${controlClass("peer-tab")}" id="corrections-tab-${id}" data-correction-tab="${id}" aria-controls="corrections-panel-${id}" aria-selected="${String(id === tab)}" tabindex="${id === tab ? "0" : "-1"}" data-test-id="corrections-tab-${id}">${esc(t(`corrections.tab.${id}`))}</button>`).join("")}</div>${CORRECTION_TABS.map(id => tabPanel(id, tab, panels[id])).join("")}</div>`;
}

export function bindCorrectionsInteractions(host, projection, { onInspect, onReference, onTabChange } = {}) {
  const tabs = [...host.querySelectorAll("[data-correction-tab]")]; const panels = [...host.querySelectorAll("[data-correction-panel]")];
  const activate = (id, focus = false) => {
    if (!CORRECTION_TABS.includes(id)) return;
    tabs.forEach(tab => { const selected = tab.dataset.correctionTab === id; tab.setAttribute("aria-selected", String(selected)); tab.tabIndex = selected ? 0 : -1; if (selected && focus) tab.focus({ preventScroll: true }); });
    panels.forEach(panel => { panel.hidden = panel.dataset.correctionPanel !== id; }); onTabChange?.(id);
  };
  tabs.forEach((tab, index) => tab.addEventListener("keydown", event => { let next = null; if (event.key === "ArrowRight") next = (index + 1) % tabs.length; if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length; if (event.key === "Home") next = 0; if (event.key === "End") next = tabs.length - 1; if (next === null) return; event.preventDefault(); activate(tabs[next].dataset.correctionTab, true); }));
  tabs.forEach(tab => tab.addEventListener("click", () => activate(tab.dataset.correctionTab)));
  host.querySelectorAll("[data-correction-node]").forEach(button => button.addEventListener("click", () => { const node = projection.nodes.find(item => item.id === button.dataset.correctionNode); if (node) onInspect?.(node.id, node); }));
  host.querySelectorAll("[data-correction-ref]").forEach(button => button.addEventListener("click", () => onReference?.(button.dataset.correctionRef, button.dataset.correctionRefKind)));
}
