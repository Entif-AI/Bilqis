import {
  constrainInspectorWidth,
  INSPECTOR_MIN_WIDTH,
  inspectorWidthForDestination,
  saveShellPreferences,
  withInspectorWidthPreference,
} from "../shell-preferences.mjs";
import { inspect } from "../shell-state.mjs";
import { focusToken, restoreFocus } from "./accessibility.mjs";
import { t } from "./i18n.mjs";

export function createInspectorController({
  document,
  window,
  getState,
  setState,
  getDefense,
  getShellPreferences,
  setShellPreferences,
  renderInspector,
  interactionController,
  setHash,
  announce,
}) {
  let focusReturnToken = null;

  function inspectorMetrics() {
    return {
      viewportWidth: document.documentElement.clientWidth || window.innerWidth,
      railWidth: document.querySelector(".rail")?.getBoundingClientRect?.().width ?? 0,
    };
  }

  function syncInspectorWidth(requestedWidth = null, { persist = false } = {}) {
    let shellPreferences = getShellPreferences();
    if (!shellPreferences) return null;
    const state = getState();
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
      setShellPreferences(shellPreferences);
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

  function openInspector(selected) {
    let state = getState();
    if (!state) return;
    focusReturnToken = focusToken(document.activeElement);
    state = inspect(state, selected);
    setState(state);
    syncInspectorWidth();
    renderInspector(state, getDefense());
    interactionController.render();
    setHash();
    window.queueMicrotask(() => document.querySelector("#inspector-close")?.focus());
    announce(t("shell.announce.inspectorOpened", { id: selected.id }));
  }

  function closeInspector() {
    let state = getState();
    if (!state?.inspectorOpen) return;
    state = inspect(state, null);
    setState(state);
    renderInspector(state, getDefense());
    interactionController.render();
    setHash();
    window.queueMicrotask(() => restoreFocus(document, focusReturnToken));
    announce(t("shell.announce.inspectorClosed"));
  }

  return Object.freeze({ openInspector, closeInspector, syncInspectorWidth });
}
