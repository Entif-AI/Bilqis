import {
  loadAbiRow,
  loadAtlasOverview,
  loadSemanticIdentity,
  renderAtlasMarkup,
} from "./semantic-atlas.mjs";
import { ATLAS_TABS } from "./atlas-view-parts.mjs";
import { t } from "../foundation/i18n.mjs";

let atlasState = {
  status: "idle",
  error: null,
  overview: null,
  selection: null,
  lens: "canonical",
  selectedBank: null,
  activeTab: "lookup",
  semanticQuery: "",
  abiBankQuery: "0",
  abiRowQuery: "",
};
let contextIdentity = null;
let epoch = 0;

export function invalidateAtlasRequests() {
  epoch += 1;
  if (atlasState.status === "loading" || atlasState.status === "error") {
    atlasState = { ...atlasState, status: "idle", error: null };
  }
}

function beginRequest(context, isActive) {
  const token = ++epoch;
  return () => token === epoch && contextIdentity === context && isActive();
}

function bindContext(context) {
  const next = context;
  if (contextIdentity === next) return;
  invalidateAtlasRequests();
  contextIdentity = next;
  atlasState = {
    status: "idle",
    error: null,
    overview: null,
    selection: null,
    lens: "canonical",
    selectedBank: null,
    activeTab: "lookup",
    semanticQuery: "",
    abiBankQuery: "0",
    abiRowQuery: "",
  };
}

function selectedObject() {
  const concept = atlasState.selection?.concept;
  const state = atlasState.selection?.state;
  const semanticId = concept?.semantic_id ?? state?.semantic_id ??
    atlasState.selection?.held?.semantic_id ?? atlasState.selection?.semanticId;
  if (!semanticId) return null;
  return {
    kind: "semantic",
    id: semanticId,
    label: semanticId,
    details: {
      [t("atlas.inspector.kind")]: concept?.kind ?? t("atlas.value.unknown"),
      [t("atlas.inspector.abi")]: concept
        ? `${t("atlas.abi.bank")} ${concept.abi_bank} · ${t("atlas.abi.row")} ${concept.abi_row}`
        : t("atlas.value.unavailable"),
      [t("atlas.inspector.sourceRevision")]: concept?.atlas_release_sha256 ?? t("atlas.value.unavailable"),
      [t("atlas.inspector.generationState")]: state?.admission_state ?? t("atlas.value.unavailable"),
    },
  };
}

function bindTabs(host, rerender) {
  const tabs = [...host.querySelectorAll("[data-atlas-tab]")];
  tabs.forEach((button, index) => {
    const activate = (focus = false) => {
      const id = button.dataset.atlasTab;
      if (!ATLAS_TABS.some(([candidate]) => candidate === id)) return;
      atlasState = { ...atlasState, activeTab: id };
      rerender();
      if (focus) document.querySelector(`[data-atlas-tab="${id}"]`)?.focus();
    };
    button.addEventListener("click", () => activate(true));
    button.addEventListener("keydown", (event) => {
      const next = event.key === "ArrowRight" ? (index + 1) % tabs.length
        : event.key === "ArrowLeft" ? (index - 1 + tabs.length) % tabs.length
        : event.key === "Home" ? 0
        : event.key === "End" ? tabs.length - 1
        : null;
      if (next === null) return;
      event.preventDefault();
      const id = tabs[next].dataset.atlasTab;
      atlasState = { ...atlasState, activeTab: id };
      rerender();
      document.querySelector(`[data-atlas-tab="${id}"]`)?.focus();
    });
  });
}

