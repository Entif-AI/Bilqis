import {
  FILTERS,
  exportSchoolCsv,
  paginateRows,
  projectRows,
  scoreQuad,
  selectionNeighborhood,
} from "./school-model.mjs";
import { schoolFixtureRows } from "./school-fixture.mjs";
import { isActivationKey, nextRovingIndex } from "../foundation/accessibility.mjs";
import { objectDomAttributes } from "../interactions/dom-ref.mjs";

const rows = schoolFixtureRows();
const ui = {
  filters: new Set(),
  sortKey: "id",
  direction: "asc",
  page: 1,
  pageSize: 50,
  selectedId: "B.AND",
  graphEnabled: true,
  groupByFamily: true,
};

function capabilityRelations(id) {
  const neighborhood = selectionNeighborhood(rows, id);
  return [
    ...neighborhood.prerequisites.map((relatedId) => ({
      kind: "capability", id: relatedId, relation: "prerequisite",
    })),
    ...neighborhood.dependents.map((relatedId) => ({
      kind: "capability", id: relatedId, relation: "dependent",
    })),
  ];
}

function stateCue(row) {
  if (row.sourceState === "SOURCE_HELD") return "source-held";
  if (row.implementationState === "IMPLEMENTATION_UNCOVERED") return "implementation-uncovered";
  if (row.qualificationState === "QUALIFIED") return "qualified";
  if (row.lifecycleState === "EXPOSED") return "exposed";
  return "staged";
}

function statusCell(row) {
  return `<div class="school-state-stack">
    <span data-school-state="${row.sourceState}">${row.sourceState}</span>
    <span data-school-state="${row.implementationState}">${row.implementationState}</span>
    <span data-school-state="${row.qualificationState}">${row.qualificationState}</span>
  </div>`;
}

function tableRows(projectedRows) {
  let family = null;
  return projectedRows.map((row) => {
    const group = ui.groupByFamily && row.family !== family
      ? `<tr class="family-row"><th colspan="18">${row.family.toUpperCase()} family</th></tr>`
      : "";
    family = row.family;
    const selected = row.id === ui.selectedId ? "true" : "false";
    return group + `<tr data-capability-id="${row.id}" data-selected="${selected}" ${objectDomAttributes({
      kind: "capability", id: row.id, relations: capabilityRelations(row.id),
    })}>
      <th class="capability-cell" scope="row"><button type="button" data-select-capability="${row.id}" data-focus-key="school:${row.id}" title="Inspect exact capability ${row.id}">${row.id}</button></th>
      <td>${row.grade}</td>
      <td title="${row.prerequisites.join(", ") || "none"}">${row.prerequisites.join(", ") || "—"}</td>
      <td class="num" title="WAS ${row.was}/${row.total}">${row.was}</td>
      <td class="num" title="TOP ${row.top}/${row.total}">${row.top}</td>
      <td class="num" title="NOW ${row.now}/${row.total}">${row.now}</td>
      <td class="num">${row.total}</td>
      <td class="num" title="Terminal quad ${scoreQuad(row)}">${row.growth >= 0 ? "+" : ""}${row.growth}</td>
      <td class="num">${row.debt}</td>
      <td class="num">${row.pRet === null ? "—" : row.pRet.toFixed(2)}</td>
      <td class="num">${row.visits}</td>
      <td class="num">${row.retainedSteps}</td>
      <td>${row.lastGain}</td>
      <td>${row.lastRegression}</td>
      <td>${row.strategy}</td>
      <td>${row.sourceFamilies.join(", ")}</td>
      <td colspan="2">${statusCell(row)}</td>
    </tr>`;
  }).join("");
}

