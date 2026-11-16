import { createFrameShell } from "./frames/frame-shell.mjs";
import {
  navigate,
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
import {
  applyShellPreferences,
  loadShellPreferences,
} from "./shell-preferences.mjs";
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
import { createTeacherController } from "./teacher/teacher-controller.mjs";
import { createSalienceController } from "./salience/salience-controller.mjs";
import { createOperateController } from "./operate/operate-controller.mjs";
import { activateDomainViews } from "./foundation/domain-controller.mjs";
import { createShellCapabilityExplorer } from "./foundation/capability-controller.mjs";
import { createInspectorController } from "./foundation/inspector-controller.mjs";
import { createInteractionController } from "./interactions/controller.mjs";
import { createProductionLearningController } from "./learning/controller.mjs";
import { createProductionNeuralController } from "./neural/neural-controller.mjs";
import { routeForObjectRef } from "./interactions/app-uri.mjs";
import { withHistoricalLens } from "./interactions/model.mjs";
import {
  constrainRouteToLaunchMode,
  createBootstrapController,
} from "./foundation/bootstrap-controller.mjs";
import { bindStaticInteractions } from "./foundation/static-interactions.mjs";
import { t } from "./foundation/i18n.mjs";

const launchMode = window.bamfMissionControl.launchMode === "fixtures" ? "fixtures" : "production";
const fixtureSupport = launchMode === "fixtures"
  ? await import("./fixture-support.mjs")
  : null;
const routeForLaunchMode = (route) => constrainRouteToLaunchMode(route, launchMode);

let state = null;
let verifiedLiveContext = null;
let displaySettings;
let shellPreferences;
let lastRenderedView = null;
let defense = defensiveState("loading");
let bootstrapState = Object.freeze({ phase: "connecting", connection: null, error: null });
let paletteReturnToken = null;
const homeController = createHomeController(window.bamfMissionControl, fixtureSupport?.home);
const resourceController = createResourceController(window.bamfMissionControl, fixtureSupport?.resources);
const teacherController = createTeacherController(window.bamfMissionControl, { fixtureSupport: fixtureSupport?.teacher ?? null });
const salienceController = createSalienceController(window.bamfMissionControl, { fixtureSupport: fixtureSupport?.salience ?? null });
const learningController = createProductionLearningController(window.bamfMissionControl);
const neuralController = createProductionNeuralController(window.bamfMissionControl);
const interactionController = createInteractionController({
  document,
  storage: window.localStorage,
  getState: () => state,
  onTimeLens: (generation) => { state = withHistoricalLens(state, generation); render(); },
  onCurrentLens: () => {
    if (!state || !verifiedLiveContext) {
      announce(t("shell.announce.noCurrent"));
      return;
    }
    state = withDefensiveState({ ...state, context: verifiedLiveContext }, defense);
    render();
  },
  canUseCurrent: () => Boolean(verifiedLiveContext),
  onOpenRef: (ref) => { state = withRoute(state, routeForLaunchMode(routeForObjectRef(ref))); render(); },
  compareRefs: fixtureSupport?.interactions?.compareRefs,
  copyText: async (value) => {
    if (!navigator.clipboard?.writeText) return false;
    try {
      await navigator.clipboard.writeText(value);
      return true;
    } catch (_error) {
      return false;
    }
  },
  announce,
});
const inspectorController = createInspectorController({
  document,
  window,
  getState: () => state,
  setState: (next) => { state = next; },
  getDefense: () => defense,
  getShellPreferences: () => shellPreferences,
  setShellPreferences: (next) => { shellPreferences = next; },
  renderInspector,
  interactionController,
  setHash,
  announce,
});
const { openInspector, closeInspector, syncInspectorWidth } = inspectorController;
const operateController = createOperateController(window.bamfMissionControl);

const frameShell = createFrameShell({
  getState: () => state, setState: next => { state = next; }, getDefense: () => defense,
  render, onInspect: openInspector, fixtureSupport: fixtureSupport?.frame ?? null,
  contextForNeuralMode: fixtureSupport?.neural?.contextForMode ?? null,
  refresh: () => { renderContext(state, defense); renderNavigation(state, navigateTo); renderInspector(state, defense); setHash(); },
});
const { establishSnapshot } = createBootstrapController({
  api: window.bamfMissionControl,
  launchMode,
  storage: window.localStorage,
  getState: () => state,
  setState: (next) => { state = next; },
  setDefense: (next) => { defense = next; },
  setBootstrap: (next) => { bootstrapState = next; },
  setVerifiedLiveContext: (next) => { verifiedLiveContext = next; },
  resetFrameShell: () => frameShell.reset(),
  render,
  announce,
  currentHash: () => window.location.hash,
});
const capabilityExplorer = createShellCapabilityExplorer({
  document,
  api: window.bamfMissionControl,
  launchMode,
  fixtureSupport: fixtureSupport?.capability ?? null,
  getState: () => state,
  setState: (next) => { state = next; },
  render,
  renderContext,
  getDefense: () => defense,
  setHash,
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
  const nextView = state?.view ?? null;
  const primaryDestinationChanged = (
    lastRenderedView !== null &&
    nextView !== null &&
    lastRenderedView !== nextView
  );
  frameShell.beforeRender();
  renderChrome(state, defense, displaySettings, shellPreferences, {
    api: window.bamfMissionControl,
    launchMode,
    fixtureSupport,
    onEvidenceSelect: selectEvidenceRecord,
    onEvidenceReturn: returnEvidenceOrigin,
    onReconnect: () => establishSnapshot({ preserveRoute: true }),
    onNavigate: navigateTo,
    onInspect: openInspector,
    onModelDiagnosticMode: (mode) => {
      if (!state || state.view !== "model" || !["current", "historical"].includes(mode)) return;
      const context = launchMode === "fixtures"
        ? fixtureSupport?.neural?.contextForMode?.(state.context, mode) ?? state.context
        : state.context;
      state = { ...state, context, modelDiagnosticMode: mode, selected: null, inspectorOpen: false };
      render();
    },
  }, bootstrapState);
  syncInspectorWidth();
  frameShell.afterRender();
  setHash();
  activateDomainViews({
    state, getState: () => state, defense, api: window.bamfMissionControl,
    homeController, resourceController, operateController,
    teacherController, salienceController, neuralController, capabilityExplorer, learningController,
    onInspect: openInspector,
    onSelectionChange: syncDomainSelection,
    onNavigate: navigateTo, onAnnounce: announce,
    schoolDomainSupport: fixtureSupport?.school ?? null,
    atlasDomainSupport: fixtureSupport?.atlas ?? null,
    correctionsDomainSupport: fixtureSupport?.corrections ?? null,
  });
  if (primaryDestinationChanged) resetPrimaryScroll();
  lastRenderedView = nextView;
  window.queueMicrotask(() => interactionController.render());
}

function resetPrimaryScroll() {
  window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  const main = document.querySelector("#main-content");
  if (main) main.scrollTop = 0;
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
  announce(t("shell.announce.returnedEvidenceOrigin"));
}

function navigateTo(view) {
  state = navigate(state, view);
  document.querySelector("#command-palette")?.close?.();
  render();
  window.queueMicrotask(() => document.querySelector("#view-title")?.focus?.({ preventScroll: true }));
  announce(t("shell.announce.destination", { destination: t(`shell.destination.${view}`) }));
}

function syncDomainSelection(selected) {
  if (!state || !selected) return;
  state = { ...state, selected };
  if (state.inspectorOpen) renderInspector(state, defense);
  interactionController.render();
  setHash();
}

function openPalette() {
  const dialog = document.querySelector("#command-palette");
  paletteReturnToken = focusToken(document.activeElement);
  renderPaletteOptions(state, navigateTo);
  if (!dialog.open) dialog.showModal();
  window.queueMicrotask(() => dialog.querySelector("button:not(:disabled)")?.focus());
}

async function bootstrap() {
  displaySettings = loadDisplaySettings(window.localStorage);
  shellPreferences = loadShellPreferences(window.localStorage);
  applyDisplaySettings(document.documentElement, displaySettings);
  applyShellPreferences(document.documentElement, shellPreferences);
  bindStaticInteractions({
    document,
    window,
    getState: () => state,
    setState: (next) => { state = next; },
    getDisplaySettings: () => displaySettings,
    setDisplaySettings: (next) => { displaySettings = next; },
    getShellPreferences: () => shellPreferences,
    setShellPreferences: (next) => { shellPreferences = next; },
    render,
    closeInspector,
    resizeInspector: syncInspectorWidth,
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
