import {
  FILTERS, exportSchoolCsv, paginateRows, projectRows, selectionNeighborhood,
} from "./school-model.mjs";
import { isActivationKey, nextRovingIndex } from "../foundation/accessibility.mjs";
import { t } from "../foundation/i18n.mjs";
import { assertUniqueTestIds, testIdAttribute } from "../foundation/test-hooks.mjs";
import { objectDomAttributes } from "../interactions/dom-ref.mjs";
import { escapeText as esc } from "../frames/frame-model.mjs";

const ui = {
  filters: new Set(), sortKey: "id", direction: "asc", page: 1, pageSize: 50,
  selectedId: null, groupByFamily: true, secondaryColumns: false,
};

const slug = (value) => String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const present = (value) => value !== null && value !== undefined && value !== "";
const text = (value) => present(value) ? String(value) : t("school.common.notExposed");
const score = (value, total) => present(value) && present(total)
  ? t("school.matrix.score", { value, total })
  : t("school.common.notExposed");
const empty = (value) => value?.length ? value.join(", ") : t("school.common.none");

function capabilityRelations(rows, id) {
  const neighborhood = selectionNeighborhood(rows, id);
  return [
    ...neighborhood.prerequisites.map((relatedId) => ({ kind: "capability", id: relatedId, relation: "prerequisite" })),
    ...neighborhood.dependents.map((relatedId) => ({ kind: "capability", id: relatedId, relation: "dependent" })),
  ];
}

function stateCue(row) {
  if (row.sourceState === "SOURCE_HELD") return "source-held";
  if (row.implementationState === "IMPLEMENTATION_UNCOVERED") return "implementation-uncovered";
  if (row.qualificationState === "QUALIFIED") return "qualified";
  if (row.lifecycleState === "EXPOSED") return "exposed";
  if (!row.sourceState && !row.implementationState) return "projected";
  return "staged";
}

function statusCell(row) {
  return `<div class="school-state-stack">
    <span data-school-state="${esc(row.sourceState ?? "NOT_EXPOSED")}">${esc(text(row.sourceState))}</span>
    <span data-school-state="${esc(row.implementationState ?? "NOT_EXPOSED")}">${esc(text(row.implementationState))}</span>
    <span data-school-state="${esc(row.qualificationState ?? "NOT_EXPOSED")}">${esc(text(row.qualificationState))}</span>
  </div>`;
}

function visibleColumns() {
  const core = [
    ["id", "school.matrix.column.capability", "text"],
    ["grade", "school.matrix.column.grade", "text"],
    ["prerequisites", "school.matrix.column.prerequisites", "text"],
    ["was", "school.matrix.column.was", "num"], ["top", "school.matrix.column.top", "num"],
    ["now", "school.matrix.column.now", "num"], ["total", "school.matrix.column.all", "num"],
    ["growth", "school.matrix.column.growth", "num"], ["debt", "school.matrix.column.debt", "num"],
    ["pRet", "school.matrix.column.pret", "num"],
  ];
  const secondary = [
    ["visits", "school.matrix.column.visits", "num"], ["retainedSteps", "school.matrix.column.retainedSteps", "num"],
    ["lastGain", "school.matrix.column.lastGain", "text"], ["lastRegression", "school.matrix.column.lastRegression", "text"],
    ["strategy", "school.matrix.column.strategy", "text"], ["sourceFamilies", "school.matrix.column.sources", "text"],
  ];
  return [...core, ...(ui.secondaryColumns ? secondary : [])];
}

function cell(row, key, kind) {
  if (key === "id") return `<th class="capability-cell" scope="row"><button type="button" data-select-capability="${esc(row.id)}" data-focus-key="school:${esc(row.id)}" ${testIdAttribute("school", "matrix", "capability", slug(row.id))} title="${esc(t("school.matrix.inspect", { id: row.id }))}">${esc(row.id)}</button></th>`;
  if (key === "prerequisites") return `<td>${esc(row.prerequisites?.length ? row.prerequisites.join(", ") : t("school.common.notExposed"))}</td>`;
  if (["was", "top", "now"].includes(key)) return `<td class="num">${esc(score(row[key], row.total))}</td>`;
  if (key === "total") return `<td class="num">${esc(text(row.total))}</td>`;
  if (key === "growth") {
    if (!Number.isFinite(row.growth)) return `<td class="num">${esc(t("school.common.notExposed"))}</td>`;
    return `<td class="num" data-delta="${Math.sign(row.growth)}">${row.growth >= 0 ? "+" : ""}${row.growth}</td>`;
  }
  if (key === "pRet") return `<td class="num">${esc(Number.isFinite(row.pRet) ? row.pRet.toFixed(2) : t("school.common.notExposed"))}</td>`;
  if (key === "sourceFamilies") return `<td>${esc(row.sourceFamilies?.length ? row.sourceFamilies.join(", ") : t("school.common.notExposed"))}</td>`;
  return `<td class="${kind === "num" ? "num" : ""}">${esc(text(row[key]))}</td>`;
}