function matrix(projectedRows, page) {
  const headers = [
    ["id", "Capability"], ["grade", "Class"], ["prerequisites", "Prerequisites"],
    ["was", "WAS"], ["top", "TOP"], ["now", "NOW"], ["total", "ALL"],
    ["growth", "Growth"], ["debt", "Debt"], ["pRet", "P(RET)"],
    ["visits", "Visits"], ["retainedSteps", "Retained steps"], ["lastGain", "Last gain"],
    ["lastRegression", "Last regression"], ["strategy", "Strategy"], ["sourceFamilies", "Sources"],
  ];
  return `<section class="school-panel matrix-panel">
    <header><div><span class="eyebrow">Exact comparison</span><h2>Capability matrix</h2></div><div class="coverage-counter">${page.start + 1}–${page.end} of ${page.total}</div></header>
    <div class="matrix-scroll scroll-surface" role="region" aria-label="School capability matrix" tabindex="0">
      <table class="school-matrix">
        <thead><tr>${headers.map(([key, label]) => {
          const ariaSort = ui.sortKey === key ? (ui.direction === "asc" ? "ascending" : "descending") : "none";
          return `<th aria-sort="${ariaSort}"><button type="button" data-sort-key="${key}" data-focus-key="sort:${key}">Sort by ${label}<span aria-hidden="true">${ui.sortKey === key ? (ui.direction === "asc" ? " ↑" : " ↓") : ""}</span></button></th>`;
        }).join("")}<th colspan="2">Source / implementation / qualification</th></tr></thead>
        <tbody>${tableRows(projectedRows)}</tbody>
      </table>
    </div>
    <footer class="school-pagination">
      <button type="button" data-page="-1" data-focus-key="page:previous" ${page.page <= 1 ? "disabled" : ""}>Previous</button>
      <span>Page ${page.page} / ${page.pages} · complete coverage ${page.total} rows</span>
      <button type="button" data-page="1" data-focus-key="page:next" ${page.page >= page.pages ? "disabled" : ""}>Next</button>
    </footer>
  </section>`;
}

function graphNode(row, neighborhood, index) {
  const isSelected = row.id === neighborhood.selected;
  const relation = isSelected ? "selected"
    : neighborhood.prerequisites.includes(row.id) ? "prerequisite"
    : neighborhood.dependents.includes(row.id) ? "dependent" : "other";
  const x = 80 + (index % 3) * 240;
  const y = 50 + Math.floor(index / 3) * 100;
  const unlocks = rows.filter((candidate) => candidate.prerequisites.includes(row.id)).length;
  const eligibility = (row.sourceState === "SOURCE_HELD" || row.implementationState === "IMPLEMENTATION_UNCOVERED")
    ? "blocked"
    : row.lifecycleState === "READY" ? "eligible" : "other";
  const mastery = row.qualificationState === "QUALIFIED" ? "mastered" : "learning";
  return `<g class="dependency-node" data-capability-id="${row.id}" ${objectDomAttributes({
    kind: "capability", id: row.id, relations: capabilityRelations(row.id),
  })} data-focus-key="graph:${row.id}" data-relation="${relation}" data-state="${stateCue(row)}" data-lifecycle="${row.lifecycleState}" data-eligibility="${eligibility}" data-mastery="${mastery}" data-observed-debt="${row.observedDebt}" tabindex="0" role="button" aria-pressed="${isSelected}" aria-label="${row.id}; ${row.lifecycleState}; ${unlocks} direct downstream unlocks" transform="translate(${x} ${y})">
    <title>${row.id}: ${row.lifecycleState}; direct downstream unlocks ${unlocks}</title>
    <rect width="190" height="62" rx="8"></rect>
    <text x="12" y="24">${row.id}</text>
    <text class="node-state" x="12" y="44">${row.sourceState === "SOURCE_HELD" ? "SOURCE_HELD" : row.implementationState === "IMPLEMENTATION_UNCOVERED" ? "IMPLEMENTATION_UNCOVERED" : row.lifecycleState} · debt ${row.observedDebt ? row.debt : "—"} · unlock ${unlocks}</text>
  </g>`;
}

