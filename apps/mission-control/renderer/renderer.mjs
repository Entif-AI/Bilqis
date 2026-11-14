import { createFrameShell } from "./frames/frame-shell.mjs";
import {
  inspect,
  navigate,
  openSelectionOwner,
  returnFromEvidence,
  selectObject,
  withDefensiveState,
  withRoute,
} from "./shell-state.mjs";
import { buildDeepLink } from "./deep-link.mjs";
import {
  applyDisplaySettings,
  loadDisplaySettings,
} from "./settings.mjs";
import { defensiveState } from "./foundation/defensive-state.mjs";
import {
  renderChrome,
  renderContext,
  renderNavigation,
  renderInspector,
  renderPaletteOptions,
} from "./foundation/renderer-ui.mjs";
import {
  focusToken,
  restoreFocus,
} from "./foundation/accessibility.mjs";
import { createHomeController } from "./home/home-controller.mjs";
import { createResourceController } from "./resources/resource-controller.mjs";
import { createOperateController } from "./operate/operate-controller.mjs";
import { createCapabilityExplorer } from "./capability/app.mjs";
import { activateDomainViews } from "./foundation/domain-controller.mjs";
import { createInteractionController } from "./interactions/controller.mjs";
import { routeForObjectRef } from "./interactions/app-uri.mjs";
import { withHistoricalLens } from "./interactions/model.mjs";
import { createBootstrapController } from "./foundation/bootstrap-controller.mjs";
import { bindStaticInteractions } from "./foundation/static-interactions.mjs";

let state = null;
let verifiedLiveContext = null;
let displaySettings;
let defense = defensiveState("loading");
let bootstrap = Object.freeze({ phase: "connecting", connection: null, error: null });
let focusReturnToken = null;
let paletteReturnToken = null;
const homeController = createHomeController(window.bamfMissionControl);
const resourceController = createResourceController(window.bamfMissionControl);
const interactionController = createInteractionController({
  document,
  storage: window.localStorage,
  getState: () => state,
  onTimeLens: (generation) => { state = withHistoricalLens(state, generation); render(); },
  onCurrentLens: () => {
    if (!state || !verifiedLiveContext) {
      announce("No verified current context is available.");
      return;
    }
    state = withDefensiveState({ ...state, context: verifiedLiveContext }, defense);
    render();
  },
  canUseCurrent: () => Boolean(verifiedLiveContext),
  onOpenRef: (ref) => { state = withRoute(state, routeForObjectRef(ref)); render(); },
  announce,
});
const operateController = createOperateController(window.bamfMissionControl);