function tableRows(projectedRows, columnCount, allRows) {
  let family = null;
  return projectedRows.map((row) => {
    const familyRows = projectedRows.filter((candidate) => candidate.family === row.family).length;
    const group = ui.groupByFamily && row.family && row.family !== family
      ? `<tr class="family-row"><th colspan="${columnCount + 1}">${esc(t("school.matrix.family", { family: row.family, count: familyRows }))}</th></tr>` : "";
    family = row.family;
    const selected = row.id === ui.selectedId ? "true" : "false";
    return group + `<tr data-capability-id="${esc(row.id)}" data-selected="${selected}" ${testIdAttribute("school", "matrix", "row", slug(row.id))} ${objectDomAttributes({ kind: "capability", id: row.id, relations: capabilityRelations(allRows, row.id) })}>
      ${visibleColumns().map(([key, _label, kind]) => cell(row, key, kind)).join("")}
      <td class="school-state-cell">${statusCell(row)}</td>
    </tr>`;
  }).join("");
}

function sortableHeader(key, labelKey) {
  const label = t(labelKey);
  const ariaSort = ui.sortKey === key ? (ui.direction === "asc" ? "ascending" : "descending") : "none";
  return `<th aria-sort="${ariaSort}"><button type="button" data-sort-key="${key}" data-focus-key="sort:${key}" ${testIdAttribute("school", "sort", slug(key))}>${t("school.matrix.sort", { label })}<span aria-hidden="true">${ui.sortKey === key ? (ui.direction === "asc" ? " ↑" : " ↓") : ""}</span></button></th>`;
}

function matrix(projectedRows, page, allRows) {
  const columns = visibleColumns();
  const activityCount = ui.secondaryColumns ? 6 : 0;
  return `<section class="school-panel matrix-panel" ${testIdAttribute("school", "matrix")}>
    <header><div><span class="eyebrow">${t("school.matrix.eyebrow")}</span><h2>${t("school.matrix.title")}</h2></div><div class="coverage-counter">${t("school.matrix.range", { start: page.start + 1, end: page.end, total: page.total })}</div></header>
    <div class="matrix-overflow-cue" aria-hidden="true">${t("school.matrix.scrollHint")}</div>
    <div class="matrix-scroll scroll-surface" role="region" aria-label="${t("school.matrix.aria")}" tabindex="0" ${testIdAttribute("school", "matrix", "scroll")}>
      <table class="school-matrix" ${testIdAttribute("school", "matrix", "table")}>
        <thead><tr class="matrix-groups"><th colspan="3">${t("school.matrix.group.identity")}</th><th colspan="4">${t("school.matrix.group.score")}</th><th colspan="3">${t("school.matrix.group.learning")}</th>${activityCount ? `<th colspan="${activityCount}">${t("school.matrix.group.activity")}</th>` : ""}<th>${t("school.matrix.group.provenance")}</th></tr>
        <tr>${columns.map(([key, label]) => sortableHeader(key, label)).join("")}<th>${t("school.matrix.column.state")}</th></tr></thead>
        <tbody>${tableRows(projectedRows, columns.length, allRows)}</tbody>
      </table>
    </div>
    <footer class="school-pagination" ${testIdAttribute("school", "pagination")}>
      <button type="button" data-page="-1" data-focus-key="page:previous" ${testIdAttribute("school", "page", "previous")} ${page.page <= 1 ? "disabled" : ""}>${t("school.pagination.previous")}</button>
      <span>${t("school.pagination.status", { page: page.page, pages: page.pages, total: page.total })}</span>
      <button type="button" data-page="1" data-focus-key="page:next" ${testIdAttribute("school", "page", "next")} ${page.page >= page.pages ? "disabled" : ""}>${t("school.pagination.next")}</button>
    </footer>
  </section>`;
}

