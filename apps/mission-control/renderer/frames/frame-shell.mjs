import { normalizeContext } from "../shell-state.mjs";
import { mountFrameExplorer } from "./frame-explorer.mjs";

export function createFrameShell({ getState, setState, getDefense, render, refresh, onInspect }) {
  let mounted = null;
  let routeId = null;
  let returnContext = null;
  const active = () => getState()?.view === "model" && getState()?.modelSection === "frames" && getDefense().id !== "loading";
  function reset() {
    mounted?.dispose(); mounted = null; routeId = null; returnContext = null;
  }
  document.querySelectorAll("[data-model-section]").forEach(button => {
    button.addEventListener("click", () => {
      if (!getState()) return;
      setState({ ...getState(), modelSection: button.dataset.modelSection, selected: null, inspectorOpen: false });
      render();
    });
  });
  return {
    reset,
    beforeRender() {
      const state = getState();
      if (state?.view === "model") {
        const section = state.selected?.kind === "frame" ? "frames" : state.selected?.kind === "neural" ? "neural" : state.modelSection ?? "neural";
        setState({ ...state, modelSection: section });
      }
      if (!active()) {
        mounted?.dispose(); mounted = null; routeId = null;
        if (returnContext && getState()) {
          setState({ ...getState(), context: returnContext, mutationAvailable: getDefense().mutationAllowed === true });
        }
        returnContext = null;
      } else {
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
      const selectedId = state.selected?.kind === "frame" ? state.selected.id : null;
      if (mounted && (!selectedId || routeId === selectedId)) return;
      mounted?.dispose(); routeId = selectedId;
      mounted = mountFrameExplorer(host, {
        querySnapshot: request => window.bamfMissionControl.querySnapshot(request),
        context: state.context, selectedId,
        onContext(operatorView, mode) {
          setState({ ...getState(), mutationAvailable: false, context: Object.freeze({
            ...normalizeContext(operatorView), freshness: getState().context.freshness,
            mode: mode === "historical" || getDefense().historical ? "HISTORICAL" : "LIVE",
          }) });
          refresh();
        },
        onSelection(id) {
          routeId = id || null;
          if (id) onInspect({ kind: "frame", id });
          else { setState({ ...getState(), selected: null, inspectorOpen: false }); refresh(); }
        },
      });
    },
  };
}
