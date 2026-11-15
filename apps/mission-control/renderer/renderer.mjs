import { createFrameShell } from "./frames/frame-shell.mjs";
import {
  inspect,
  navigate,
  openEvidence as openEvidenceView,
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
import {
  applyShellPreferences,
  constrainInspectorWidth,
  INSPECTOR_MIN_WIDTH,
  inspectorWidthForDestination,
  loadShellPreferences,
  saveShellPreferences,
  withInspectorWidthPreference,
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
import { createCapabilityExplorer } from "./capability/app.mjs";
import { activateDomainViews } from "./foundation/domain-controller.mjs";
import { createInteractionController } from "./interactions/controller.mjs";
import { createProductionLearningController } from "./learning/controller.mjs";
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
let focusReturnToken = null;
let paletteReturnToken = null;
const homeController = createHomeController(window.bamfMissionControl, fixtureSupport?.home);
const resourceController = createResourceController(window.bamfMissionControl, fixtureSupport?.resources);
const teacherController = createTeacherController(window.bamfMissionControl, {
  fixtureSupport: fixtureSupport?.teacher ?? null,
});
const salienceController = createSalienceController(window.bamfMissionControl, {
  fixtureSupport: fixtureSupport?.salience ?? null,
});
const learningController = createProductionLearningController(window.bamfMissionControl);
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
const operateController = createOperateController(window.bamfMissionControl);

const frameShell = createFrameShell({
  getState: () => state, setState: next => { state = next; }, getDefense: () => defense,
  render, onInspect: openInspector,
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
const capabilityExplorer = createCapabilityExplorer({
  host: document.querySelector("#domain-view"),
  serviceQuery: request => window.bamfMissionControl.querySnapshot(request),
  launchMode,
  fixtureSupport: fixtureSupport?.capability ?? null,
  changeLens: (lens, capabilityId) => {
    if (!state) return;
    state = {
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
    };
    render();
  },
  openObject: (selected) => {
    if (!state) return;
    state = { ...openSelectionOwner(inspect(state, selected)), inspectorOpen: false };
    render();
  },
  openEvidence: (selected) => {
    if (!state) return;
    state = openEvidenceView(inspect(state, selected));
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
  }, bootstrapState);
  syncInspectorWidth();
  frameShell.afterRender();
  setHash();
  activateDomainViews({
    state, getState: () => state, defense, api: window.bamfMissionControl, homeController,
    resourceController, operateController, teacherController, salienceController, capabilityExplorer,
    onInspect: openInspector, onNavigate: navigateTo, onAnnounce: announce,
    learningController, schoolDomainSupport: fixtureSupport?.school ?? null,
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

function openInspector(selected) {
  if (!state) return;
  focusReturnToken = focusToken(document.activeElement);
  state = inspect(state, selected);
  syncInspectorWidth();
  renderInspector(state, defense);
  interactionController.render();
  setHash();
  window.queueMicrotask(() => document.querySelector("#inspector-close")?.focus());
  announce(t("shell.announce.inspectorOpened", { id: selected.id }));
}

function closeInspector() {
  if (!state?.inspectorOpen) return;
  state = inspect(state, null);
  renderInspector(state, defense);
  interactionController.render();
  setHash();
  window.queueMicrotask(() => restoreFocus(document, focusReturnToken));
  announce(t("shell.announce.inspectorClosed"));
}

function inspectorMetrics() {
  return {
    viewportWidth: document.documentElement.clientWidth || window.innerWidth,
    railWidth: document.querySelector(".rail")?.getBoundingClientRect?.().width ?? 0,
  };
}

function syncInspectorWidth(requestedWidth = null, { persist = false } = {}) {
  if (!shellPreferences) return null;
  const destination = state?.view ?? "mission-control";
  const preferred = requestedWidth ?? inspectorWidthForDestination(shellPreferences, destination);
  const width = constrainInspectorWidth(preferred, inspectorMetrics());
  document.documentElement.style.setProperty("--inspector-width", `${width}px`);
  const splitter = document.querySelector("#inspector-splitter");
  if (splitter) {
    const maximum = constrainInspectorWidth(Number.MAX_SAFE_INTEGER, inspectorMetrics());
    splitter.setAttribute("aria-valuemin", String(INSPECTOR_MIN_WIDTH));
    splitter.setAttribute("aria-valuemax", String(maximum));
    splitter.setAttribute("aria-valuenow", String(width));
  }
  if (requestedWidth !== null) {
    shellPreferences = withInspectorWidthPreference(shellPreferences, destination, width);
    if (persist) saveShellPreferences(window.localStorage, shellPreferences);
  }
  const open = Boolean(state?.inspectorOpen);
  const narrowOverlay = open && window.matchMedia?.("(max-width: 980px)")?.matches === true;
  const panel = document.querySelector("#inspector");
  if (narrowOverlay) panel?.setAttribute("aria-modal", "true");
  else panel?.removeAttribute("aria-modal");
  for (const background of [
    document.querySelector(".skip-link"),
    document.querySelector(".rail"),
    document.querySelector("#main-content"),
  ]) {
    if (background) background.inert = narrowOverlay;
  }
  if (splitter) {
    splitter.setAttribute("aria-hidden", String(!open || narrowOverlay));
    splitter.tabIndex = open && !narrowOverlay ? 0 : -1;
  }
  return width;
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
