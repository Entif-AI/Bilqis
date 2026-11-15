import { normalizeContext } from "../shell-state.mjs";
import { t } from "../foundation/i18n.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";

const esc = value => String(value ?? "").replace(/[&<>"']/g, character => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[character]);

function productionFrameMarkup(context) {
  const mode = context?.mode === "HISTORICAL" ? "historical" : "current";
  return `<div class="frame-explorer frame-production" ${testIdAttribute("model", "frame", "workspace")}>
    <header class="frame-heading"><div><span class="eyebrow">${esc(t("model.frame.eyebrow"))}</span><h2>${esc(t("model.frame.title"))}</h2></div><div class="frame-heading-detail"><p>${esc(t("model.frame.summary"))}</p>${contextHelpMarkup({ label: t("model.frame.help.concepts.label"), description: t("model.frame.help.concepts.description"), testId: "model-frame-help-concepts" })}</div></header>
    <section class="frame-production-posture" ${testIdAttribute("model", "frame", "production", "posture")}>
      <strong>${esc(t("model.frame.productionPosture", { mode: t(`model.frame.mode.${mode}`), runId: context?.runId ?? t("model.frame.unavailable"), generation: context?.generation ?? t("model.frame.unavailable") }))}</strong>
    </section>
    <section class="frame-production-unavailable" role="status" ${testIdAttribute("model", "frame", "production", "unavailable")}>
      <div><span class="eyebrow">${esc(t("model.frame.requestState"))}</span><h3>${esc(t("model.frame.productionUnavailable.title"))}</h3></div>
      <p>${esc(t("model.frame.productionUnavailable.detail"))}</p>
    </section>
  </div>`;
}

export function createFrameShell({
  getState, setState, getDefense, render, refresh, onInspect, fixtureSupport = null,
  contextForNeuralMode = null,
}) {
  let mounted = null;
  let routeId = null;
  let returnContext = null;
  let frameContext = null;
  const peerSelections = { neural: null, frames: null };
  const peerContexts = { neural: null, frames: null };
  const active = () => getState()?.view === "model" && getState()?.modelSection === "frames" && getDefense().id !== "loading";
  function reset() {
    mounted?.dispose(); mounted = null; routeId = null; returnContext = null; frameContext = null;
    peerSelections.neural = null; peerSelections.frames = null;
    peerContexts.neural = null; peerContexts.frames = null;
  }
  document.querySelectorAll("[data-model-section]").forEach(button => {
    button.addEventListener("click", () => {
      const current = getState();
      if (!current) return;
      const outgoing = ["neural", "frames"].includes(current.modelSection) ? current.modelSection : "neural";
      const target = button.dataset.modelSection;
      peerSelections[outgoing] = current.selected ?? null;
      if (current.context?.fixture === true) peerContexts[outgoing] = current.context;
      if (outgoing === "frames" && current.context?.fixture === true) frameContext = current.context;
      let context = current.context;
      let mutationAvailable = current.mutationAvailable;
      if (current.context?.fixture === true && peerContexts[target]) {
        if (target === "frames") returnContext ??= current.context;
        context = peerContexts[target];
        mutationAvailable = false;
      } else if (current.context?.fixture === true && target === "neural" &&
          typeof contextForNeuralMode === "function") {
        context = contextForNeuralMode(current.context, current.modelDiagnosticMode ?? "current");
        peerContexts.neural = context;
        mutationAvailable = false;
      }
      setState({ ...current, context, mutationAvailable, modelSection: target,
        selected: peerSelections[target], inspectorOpen: false });
      render();
    });
  });
  return {
    reset,
    beforeRender() {
      const state = getState();
      if (state?.view === "model") {
        const selectedSection = state.selected?.kind === "frame" ? "frames" : state.selected?.kind === "neural" ? "neural" : null;
        const section = ["neural", "frames"].includes(state.modelSection) ? state.modelSection : selectedSection ?? "neural";
        setState({ ...state, modelSection: section });
      }
      if (!active()) {
        mounted?.dispose(); mounted = null; routeId = null;
        const current = getState();
        if (returnContext && current?.view !== "model" && current?.modelSection === "frames") {
          setState({ ...current, context: returnContext, mutationAvailable: getDefense().mutationAllowed === true });
        }
        if (current?.view !== "model" || current?.modelSection !== "frames") returnContext = null;
      } else if (getState()?.context?.fixture === true) {
        returnContext ??= getState().context;
      }
    },
    afterRender() {
      const state = getState();
      const host = document.querySelector('[data-test-id="model-frame-workspace-host"]');
      host.hidden = !active();
      document.querySelector('[data-test-id="shell-model-subnav"]').hidden = state?.view !== "model";
      document.querySelectorAll("[data-model-section]").forEach(button => {
        button.setAttribute("aria-pressed", String(button.dataset.modelSection === state?.modelSection));
      });
      if (!active()) return;
      if (state.context?.fixture !== true) {
        mounted?.dispose(); mounted = null; routeId = null;
        host.innerHTML = productionFrameMarkup(state.context);
        return;
      }
      const selectedId = state.selected?.kind === "frame" ? state.selected.id : null;
      if (mounted && (!selectedId || routeId === selectedId)) return;
      if (typeof fixtureSupport?.mountFrameExplorer !== "function") {
        mounted?.dispose(); mounted = null; routeId = null;
        host.innerHTML = "";
        return;
      }
      mounted?.dispose(); routeId = selectedId;
      mounted = fixtureSupport.mountFrameExplorer(host, {
        querySnapshot: request => window.bamfMissionControl.querySnapshot(request),
        context: state.context, selectedId,
        onContext(operatorView, mode) {
          const historical = mode === "historical" || getDefense().historical;
          frameContext = Object.freeze({
            ...normalizeContext(operatorView), freshness: getState().context.freshness,
            mode: historical ? "HISTORICAL" : "LIVE",
            historicalPinned: mode === "historical",
            fixture: true,
          });
          peerContexts.frames = frameContext;
          setState({ ...getState(), mutationAvailable: false, context: frameContext });
          refresh();
        },
        onSelection(id) {
          routeId = id || null;
          peerSelections.frames = id ? { kind: "frame", id } : null;
          if (id) onInspect(peerSelections.frames);
          else { setState({ ...getState(), selected: null, inspectorOpen: false }); refresh(); }
        },
      });
    },
  };
}
