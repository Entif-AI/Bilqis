import {
  blockerExplanation, buildCurriculumGraph, CURRICULUM_NODE_HEIGHT, boundedFamilyExpansion,
  curriculumConsequence, dependentsFor, gradeFamilySummary, nodeRelation, traceSelection,
} from "./curriculum-atlas-model.mjs";
import { curriculumLargeFixture } from "./curriculum-atlas-fixture.mjs";
import { FILTERS } from "./school-model.mjs";
import { t } from "../foundation/i18n.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";

export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

const slug = (value) => String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const none = (values) => values?.length ? values.join(", ") : t("school.common.none");

export function route(view, kind, id) {
  const params = new URLSearchParams({ kind, id });
  return "#/view/" + view + "?" + params.toString();
}

function nodeState(node) {
  if (node.sourceState === "SOURCE_HELD") return "source-held";
  if (node.implementationState === "IMPLEMENTATION_UNCOVERED") return "uncovered";
  if (node.qualificationState === "QUALIFIED") return "qualified";
  if (node.lifecycleState === "EXPOSED") return "active";
  if (node.lifecycleState === "READY") return "eligible";
  return "staged";
}

function nodeStateLabel(node) {
  const state = nodeState(node);
  if (["qualified", "active", "eligible"].includes(state)) return t(`curriculum.node.${state}`);
  if (state === "source-held") return t("curriculum.node.held");
  if (state === "uncovered") return t("curriculum.node.uncovered");
  return node.lifecycleState;
}

function semanticDisplay(node, binding) {
  const concept = binding?.state === "PRESENT" ? binding.concepts[0] : null;
  const preferred = concept?.labels?.find((label) => label.role === "prefLabel") ?? concept?.labels?.[0] ?? null;
  return Object.freeze({
    semanticId: concept?.semantic_id ?? node.semanticId,
    label: preferred?.value ?? node.label,
    authority: t(concept ? "curriculum.authority.sourceCanonical" : "curriculum.authority.fixtureDisplay"),
    sourceLoci: concept?.source_loci ?? [],
  });
}

function bindingReason(reason) {
  if (reason === "Historical reverse capability lookup is not release-bounded by CP03.") return t("curriculum.binding.historicalUnavailable");
  if (reason === "CP03 query capability unavailable.") return t("curriculum.binding.queryUnavailable");
  if (reason === "EXACT_RELEASE_CAPABILITY_BINDING") return t("curriculum.binding.exact");
  if (reason === "NO_EXACT_RELEASE_BINDING") return t("curriculum.binding.missing");
  return reason;
}

export function nodeCard(node, position, trace, visible, binding = null) {
  const display = semanticDisplay(node, binding);
  const relation = nodeRelation(trace, node.id);
  const newLabel = node.newThisGrade ? `<span class="curriculum-new">${esc(t("curriculum.node.new"))}</span>` : "";
  const carryover = position.stratum === "current" && !node.newThisGrade ? `<span class="curriculum-carryover">${esc(t("curriculum.node.carryover"))}</span>` : "";
  const blocked = node.blocker ? `<span class="curriculum-blocker">${esc(node.blocker.code)}</span>` : "";
  return `<button type="button" class="curriculum-node" data-curriculum-node="${esc(node.id)}" data-focus-key="curriculum:${esc(node.id)}" data-relation="${relation}" data-visible="${visible}" data-state="${nodeState(node)}" data-stratum="${position.stratum}" data-x="${position.x}" data-y="${position.y}" aria-pressed="${trace.selectedId === node.id}" ${testIdAttribute("curriculum", "node", slug(node.id))}>
    <span class="curriculum-node-state">${esc(nodeStateLabel(node))}</span>${newLabel}${carryover}
    <strong>${esc(node.id)}</strong><span class="curriculum-node-label">${esc(display.label)}</span>
    <small class="curriculum-node-semantic">${esc(display.semanticId)} · ${esc(display.authority)}</small>
    <small>${esc(t("curriculum.node.meta", { grade: node.grade, lifecycle: node.lifecycleState, debt: node.debt }))}</small>${blocked}
  </button>`;
}

