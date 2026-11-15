import { lineageT } from "./lineage-messages.mjs";
import {
  assertQueryPage,
  buildGenerationQuery,
  buildRejectedQuery,
  rejectedDecisions,
  selectGenerationRecord,
} from "./production-query.mjs";
import {
  productionLineageMarkup,
  PRODUCTION_LINEAGE_TABS,
} from "./production-view.mjs";

export function createProductionLineageController(api) {
  let epoch = 0;
  let contextKey = null;
  let generationPage = null;
  let rejectedPage = null;
  let generation = null;
  let activeTab = "generations";

  function activateTab(target, id, focus = false) {
    if (!PRODUCTION_LINEAGE_TABS.some(([candidate]) => candidate === id)) return;
    activeTab = id;
    target.querySelectorAll("[data-lineage-production-tab]").forEach(button => {
      const active = button.dataset.lineageProductionTab === id;
      button.setAttribute("aria-selected", String(active));
      button.tabIndex = active ? 0 : -1;
      if (active && focus) button.focus();
    });
    target.querySelectorAll("[data-lineage-production-panel]").forEach(panel => {
      panel.hidden = panel.dataset.lineageProductionPanel !== id;
    });
  }

  function bind(target, onInspect) {
    const tabs = [...target.querySelectorAll("[data-lineage-production-tab]")];
    tabs.forEach((button, index) => {
      button.addEventListener("click", () => {
        activateTab(target, button.dataset.lineageProductionTab);
      });
      button.addEventListener("keydown", event => {
        const next = event.key === "ArrowRight" ? (index + 1) % tabs.length
          : event.key === "ArrowLeft" ? (index - 1 + tabs.length) % tabs.length
          : event.key === "Home" ? 0
          : event.key === "End" ? tabs.length - 1
          : null;
        if (next === null) return;
        event.preventDefault();
        activateTab(target, tabs[next].dataset.lineageProductionTab, true);
      });
    });
    target.querySelector("[data-lineage-production-inspect]")?.addEventListener(
      "click",
      () => {
        if (!generation) return;
        const run = generation.meta.run;
        onInspect({
          kind: "generation",
          id: generation.meta.record_id,
          label: lineageT("lineage.dossier.title", { generation: run.generation }),
          relations: [{
            kind: "checkpoint",
            id: "checkpoint:" + generation.checkpoint_sha256,
            relation: "checkpoint",
          }],
          details: {
            [lineageT("lineage.dossier.generation")]: run.generation,
            [lineageT("lineage.production.manifest")]: run.generation_manifest_sha256,
            [lineageT("lineage.production.parentManifest")]:
              generation.parent_manifest_sha256 ?? lineageT("lineage.graph.genesis"),
            [lineageT("lineage.production.checkpoint")]: generation.checkpoint_sha256,
            [lineageT("lineage.production.status")]: generation.status,
          },
        });
      },
    );
  }

  function paint(target, context, onInspect) {
    target.innerHTML = productionLineageMarkup({
      context,
      generation,
      generationState: generationPage?.state ?? "UNKNOWN",
      rejected: rejectedDecisions(rejectedPage),
      activeTab,
    });
    bind(target, onInspect);
  }

  async function activate(context, { target, onInspect }) {
    const key = [context.runId, context.generation, context.mode].join("|");
    if (contextKey === key && generationPage) {
      paint(target, context, onInspect);
      return;
    }
    contextKey = key;
    generationPage = null;
    rejectedPage = null;
    generation = null;
    target.innerHTML =
      '<p data-test-id="lineage-production-loading">' +
      lineageT("lineage.production.loading") +
      "</p>";
    const token = ++epoch;
    try {
      generationPage = assertQueryPage(await api.query(buildGenerationQuery(context)));
      if (token !== epoch) return;
      generation = selectGenerationRecord(generationPage, context);
    } catch (_error) {
      if (token !== epoch) return;
      generationPage = { state: "UNAVAILABLE", records: [] };
      generation = null;
    }
    try {
      rejectedPage = assertQueryPage(await api.query(buildRejectedQuery(context)));
    } catch (_error) {
      rejectedPage = { state: "UNAVAILABLE", records: [] };
    }
    if (token !== epoch) return;
    paint(target, context, onInspect);
  }

  return Object.freeze({
    activate,
    deactivate() {
      epoch += 1;
      contextKey = null;
      generationPage = null;
      rejectedPage = null;
      generation = null;
    },
  });
}
