import {
  HOME_FAMILIES,
  familyForEvent,
  projectionFromPages,
  queryRequest,
} from "./home-model.mjs";
import { bindHomeInteractions, renderHomeMarkup } from "./home-view.mjs";

function acceptedIdentity(page) {
  const run = page?.records?.find((record) => record.schema_version?.endsWith(".run-context/v1"));
  const ref = run?.meta?.run;
  return ref ? JSON.stringify([ref.run_id, ref.generation, ref.generation_manifest_sha256]) : null;
}

export function createHomeController(api, {
  referenceProjection = null,
  schedule = (callback, delay) => { const timer = setTimeout(callback, delay); timer.unref?.(); return timer; },
  cancel = (timer) => clearTimeout(timer),
} = {}) {
  let pages = {}, model = null, context = null, historical = false;
  let renderTarget = null, inspectTarget = null, navigateTarget = null;
  let unsubscribe = null, timer = null, epoch = 0, queue = Promise.resolve();
  let disconnected = false, needsSnapshot = false, pending = new Map();
  let activationKey = null;

  function keyFor(nextContext, nextHistorical) {
    return JSON.stringify([
      nextContext?.runId ?? null,
      nextContext?.generation ?? null,
      nextContext?.mode ?? null,
      nextContext?.generationManifest ?? null,
      nextContext?.factoryRelease ?? null,
      nextContext?.semanticRelease ?? null,
      nextContext?.topologyId ?? null,
      nextContext?.fixture === true,
      nextHistorical,
    ]);
  }

  function render({ resetDetails = false } = {}) {
    if (!renderTarget || !model) return;
    const openIds = resetDetails ? [] : [...renderTarget.querySelectorAll("details[data-test-id][open]")]
      .map((item) => item.dataset.testId);
    renderTarget.hidden = false;
    renderTarget.innerHTML = renderHomeMarkup(model, { historical });
    for (const id of openIds) {
      const details = renderTarget.querySelector(`[data-test-id="${id}"]`);
      if (details) details.open = true;
    }
    bindHomeInteractions(renderTarget, inspectTarget ?? (() => {}), navigateTarget ?? (() => {}));
  }
  function project(fixtureFallback = true) {
    model = projectionFromPages(pages, context);
    if (fixtureFallback && referenceProjection && context?.fixture === true && context?.mode !== "HISTORICAL" &&
        HOME_FAMILIES.every((family) => pages[family]?.accepted !== true || pages[family]?.state === "EMPTY")) {
      const fixture = referenceProjection();
      model = { ...fixture, runtime: { ...fixture.runtime, running: context?.operatorActive ?? fixture.runtime.running } };
    }
    render();
  }
  function failed(current) {
    if (current !== epoch) return;
    disconnected = true;
    context = { ...context, transportDisconnected: true, operatorActive: null };
    project();
  }
  function enqueue(current, operation) {
    const result = queue.then(async () => {
      if (current !== epoch) return;
      try { await operation(); } catch (_error) { failed(current); }
    });
    queue = result;
    return result;
  }
  async function loadFamily(family, current) {
    const page = await api.query(queryRequest(family, context));
    if (current !== epoch) return null;
    if (page?.accepted !== true) throw new Error("HOME_QUERY_UNAVAILABLE");
    pages = { ...pages, [family]: page };
    project();
    return page;
  }
  async function loadAll(current) {
    const source = context;
    const request = (family) => api.query(queryRequest(family, source));
    const anchor = historical ? null : await request("run");
    if (current !== epoch) return;
    const families = historical ? HOME_FAMILIES : HOME_FAMILIES.filter((family) => family !== "run");
    const entries = await Promise.all(families.map(async (family) => [family, await request(family)]));
    if (current !== epoch) return;
    const frontier = historical ? null : await request("run");
    if (current !== epoch) return;
    if ([...entries.map(([, page]) => page), ...[anchor, frontier].filter(Boolean)]
      .some((page) => page?.accepted !== true)) throw new Error("HOME_QUERY_UNAVAILABLE");
    if (!historical && acceptedIdentity(anchor) !== acceptedIdentity(frontier)) {
      needsSnapshot = true;
      return;
    }
    pages = Object.fromEntries(historical ? entries : [...entries, ["run", frontier]]);
    needsSnapshot = false;
    disconnected = false;
    context = { ...context, transportDisconnected: false };
    project(true);
  }
  async function refreshRun(current) {
    const page = await api.query(queryRequest("run", context));
    if (current !== epoch) return;
    if (page?.accepted !== true) throw new Error("HOME_QUERY_UNAVAILABLE");
    if (needsSnapshot || acceptedIdentity(pages.run) !== acceptedIdentity(page)) return loadAll(current);
    pages = { ...pages, run: page };
    project(true);
  }
  async function refreshStatus(current) {
    if (historical || typeof api.status !== "function") return;
    const status = await api.status();
    if (current !== epoch) return;
    context = { ...context, operatorActive: typeof status?.learnerActive === "boolean" ? status.learnerActive : null };
    project();
  }
  function enqueueOnce(current, key, operation) {
    if (pending.has(key)) return pending.get(key);
    const tasks = pending;
    const result = enqueue(current, operation).finally(() => { if (tasks.get(key) === result) tasks.delete(key); });
    tasks.set(key, result);
    return result;
  }
  async function subscribe(current) {
    if (historical || typeof api.subscribeEvents !== "function") return;
    let stop;
    try { stop = await api.subscribeEvents((event) => enqueueOnce(current, event?.event_family ?? "unknown", async () => {
      if (event?.event_family === "operator.action.state") return refreshStatus(current);
      const family = familyForEvent(event);
      if (!family) return;
      if (event.event_family === "run.trainer.observed") return refreshRun(current);
      if (event.event_family?.startsWith("run.") || event.event_family?.startsWith("checkpoint.")) return loadAll(current);
      return loadFamily(family, current);
    })); } catch (_error) { return; }
    if (current !== epoch) { if (typeof stop === "function") await stop(); return; }
    unsubscribe = stop;
  }
  async function recover(current) {
    if (disconnected) {
      if (typeof api.connect === "function") await api.connect();
      if (current !== epoch) return;
      const stop = unsubscribe;
      unsubscribe = null;
      if (typeof stop === "function") await stop();
      if (current !== epoch) return;
      await subscribe(current);
      if (current !== epoch) return;
      await refreshStatus(current);
      await loadAll(current);
    } else {
      await refreshStatus(current);
      if (current !== epoch) return;
      await refreshRun(current);
    }
  }
  function startTimer(current) {
    if (current !== epoch || historical) return;
    timer = schedule(async () => {
      timer = null;
      await enqueue(current, () => recover(current));
      startTimer(current);
    }, 2000);
  }
  async function activate(nextContext, { host, onInspect, onNavigate, defense } = {}) {
    const nextHistorical = Boolean(defense?.historical || nextContext?.mode === "HISTORICAL");
    const nextKey = keyFor(nextContext, nextHistorical);
    if (activationKey === nextKey) {
      renderTarget = host;
      inspectTarget = onInspect;
      navigateTarget = onNavigate;
      render();
      return queue;
    }
    const current = ++epoch;
    if (timer !== null) { cancel(timer); timer = null; }
    const stop = unsubscribe;
    unsubscribe = null;
    queue = Promise.resolve(); pending = new Map();
    renderTarget = host; inspectTarget = onInspect; navigateTarget = onNavigate;
    historical = nextHistorical;
    activationKey = nextKey;
    context = { ...nextContext, mode: historical ? "HISTORICAL" : nextContext?.mode }; pages = {}; disconnected = false; needsSnapshot = false;
    model = referenceProjection && nextContext?.fixture === true && !historical ? referenceProjection() : null;
    render({ resetDetails: true });
    if (typeof stop === "function") await stop();
    if (current !== epoch) return;
    await enqueue(current, async () => {
      await subscribe(current);
      if (current !== epoch) return;
      await refreshStatus(current);
      if (current !== epoch) return;
      await loadAll(current);
    });
    startTimer(current);
  }
  async function deactivate() {
    ++epoch;
    activationKey = null;
    if (timer !== null) { cancel(timer); timer = null; }
    const stop = unsubscribe;
    unsubscribe = null;
    renderTarget = null; inspectTarget = null; navigateTarget = null;
    if (typeof stop === "function") await stop();
  }
  return Object.freeze({ activate, deactivate, currentModel: () => model });
}