function graphEdges(neighborhood) {
  const selected = rows.findIndex((row) => row.id === neighborhood.selected);
  if (selected < 0) return "";
  const sx = 80 + (selected % 3) * 240 + 95;
  const sy = 50 + Math.floor(selected / 3) * 100 + 31;
  return [...neighborhood.prerequisites, ...neighborhood.dependents].map((id) => {
    const index = rows.findIndex((row) => row.id === id);
    if (index < 0) return "";
    const tx = 80 + (index % 3) * 240 + 95;
    const ty = 50 + Math.floor(index / 3) * 100 + 31;
    return `<line x1="${sx}" y1="${sy}" x2="${tx}" y2="${ty}" data-edge-to="${id}"></line>`;
  }).join("");
}

function dependencyTable(neighborhood) {
  return `<table class="dependency-fallback"><caption>Equivalent table for the selected capability dependency graph</caption><thead><tr><th>Relation</th><th>Capability ID</th></tr></thead><tbody>
    ${neighborhood.prerequisites.map((id) => `<tr><td>Prerequisite</td><td>${id}</td></tr>`).join("")}
    ${neighborhood.dependents.map((id) => `<tr><td>Dependent</td><td>${id}</td></tr>`).join("")}
  </tbody></table>`;
}

function dependencyGraph() {
  const neighborhood = selectionNeighborhood(rows, ui.selectedId);
  if (!ui.graphEnabled) {
    return `<section class="school-panel graph-panel"><header><div><span class="eyebrow">Topology</span><h2>Dependency table</h2></div><button type="button" data-toggle-graph data-focus-key="graph:toggle">Enable graph</button></header>${dependencyTable(neighborhood)}</section>`;
  }
  return `<section class="school-panel graph-panel"><header><div><span class="eyebrow">Topology</span><h2>Prerequisite graph</h2></div><button type="button" data-toggle-graph data-focus-key="graph:toggle">Use table alternative</button></header>
    <div class="graph-legend"><span><i data-edge="source"></i>eligible / qualified</span><span><i data-edge="held"></i>SOURCE_HELD</span><span><i data-edge="derived"></i>IMPLEMENTATION_UNCOVERED</span></div>
    <p id="school-graph-summary" class="sr-only">Interactive prerequisite graph. Arrow keys move between capability nodes. Enter or Space inspects a node. An equivalent relationship table follows the graph.</p>
    <svg class="school-graph" viewBox="0 0 760 360" role="group" aria-label="Capability prerequisite dependency graph" aria-describedby="school-graph-summary">${graphEdges(neighborhood)}${rows.map((row, index) => graphNode(row, neighborhood, index)).join("")}</svg>
    ${dependencyTable(neighborhood)}
  </section>`;
}

function filterBar(projectedRows) {
  return `<div class="school-controls">
    <div class="filter-set" role="group" aria-label="School filters">${FILTERS.map((filter) => `<button type="button" data-filter="${filter}" data-focus-key="filter:${filter}" aria-pressed="${ui.filters.has(filter)}">${filter}</button>`).join("")}</div>
    <label><input type="checkbox" data-group-family data-focus-key="group:family" ${ui.groupByFamily ? "checked" : ""}/> Group by family</label>
    <button type="button" data-export data-focus-key="school:export">Export ${projectedRows.length} displayed identities</button>
  </div>`;
}

function restoreSchoolFocus(container, key) {
  const target = [...container.querySelectorAll("[data-focus-key]")]
    .find((candidate) => candidate.dataset.focusKey === key);
  target?.focus();
}

function rerenderFrom(container, inspectCapability, control) {
  const key = control?.dataset?.focusKey;
  renderSchoolView(container, inspectCapability);
  if (key) restoreSchoolFocus(container, key);
}

