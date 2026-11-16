import { loadSalienceSnapshot } from "./salience-live.mjs";
import { productionSalienceMarkup } from "./salience-production-view.mjs";
import { bindSalienceTabs, SALIENCE_TABS } from "./salience-tabs.mjs";
import { t } from "./salience-view-shared.mjs";

function contextKey(context, launchMode) {
  if (!context) return `${launchMode}:none`;
  return [launchMode, context.runId, context.mode, context.generation].join(":");
}

function rawAxis(axis) {
  if (!axis || axis.state !== "PRESENT") return axis?.state ?? "UNKNOWN";
  return `${axis.value}${axis.units ? ` ${axis.units}` : ""} · ${axis.origin}`;
}

export function createSalienceController(api, { fixtureSupport = null } = {}) {
  let key = null;
  let host = null;
  let inspect = null;
  let context = null;
  let launchMode = "production";
  let model = null;
  let activeTab = "observations";
  let selectedObservationId = null;
  let epoch = 0;

  function inspectProduction(event) {
    if (!event || !inspect) return;
    selectedObservationId = event.recordId;
    inspect({
      kind: "salience-observation",
      id: event.recordId,
      label: event.salienceId,
      relations: [],
      details: {
        [t("salience.inspector.capability")]: event.capabilityId,
        [t("salience.inspector.action")]: event.actionKind,
        [t("salience.inspector.time")]: event.observedAt ?? t("salience.value.unavailable"),
        [t("salience.production.materialized")]: event.materializedAt ?? t("salience.value.unavailable"),
        [t("salience.production.authority")]: event.authority,
        [t("salience.observations.impact")]: rawAxis(event.axes.impact),
        [t("salience.observations.exigency")]: rawAxis(event.axes.exigency),
        [t("salience.observations.novelty")]: rawAxis(event.axes.novelty),
        [t("salience.production.sourceRefs")]: event.sourceRefs.length ? event.sourceRefs : [t("salience.value.noneRecorded")],
        [t("salience.production.evidenceRefs")]: event.evidenceRefs.length ? event.evidenceRefs : [t("salience.value.noneRecorded")],
        [t("salience.production.receiptRefs")]: event.receiptRefs.length ? event.receiptRefs : [t("salience.value.noneRecorded")],
      },
    });
  }

  function bindProduction() {
    if (!host) return;
    bindSalienceTabs(host, (tab) => {
      if (!SALIENCE_TABS.includes(tab) || tab === activeTab) return;
      activeTab = tab;
      renderProduction();
      host.querySelector(`[data-salience-tab="${tab}"]`)?.focus({ preventScroll: true });
    });
    host.querySelectorAll("[data-production-salience-inspect]").forEach((button) => {
      button.addEventListener("click", () => {
        const event = model?.events?.find((item) => item.recordId === button.dataset.productionSalienceInspect);
        inspectProduction(event);
      });
    });
  }

  function renderProduction() {
    if (!host) return;
    host.hidden = false;
    host.innerHTML = productionSalienceMarkup(model, { activeTab, selectedId: selectedObservationId, context });
    bindProduction();
  }

  function renderFixture(selectedId = null) {
    if (!host || !fixtureSupport?.renderSalienceView) return;
    host.hidden = false;
    fixtureSupport.renderSalienceView(host, (id, details) => inspect?.({
      kind: "salience-observation",
      id,
      details,
    }), selectedId);
  }

  async function load(runEpoch) {
    try {
      model = await loadSalienceSnapshot(api, context);
    } catch (_error) {
      model = Object.freeze({ state: "UNAVAILABLE", coverage: "UNKNOWN", events: Object.freeze([]) });
    }
    if (runEpoch !== epoch) return;
    if (selectedObservationId && !model.events.some((event) => event.recordId === selectedObservationId)) {
      selectedObservationId = null;
    }
    renderProduction();
  }

  async function activate(nextContext, { target, onInspect, selected = null, mode = "production" } = {}) {
    const nextMode = mode === "fixtures" ? "fixtures" : "production";
    const nextKey = contextKey(nextContext, nextMode);
    host = target;
    inspect = onInspect;
    context = nextContext;
    launchMode = nextMode;
    if (selected?.kind === "salience-observation") selectedObservationId = selected.id;
    if (nextKey === key) {
      if (launchMode === "fixtures") renderFixture(selectedObservationId);
      else renderProduction();
      return;
    }
    key = nextKey;
    const runEpoch = ++epoch;
    if (launchMode === "fixtures") {
      model = null;
      renderFixture(selectedObservationId);
      return;
    }
    model = Object.freeze({ state: "LOADING", coverage: "UNKNOWN", events: Object.freeze([]) });
    renderProduction();
    await load(runEpoch);
  }

  function deactivate() {
    epoch += 1;
    key = null;
    host = null;
    inspect = null;
    context = null;
    model = null;
  }

  return Object.freeze({ activate, deactivate, state: () => ({ model, activeTab, selectedObservationId, launchMode }) });
}
