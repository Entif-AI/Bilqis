import { correctionQuery, productionProjectionFromPage } from "./corrections-model.mjs";
import { bindCorrectionsInteractions, renderCorrectionsMarkup } from "./corrections-view.mjs";

function contextKey(context) { return context ? [context.runId, context.generation, context.mode, context.fixture === true].join(":") : "none"; }

export function createCorrectionsController(api, { fixtureSupport = null } = {}) {
  let key = null; let context = null; let host = null; let inspect = null; let selected = null; let projection = null;
  let activeTab = "context"; let request = 0;

  function render() {
    if (!host || !projection) return;
    const openIds = [...host.querySelectorAll("details[data-test-id][open]")].map(item => item.dataset.testId);
    const focused = host.ownerDocument?.activeElement?.getAttribute?.("data-focus-key") ?? null;
    const fixture = context?.fixture === true && fixtureSupport;
    host.hidden = false;
    host.innerHTML = renderCorrectionsMarkup(projection, {
      activeTab,
      messages: fixture?.messages,
      fixtureNotice: fixture?.notice ?? null,
    });
    bindCorrectionsInteractions(host, projection, {
      onTabChange: tab => { activeTab = tab; },
      onInspect: (id, node) => inspect?.({ kind: "correction", id, fixtureBacked: context?.fixture === true, details: { "Artifact class": node.kind, "Impact state": node.state, "Evidence references": node.evidenceRefs } }),
      onReference: (ref, kind) => inspect?.({ kind: "correction", id: ref, fixtureBacked: context?.fixture === true, details: { "Exact reference": ref, "Reference type": kind } }),
    });
    for (const id of openIds) { const disclosure = host.querySelector(`[data-test-id="${id}"]`); if (disclosure) disclosure.open = true; }
    if (focused) host.querySelector(`[data-focus-key="${focused}"]`)?.focus?.({ preventScroll: true });
  }

  async function load() {
    const epoch = ++request; const source = context; const fixture = source?.fixture === true && fixtureSupport;
    if (fixture) { projection = fixture.projection; render(); return; }
    try {
      const page = await api.query(correctionQuery(source));
      if (epoch !== request || source !== context) return;
      projection = productionProjectionFromPage(page, source, selected?.id ?? null);
    } catch (_error) {
      if (epoch !== request || source !== context) return;
      projection = productionProjectionFromPage(null, source, selected?.id ?? null);
    }
    render();
  }

  async function activate(nextContext, { target, onInspect, selection } = {}) {
    const nextKey = contextKey(nextContext);
    host = target; inspect = onInspect; selected = selection ?? null;
    if (key === nextKey) { render(); return; }
    key = nextKey; context = nextContext; activeTab = "context"; projection = null;
    return load();
  }
  async function deactivate() { request += 1; key = null; context = null; host = null; inspect = null; selected = null; projection = null; }
  return Object.freeze({ activate, deactivate, currentProjection: () => projection });
}
