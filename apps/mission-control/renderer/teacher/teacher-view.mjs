import { STRATEGY_FIXTURES } from "./teacher-fixture.mjs";
import { comparisonPanel, availableScopes } from "./teacher-comparison-view.mjs";
import { fidelityPanel } from "./teacher-fidelity-view.mjs";
import { rosterPanel, strategyRelations } from "./teacher-roster-view.mjs";
import { esc, t, testIdAttribute } from "./teacher-view-shared.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";
import { bindTeacherTabs, teacherTabPanelMarkup, teacherTabsMarkup, TEACHER_TABS } from "./teacher-tabs.mjs";

const ui = {
  selectedStrategyId: STRATEGY_FIXTURES[0].id,
  selectedStrategyIds: Object.freeze([
    "strategy:fixture:incumbent-deep-contrast",
    "strategy:fixture:retired-shallow",
  ]),
  scope: Object.freeze({ kind: "capability", value: "B.IFF" }),
  activeTab: "roster",
};

function normalizeScope() {
  const scopes = availableScopes(ui.selectedStrategyIds);
  if (!scopes.some((scope) => scope.kind === ui.scope.kind && scope.value === ui.scope.value)) {
    ui.scope = Object.freeze({ kind: "whole-school", value: "ALL" });
  }
}

function bind(container, inspectStrategy) {
  bindTeacherTabs(container, (tab) => {
    if (!TEACHER_TABS.includes(tab) || tab === ui.activeTab) return;
    ui.activeTab = tab;
    renderTeacherView(container, inspectStrategy);
    container.querySelector(`[data-teacher-tab="${tab}"]`)?.focus({ preventScroll: true });
  });
  container.querySelectorAll("[data-strategy-select]").forEach((button) => button.addEventListener("click", () => {
    ui.selectedStrategyId = button.dataset.strategySelect;
    renderTeacherView(container, inspectStrategy);
  }));
  container.querySelector("[data-strategy-inspect]")?.addEventListener("click", (event) => {
    const strategy = STRATEGY_FIXTURES.find((item) => item.id === event.currentTarget.dataset.strategyInspect);
    inspectStrategy(strategy?.id, strategy, strategy ? strategyRelations(strategy) : []);
  });
  container.querySelectorAll("[data-compare-strategy]").forEach((button) => button.addEventListener("click", () => {
    const selected = new Set(ui.selectedStrategyIds);
    const id = button.dataset.compareStrategy;
    if (selected.has(id)) {
      if (selected.size > 2) selected.delete(id);
    } else {
      selected.add(id);
    }
    ui.selectedStrategyIds = Object.freeze([...selected]);
    normalizeScope();
    renderTeacherView(container, inspectStrategy);
  }));
  container.querySelector("[data-compare-scope]")?.addEventListener("change", (event) => {
    const [kind, ...rest] = event.currentTarget.value.split(":");
    ui.scope = Object.freeze({ kind, value: rest.join(":") });
    renderTeacherView(container, inspectStrategy);
  });
}

export function teacherMarkupForTest(
  selectedStrategyId = ui.selectedStrategyId,
  selectedStrategyIds = ui.selectedStrategyIds,
  scope = ui.scope,
  activeTab = ui.activeTab,
) {
  const tab = TEACHER_TABS.includes(activeTab) ? activeTab : "roster";
  return `<div class="teacher-view" ${testIdAttribute("teacher", "view")}>
    <header class="teacher-heading" ${testIdAttribute("teacher", "heading")}><div>
      <span class="eyebrow">${esc(t("teacher.view.eyebrow"))}</span><h2>${esc(t("teacher.view.title"))}</h2>
    </div><div class="teacher-heading-context"><p>${esc(t("teacher.view.summary"))}</p>${contextHelpMarkup({
      label: t("teacher.help.mutation.label"), description: t("teacher.help.mutation.body"), testId: "teacher-help-mutation",
    })}</div></header>
    <div class="teacher-fixture-notice" role="note" ${testIdAttribute("teacher", "fixture", "notice")}>
      <strong>${esc(t("teacher.fixture.label"))}</strong><span>${esc(t("teacher.fixture.detail"))}</span>${contextHelpMarkup({
        label: t("teacher.help.provenance.label"), description: t("teacher.help.provenance.fixtureBody"), testId: "teacher-help-provenance",
      })}
    </div>
    ${teacherTabsMarkup(tab)}
    ${teacherTabPanelMarkup("roster", rosterPanel(selectedStrategyId), tab)}
    ${teacherTabPanelMarkup("comparison", comparisonPanel(selectedStrategyIds, scope), tab)}
    ${teacherTabPanelMarkup("fidelity", fidelityPanel(), tab)}
  </div>`;
}

export function renderTeacherView(container, inspectStrategy, selectedId = null) {
  if (selectedId && STRATEGY_FIXTURES.some((strategy) => strategy.id === selectedId)) {
    ui.selectedStrategyId = selectedId;
  }
  container.innerHTML = teacherMarkupForTest(ui.selectedStrategyId, ui.selectedStrategyIds, ui.scope);
  bind(container, inspectStrategy);
}

export function teacherComparisonStateForTest() {
  return Object.freeze({
    selectedStrategyId: ui.selectedStrategyId,
    selectedStrategyIds: Object.freeze([...ui.selectedStrategyIds]),
    scope: Object.freeze({ ...ui.scope }),
    activeTab: ui.activeTab,
  });
}
