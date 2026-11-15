import {
  buildCurriculumGraph,
  dependentsFor,
  resolveExactSemanticSearch,
  resolveCapabilitySemanticBindings,
  stableLayout,
  strataFor,
  traceSelection,
  visibilityFor,
} from "./curriculum-atlas-model.mjs";
import { curriculumFixtureSnapshot } from "./curriculum-atlas-fixture.mjs";
import {
  dossierMarkup,
  edgeMarkup,
  esc,
  nodeCard,
  scaleMarkup,
  tableMarkup,
  toolbarMarkup,
} from "./curriculum-atlas-markup.mjs";
import { t } from "../foundation/i18n.mjs";
import { assertUniqueTestIds, testIdAttribute } from "../foundation/test-hooks.mjs";

const ui = {
  selectedId: null, traceMode: "both", grade: "all", state: "all", family: "all",
  issue: "all", search: "", newOnly: false, consequenceOpen: false,
  familyFocus: null, semanticBindings: new Map(), semanticLoading: null, searchStatus: null,
};
let contextKey = null;
let semanticEpoch = 0;

export function invalidateCurriculumAtlasRequests() {
  semanticEpoch += 1;
  ui.semanticLoading = null;
}

function bindContext(context) {
  const next = [
    context?.runId ?? "unknown",
    context?.generation ?? "unknown",
    context?.mode ?? "unknown",
    context?.semanticRelease ?? "unknown",
  ].join("|");
  if (contextKey === next) return;
  contextKey = next;
  semanticEpoch += 1;
  ui.semanticBindings = new Map();
  ui.semanticLoading = null;
  ui.searchStatus = null;
  ui.consequenceOpen = false;
}

export function curriculumFixtureModeForContext(context) {
  return context?.mode === "HISTORICAL" && context?.freshness === "FRESH"
    ? "historical"
    : "current";
}

function snapshotFor(context) {
  return curriculumFixtureSnapshot(
    curriculumFixtureModeForContext(context),
    context?.generation ?? null,
  );
}

