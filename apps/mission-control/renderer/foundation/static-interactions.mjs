import { parseDeepLink } from "../deep-link.mjs";
import { withRoute, openEvidence, openSelectionOwner } from "../shell-state.mjs";
import {
  DENSITIES,
  THEMES,
  applyDisplaySettings,
  cycleSetting,
  saveDisplaySettings,
} from "../settings.mjs";
import {
  applyShellPreferences,
  saveShellPreferences,
  toggleRailPreference,
} from "../shell-preferences.mjs";

const POPUP_OWNER_SELECTOR = ".ui-context-help, .ui-temporal";
const POPUP_DETAIL_SELECTOR = ".ui-context-help__content, .ui-temporal__detail";
const POPUP_VIEWPORT_MARGIN = 16;
const POPUP_MINIMUM_SPACE = 120;
const POPUP_MAX_WIDTH = 448;

function popupOwner(target) {
  return target?.closest?.(POPUP_OWNER_SELECTOR) ?? null;
}

function popupDetail(owner) {
  return owner?.querySelector?.(POPUP_DETAIL_SELECTOR) ?? null;
}

function detailIsOpen(detail) {
  if (!detail) return false;
  try {
    return detail.matches(":popover-open") || detail.dataset.popupOpen === "true";
  } catch {
    return detail.dataset.popupOpen === "true";
  }
}

function closePopup(owner) {
  const detail = popupDetail(owner);
  if (!detail) return;
  try {
    if (typeof detail.hidePopover === "function" && detail.matches(":popover-open")) {
      detail.hidePopover();
    }
  } catch {
    // Fallback state below remains authoritative for older renderer engines.
  }
  delete detail.dataset.popupOpen;
}

function anchorPopup(owner, window) {
  if (!owner) return;
  const anchor = owner.matches(".ui-temporal")
    ? owner
    : owner.querySelector(".ui-context-help__trigger");
  if (!anchor) return;
  const rect = anchor.getBoundingClientRect();
  const maximumLeft = Math.max(
    POPUP_VIEWPORT_MARGIN,
    window.innerWidth - POPUP_MAX_WIDTH - POPUP_VIEWPORT_MARGIN,
  );
  const left = Math.max(
    POPUP_VIEWPORT_MARGIN,
    Math.min(rect.left, maximumLeft),
  );
  const below = window.innerHeight - rect.bottom - POPUP_VIEWPORT_MARGIN;
  owner.style.setProperty("--popup-left", `${left}px`);
  if (below >= POPUP_MINIMUM_SPACE) {
    owner.style.setProperty("--popup-top", `${rect.bottom}px`);
    owner.style.setProperty("--popup-bottom", "auto");
  } else {
    owner.style.setProperty("--popup-top", "auto");
    owner.style.setProperty(
      "--popup-bottom",
      `${Math.max(POPUP_VIEWPORT_MARGIN, window.innerHeight - rect.top)}px`,
    );
  }
}

function openPopup(owner, window, document) {
  if (!owner || owner.dataset.popupDismissed === "true") return;
  anchorPopup(owner, window);
  const detail = popupDetail(owner);
  if (!detail) return;
  for (const candidate of document.querySelectorAll(POPUP_DETAIL_SELECTOR)) {
    if (candidate !== detail && detailIsOpen(candidate)) {
      closePopup(popupOwner(candidate));
    }
  }
  try {
    if (typeof detail.showPopover === "function" && !detail.matches(":popover-open")) {
      detail.showPopover();
      return;
    }
  } catch {
    // Fallback state below preserves the same interaction contract.
  }
  detail.dataset.popupOpen = "true";
}

export function bindStaticInteractions({
  document,
  window,
  getState,
  setState,
  getDisplaySettings,
  setDisplaySettings,
  getShellPreferences,
  setShellPreferences,
  render,
  closeInspector,
  openPalette,
  interactionController,
}) {
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    for (const detail of document.querySelectorAll(POPUP_DETAIL_SELECTOR)) {
      if (!detailIsOpen(detail)) continue;
      const owner = popupOwner(detail);
      if (!owner) continue;
      owner.dataset.popupDismissed = "true";
      closePopup(owner);
    }
  });
  document.addEventListener("focusout", (event) => {
    const owner = popupOwner(event.target);
    if (owner && !owner.contains(event.relatedTarget)) {
      delete owner.dataset.popupDismissed;
      if (!owner.matches(":hover")) closePopup(owner);
    }
  });
  document.addEventListener("pointerout", (event) => {
    const owner = popupOwner(event.target);
    if (owner && !owner.contains(event.relatedTarget)) {
      delete owner.dataset.popupDismissed;
      if (!owner.contains(document.activeElement)) closePopup(owner);
    }
  });
  document.addEventListener("focusin", (event) => {
    openPopup(popupOwner(event.target), window, document);
  });
  document.addEventListener("pointerover", (event) => {
    openPopup(popupOwner(event.target), window, document);
  });
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
  document.querySelector("#rail-toggle").addEventListener("click", () => {
    const next = toggleRailPreference(getShellPreferences());
    setShellPreferences(next);
    saveShellPreferences(window.localStorage, next);
    applyShellPreferences(document.documentElement, next);
    render();
  });
  const contextDisclosures = [
    document.querySelector("#system-context-disclosure"),
    document.querySelector("#view-settings-disclosure"),
  ];
  contextDisclosures.forEach((disclosure) => {
    disclosure.addEventListener("toggle", () => {
      if (!disclosure.open) return;
      contextDisclosures.forEach((other) => {
        if (other !== disclosure) other.removeAttribute("open");
      });
    });
  });
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
