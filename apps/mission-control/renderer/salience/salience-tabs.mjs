import { bindRovingNavigation } from "../foundation/accessibility.mjs";
import { controlClass } from "../foundation/primitives.mjs";
import { esc, t, testIdAttribute } from "./salience-view-shared.mjs";

export const SALIENCE_TABS = Object.freeze(["observations", "aggregation", "routing"]);

export function salienceTabsMarkup(activeTab = "observations") {
  const active = SALIENCE_TABS.includes(activeTab) ? activeTab : "observations";
  return `<nav class="salience-tabs" role="tablist" aria-label="${esc(t("salience.tabs.label"))}" ${testIdAttribute("salience", "tabs")}>
    ${SALIENCE_TABS.map((tab) => `<button type="button" role="tab" class="${controlClass("peer-tab")} salience-tab"
      id="salience-tab-${tab}" data-salience-tab="${tab}" aria-selected="${tab === active}"
      aria-controls="salience-panel-${tab}" tabindex="${tab === active ? "0" : "-1"}"
      ${testIdAttribute("salience", "tab", tab)}>${esc(t(`salience.tabs.${tab}`))}</button>`).join("")}
  </nav>`;
}

export function salienceTabPanelMarkup(tab, body, activeTab) {
  const active = tab === activeTab;
  return `<div class="salience-tab-panel" id="salience-panel-${tab}" role="tabpanel"
    aria-labelledby="salience-tab-${tab}" ${active ? "" : "hidden"}
    ${testIdAttribute("salience", "panel", tab)}>${active ? body : ""}</div>`;
}

export function bindSalienceTabs(container, onSelect) {
  const tabs = container.querySelector('[data-test-id="salience-tabs"]');
  if (!tabs) return;
  tabs.querySelectorAll("[data-salience-tab]").forEach((button) => {
    button.addEventListener("click", () => onSelect(button.dataset.salienceTab));
  });
  bindRovingNavigation(tabs, "[role=tab]");
}
