import {
  loadAbiRow,
  loadAtlasOverview,
  loadSemanticIdentity,
  renderAtlasMarkup,
} from "./semantic-atlas.mjs";

let atlasState = {
  status: "idle",
  error: null,
  overview: null,
  selection: null,
  lens: "canonical",
  selectedBank: null,
};
let contextIdentity = null;
let epoch = 0;

export function invalidateAtlasRequests() {
  epoch += 1;
  if (atlasState.status === "loading") atlasState = { ...atlasState, status: "idle" };
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
  };
}

export function renderAtlasDomain(api, context, isActive = () => true) {
  bindContext(context);
  const host = document.querySelector("#domain-view");
  host.hidden = false;
  host.innerHTML = renderAtlasMarkup({ ...atlasState, context });
  host.querySelectorAll("[data-atlas-lens]").forEach((button) => {
    button.addEventListener("click", () => {
      atlasState = { ...atlasState, lens: button.dataset.atlasLens };
      renderAtlasDomain(api, context, isActive);
    });
  });
  host.querySelectorAll("[data-atlas-bank]").forEach((button) => {
    button.addEventListener("click", () => {
      atlasState = { ...atlasState, selectedBank: Number(button.dataset.atlasBank) };
      renderAtlasDomain(api, context, isActive);
    });
  });
  host.querySelector('[data-test-id="atlas-search-form"]')?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const semanticId = new FormData(event.currentTarget).get("semanticId")?.toString().trim();
    if (!semanticId) return;
    const isCurrent = beginRequest(context, isActive);
    atlasState = { ...atlasState, status: "loading", error: null };
    renderAtlasDomain(api, context, isActive);
    try {
      const selection = await loadSemanticIdentity(api, context, semanticId);
      if (!isCurrent()) return;
      atlasState = { ...atlasState, status: "ready", selection };
    } catch (error) {
      if (!isCurrent()) return;
      atlasState = {
        ...atlasState,
        status: "error",
        error: error?.code ?? error?.message ?? "Semantic query failed",
      };
    }
    renderAtlasDomain(api, context, isActive);
  });
  host.querySelector('[data-test-id="atlas-abi-form"]')?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const bank = Number(form.get("bank"));
    const row = Number(form.get("row"));
    if (!Number.isSafeInteger(bank) || bank < 0 || !Number.isSafeInteger(row) || row < 0) return;
    const isCurrent = beginRequest(context, isActive);
    atlasState = { ...atlasState, status: "loading", error: null, selectedBank: bank };
    renderAtlasDomain(api, context, isActive);
    try {
      const selection = await loadAbiRow(api, context, bank, row);
      if (!isCurrent()) return;
      atlasState = { ...atlasState, status: "ready", selection };
    } catch (error) {
      if (!isCurrent()) return;
      atlasState = {
        ...atlasState,
        status: "error",
        error: error?.code ?? error?.message ?? "ABI query failed",
      };
    }
    renderAtlasDomain(api, context, isActive);
  });
}

export async function ensureAtlasOverview(api, context, isActive = () => true) {
  bindContext(context);
  if (atlasState.status !== "idle") return;
  const isCurrent = beginRequest(context, isActive);
  atlasState = { ...atlasState, status: "loading", error: null };
  renderAtlasDomain(api, context, isActive);
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
  if (isActive()) renderAtlasDomain(api, context, isActive);
}

export async function ensureAtlasSelection(
  api, context, semanticId, isActive = () => true,
) {
  bindContext(context);
  if (!semanticId ||
      (atlasState.status === "ready" && atlasState.selection?.semanticId === semanticId)) {
    return;
  }
  const isCurrent = beginRequest(context, isActive);
  atlasState = { ...atlasState, status: "loading", error: null };
  renderAtlasDomain(api, context, isActive);
  try {
    const [selection, overview] = await Promise.all([
      loadSemanticIdentity(api, context, semanticId),
      atlasState.overview ? Promise.resolve(atlasState.overview) : loadAtlasOverview(api, context),
    ]);
    if (!isCurrent()) return;
    atlasState = { ...atlasState, status: "ready", selection, overview };
  } catch (error) {
    if (!isCurrent()) return;
    atlasState = {
      ...atlasState,
      status: "error",
      error: error?.code ?? error?.message ?? "Semantic query failed",
    };
  }
  if (isActive()) renderAtlasDomain(api, context, isActive);
}
