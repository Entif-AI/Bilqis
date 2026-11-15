import {
  historicalResourceQuery, resourceProfileFromPage, resourceQuery,
} from "./resource-model.mjs";
import { bindResourceInteractions, renderResourceMarkup } from "./resource-view.mjs";

function contextKey(context) {
  return context ? [context.runId, context.generation, context.mode].join(":") : "none";
}

export function createResourceController(api, { launchMode = "production" } = {}) {
  let key = null;
  let context = null;
  let state = null;
  let host = null;
  let inspect = null;
  let historical = false;
  let unsubscribe = null;
  let loadPromise = null;
  let epoch = 0;
  let currentRequest = 0;
  let comparisonRequest = 0;
  let fixtureStatePromise = null;
  const fixtureEnabled = launchMode === "fixtures";
  const fixtureState = () => fixtureStatePromise ??= import("./resource-fixture-state.mjs");

  function render(preserve = true) {
    if (!host) return;
    const input = preserve && host.querySelector('[data-test-id="resources-compare-generation"]');
    const focused = input && input.ownerDocument?.activeElement === input;
    const draft = input?.value;
    const selection = input && [input.selectionStart, input.selectionEnd, input.selectionDirection];
    const activeHook = preserve && host.ownerDocument?.activeElement?.getAttribute("data-test-id");
    const disclosure = host.querySelector('[data-test-id="resources-semantics"]');
    const expanded = preserve ? disclosure?.open : undefined;
    host.hidden = false;
    host.innerHTML = renderResourceMarkup(state, { historical });
    host.__resourceState = state;
    bindResourceInteractions(host, { onInspect: inspect, onCompare: loadComparison });
    const next = host.querySelector('[data-test-id="resources-compare-generation"]');
    if (next && draft !== undefined) next.value = draft;
    if (focused) {
      next?.focus({ preventScroll: true });
      if (next && selection?.[0] != null) next.setSelectionRange(...selection);
    } else if (activeHook) {
      [...host.querySelectorAll("[data-test-id]")].find(element => element.getAttribute("data-test-id") === activeHook)?.focus({ preventScroll: true });
    }
    const nextDisclosure = host.querySelector('[data-test-id="resources-semantics"]');
    if (nextDisclosure && expanded !== undefined) nextDisclosure.open = expanded;
  }

  function comparisonFields() {
    return {
      comparison: state?.comparison ?? null,
      comparisonState: state?.comparisonState ?? "EMPTY",
      comparisonGeneration: state?.comparisonGeneration ?? null,
    };
  }

  async function loadCurrent() {
    const runEpoch = epoch;
    const request = ++currentRequest;
    const requestContext = context;
    const fixture = fixtureEnabled && requestContext?.runId === "fixture-run";
    const valid = () => runEpoch === epoch && request === currentRequest;
    try {
      const page = await api.query(resourceQuery(requestContext));
      if (!valid()) return;
      const fixtures = fixture ? await fixtureState() : null;
      if (fixture && historical &&
          requestContext.generation === fixtures.historicalResourceFixture().generation) {
        state = { current: fixtures.historicalResourceFixture(), ...comparisonFields() };
      } else if (fixture && !historical && (page?.accepted !== true || page?.state === "EMPTY")) {
        state = { ...fixtures.referenceResourceState(), ...comparisonFields() };
      } else {
        state = { current: resourceProfileFromPage(page, requestContext), ...comparisonFields() };
      }
    } catch (_error) {
      if (!valid()) return;
      if (fixture) {
        const fixtures = await fixtureState();
        if (historical && requestContext.generation === fixtures.historicalResourceFixture().generation) {
          state = { current: fixtures.historicalResourceFixture(), ...comparisonFields() };
        } else if (!historical) {
          state = { ...fixtures.referenceResourceState(), ...comparisonFields() };
        } else {
          state = { current: null, currentState: "UNAVAILABLE", ...comparisonFields() };
        }
      } else state = { current: null, currentState: "UNAVAILABLE", ...comparisonFields() };
    }
    state = Object.freeze(state);
    render();
  }

  async function loadComparison(generation) {
    if (!context) return;
    const requestContext = context;
    const query = historicalResourceQuery(requestContext, generation);
    const runEpoch = epoch;
    const request = ++comparisonRequest;
    state = Object.freeze({ ...state, comparison: null, comparisonState: "LOADING", comparisonGeneration: generation });
    render();
    if (fixtureEnabled && requestContext.runId === "fixture-run") {
      const fixtures = await fixtureState();
      if (generation === fixtures.historicalResourceFixture().generation) {
        state = Object.freeze({
          ...state,
          comparison: fixtures.historicalResourceFixture(),
          comparisonState: "PRESENT",
        });
        render();
        return;
      }
    }
    try {
      const page = await api.query(query);
      if (runEpoch !== epoch || request !== comparisonRequest) return;
      const profile = resourceProfileFromPage(page, { ...requestContext, mode: "HISTORICAL", generation });
      state = Object.freeze({ ...state, comparison: page?.accepted === true && profile.timeline.length > 0 ? profile : null,
        comparisonState: page?.accepted === true ? page.state : "UNAVAILABLE" });
    } catch (_error) {
      if (runEpoch !== epoch || request !== comparisonRequest) return;
      state = Object.freeze({ ...state, comparison: null, comparisonState: "UNAVAILABLE" });
    }
    render();
  }

  function subscribe(runEpoch) {
    if (runEpoch !== epoch || historical || typeof api.subscribeEvents !== "function") return;
    try {
      unsubscribe = api.subscribeEvents(async (event) => {
        if (runEpoch !== epoch || !String(event?.event_family ?? "").startsWith("resource.")) return;
        await loadCurrent();
      });
    } catch (_error) { unsubscribe = null; }
  }

  async function activate(nextContext, { target, onInspect, defense } = {}) {
    const nextHistorical = Boolean(defense?.historical || nextContext?.mode === "HISTORICAL");
    const nextKey = `${contextKey(nextContext)}:${nextHistorical}`;
    if (key === nextKey) {
      host = target;
      inspect = onInspect;
      render();
      return loadPromise;
    }
    const runEpoch = ++epoch;
    const stop = unsubscribe;
    unsubscribe = null;
    host = target;
    inspect = onInspect;
    context = nextContext;
    historical = nextHistorical;
    key = nextKey;
    state = { current: null, currentState: "LOADING", comparison: null, comparisonState: "EMPTY" };
    render(false);
    if (typeof stop === "function") await stop();
    if (runEpoch !== epoch) return;
    loadPromise = loadCurrent().then(() => subscribe(runEpoch));
    return loadPromise;
  }

  async function deactivate() {
    epoch += 1;
    const stop = unsubscribe;
    unsubscribe = null;
    host = null;
    inspect = null;
    context = null;
    key = null;
    if (typeof stop === "function") await stop();
  }

  return Object.freeze({ activate, deactivate, currentState: () => state, loadComparison });
}
