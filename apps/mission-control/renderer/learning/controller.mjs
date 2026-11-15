import { t } from "../foundation/i18n.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";
import {
  assertLearningPage,
  buildLearningQuery,
  recordId,
  recordKind,
  recordLabel,
} from "./query.mjs";
import { productionLearningMarkup, PRODUCTION_LEARNING_TABS } from "./view.mjs";

export function createProductionLearningController(api) {
  let epoch = 0;
  let page = null;
  let contextKey = null;
  let selectedId = null;
  let activeTab = "transaction";

  function activateTab(target, id, focus = false) {
    if (!PRODUCTION_LEARNING_TABS.some(([candidate]) => candidate === id)) return;
    activeTab = id;
    target.querySelectorAll("[data-learning-production-tab]").forEach((button) => {
      const active = button.dataset.learningProductionTab === id;
      button.setAttribute("aria-selected", String(active));
      button.tabIndex = active ? 0 : -1;
      if (active && focus) button.focus();
    });
    target.querySelectorAll("[data-learning-production-panel]").forEach((panel) => {
      panel.hidden = panel.dataset.learningProductionPanel !== id;
    });
  }

  function bind(target, context, onInspect) {
    target.querySelector("[data-learning-production-selector]")?.addEventListener(
      "change",
      (event) => {
        selectedId = event.target.value;
        paint(target, context, onInspect);
      },
    );
    target.querySelector("[data-learning-production-inspect]")?.addEventListener(
      "click",
      () => {
        const record = page?.records?.find((item) => recordId(item) === selectedId) ??
          page?.records?.[0] ?? null;
        if (!record) return;
        onInspect({
          kind: recordKind(record),
          id: recordId(record),
          label: recordLabel(record, t("learning.value.unknown")),
          details: {
            [t("learning.production.capability")]: record.capability_id,
            [t("learning.production.authority")]: record.meta?.authority,
            [t("learning.production.coverage")]: record.meta?.coverage,
          },
        });
      },
    );
    const tabs = [...target.querySelectorAll("[data-learning-production-tab]")];
    tabs.forEach((button, index) => {
      button.addEventListener("click", () => {
        activateTab(target, button.dataset.learningProductionTab);
      });
      button.addEventListener("keydown", (event) => {
        const next = event.key === "ArrowRight" ? (index + 1) % tabs.length
          : event.key === "ArrowLeft" ? (index - 1 + tabs.length) % tabs.length
          : event.key === "Home" ? 0
          : event.key === "End" ? tabs.length - 1
          : null;
        if (next === null) return;
        event.preventDefault();
        activateTab(target, tabs[next].dataset.learningProductionTab, true);
      });
    });
  }

  function paint(target, context, onInspect) {
    target.innerHTML = productionLearningMarkup({
      context,
      records: page?.records ?? [],
      selectedId,
      activeTab,
      status: page?.state ?? "UNKNOWN",
    });
    bind(target, context, onInspect);
  }

  async function activate(context, { target, onInspect, selection = null }) {
    const key = [context.runId, context.generation, context.mode].join("|");
    const requestedId = ["episode", "candidate"].includes(selection?.kind)
      ? selection.id : null;
    if (contextKey === key && page && (!requestedId || requestedId === selectedId)) {
      paint(target, context, onInspect);
      return;
    }
    contextKey = key;
    selectedId = requestedId;
    page = null;
    target.innerHTML = "<p " + testIdAttribute("learning", "production", "loading") +
      ">" + t("learning.production.loading") + "</p>";
    const token = ++epoch;
    try {
      const response = assertLearningPage(await api.query(
        buildLearningQuery(context, requestedId),
      ));
      if (token !== epoch) return;
      page = response;
      selectedId ??= response.records?.[0]?.meta?.record_id ?? null;
    } catch (_error) {
      if (token !== epoch) return;
      page = { state: "UNAVAILABLE", records: [] };
    }
    paint(target, context, onInspect);
  }

  return Object.freeze({
    activate,
    deactivate() {
      epoch += 1;
      contextKey = null;
      page = null;
    },
  });
}