export function edgeMarkup(edge, layout, trace) {
  const source = layout.positions.get(edge.source);
  const target = layout.positions.get(edge.target);
  if (!source || !target) return "";
  const sameColumn = source.x === target.x;
  const sx = source.x + 244;
  const halfNode = CURRICULUM_NODE_HEIGHT / 2;
  const sy = source.y + halfNode;
  const tx = sameColumn ? target.x + 122 : target.x;
  const ty = target.y + halfNode;
  const active = (trace.visibleUpstream.has(edge.source) && (trace.selectedId === edge.target || trace.visibleUpstream.has(edge.target))) ||
    (trace.visibleDownstream.has(edge.target) && (trace.selectedId === edge.source || trace.visibleDownstream.has(edge.source)));
  const path = sameColumn
    ? `M ${source.x + 122} ${source.y + CURRICULUM_NODE_HEIGHT} C ${source.x + 300} ${source.y + CURRICULUM_NODE_HEIGHT + 12}, ${target.x + 300} ${target.y - 8}, ${tx} ${target.y}`
    : `M ${sx} ${sy} C ${sx + 48} ${sy}, ${tx - 48} ${ty}, ${tx} ${ty}`;
  const label = t("curriculum.graph.edgeAria", { source: edge.source, target: edge.target });
  const title = t("curriculum.graph.edgeTitle", { source: edge.source, target: edge.target });
  return `<path d="${path}" data-edge-kind="${edge.kind}" data-authority="${edge.authority}" data-trace="${active ? "active" : "context"}" role="img" aria-label="${esc(label)}"><title>${esc(title)}</title></path>`;
}

export function tableMarkup(graph, visibility, semanticBindings = null, selectedId = null) {
  const body = graph.nodes.map((node) => {
    const dependents = dependentsFor(graph, node.id);
    const display = semanticDisplay(node, semanticBindings?.get?.(node.id));
    return `<tr data-visible="${visibility.get(node.id)}" data-selected="${node.id === selectedId}" ${testIdAttribute("curriculum", "table", "row", slug(node.id))}>
      <th scope="row"><button type="button" data-curriculum-node="${esc(node.id)}" data-focus-key="curriculum-table:${esc(node.id)}" ${testIdAttribute("curriculum", "table", "capability", slug(node.id))}>${esc(node.id)}</button></th>
      <td class="curriculum-semantic-cell"><strong>${esc(display.label)}</strong><span>${esc(display.semanticId)}</span><small>${esc(display.authority)}</small></td>
      <td>${esc(node.grade)}</td><td>${esc(node.lifecycleState)} · ${esc(node.qualificationState)}${node.blocker ? " · " + esc(node.blocker.code) : ""}</td>
      <td>${esc(none(node.prerequisites))}</td><td>${esc(none(dependents))}</td>
      <td class="curriculum-evidence-cell">${esc(t("curriculum.table.evidenceValue", { now: node.now, top: node.top, total: node.total, debt: node.debt }))}</td>
    </tr>`;
  }).join("");
  return `<section class="curriculum-equivalent" ${testIdAttribute("curriculum", "equivalent")}><header><div><span class="eyebrow">${esc(t("curriculum.table.aria"))}</span><h3>${esc(t("curriculum.table.caption"))}</h3></div></header>
    <div class="curriculum-table-wrap" role="region" aria-label="${esc(t("curriculum.table.aria"))}" tabindex="0" ${testIdAttribute("curriculum", "table", "scroll")}>
      <table class="curriculum-table"><caption class="sr-only">${esc(t("curriculum.table.caption"))}</caption><thead><tr>
        <th>${esc(t("curriculum.table.capability"))}</th><th>${esc(t("curriculum.table.semantic"))}</th><th>${esc(t("curriculum.table.grade"))}</th><th>${esc(t("curriculum.table.state"))}</th><th>${esc(t("curriculum.table.prerequisites"))}</th><th>${esc(t("curriculum.table.dependents"))}</th><th>${esc(t("curriculum.table.evidence"))}</th>
      </tr></thead><tbody>${body}</tbody></table>
    </div></section>`;
}