function bind(container, context, api, onInspect, onModeChange, isActive) {
  const focusKey = () => container.contains(document.activeElement)
    ? document.activeElement?.dataset?.focusKey ?? null
    : null;
  const restoreFocus = (key) => {
    if (!key) return;
    [...container.querySelectorAll("[data-focus-key]")]
      .find((candidate) => candidate.dataset.focusKey === key)?.focus();
  };
  const rerender = (requestedFocusKey = null) => {
    const key = requestedFocusKey ?? focusKey();
    if (!isActive()) return;
    renderCurriculumAtlasView(container, {
      context, api, onInspect, onModeChange, isActive,
    });
    restoreFocus(key);
  };
  const inspectNode = (node) => {
    if (!node) return;
    onInspect(node.id, node, ui.semanticBindings.get(node.id) ?? null);
  };
  container.querySelectorAll("[data-curriculum-node]").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.focusKey;
      ui.selectedId = button.dataset.curriculumNode;
      ui.consequenceOpen = false;
      const node = snapshotFor(context).nodes.find((item) => item.id === ui.selectedId);
      inspectNode(node);
      rerender(key);
    });
  });
  container.querySelectorAll("[data-trace-mode]").forEach((button) => {
    button.addEventListener("click", () => {
      ui.traceMode = button.dataset.traceMode;
      rerender();
      const live = container.querySelector("[data-trace-status]");
      if (!live) return;
      const message = live.dataset.message;
      live.textContent = "";
      window.queueMicrotask(() => { live.textContent = message; });
    });
  });
  container.querySelector("[data-curriculum-search]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const key = focusKey();
    ui.search = new FormData(event.currentTarget).get("search")?.toString() ?? "";
    const graph = buildCurriculumGraph(snapshotFor(context));
    let visibility = visibilityFor(graph, ui, ui.semanticBindings);
    let matches = graph.nodes.filter((node) => visibility.get(node.id));
    ui.searchStatus = null;
    if (matches.length === 0 && ui.search.trim()) {
      const token = ++semanticEpoch;
      ui.searchStatus = t("curriculum.search.resolving");
      rerender(key);
      try {
        const hydrated = await resolveGraphSemanticBindings(api, context, graph);
        if (token !== semanticEpoch || !isActive()) return;
        for (const [id, binding] of hydrated) ui.semanticBindings.set(id, binding);
        visibility = visibilityFor(graph, ui, ui.semanticBindings);
        matches = graph.nodes.filter((node) => visibility.get(node.id));
        if (matches.length === 0) {
          const result = await resolveExactSemanticSearch(api, context, ui.search.trim(), graph);
          if (token !== semanticEpoch || !isActive()) return;
          ui.searchStatus = result.state + " · " + result.reason;
          if (result.state === "PRESENT") {
            ui.selectedId = result.capabilityIds[0];
            ui.semanticBindings.set(ui.selectedId, Object.freeze({
              state: "PRESENT",
              reason: "EXACT_RELEASE_SEMANTIC_IDENTITY",
              concepts: Object.freeze([result.concept]),
            }));
            matches = graph.nodes.filter((node) => node.id === ui.selectedId);
          }
        } else {
          ui.searchStatus = t("curriculum.search.sourceMatches", { count: matches.length });
        }
      } catch (error) {
        if (token !== semanticEpoch || !isActive()) return;
        ui.searchStatus = t("curriculum.search.unavailable", {
          reason: error?.code ?? error?.message ?? "SEMANTIC_SEARCH_FAILED",
        });
      }
    }
    if (matches.length === 1) {
      ui.selectedId = matches[0].id;
      inspectNode(matches[0]);
    } else if (matches.length > 1 && !ui.searchStatus) {
      ui.searchStatus = t("curriculum.search.fixtureMatches", { count: matches.length });
    }
    rerender(key);
  });
  container.querySelector("[data-jump-active]")?.addEventListener("click", (event) => {
    ui.selectedId = snapshotFor(context).activeId;
    ui.search = "";
    inspectNode(snapshotFor(context).nodes.find((node) => node.id === ui.selectedId));
    rerender(event.currentTarget.dataset.focusKey);
  });
  container.querySelectorAll("[data-filter]").forEach((select) => {
    select.addEventListener("change", () => { ui[select.dataset.filter] = select.value; rerender(); });
  });
  container.querySelector("[data-new-only]")?.addEventListener("change", (event) => {
    ui.newOnly = event.currentTarget.checked;
    rerender();
  });
  container.querySelector("[data-reset-filters]")?.addEventListener("click", () => {
    Object.assign(ui, {
      grade: "all", state: "all", family: "all", issue: "all", search: "", newOnly: false,
    });
    ui.searchStatus = null;
    rerender();
  });
  container.querySelector("[data-consequence-toggle]")?.addEventListener("click", () => {
    ui.consequenceOpen = !ui.consequenceOpen;
    rerender();
  });
  container.querySelectorAll("[data-family-focus]").forEach((button) => {
    button.addEventListener("click", () => {
      ui.familyFocus = button.dataset.familyFocus;
      ui.largeSelectedId = null;
      rerender();
    });
  });
  container.querySelectorAll("[data-large-semantic]").forEach((button) => {
    button.addEventListener("click", () => {
      ui.largeSelectedId = button.dataset.largeSemantic;
      rerender();
    });
  });
  container.querySelectorAll("[data-school-mode]").forEach((button) => {
    button.addEventListener("click", () =>
      onModeChange(button.dataset.schoolMode, ui.selectedId, true));
  });
  container.querySelector("[data-resolve-semantic]")?.addEventListener("click", async (event) => {
    const id = event.currentTarget.dataset.resolveSemantic;
    const key = event.currentTarget.dataset.focusKey;
    const token = ++semanticEpoch;
    ui.semanticLoading = id;
    rerender(key);
    try {
      const result = await resolveCapabilitySemanticBindings(api, context, id);
      if (token !== semanticEpoch || !isActive()) return;
      ui.semanticBindings.set(id, result);
      inspectNode(snapshotFor(context).nodes.find((node) => node.id === id));
    } catch (error) {
      if (token !== semanticEpoch || !isActive()) return;
      ui.semanticBindings.set(id, Object.freeze({
        state: "UNAVAILABLE",
        reason: error?.code ?? error?.message ?? "SEMANTIC_LOOKUP_FAILED",
        concepts: Object.freeze([]),
      }));
    } finally {
      if (token !== semanticEpoch || !isActive()) return;
      ui.semanticLoading = null;
      rerender(key);
    }
  });
}

