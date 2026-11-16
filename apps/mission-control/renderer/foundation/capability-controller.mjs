import { createCapabilityExplorer } from "../capability/app.mjs";
import { inspect, openEvidence, openSelectionOwner } from "../shell-state.mjs";

export function createShellCapabilityExplorer({
  document,
  api,
  launchMode,
  fixtureSupport,
  getState,
  setState,
  render,
  renderContext,
  getDefense,
  setHash,
}) {
  return createCapabilityExplorer({
    host: document.querySelector("#domain-view"),
    serviceQuery: request => api.querySnapshot(request),
    launchMode,
    fixtureSupport,
    changeLens: (lens, capabilityId) => {
      const state = getState();
      if (!state) return;
      setState({
        ...state,
        context: Object.freeze({
          ...state.context, ...lens,
          fixture: launchMode === "fixtures",
          historicalPinned: lens.mode === "HISTORICAL",
          generationManifest: "UNKNOWN", topologyId: "UNKNOWN",
          factoryRelease: "UNKNOWN", semanticRelease: "UNKNOWN",
          coverage: "UNKNOWN", freshness: "UNKNOWN",
        }),
        selected: { kind: "capability", id: capabilityId },
        inspectorOpen: false,
        mutationAvailable: false,
      });
      render();
    },
    openObject: (selected) => {
      const state = getState();
      if (!state) return;
      setState({ ...openSelectionOwner(inspect(state, selected)), inspectorOpen: false });
      render();
    },
    openEvidence: (selected) => {
      const state = getState();
      if (!state) return;
      setState(openEvidence(inspect(state, selected)));
      render();
    },
    resolvePins: (meta) => {
      const state = getState();
      if (!state) return;
      const next = {
        ...state,
        context: Object.freeze({
          ...state.context,
          generationManifest: meta.run.generation_manifest_sha256,
          topologyId: meta.run.topology_sha256,
          factoryRelease: meta.run.factory_release_sha256,
          semanticRelease: meta.run.semantic_release_sha256,
          coverage: meta.coverage,
        }),
      };
      setState(next);
      renderContext(next, getDefense());
      setHash();
    },
  });
}