function bind(container, inspectCapability) {
  container.querySelectorAll("[data-filter]").forEach((button) => button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    ui.filters.has(filter) ? ui.filters.delete(filter) : ui.filters.add(filter);
    ui.page = 1;
    rerenderFrom(container, inspectCapability, button);
  }));
  container.querySelectorAll("[data-sort-key]").forEach((button) => button.addEventListener("click", () => {
    const key = button.dataset.sortKey;
    ui.direction = ui.sortKey === key && ui.direction === "asc" ? "desc" : "asc";
    ui.sortKey = key;
    rerenderFrom(container, inspectCapability, button);
  }));
  container.querySelectorAll("[data-page]").forEach((button) => button.addEventListener("click", () => {
    ui.page += Number(button.dataset.page);
    rerenderFrom(container, inspectCapability, button);
  }));
  container.querySelector("[data-group-family]")?.addEventListener("change", (event) => {
    ui.groupByFamily = event.currentTarget.checked;
    rerenderFrom(container, inspectCapability, event.currentTarget);
  });
  container.querySelector("[data-toggle-graph]")?.addEventListener("click", (event) => {
    ui.graphEnabled = !ui.graphEnabled;
    rerenderFrom(container, inspectCapability, event.currentTarget);
  });
  container.querySelectorAll("[data-select-capability], .dependency-node").forEach((node) => {
    const activate = () => {
      ui.selectedId = node.dataset.selectCapability ?? node.dataset.capabilityId;
      inspectCapability(
        ui.selectedId,
        rows.find((row) => row.id === ui.selectedId),
        selectionNeighborhood(rows, ui.selectedId),
      );
      renderSchoolView(container, inspectCapability);
    };
    node.addEventListener("click", activate);
    node.addEventListener("keydown", (event) => {
      if (isActivationKey(event.key)) {
        event.preventDefault();
        activate();
      }
    });
  });
  const graphNodes = [...container.querySelectorAll(".dependency-node")];
  graphNodes.forEach((node, index) => node.addEventListener("keydown", (event) => {
    const next = nextRovingIndex(index, event.key, graphNodes.length);
    if (next === index) return;
    event.preventDefault();
    graphNodes[next]?.focus();
  }));
  container.querySelector("[data-export]")?.addEventListener("click", (event) => {
    const projected = projectRows(rows, { filters: [...ui.filters], sortKey: ui.sortKey, direction: ui.direction, groupByFamily: ui.groupByFamily });
    const blob = new Blob([exportSchoolCsv(projected)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "bilqis-school-filtered.csv";
    anchor.click();
    URL.revokeObjectURL(url);
    event.currentTarget.textContent = "Exported " + projected.length + " identities";
  });
}

export function renderSchoolView(container, inspectCapability, selectedId = null) {
  if (selectedId && rows.some((row) => row.id === selectedId)) ui.selectedId = selectedId;
  const projected = projectRows(rows, { filters: [...ui.filters], sortKey: ui.sortKey, direction: ui.direction, groupByFamily: ui.groupByFamily });
  const page = paginateRows(projected, ui.page, ui.pageSize);
  container.innerHTML = `<div class="school-view">
    <header class="school-heading"><div><span class="eyebrow">GUI04 · School / Curriculum</span><h2>Exact evidence, topology-aware</h2></div><p>Grade labels organize the view only. Eligibility, debt, promotion and scheduling semantics remain evidence-driven and grade-neutral.</p></header>
    <div class="school-fixture-notice" role="status"><strong>FIXTURE · REPRESENTATIVE TERMINAL METRICS</strong><span>These School rows prove GUI04 behavior and mirror the terminal metric classes; they are not current learner evidence.</span></div>
    ${filterBar(projected)}
    <div class="ui-glossary" aria-label="Capability matrix metric definitions"><span><strong>WAS</strong> prior measured score.</span><span><strong>TOP</strong> best measured score.</span><span><strong>NOW</strong> current measured score.</span><span><strong>ALL</strong> questions in the panel.</span><span><strong>P(RET)</strong> observed retention probability.</span><span>Scroll the matrix horizontally for later evidence columns.</span></div>
    ${matrix(page.rows, page)}
    ${dependencyGraph()}
  </div>`;
  bind(container, inspectCapability);
}

export function schoolRowsForTest() {
  return rows.map((row) => ({ ...row, prerequisites: [...row.prerequisites] }));
}