function graphNode(row, neighborhood, index, rows) {
  const isSelected = row.id === neighborhood.selected;
  const relation = isSelected ? "selected" : neighborhood.prerequisites.includes(row.id) ? "prerequisite" : neighborhood.dependents.includes(row.id) ? "dependent" : "other";
  const x = 80 + (index % 3) * 240;
  const y = 50 + Math.floor(index / 3) * 100;
  const unlocks = rows.filter((candidate) => candidate.prerequisites.includes(row.id)).length;
  const eligibility = (row.sourceState === "SOURCE_HELD" || row.implementationState === "IMPLEMENTATION_UNCOVERED") ? "blocked" : row.lifecycleState === "READY" ? "eligible" : "other";
  const mastery = row.qualificationState === "QUALIFIED" ? "mastered" : "learning";
  const debt = row.observedDebt ? row.debt : t("school.common.notMeasured");
  const state = row.sourceState === "SOURCE_HELD" ? row.sourceState : row.implementationState === "IMPLEMENTATION_UNCOVERED" ? row.implementationState : row.lifecycleState;
  const stateText = t("school.dependency.nodeState", { state, debt, unlocks });
  const accessibleName = `${row.id}${stateText}`;
  return `<g class="dependency-node" data-capability-id="${esc(row.id)}" ${testIdAttribute("school", "graph", "node", slug(row.id))} ${objectDomAttributes({ kind: "capability", id: row.id, relations: capabilityRelations(rows, row.id) })} data-focus-key="graph:${esc(row.id)}" data-relation="${relation}" data-state="${stateCue(row)}" data-lifecycle="${esc(row.lifecycleState)}" data-eligibility="${eligibility}" data-mastery="${mastery}" data-observed-debt="${row.observedDebt}" tabindex="0" role="button" aria-pressed="${isSelected}" aria-label="${esc(accessibleName)}" transform="translate(${x} ${y})">
    <rect width="190" height="62" rx="4"></rect>
    <text x="12" y="24">${esc(row.id)}</text><text class="node-state" x="12" y="44">${esc(stateText)}</text></g>`;
}

function graphEdges(neighborhood, rows) {
  const selected = rows.findIndex((row) => row.id === neighborhood.selected);
  if (selected < 0) return "";
  const sx = 80 + (selected % 3) * 240 + 95;
  const sy = 50 + Math.floor(selected / 3) * 100 + 31;
  return [...neighborhood.prerequisites, ...neighborhood.dependents].map((id) => {
    const index = rows.findIndex((row) => row.id === id);
    if (index < 0) return "";
    return `<line x1="${sx}" y1="${sy}" x2="${80 + (index % 3) * 240 + 95}" y2="${50 + Math.floor(index / 3) * 100 + 31}" data-edge-to="${id}"></line>`;
  }).join("");
}

function dependencyTable(neighborhood) {
  const relationRows = [
    ...neighborhood.prerequisites.map((id) => ["prerequisite", id]),
    ...neighborhood.dependents.map((id) => ["dependent", id]),
  ];
  return `<div class="dependency-table-wrap" ${testIdAttribute("school", "dependency", "table")}><table class="dependency-fallback"><caption>${esc(t("school.dependency.caption", { id: neighborhood.selected }))}</caption><thead><tr><th>${esc(t("school.dependency.column.relation"))}</th><th>${esc(t("school.dependency.column.capability"))}</th></tr></thead><tbody>
    ${relationRows.map(([relation, id]) => `<tr><td>${esc(t(`school.dependency.relation.${relation}`))}</td><td><button type="button" data-select-capability="${esc(id)}" data-focus-key="dependency-table:${esc(id)}" ${testIdAttribute("school", "dependency", "row", slug(id))}>${esc(id)}</button></td></tr>`).join("") || `<tr><td colspan="2">${esc(t("school.dependency.empty"))}</td></tr>`}
  </tbody></table></div>`;
}

