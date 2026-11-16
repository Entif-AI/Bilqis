import {
  buildEvidenceRequest,
  criteriaForSelection,
  loadEvidencePage,
  loadRecordById,
  loadRecordLinks,
  mergeEvidencePages,
} from "./evidence-query.mjs";
import { renderEvidenceMarkup } from "./evidence-markup.mjs";
import { evidenceT } from "./evidence-messages.mjs";
import { replaceEvidenceMarkup } from "./evidence-paint.mjs";

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
  returnAvailable: false, origin: null,
};
let queryEpoch = 0;
let selectionEpoch = 0;

function errorCode(error, fallback = "EVIDENCE_TRAVERSAL_FAILED") {
  if (error?.message === "api.query is not a function") {
    return evidenceT("evidence.query.disconnected");
  }
  return error?.code ?? error?.message ?? fallback;
}

export function prepareEvidenceSearch(state, criteria, append = false) {
  const next = {
    ...state, status: "loading", error: null, criteria,
  };
  if (!append) Object.assign(next, {
    page: null, records: [], links: [], selected: null, selectedLinks: null, raw: false, traversalError: null,
  });
  return next;
}

export function deactivateEvidenceView() {
  if (ui.contextKey === null && ui.status === "idle") return;
  queryEpoch += 1;
  selectionEpoch += 1;
  Object.assign(ui, {
    contextKey: null, status: "idle", criteria: { kind: "context", value: "" },
    page: null, records: [], links: [], selected: null, selectedLinks: null,
    pendingRecordId: null, raw: false, error: null, traversalError: null,
    returnAvailable: false, origin: null,
  });
}

async function search(
  container, api, context, criteria, cursor = null, append = false,
  onSelection = null, onReturnOrigin = null, bootstrap = false,
) {
  if (append && ui.status === "loading") return;
  const epoch = ++queryEpoch;
  if (!append) {
    selectionEpoch += 1;
    if (!bootstrap) ui.pendingRecordId = null;
  }
  const contextKey = ui.contextKey;
  Object.assign(ui, prepareEvidenceSearch(ui, criteria, append));
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin, {resetDraft: !append, resetDetails: !append});
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
          void hydrateSelectedLinks(container, api, context, ui.selected, onSelection, onReturnOrigin);
        }
      }
    }
  } catch (error) {
    if (epoch !== queryEpoch || contextKey !== ui.contextKey) return;
    ui.status = "error"; ui.error = errorCode(error, "EVIDENCE_QUERY_FAILED");
    if (!append) {
      ui.page = null; ui.records = []; ui.links = [];
      ui.selected = null; ui.selectedLinks = null; ui.raw = false; ui.pendingRecordId = null;
    }
  }
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin);
}

async function hydrateSelectedLinks(container, api, context, record, onSelection, onReturnOrigin) {
  const epoch = ++selectionEpoch;
  const contextKey = ui.contextKey;
  const current = () => epoch === selectionEpoch && contextKey === ui.contextKey
    && ui.selected?.meta?.record_id === record.meta.record_id;
  try {
    const links = await loadRecordLinks(api, record);
    if (!current()) return;
    ui.selectedLinks = links;
  } catch (error) {
    if (!current()) return;
    ui.selectedLinks = null; ui.traversalError = errorCode(error);
  }
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin);
}

function select(container, api, context, record, onSelection = null, onReturnOrigin = null) {
  ui.selected = record; ui.raw = false; ui.selectedLinks = null; ui.traversalError = null;
  onSelection?.({ kind: "evidence", id: record.meta.record_id });
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin, {resetDetails: true, focusId: "evidence-detail-heading"});
  return hydrateSelectedLinks(container, api, context, record, onSelection, onReturnOrigin);
}

async function hydrateTarget(
  container, api, context, recordId, onSelection, onReturnOrigin,
) {
  const epoch = ++selectionEpoch;
  const contextKey = ui.contextKey;
  ui.traversalError = null;
  try {
    const found = await loadRecordById(api, context, recordId);
    if (epoch !== selectionEpoch || contextKey !== ui.contextKey) return;
    if (found.record) {
      return void select(
        container, api, context, found.record, onSelection, onReturnOrigin,
      );
    }
    ui.traversalError = "EVIDENCE_TARGET_MISSING";
  } catch (error) {
    if (epoch !== selectionEpoch || contextKey !== ui.contextKey) return;
    ui.traversalError = errorCode(error);
  }
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin);
}

function bind(container, api, context, onSelection = null, onReturnOrigin = null) {
  container.querySelector('[data-test-id="evidence-query-form"]')?.addEventListener("submit", (event) => {
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
  container.querySelectorAll("[data-evidence-mode]").forEach((button) => button.addEventListener("click", () => {
    ui.raw = button.dataset.evidenceMode === "raw";
    paintEvidenceView(container, api, context, onSelection, onReturnOrigin);
  }));
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
  container, api, context, onSelection = null, onReturnOrigin = null, options = {},
) {
  replaceEvidenceMarkup(container, renderEvidenceMarkup(ui), options);
  bind(container, api, context, onSelection, onReturnOrigin);
}

export function renderEvidenceView(
  container, api, context, initialSelection = null,
  onSelection = null, onReturnOrigin = null, origin = null,
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
  ui.origin = origin;
  if (changed) { queryEpoch += 1; selectionEpoch += 1; }
  paintEvidenceView(container, api, context, onSelection, onReturnOrigin, {resetDraft: changed, resetDetails: changed});
  if (ui.status === "idle") {
    void search(
      container, api, context, ui.criteria, null, false, onSelection, onReturnOrigin, true,
    );
  }
}
