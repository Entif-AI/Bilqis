import {
  buildEvidenceRequest,
  criteriaForSelection,
  loadEvidencePage,
  loadRecordById,
  loadRecordLinks,
  mergeEvidencePages,
} from "./evidence-query.mjs";
import { renderEvidenceMarkup } from "./evidence-markup.mjs";

export {
  assertEvidencePage,
  buildEvidenceRequest,
  criteriaForSelection,
  loadEvidencePage,
  loadRecordById,
  loadRecordLinks,
  mergeEvidencePages,
  SEARCH_KINDS,
} from "./evidence-query.mjs";
export { renderEvidenceMarkup } from "./evidence-markup.mjs";

const ui = {
  contextKey: null, status: "idle", criteria: { kind: "context", value: "" },
  page: null, records: [], links: [], selected: null, selectedLinks: null,
  pendingRecordId: null, raw: false, error: null, traversalError: null,
  returnAvailable: false,
};
let queryEpoch = 0;

function errorCode(error, fallback = "Evidence traversal failed") {
  if (error?.message === "api.query is not a function") {
    return "Evidence queries are unavailable while the local evidence service is disconnected.";
  }
  return error?.code ?? error?.message ?? fallback;
}

export function prepareEvidenceSearch(state, criteria, append = false) {
  const next = {
    ...state, status: "loading", error: null, traversalError: null, criteria,
  };
  if (!append) Object.assign(next, {
    page: null, records: [], links: [], selected: null, selectedLinks: null, raw: false,
  });
  return next;
}

export function deactivateEvidenceView() {
  if (ui.contextKey === null && ui.status === "idle") return;
  queryEpoch += 1;
  Object.assign(ui, {
    contextKey: null, status: "idle", criteria: { kind: "context", value: "" },
    page: null, records: [], links: [], selected: null, selectedLinks: null,
    pendingRecordId: null, raw: false, error: null, traversalError: null,
    returnAvailable: false,
  });
}

async function search(
  container, api, context, criteria, cursor = null, append = false,
  onSelection = null, onReturnOrigin = null,
) {
  const epoch = ++queryEpoch;
  const contextKey = ui.contextKey;
  Object.assign(ui, prepareEvidenceSearch(ui, criteria, append));
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin);
  try {
    const page = await loadEvidencePage(api, context, criteria, cursor);
    if (epoch !== queryEpoch || contextKey !== ui.contextKey) return;
    ui.page = append ? mergeEvidencePages(ui.page, page) : page; ui.status = "ready";
    ui.records = append ? [...ui.records, ...(page.records ?? [])] : [...(page.records ?? [])];
    ui.links = append ? [...ui.links, ...(page.links ?? [])] : [...(page.links ?? [])];
    if (!append) {
      ui.selected = null; ui.selectedLinks = null; ui.raw = false;
      if (ui.pendingRecordId) {
        ui.selected = ui.records.find(
          (record) => record?.meta?.record_id === ui.pendingRecordId,
        ) ?? null;
        ui.pendingRecordId = null;
        if (ui.selected) {
          try {
            const links = await loadRecordLinks(api, ui.selected);
            if (epoch !== queryEpoch || contextKey !== ui.contextKey) return;
            ui.selectedLinks = links;
          } catch (error) {
            if (epoch !== queryEpoch || contextKey !== ui.contextKey) return;
            ui.selectedLinks = null; ui.traversalError = errorCode(error);
          }
        }
      }
    }
  } catch (error) {
    if (epoch !== queryEpoch || contextKey !== ui.contextKey) return;
    ui.status = "error"; ui.error = errorCode(error, "Evidence query failed");
    if (!append) {
      ui.page = null; ui.records = []; ui.links = [];
      ui.selected = null; ui.selectedLinks = null; ui.raw = false; ui.pendingRecordId = null;
    }
  }
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin);
}

async function select(
  container, api, context, record, onSelection = null, onReturnOrigin = null,
) {
  const epoch = ++queryEpoch;
  const contextKey = ui.contextKey;
  ui.selected = record; ui.raw = false; ui.selectedLinks = null; ui.traversalError = null;
  onSelection?.({ kind: "evidence", id: record.meta.record_id });
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin);
  try {
    const links = await loadRecordLinks(api, record);
    if (epoch !== queryEpoch || contextKey !== ui.contextKey
        || ui.selected?.meta?.record_id !== record.meta.record_id) return;
    ui.selectedLinks = links;
  } catch (error) {
    if (epoch !== queryEpoch || contextKey !== ui.contextKey) return;
    ui.selectedLinks = null; ui.traversalError = errorCode(error);
  }
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin);
}

