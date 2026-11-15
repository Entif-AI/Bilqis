import { parseDeepLink } from "../deep-link.mjs";
import { withRoute, openEvidence, openSelectionOwner } from "../shell-state.mjs";
import {
  DENSITIES,
  THEMES,
  applyDisplaySettings,
  cycleSetting,
  saveDisplaySettings,
} from "../settings.mjs";

export function bindStaticInteractions({
  document,
  window,
  getState,
  setState,
  getDisplaySettings,
  setDisplaySettings,
  render,
  closeInspector,
  openPalette,
  interactionController,
}) {
  const skipMain = document.querySelector('[data-test-id="shell-skip-main"]');
  const focusMain = (event) => {
    event.preventDefault();
    const main = document.querySelector('[data-test-id="shell-main-content"]');
    main.focus({ preventScroll: true });
    main.scrollIntoView({ block: "start" });
  };
  skipMain.addEventListener("click", focusMain);
  skipMain.addEventListener("keydown", (event) => {
    if (event.key === "Enter") focusMain(event);
  });
  document.querySelector("#inspector-close").addEventListener("click", closeInspector);
  document.querySelector("#open-owner").addEventListener("click", () => {
    const state = getState();
    if (!state) return;
    setState(openSelectionOwner(state));
    render();
  });
  document.querySelector("#open-evidence").addEventListener("click", () => {
    const state = getState();
    if (!state?.selected) return;
    setState(openEvidence(state));
    render();
  });
  document.querySelector("#theme-trigger").addEventListener("click", () => {
    const next = { ...getDisplaySettings(), theme: cycleSetting(getDisplaySettings().theme, THEMES) };
    setDisplaySettings(next);
    saveDisplaySettings(window.localStorage, next);
    applyDisplaySettings(document.documentElement, next);
    render();
  });
  document.querySelector("#density-trigger").addEventListener("click", () => {
    const next = { ...getDisplaySettings(), density: cycleSetting(getDisplaySettings().density, DENSITIES) };
    setDisplaySettings(next);
    saveDisplaySettings(window.localStorage, next);
    applyDisplaySettings(document.documentElement, next);
    render();
  });
  document.querySelector("#palette-trigger").addEventListener("click", openPalette);
  document.querySelector("#palette-close").addEventListener("click", () => {
    document.querySelector("#command-palette").close();
  });
  window.addEventListener("hashchange", () => {
    const state = getState();
    if (!state) return;
    setState(withRoute(state, parseDeepLink(window.location.hash)));
    render();
  });
  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      openPalette();
    } else if (event.key === "Escape" && getState()?.inspectorOpen &&
      !document.querySelector("#command-palette").open) {
      event.preventDefault();
      closeInspector();
    }
  });
  interactionController.bindStatic();
}