function actionsMarkup(node, semanticBinding, ui) {
  const school = route("school", "capability", node.id);
  const capability = route("capability", "capability", node.id);
  const evidence = route("evidence", "capability", node.id);
  let atlas = `<button type="button" data-resolve-semantic="${esc(node.id)}" data-focus-key="curriculum:resolve-semantic" ${testIdAttribute("curriculum", "action", "resolve")} ${ui.semanticLoading === node.id ? "disabled" : ""}>${esc(t(ui.semanticLoading === node.id ? "curriculum.action.resolving" : "curriculum.action.resolve"))}</button>`;
  if (semanticBinding?.state === "PRESENT") {
    atlas = semanticBinding.concepts.map((concept, index) => `<a href="${route("atlas", "semantic", concept.semantic_id)}" ${testIdAttribute("curriculum", "action", "atlas", index)}>${esc(t("curriculum.action.openAtlas", { id: concept.semantic_id }))}</a>`).join("");
  }
  return `<nav class="curriculum-actions" aria-label="${esc(t("curriculum.dossier.eyebrow"))}">
    <button type="button" data-school-mode="matrix" data-focus-key="school-mode:matrix" ${testIdAttribute("curriculum", "action", "school")}>${esc(t("curriculum.action.openSchool"))}</button>
    <a href="${capability}" ${testIdAttribute("curriculum", "action", "capability")}>${esc(t("curriculum.action.openCapability"))}</a>${atlas}
    <button type="button" disabled title="${esc(t("curriculum.action.lineageTitle"))}" ${testIdAttribute("curriculum", "action", "lineage")}>${esc(t("curriculum.action.lineageUnavailable"))}</button>
    <a href="${evidence}" ${testIdAttribute("curriculum", "action", "evidence")}>${esc(t("curriculum.action.openEvidence"))}</a>
    <a href="${school}" ${testIdAttribute("curriculum", "action", "deep-link")}>${esc(t("curriculum.action.schoolDeepLink"))}</a>
  </nav>`;
}

export function dossierMarkup(graph, node, semanticBinding, ui) {
  const display = semanticDisplay(node, semanticBinding);
  const blocker = node.blocker ? blockerExplanation(node) : null;
  const dependents = dependentsFor(graph, node.id);
  const consequence = curriculumConsequence(graph, node.id);
  const consequenceBody = consequence.byGrade.length
    ? consequence.byGrade.map((group) => `<p>${esc(t("curriculum.dossier.gradeReach", { grade: group.grade, count: group.ids.length, ids: group.ids.join(", ") }))}</p>`).join("")
    : `<p>${esc(t("curriculum.dossier.noLater"))}</p>`;
  const binding = semanticBinding ? `${semanticBinding.state} · ${bindingReason(semanticBinding.reason)}` : t("curriculum.dossier.unresolved");
  return `<section class="curriculum-dossier" aria-labelledby="curriculum-dossier-title" ${testIdAttribute("curriculum", "dossier")}>
    <header><div><span class="eyebrow">${esc(t("curriculum.dossier.eyebrow"))}</span><h2 id="curriculum-dossier-title">${esc(node.id)} · ${esc(node.label)}</h2></div><span class="curriculum-state">${esc(node.lifecycleState)}</span></header>
    <div class="curriculum-dossier-grid"><dl>
      <div><dt>${esc(t("curriculum.dossier.capability"))}</dt><dd>${esc(node.id)}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.semantic"))}</dt><dd>${esc(display.semanticId)} · ${esc(display.label)} · ${esc(display.authority)}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.sourceLoci"))}</dt><dd>${esc(display.sourceLoci.length ? display.sourceLoci.join(", ") : t("school.common.unavailable"))}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.grade"))}</dt><dd>${esc(node.grade)} / ${esc(node.firstIntroducedGrade)}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.lifecycle"))}</dt><dd>${esc(node.lifecycleState)} / ${esc(node.qualificationState)}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.score"))}</dt><dd>${esc(t("curriculum.dossier.scoreValue", { now: node.now, top: node.top, total: node.total, debt: node.debt, pret: node.pRet ?? t("school.common.notMeasured") }))}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.prerequisites"))}</dt><dd>${esc(none(node.prerequisites))}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.directUnlocks"))}</dt><dd>${dependents.length}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.dependents"))}</dt><dd>${esc(none(dependents))}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.transitive"))}</dt><dd>${traceSelection(graph, node.id, "unlocks").downstream.size}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.sourceRefs"))}</dt><dd>${esc(none(node.sourceRefs))}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.release"))}</dt><dd>${esc(t("curriculum.dossier.releaseUnavailable"))}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.lastEvent"))}</dt><dd>${esc(node.lastRelevantEvent)}</dd></div>
      <div><dt>${esc(t("curriculum.dossier.requalification"))}</dt><dd>${esc(node.requalificationState)}</dd></div>
    </dl>
    <div class="curriculum-investigation"><p class="curriculum-rule">${esc(t("curriculum.dossier.rule"))}</p>
      <div class="curriculum-why"><strong>${esc(t("curriculum.dossier.whyBlocked"))}</strong>${blocker ? `<span>${esc(blocker.code)} · ${esc(blocker.detail)}</span><small>${esc(blocker.evidence.length ? blocker.evidence.join(", ") : t("curriculum.dossier.noBlockerEvidence"))}</small>` : `<span>${esc(t("curriculum.dossier.notBlocked"))}</span>`}</div>
      <details class="curriculum-history"><summary>${esc(t("curriculum.dossier.history"))}</summary><ol>${node.historyEvents.map((event) => `<li data-history-posture="${esc(event.posture)}"><span>${esc(event.posture)}</span> · ${esc(event.kind)} · ${esc(event.label)}</li>`).join("")}</ol></details>
      <button type="button" data-consequence-toggle data-focus-key="curriculum:consequence" ${testIdAttribute("curriculum", "consequence", "toggle")} aria-expanded="${ui.consequenceOpen}">${esc(t(ui.consequenceOpen ? "curriculum.dossier.hideConsequence" : "curriculum.dossier.showConsequence"))}</button>
      ${ui.consequenceOpen ? `<div class="curriculum-consequence"><strong>${esc(t("curriculum.dossier.consequence"))}</strong>${consequenceBody}</div>` : ""}
      <div class="semantic-binding"><strong>${esc(t("curriculum.dossier.canonical"))}</strong><span>${esc(binding)}</span></div>
      ${actionsMarkup(node, semanticBinding, ui)}
    </div></div>
  </section>`;
}