async function hydrateTarget(
  container, api, context, recordId, onSelection, onReturnOrigin,
) {
  const epoch = ++queryEpoch;
  const contextKey = ui.contextKey;
  ui.traversalError = null;
  try {
    const found = await loadRecordById(api, context, recordId);
    if (epoch !== queryEpoch || contextKey !== ui.contextKey) return;
    if (found.record) {
      return void select(
        container, api, context, found.record, onSelection, onReturnOrigin,
      );
    }
    ui.traversalError = "EVIDENCE_TARGET_MISSING";
  } catch (error) {
    if (epoch !== queryEpoch || contextKey !== ui.contextKey) return;
    ui.traversalError = errorCode(error);
  }
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin);
}

function bind(container, api, context, onSelection = null, onReturnOrigin = null) {
  container.querySelector("#evidence-search-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    void search(container, api, context, {
      kind: data.get("kind")?.toString() ?? "context",
      value: data.get("value")?.toString() ?? "",
    }, null, false, onSelection, onReturnOrigin);
  });
  container.querySelectorAll("[data-evidence-record]").forEach((button) => button.addEventListener("click", () =>
    void select(
      container, api, context, ui.records[Number(button.dataset.evidenceRecord)],
      onSelection, onReturnOrigin,
    )));
  container.querySelectorAll("[data-evidence-target]").forEach((button) => button.addEventListener("click", async () => {
    const link = ui.links[Number(button.dataset.evidenceTarget)];
    if (!link?.target_record_id) return;
    await hydrateTarget(
      container, api, context, link.target_record_id, onSelection, onReturnOrigin,
    );
  }));
  container.querySelectorAll("[data-evidence-selected-target]").forEach((button) => button.addEventListener("click", async () => {
    const link = ui.selectedLinks?.links?.[Number(button.dataset.evidenceSelectedTarget)];
    if (!link?.target_record_id) return;
    await hydrateTarget(
      container, api, context, link.target_record_id, onSelection, onReturnOrigin,
    );
  }));
  container.querySelectorAll("[data-evidence-ref]").forEach((button) => button.addEventListener("click", () =>
    void search(container, api, context, {
      kind: "reference", value: button.dataset.evidenceRef,
    }, null, false, onSelection, onReturnOrigin)));
  container.querySelector("[data-evidence-raw]")?.addEventListener("click", () => {
    ui.raw = !ui.raw;
    paintEvidenceView(container, api, context, onSelection, onReturnOrigin);
  });
  container.querySelector("[data-evidence-more]")?.addEventListener("click", () =>
    void search(
      container, api, context, ui.criteria, ui.page?.next_cursor ?? null, true,
      onSelection, onReturnOrigin,
    ));
  container.querySelector("[data-evidence-return]")?.addEventListener("click", () => {
    onReturnOrigin?.();
  });
}

function paintEvidenceView(
  container, api, context, onSelection = null, onReturnOrigin = null,
) {
  container.innerHTML = renderEvidenceMarkup(ui);
  bind(container, api, context, onSelection, onReturnOrigin);
}

export function renderEvidenceView(
  container, api, context, initialSelection = null,
  onSelection = null, onReturnOrigin = null,
) {
  const criteria = criteriaForSelection(initialSelection);
  const key = `${context.mode}:${context.runId}:${context.generation}:${criteria.kind}:${criteria.value}`;
  const changed = ui.contextKey !== key;
  if (changed) Object.assign(ui, {
    contextKey: key, status: "idle", criteria,
    page: null, records: [], links: [], selected: null, selectedLinks: null,
    pendingRecordId: initialSelection?.kind === "evidence" ? initialSelection.id : null,
    raw: false, error: null, traversalError: null,
  });
  ui.returnAvailable = typeof onReturnOrigin === "function";
  if (changed) queryEpoch += 1;
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin);
  if (ui.status === "idle") {
    void search(
      container, api, context, ui.criteria, null, false, onSelection, onReturnOrigin,
    );
  }
}