const frameShell = createFrameShell({
  getState: () => state, setState: next => { state = next; }, getDefense: () => defense,
  render, onInspect: openInspector,
  refresh: () => { renderContext(state, defense); renderNavigation(state, navigateTo); renderInspector(state, defense); setHash(); },
});
const { establishSnapshot } = createBootstrapController({
  api: window.bamfMissionControl,
  storage: window.localStorage,
  getState: () => state,
  setState: (next) => { state = next; },
  setDefense: (next) => { defense = next; },
  setBootstrap: (next) => { bootstrap = next; },
  setVerifiedLiveContext: (next) => { verifiedLiveContext = next; },
  resetFrameShell: () => frameShell.reset(),
  render,
  announce,
  currentHash: () => window.location.hash,
});
const capabilityExplorer = createCapabilityExplorer({
  host: document.querySelector("#domain-view"),
  serviceQuery: request => window.bamfMissionControl.querySnapshot(request),
  changeLens: (lens, capabilityId) => {
    if (!state) return;
    state = {
      ...state,
      context: Object.freeze({
        ...state.context, ...lens,
        historicalPinned: lens.mode === "HISTORICAL",
        generationManifest: "UNKNOWN", topologyId: "UNKNOWN",
        factoryRelease: "UNKNOWN", semanticRelease: "UNKNOWN",
        coverage: "UNKNOWN", freshness: "UNKNOWN",
      }),
      selected: { kind: "capability", id: capabilityId },
      inspectorOpen: false,
      mutationAvailable: false,
    };
    render();
  },
  openObject: (selected) => {
    if (!state) return;
    state = { ...openSelectionOwner(inspect(state, selected)), inspectorOpen: false };
    render();
  },
  resolvePins: (meta) => {
    if (!state) return;
    state = {
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
    renderContext(state, defense);
    setHash();
  },
});

function setHash() {
  if (!state) return;
  const next = buildDeepLink(state);
  if (window.location.hash !== next) history.replaceState(null, "", next);
}

function announce(message) {
  const announcer = document.querySelector("#announcer");
  announcer.textContent = "";
  window.queueMicrotask(() => { announcer.textContent = message; });
}

function render() {
  frameShell.beforeRender();
  renderChrome(state, defense, displaySettings, {
    api: window.bamfMissionControl,
    onEvidenceSelect: selectEvidenceRecord,
    onEvidenceReturn: returnEvidenceOrigin,
    onReconnect: () => establishSnapshot({ preserveRoute: true }),
    onNavigate: navigateTo,
    onInspect: openInspector,
  }, bootstrap);
  frameShell.afterRender();
  setHash();
  activateDomainViews({
    state, getState: () => state, defense, api: window.bamfMissionControl,
    homeController, resourceController, operateController,
    capabilityExplorer, onInspect: openInspector, onAnnounce: announce,
  });
  window.queueMicrotask(() => interactionController.render());
}

function selectEvidenceRecord(selected) {
  if (!state) return;
  state = selectObject(state, selected);
  renderInspector(state, defense);
  interactionController.render();
  setHash();
}

function returnEvidenceOrigin() {
  if (!state?.evidenceOrigin) return;
  state = returnFromEvidence(state);
  render();
  announce("Returned to the inspected evidence origin.");
}

function navigateTo(view) {
  state = navigate(state, view);
  document.querySelector("#command-palette")?.close?.();
  render();
  window.queueMicrotask(() => document.querySelector("#view-title")?.focus?.({ preventScroll: true }));
}

function openInspector(selected) {
  if (!state) return;
  focusReturnToken = focusToken(document.activeElement);
  state = inspect(state, selected);
  renderInspector(state, defense);
  interactionController.render();
  setHash();
  window.queueMicrotask(() => document.querySelector("#inspector-close")?.focus());
  announce(`Inspector opened for ${selected.id}`);
}

function closeInspector() {
  if (!state?.inspectorOpen) return;
  state = inspect(state, null);
  renderInspector(state, defense);
  interactionController.render();
  setHash();
  window.queueMicrotask(() => restoreFocus(document, focusReturnToken));
  announce("Inspector closed");
}

function openPalette() {
  const dialog = document.querySelector("#command-palette");
  paletteReturnToken = focusToken(document.activeElement);
  renderPaletteOptions(state, (view) => {
    navigateTo(view);
    window.queueMicrotask(() => document.querySelector("#main-content")?.focus());
  });
  if (!dialog.open) dialog.showModal();
  window.queueMicrotask(() => dialog.querySelector("button:not(:disabled)")?.focus());
}

async function bootstrap() {
  displaySettings = loadDisplaySettings(window.localStorage);
  applyDisplaySettings(document.documentElement, displaySettings);
  bindStaticInteractions({
    document,
    window,
    getState: () => state,
    setState: (next) => { state = next; },
    getDisplaySettings: () => displaySettings,
    setDisplaySettings: (next) => { displaySettings = next; },
    render,
    closeInspector,
    openPalette,
    interactionController,
  });
  document.querySelector("#command-palette").addEventListener("close", () => {
    window.queueMicrotask(() => restoreFocus(document, paletteReturnToken));
  });
  render();
  await establishSnapshot();
}

bootstrap();