export function toolbarMarkup(graph, snapshot, ui) {
  const grades = [...new Set(graph.nodes.map((node) => node.grade))].sort();
  const states = [...new Set(graph.nodes.flatMap((node) => [node.lifecycleState, node.qualificationState]))].sort();
  const families = [...new Set(graph.nodes.map((node) => node.family))].sort();
  const options = (values, selected) => `<option value="all">${esc(t("curriculum.filter.all"))}</option>` + values.map((value) => `<option value="${esc(value)}"${selected === value ? " selected" : ""}>${esc(value)}</option>`).join("");
  const traces = [["prerequisites", "curriculum.trace.prerequisites"], ["both", "curriculum.trace.both"], ["unlocks", "curriculum.trace.unlocks"]];
  return `<section class="curriculum-toolbar" aria-label="${esc(t("curriculum.toolbar.aria"))}" ${testIdAttribute("curriculum", "controls")}>
    <form class="curriculum-search" data-curriculum-search ${testIdAttribute("curriculum", "search")}><label>${esc(t("curriculum.search.label"))}<input name="search" data-focus-key="curriculum:search" ${testIdAttribute("curriculum", "search", "input")} value="${esc(ui.search)}" placeholder="${esc(t("curriculum.search.placeholder"))}" /></label><button type="submit" data-focus-key="curriculum:find" ${testIdAttribute("curriculum", "search", "submit")}>${esc(t("curriculum.search.find"))}</button><button type="button" data-jump-active data-focus-key="curriculum:jump-active" ${testIdAttribute("curriculum", "jump", "active")}>${esc(t("curriculum.search.jumpActive", { id: snapshot.activeId }))}</button></form>
    <fieldset class="trace-controls"><legend>${esc(t("curriculum.trace.label"))}</legend>${traces.map(([id, key]) => `<button type="button" data-trace-mode="${id}" data-focus-key="curriculum:trace:${id}" ${testIdAttribute("curriculum", "trace", id)} aria-pressed="${ui.traceMode === id}">${esc(t(key))}</button>`).join("")}</fieldset>
    <div class="curriculum-filters" ${testIdAttribute("curriculum", "filters")}>
      <label>${esc(t("curriculum.filter.grade"))}<select data-filter="grade" data-focus-key="curriculum:filter:grade" ${testIdAttribute("curriculum", "filter", "grade")}>${options(grades, ui.grade)}</select></label>
      <label>${esc(t("curriculum.filter.state"))}<select data-filter="state" data-focus-key="curriculum:filter:state" ${testIdAttribute("curriculum", "filter", "state")}>${options(states, ui.state)}</select></label>
      <label>${esc(t("curriculum.filter.family"))}<select data-filter="family" data-focus-key="curriculum:filter:family" ${testIdAttribute("curriculum", "filter", "family")}>${options(families, ui.family)}</select></label>
      <label>${esc(t("curriculum.filter.attention"))}<select data-filter="issue" data-focus-key="curriculum:filter:issue" ${testIdAttribute("curriculum", "filter", "attention")}>${[...new Set(["all", "debt", "blocked", ...FILTERS])].map((value) => `<option value="${value}"${ui.issue === value ? " selected" : ""}>${esc(value === "all" ? t("curriculum.filter.all") : t(`school.filter.${value}`) ?? value)}</option>`).join("")}</select></label>
      <label class="curriculum-new-only"><input type="checkbox" data-new-only data-focus-key="curriculum:filter:new" ${testIdAttribute("curriculum", "filter", "new")} ${ui.newOnly ? "checked" : ""}/><span>${esc(t("curriculum.filter.newOnly"))}</span></label>
      <button type="button" data-reset-filters data-focus-key="curriculum:reset" ${testIdAttribute("curriculum", "filter", "reset")}>${esc(t("curriculum.filter.reset"))}</button>
    </div>
  </section>`;
}