function dependencyView(rows, topologyAvailable) {
  if (!topologyAvailable) {
    return `<section class="school-panel graph-panel school-topology-unavailable" ${testIdAttribute("school", "dependency")}><header><div><span class="eyebrow">${esc(t("school.dependency.eyebrow"))}</span><h2>${esc(t("school.dependency.graphTitle"))}</h2></div></header><p>${esc(t("school.dependency.productionUnavailable"))}</p></section>`;
  }
  const neighborhood = selectionNeighborhood(rows, ui.selectedId);
  return `<section class="school-panel graph-panel" ${testIdAttribute("school", "dependency")}><header><div><span class="eyebrow">${esc(t("school.dependency.eyebrow"))}</span><h2>${esc(t("school.dependency.graphTitle"))}</h2></div><div class="graph-legend" aria-label="${esc(t("school.dependency.legend"))}"><span><i data-edge="source"></i>${esc(t("school.dependency.legend.qualified"))}</span><span><i data-edge="held"></i>${esc(t("school.dependency.legend.held"))}</span><span><i data-edge="derived"></i>${esc(t("school.dependency.legend.uncovered"))}</span><span><i data-edge="selected"></i>${esc(t("school.dependency.legend.selected"))}</span></div></header>
    <p id="school-graph-summary" class="graph-guidance">${esc(t("school.dependency.summary"))}</p>
    <div class="dependency-peers"><div class="dependency-graph-wrap"><svg class="school-graph" viewBox="0 0 760 360" role="group" aria-label="${esc(t("school.dependency.aria"))}" aria-describedby="school-graph-summary" ${testIdAttribute("school", "dependency", "graph")}>${graphEdges(neighborhood, rows)}${rows.map((row, index) => graphNode(row, neighborhood, index, rows)).join("")}</svg></div>${dependencyTable(neighborhood)}</div>
  </section>`;
}

function filterBar(projectedRows, rows) {
  const familyAvailable = rows.some((row) => present(row.family));
  return `<div class="school-controls" ${testIdAttribute("school", "controls")}>
    <fieldset class="filter-set"><legend>${t("school.controls.filters")}</legend>${FILTERS.map((filter) => `<button type="button" data-filter="${filter}" data-focus-key="filter:${filter}" ${testIdAttribute("school", "filter", slug(filter))} aria-pressed="${ui.filters.has(filter)}">${t(`school.filter.${filter}`)}</button>`).join("")}</fieldset>
    <label class="school-group-control"><input type="checkbox" data-group-family data-focus-key="group:family" ${testIdAttribute("school", "group", "family")} ${ui.groupByFamily ? "checked" : ""} ${familyAvailable ? "" : "disabled"}/> ${esc(familyAvailable ? t("school.controls.groupFamily") : t("school.controls.groupFamilyUnavailable"))}</label>
    <button type="button" class="school-column-control" data-toggle-columns data-focus-key="columns:toggle" ${testIdAttribute("school", "columns", "toggle")} aria-pressed="${ui.secondaryColumns}">${t(ui.secondaryColumns ? "school.controls.hideSecondary" : "school.controls.showSecondary")}</button>
    <button type="button" class="school-export-control" data-export data-focus-key="school:export" ${testIdAttribute("school", "export")}>${t("school.controls.export", { count: projectedRows.length })}</button>
  </div>`;
}

function restoreSchoolFocus(container, key) {
  [...container.querySelectorAll("[data-focus-key]")].find((candidate) => candidate.dataset.focusKey === key)?.focus();
}

function rerenderFrom(container, inspectCapability, control, viewState) {
  const key = control?.dataset?.focusKey;
  renderSchoolView(container, inspectCapability, viewState);
  if (key) restoreSchoolFocus(container, key);
}

