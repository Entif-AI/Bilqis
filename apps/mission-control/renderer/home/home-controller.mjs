import {
  HOME_FAMILIES,
  familyForEvent,
  projectionFromPages,
  queryRequest,
} from "./home-model.mjs";
import { bindHomeInteractions, renderHomeMarkup } from "./home-view.mjs";

function contextKey(context) {
  return context
    ? [context.runId, context.generation, context.mode, context.operatorActive].join(":")
    : "none";
}

export function createHomeController(api, { launchMode = "production" } = {}) {
  let key = null;
  let pages = {};
  let model = null;
  let loadPromise = null;
  let unsubscribe = null;
  let renderTarget = null;
  let inspectTarget = null;
  let navigateTarget = null;
  let context = null;
  let historical = false;
  let fixtureModulePromise = null;
  const fixtureEnabled = launchMode === "fixtures";
  const fixtureProjection = async () => {
    fixtureModulePromise ??= import("./home-fixture.mjs");
    return (await fixtureModulePromise).referenceHomeProjection();
  };

  function render() {
    if (!renderTarget || !model) return;
    renderTarget.hidden = false;
    renderTarget.innerHTML = renderHomeMarkup(model, { historical });
    bindHomeInteractions(renderTarget, inspectTarget ?? (() => {}), navigateTarget ?? (() => {}));
  }

  async function loadFamily(family) {
    const request = queryRequest(family, context);
    const page = await api.query(request);
    pages = { ...pages, [family]: page };
    model = projectionFromPages(pages, context);
    render();
  }

  async function loadAll() {
    const entries = await Promise.all(HOME_FAMILIES.map(async (family) => {
      try {
        return [family, await api.query(queryRequest(family, context))];
      } catch (_error) {
        return [family, { accepted: false, state: "UNAVAILABLE", records: [] }];
      }
    }));
    pages = Object.fromEntries(entries);
    model = projectionFromPages(pages, context);
    if (fixtureEnabled && context?.runId === "fixture-run" && context?.mode !== "HISTORICAL" &&
        HOME_FAMILIES.every((family) => pages[family]?.accepted !== true || pages[family]?.state === "EMPTY")) {
      model = await fixtureProjection();
    }
    render();
  }

  async function refreshOperatorStatus() {
    let operatorActive = null;
    if (!historical && typeof api.status === "function") {
      try {
        const status = await api.status();
        operatorActive = typeof status?.learnerActive === "boolean"
          ? status.learnerActive
          : null;
      } catch (_error) {
        operatorActive = null;
      }
    }
    context = Object.freeze({ ...context, operatorActive });
  }

  async function subscribe() {
    if (historical || typeof api.subscribeEvents !== "function") return;
    try {
      unsubscribe = api.subscribeEvents(async (event) => {
        if (event?.event_family === "operator.action.state") {
          await refreshOperatorStatus();
          model = projectionFromPages(pages, context);
          render();
          return;
        }
        const family = familyForEvent(event);
        if (!family || context?.mode === "HISTORICAL") return;
        try {
          await loadFamily(family);
        } catch (_error) {
          pages = { ...pages, [family]: { accepted: false, state: "UNAVAILABLE", records: [] } };
          model = projectionFromPages(pages, context);
          render();
        }
      });
    } catch (_error) {
      unsubscribe = null;
    }
  }

  async function activate(nextContext, { host, onInspect, onNavigate, defense } = {}) {
    renderTarget = host;
    inspectTarget = onInspect;
    navigateTarget = onNavigate;
    historical = Boolean(defense?.historical || nextContext?.mode === "HISTORICAL");
    context = nextContext;
    await refreshOperatorStatus();
    const nextKey = contextKey(context) + `:${historical}`;
    if (key === nextKey) {
      render();
      return loadPromise;
    }
    key = nextKey;
    pages = {};
    model = fixtureEnabled && nextContext?.runId === "fixture-run" && nextContext?.mode !== "HISTORICAL"
      ? await fixtureProjection() : null;
    if (typeof unsubscribe === "function") {
      await unsubscribe();
      unsubscribe = null;
    }
    render();
    loadPromise = loadAll().then(subscribe);
    return loadPromise;
  }

  async function deactivate() {
    const stop = unsubscribe;
    unsubscribe = null;
    renderTarget = null;
    inspectTarget = null;
    navigateTarget = null;
    key = null;
    if (typeof stop === "function") await stop();
  }

  function currentModel() {
    return model;
  }

  return Object.freeze({ activate, deactivate, currentModel });
}