export function scaleMarkup(ui) {
  const large = curriculumLargeFixture(243);
  const largeGraph = buildCurriculumGraph({ nodes: large, currentGrade: "C" });
  const preview = gradeFamilySummary(large).slice(0, 12);
  let expansion = "";
  if (ui.familyFocus) {
    const [grade, family] = ui.familyFocus.split("::");
    const expanded = boundedFamilyExpansion(large, grade, family, 12);
    const selected = expanded.find((node) => node.id === ui.largeSelectedId) ?? expanded[0] ?? null;
    const directDependents = selected ? dependentsFor(largeGraph, selected.id) : [];
    const allTransitive = selected ? [...traceSelection(largeGraph, selected.id, "unlocks").downstream] : [];
    const transitive = allTransitive.slice(0, 24);
    expansion = `<div class="curriculum-scale-expansion"><strong>${esc(t("curriculum.scale.expansion", { family: ui.familyFocus }))}</strong><div class="family-summary">${expanded.map((node) => `<button type="button" data-large-semantic="${esc(node.id)}" data-focus-key="curriculum:large:${esc(node.id)}" ${testIdAttribute("curriculum", "scale", "semantic", slug(node.id))}>${esc(node.id)}</button>`).join("")}</div>${selected ? `<p><strong>${esc(t("curriculum.scale.selected", { id: selected.id }))}</strong> · ${esc(t("curriculum.scale.prerequisites", { value: none(selected.prerequisites) }))} · ${esc(t("curriculum.scale.directDependents", { value: none(directDependents) }))}</p><p>${esc(t("curriculum.scale.transitive", { value: none(transitive) }))}${allTransitive.length > transitive.length ? ` · ${esc(t("curriculum.scale.more"))}` : ""}</p>` : ""}</div>`;
  }
  return `<details class="curriculum-scale" ${testIdAttribute("curriculum", "scale")}><summary>${esc(t("curriculum.scale.summary"))}</summary><p>${esc(t("curriculum.scale.detail"))}</p><div class="family-summary">${preview.map((group) => `<button type="button" data-family-focus="${esc(group.grade)}::${esc(group.family)}" data-focus-key="curriculum:family:${esc(group.grade)}:${esc(group.family)}" ${testIdAttribute("curriculum", "scale", "family", slug(group.grade), slug(group.family))}>${esc(t("curriculum.scale.family", { grade: group.grade, family: group.family, count: group.count }))}</button>`).join("")}</div>${expansion}</details>`;
}