function bind(container, inspectCapability, viewState) {
  container.querySelectorAll("[data-filter]").forEach((button) => button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    ui.filters.has(filter) ? ui.filters.delete(filter) : ui.filters.add(filter);
    ui.page = 1; rerenderFrom(container, inspectCapability, button, viewState);
  }));
  container.querySelectorAll("[data-sort-key]").forEach((button) => button.addEventListener("click", () => {
    const key = button.dataset.sortKey;
    ui.direction = ui.sortKey === key && ui.direction === "asc" ? "desc" : "asc";
    ui.sortKey = key; rerenderFrom(container, inspectCapability, button, viewState);
  }));
  container.querySelectorAll("[data-page]").forEach((button) => button.addEventListener("click", () => {
    ui.page += Number(button.dataset.page); rerenderFrom(container, inspectCapability, button, viewState);
  }));
  container.querySelector("[data-group-family]")?.addEventListener("change", (event) => {
    ui.groupByFamily = event.currentTarget.checked; rerenderFrom(container, inspectCapability, event.currentTarget, viewState);
  });
  container.querySelector("[data-toggle-columns]")?.addEventListener("click", (event) => {
    ui.secondaryColumns = !ui.secondaryColumns; rerenderFrom(container, inspectCapability, event.currentTarget, viewState);
  });
  container.querySelectorAll("[data-select-capability], .dependency-node").forEach((node) => {
    const activate = () => {
      const rows = viewState.rows;
      ui.selectedId = node.dataset.selectCapability ?? node.dataset.capabilityId;
      inspectCapability(ui.selectedId, rows.find((row) => row.id === ui.selectedId), selectionNeighborhood(rows, ui.selectedId));
      renderSchoolView(container, inspectCapability, viewState);
    };
    node.addEventListener("click", activate);
    node.addEventListener("keydown", (event) => { if (isActivationKey(event.key)) { event.preventDefault(); activate(); } });
  });
  const graphNodes = [...container.querySelectorAll(".dependency-node")];
  graphNodes.forEach((node, index) => node.addEventListener("keydown", (event) => {
    const next = nextRovingIndex(index, event.key, graphNodes.length);
    if (next === index) return;
    event.preventDefault(); graphNodes[next]?.focus();
  }));
  container.querySelector("[data-export]")?.addEventListener("click", (event) => {
    const projected = projectRows(viewState.rows, { filters: [...ui.filters], sortKey: ui.sortKey, direction: ui.direction, groupByFamily: ui.groupByFamily });
    const blob = new Blob([exportSchoolCsv(projected)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob); const anchor = document.createElement("a");
    anchor.href = url; anchor.download = "bilqis-school-filtered.csv"; anchor.click(); URL.revokeObjectURL(url);
    event.currentTarget.textContent = t("school.controls.exported", { count: projected.length });
  });
}

export function renderSchoolView(container, inspectCapability, {
  rows = [],
  selectedId = null,
  fixture = false,
  topologyAvailable = false,
  queryState = "PRESENT",
} = {}) {
  const viewState = { rows, selectedId, fixture, topologyAvailable, queryState };
  if (selectedId && rows.some((row) => row.id === selectedId)) ui.selectedId = selectedId;
  if (!rows.some((row) => row.id === ui.selectedId)) ui.selectedId = rows[0]?.id ?? null;
  const projected = projectRows(rows, { filters: [...ui.filters], sortKey: ui.sortKey, direction: ui.direction, groupByFamily: ui.groupByFamily });
  const page = paginateRows(projected, ui.page, ui.pageSize);
  const markup = `<div class="school-view" ${testIdAttribute("school", "root")}>
    <header class="school-heading"><div><span class="eyebrow">${esc(t("school.heading.eyebrow"))}</span><h2>${esc(t("school.heading.title"))}</h2></div><p>${esc(t("school.heading.summary"))}</p></header>
    ${fixture ? `<div class="school-fixture-notice" role="status" ${testIdAttribute("school", "fixture")}><strong>${esc(t("school.fixture.title"))}</strong><span>${esc(t("school.fixture.detail"))}</span></div>` : ""}
    ${rows.length ? filterBar(projected, rows) : ""}
    <div class="ui-glossary" aria-label="${esc(t("school.matrix.aria"))}" ${testIdAttribute("school", "glossary")}><span>${esc(t("school.glossary.was"))}</span><span>${esc(t("school.glossary.top"))}</span><span>${esc(t("school.glossary.now"))}</span><span>${esc(t("school.glossary.all"))}</span><span>${esc(t("school.glossary.pret"))}</span><span>${esc(t("school.glossary.scroll"))}</span></div>
    ${rows.length ? matrix(page.rows, page, rows) : `<section class="school-panel school-empty" ${testIdAttribute("school", "matrix")}><p>${esc(t("school.production.empty", { state: queryState }))}</p></section>`}
    ${dependencyView(rows, topologyAvailable)}
  </div>`;
  assertUniqueTestIds(markup);
  container.innerHTML = markup;
  bind(container, inspectCapability, viewState);
}

export function schoolRowsForTest(rows = []) {
  return rows.map((row) => ({ ...row, prerequisites: [...row.prerequisites] }));
}