export function renderAtlasDomain(
  api, context, isActive = () => true, onInspect = () => {}, onSelectionChange = () => {},
) {
  bindContext(context);
  const host = document.querySelector("#domain-view");
  host.hidden = false;
  host.innerHTML = renderAtlasMarkup({ ...atlasState, context });
  const rerender = () => renderAtlasDomain(api, context, isActive, onInspect, onSelectionChange);
  bindTabs(host, rerender);
  host.querySelectorAll("[data-atlas-lens]").forEach((button) => {
    button.addEventListener("click", () => {
      atlasState = { ...atlasState, lens: button.dataset.atlasLens };
      rerender();
    });
  });
  host.querySelectorAll("[data-atlas-bank]").forEach((button) => {
    button.addEventListener("click", () => {
      atlasState = {
        ...atlasState,
        selectedBank: Number(button.dataset.atlasBank),
        abiBankQuery: button.dataset.atlasBank,
      };
      rerender();
    });
  });
  host.querySelector('[data-test-id="atlas-search-input"]')?.addEventListener("input", (event) => {
    atlasState = { ...atlasState, semanticQuery: event.currentTarget.value };
  });
  host.querySelector('[data-test-id="atlas-abi-bank-input"]')?.addEventListener("input", (event) => {
    atlasState = { ...atlasState, abiBankQuery: event.currentTarget.value };
  });
  host.querySelector('[data-test-id="atlas-abi-row-input"]')?.addEventListener("input", (event) => {
    atlasState = { ...atlasState, abiRowQuery: event.currentTarget.value };
  });
  host.querySelector("[data-atlas-inspect]")?.addEventListener("click", () => {
    const selected = selectedObject();
    if (selected) onInspect(selected);
  });
  host.querySelector('[data-test-id="atlas-search-form"]')?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const semanticId = new FormData(event.currentTarget).get("semanticId")?.toString().trim();
    if (!semanticId) return;
    const isCurrent = beginRequest(context, isActive);
    atlasState = { ...atlasState, status: "loading", error: null, semanticQuery: semanticId };
    rerender();
    try {
      const selection = await loadSemanticIdentity(api, context, semanticId);
      if (!isCurrent()) return;
      atlasState = { ...atlasState, status: "ready", selection, activeTab: "dossier" };
      const selected = selectedObject();
      if (selected) onSelectionChange(selected);
    } catch (error) {
      if (!isCurrent()) return;
      atlasState = {
        ...atlasState,
        status: "error",
        error: error?.code ?? error?.message ?? "Semantic query failed",
      };
    }
    rerender();
  });
  host.querySelector('[data-test-id="atlas-abi-form"]')?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const bankValue = form.get("bank")?.toString().trim() ?? "";
    const rowValue = form.get("row")?.toString().trim() ?? "";
    const bank = Number(bankValue);
    const row = Number(rowValue);
    if (!Number.isSafeInteger(bank) || bank < 0 || !Number.isSafeInteger(row) || row < 0) return;
    const isCurrent = beginRequest(context, isActive);
    atlasState = {
      ...atlasState,
      status: "loading",
      error: null,
      selectedBank: bank,
      abiBankQuery: bankValue,
      abiRowQuery: rowValue,
    };
    rerender();
    try {
      const selection = await loadAbiRow(api, context, bank, row);
      if (!isCurrent()) return;
      atlasState = { ...atlasState, status: "ready", selection, activeTab: "dossier" };
      const selected = selectedObject();
      if (selected) onSelectionChange(selected);
    } catch (error) {
      if (!isCurrent()) return;
      atlasState = {
        ...atlasState,
        status: "error",
        error: error?.code ?? error?.message ?? "ABI query failed",
      };
    }
    rerender();
  });
}

export async function ensureAtlasOverview(
  api, context, isActive = () => true, onInspect = () => {}, onSelectionChange = () => {},
) {
  bindContext(context);
  if (atlasState.status !== "idle") return;
  const isCurrent = beginRequest(context, isActive);
  atlasState = { ...atlasState, status: "loading", error: null };
  renderAtlasDomain(api, context, isActive, onInspect, onSelectionChange);
  try {
    const overview = await loadAtlasOverview(api, context);
    if (!isCurrent()) return;
    atlasState = { ...atlasState, status: "ready", overview };
  } catch (error) {
    if (!isCurrent()) return;
    atlasState = {
      ...atlasState,
      status: "error",
      error: error?.code ?? error?.message ?? "Semantic Atlas unavailable",
    };
  }
  if (isActive()) renderAtlasDomain(api, context, isActive, onInspect, onSelectionChange);
}

export async function ensureAtlasSelection(
  api, context, semanticId, isActive = () => true, onInspect = () => {}, onSelectionChange = () => {},
) {
  bindContext(context);
  if (!semanticId ||
      (atlasState.status === "ready" && atlasState.selection?.semanticId === semanticId)) {
    return;
  }
  const isCurrent = beginRequest(context, isActive);
  atlasState = { ...atlasState, status: "loading", error: null, semanticQuery: semanticId };
  renderAtlasDomain(api, context, isActive, onInspect, onSelectionChange);
  try {
    const [selection, overview] = await Promise.all([
      loadSemanticIdentity(api, context, semanticId),
      atlasState.overview ? Promise.resolve(atlasState.overview) : loadAtlasOverview(api, context),
    ]);
    if (!isCurrent()) return;
    atlasState = { ...atlasState, status: "ready", selection, overview, activeTab: "dossier" };
    const selected = selectedObject();
    if (selected) onSelectionChange(selected);
  } catch (error) {
    if (!isCurrent()) return;
    atlasState = {
      ...atlasState,
      status: "error",
      error: error?.code ?? error?.message ?? "Semantic query failed",
    };
  }
  if (isActive()) renderAtlasDomain(api, context, isActive, onInspect, onSelectionChange);
}
