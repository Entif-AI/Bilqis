import { bindRovingNavigation } from "../foundation/accessibility.mjs";
import { controlClass } from "../foundation/primitives.mjs";
import { esc, t, testIdAttribute } from "./teacher-view-shared.mjs";

export const TEACHER_TABS = Object.freeze(["roster", "comparison", "fidelity"]);

export function teacherTabsMarkup(activeTab = "roster") {
  const active = TEACHER_TABS.includes(activeTab) ? activeTab : "roster";
  return `<nav class="teacher-tabs" role="tablist" aria-label="${esc(t("teacher.tabs.label"))}" ${testIdAttribute("teacher", "tabs")}>
    ${TEACHER_TABS.map((tab) => `<button type="button" role="tab" class="${controlClass("peer-tab")} teacher-tab"
      id="teacher-tab-${tab}" data-teacher-tab="${tab}" aria-selected="${tab === active}"
      aria-controls="teacher-panel-${tab}" tabindex="${tab === active ? "0" : "-1"}"
      ${testIdAttribute("teacher", "tab", tab)}>${esc(t(`teacher.tabs.${tab}`))}</button>`).join("")}
  </nav>`;
}

export function teacherTabPanelMarkup(tab, body, activeTab) {
  const active = tab === activeTab;
  return `<div class="teacher-tab-panel" id="teacher-panel-${tab}" role="tabpanel"
    aria-labelledby="teacher-tab-${tab}" ${active ? "" : "hidden"}
    ${testIdAttribute("teacher", "panel", tab)}>${active ? body : ""}</div>`;
}

export function bindTeacherTabs(container, onSelect) {
  const tabs = container.querySelector('[data-test-id="teacher-tabs"]');
  if (!tabs) return;
  tabs.querySelectorAll("[data-teacher-tab]").forEach((button) => {
    button.addEventListener("click", () => onSelect(button.dataset.teacherTab));
  });
  bindRovingNavigation(tabs, "[role=tab]");
}
