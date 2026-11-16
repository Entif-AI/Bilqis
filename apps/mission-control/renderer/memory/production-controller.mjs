import { historicalMemoryQuery, memoryProfileFromPage, memoryQuery } from "./production-model.mjs";
import { bindProductionMemory, productionMemoryMarkup } from "./production-view.mjs";

const contextKey = context => context ? [context.runId, context.generation, context.mode].join(":") : "none";

export function createProductionMemoryController(api) {
  let key = null;
  let context = null;
  let host = null;
  let inspect = null;
  let historical = false;
  let activeTab = "overview";
  let state = null;
  let epoch = 0;
  let compareRequest = 0;
  let unsubscribe = null;

  function paint() {
    if (!host) return;
    const draft = host.querySelector('[data-test-id="memory-production-compare-generation"]')?.value;
    host.hidden = false;
    host.innerHTML = productionMemoryMarkup(state, { activeTab, historical });
    bindProductionMemory(host, {
      state,
      onInspect: inspect,
      onTabChange: id => { activeTab = id; },
      onCompare: loadComparison,
    });
    const input = host.querySelector('[data-test-id="memory-production-compare-generation"]');
    if (input && draft !== undefined) input.value = draft;
  }

  function comparisonFields() {
    return {
      comparison: state?.comparison ?? null,
      comparisonState: state?.comparisonState ?? "EMPTY",
      comparisonGeneration: state?.comparisonGeneration ?? null,
    };
  }

  async function loadCurrent(runEpoch) {
    try {
      const page = await api.query(memoryQuery(context));
      if (runEpoch !== epoch) return;
      state = Object.freeze({ current: memoryProfileFromPage(page, context), currentState: page?.accepted === true ? page.state : "UNAVAILABLE", ...comparisonFields() });
    } catch (_error) {
      if (runEpoch !== epoch) return;
      state = Object.freeze({ current: null, currentState: "UNAVAILABLE", ...comparisonFields() });
    }
    paint();
  }

  async function loadComparison(generation) {
    if (!context) return;
    const token = ++compareRequest;
    const runEpoch = epoch;
    state = Object.freeze({ ...state, comparison: null, comparisonState: "LOADING", comparisonGeneration: generation });
    paint();
    try {
      const page = await api.query(historicalMemoryQuery(context, generation));
      if (runEpoch !== epoch || token !== compareRequest) return;
      const profile = memoryProfileFromPage(page, { ...context, mode: "HISTORICAL", generation });
      state = Object.freeze({ ...state, comparison: profile, comparisonState: page?.accepted === true ? page.state : "UNAVAILABLE" });
    } catch (_error) {
      if (runEpoch !== epoch || token !== compareRequest) return;
      state = Object.freeze({ ...state, comparison: null, comparisonState: "UNAVAILABLE" });
    }
    paint();
  }

  function subscribe(runEpoch) {
    if (historical || typeof api.subscribeEvents !== "function") return;
    try {
      unsubscribe = api.subscribeEvents(event => {
        if (runEpoch !== epoch || !String(event?.event_family ?? "").startsWith("memory.")) return;
        void loadCurrent(runEpoch);
      });
    } catch (_error) { unsubscribe = null; }
  }

  async function activate(nextContext, { target, onInspect, defense } = {}) {
    const nextHistorical = Boolean(defense?.historical || nextContext?.mode === "HISTORICAL");
    const nextKey = `${contextKey(nextContext)}:${nextHistorical}`;
    if (key === nextKey && state) {
      host = target;
      inspect = onInspect;
      paint();
      return;
    }
    epoch += 1;
    const runEpoch = epoch;
    const stop = unsubscribe;
    unsubscribe = null;
    key = nextKey;
    context = nextContext;
    host = target;
    inspect = onInspect;
    historical = nextHistorical;
    activeTab = "overview";
    state = Object.freeze({ current: null, currentState: "LOADING", comparison: null, comparisonState: "EMPTY", comparisonGeneration: null });
    paint();
    if (typeof stop === "function") await stop();
    if (runEpoch !== epoch) return;
    await loadCurrent(runEpoch);
    subscribe(runEpoch);
  }

  async function deactivate() {
    epoch += 1;
    const stop = unsubscribe;
    unsubscribe = null;
    key = null;
    context = null;
    host = null;
    inspect = null;
    if (typeof stop === "function") await stop();
  }

  return Object.freeze({ activate, deactivate, currentState: () => state, loadComparison });
}