export function renderCurriculumAtlasView(
  container, {
    context, api, onInspect, onModeChange, selectedId = null,
    isActive = () => true,
  },
) {
  bindContext(context);
  const snapshot = snapshotFor(context);
  const graph = buildCurriculumGraph(snapshot);
  if (selectedId && graph.nodes.some((node) => node.id === selectedId)) {
    ui.selectedId = selectedId;
  }
  if (!graph.nodes.some((node) => node.id === ui.selectedId)) ui.selectedId = snapshot.activeId;
  const selected = graph.nodes.find((node) => node.id === ui.selectedId) ?? graph.nodes[0];
  const trace = traceSelection(graph, selected.id, ui.traceMode);
  const visibility = visibilityFor(graph, ui, ui.semanticBindings);
  const layout = stableLayout(graph);
  const strata = strataFor(graph);
  const semanticBinding = ui.semanticBindings.get(selected.id) ?? null;
  const status = t("curriculum.trace.status", {
    id: selected.id, upstream: trace.visibleUpstream.size,
    downstream: trace.visibleDownstream.size, mode: trace.mode,
  });
  const edges = graph.edges.map((edge) => edgeMarkup(edge, layout, trace)).join("");
  const nodes = graph.nodes.map((node) =>
    nodeCard(
      node,
      layout.positions.get(node.id),
      trace,
      visibility.get(node.id),
      ui.semanticBindings.get(node.id) ?? null,
    )).join("");

  const markup =
    '<div class="curriculum-atlas" ' + testIdAttribute("curriculum", "root") + '>' +
      '<div class="curriculum-fixture-notice" ' + testIdAttribute("curriculum", "fixture") + '><strong>' + esc(t("curriculum.fixture.title")) + '</strong>' +
        '<span>' + esc(t("curriculum.fixture.detail")) + '</span>' +
        '<span>' + esc(t("curriculum.fixture.context", {
          label: t(snapshot.id === "historical" ? "curriculum.fixture.historical" : "curriculum.fixture.current"), boundary: snapshot.fixtureBoundary,
          generation: context?.generation ?? "unknown", mode: context?.mode ?? "LIVE",
        })) + '</span></div>' +
      '<nav class="school-subnav" aria-label="' + esc(t("shell.school.subnav")) + '" data-test-id="shell-school-subnav">' +
        '<button type="button" class="ui-control ui-control--peer-tab" data-school-mode="matrix" data-focus-key="school-mode:matrix" ' +
          testIdAttribute("shell", "school-mode", "matrix") + '>' + esc(t("shell.school.matrix")) + '</button>' +
        '<button type="button" class="ui-control ui-control--peer-tab" aria-current="page" data-focus-key="school-mode:atlas" ' +
          testIdAttribute("shell", "school-mode", "atlas") + '>' + esc(t("shell.school.atlas")) + '</button></nav>' +
      toolbarMarkup(graph, snapshot, ui) +
      (ui.searchStatus
        ? '<p class="curriculum-search-status" role="status" ' + testIdAttribute("curriculum", "search", "status") + '>' + esc(ui.searchStatus) + '</p>'
        : '') +
      '<p class="sr-only" role="status" aria-live="polite" aria-atomic="true" ' +
        'data-trace-status data-message="' + esc(status) + '" ' + testIdAttribute("curriculum", "trace", "status") + '>' + esc(status) + '</p>' +
      '<div class="curriculum-topology-grid" ' + testIdAttribute("curriculum", "topology") + '>' +
      '<section class="curriculum-graph-panel" ' + testIdAttribute("curriculum", "graph") + '><header><div><span class="eyebrow">' + esc(t("curriculum.graph.eyebrow")) + '</span>' +
        '<h2>' + esc(t("curriculum.graph.title")) + '</h2></div><div class="curriculum-legend">' +
        '<span>' + esc(t("curriculum.graph.legend.qualified")) + '</span><span>' + esc(t("curriculum.graph.legend.active")) + '</span><span>' + esc(t("curriculum.graph.legend.eligible")) + '</span>' +
        '<span>' + esc(t("curriculum.graph.legend.blocked")) + '</span><span>' + esc(t("curriculum.graph.legend.future")) + '</span></div></header>' +
        '<p>' + esc(t("curriculum.graph.description")) + '</p>' +
        '<div class="curriculum-scroll" tabindex="0" role="region" aria-label="' + esc(t("curriculum.graph.aria")) + '" ' + testIdAttribute("curriculum", "graph", "scroll") + '><div class="curriculum-canvas" ' +
        'data-height="' + layout.height + '">' +
          '<div class="curriculum-stratum foundation"><strong>' + esc(t("curriculum.graph.foundation")) + '</strong><span>' + esc(t("curriculum.graph.foundationDetail", { count: strata.foundation.length })) + '</span></div>' +
          '<div class="curriculum-stratum current"><strong>' + esc(t("curriculum.graph.current", { grade: snapshot.currentGrade })) + '</strong><span>' + esc(t("curriculum.graph.currentDetail")) + '</span></div>' +
          '<div class="curriculum-stratum forward"><strong>' + esc(t("curriculum.graph.forward")) + '</strong><span>' + esc(t("curriculum.graph.forwardDetail", { count: strata.forward.length })) + '</span></div>' +
          '<svg class="curriculum-edges" viewBox="0 0 1010 ' + layout.height +
            '" aria-label="' + esc(t("curriculum.graph.edgesAria")) + '"><defs><marker id="curriculum-arrow" ' +
            'viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">' +
            '<path d="M 0 0 L 10 5 L 0 10 z"></path></marker></defs>' + edges + '</svg>' +
          nodes + '</div></div>' +
        '<div class="relationship-summary"><span>' + esc(t("curriculum.relationship.prerequisites", { value: selected.prerequisites.length ? selected.prerequisites.join(", ") : t("school.common.none") })) +
          '</span><span>' + esc(t("curriculum.relationship.dependents", { value: dependentsFor(graph, selected.id).join(", ") || t("school.common.none") })) +
          '</span></div></section>' +
      tableMarkup(graph, visibility, ui.semanticBindings, selected.id) + '</div>' +
      dossierMarkup(graph, selected, semanticBinding, ui) +
      scaleMarkup(ui) +
    '</div>';
  assertUniqueTestIds(markup);
  container.innerHTML = markup;
  bind(container, context, api, onInspect, onModeChange, isActive);
}
