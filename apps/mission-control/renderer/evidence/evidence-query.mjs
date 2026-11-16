const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";
const PAGE_SIZE = 16;

export const SEARCH_KINDS = Object.freeze([
  ["context", "Current run / generation"], ["record", "Exact record ID"],
  ["run", "Run ID"], ["generation", "Generation"],
  ["checkpoint", "Checkpoint digest"], ["capability", "Capability ID"],
  ["episode", "Candidate / episode ID"], ["source", "Source / source revision"],
  ["semantic", "Semantic ID"], ["frame", "Frame ID"],
  ["memory", "Memory motif / slot identity"],
  ["correction", "Correction / requalification ID"],
  ["command", "Command operation ID"], ["reference", "Receipt / evidence reference"],
]);

function request(overrides = {}) {
  return {
    schema: QUERY_SCHEMA, family: "record", mode: "current", run_id: null,
    record_id: null, schema_version: null, generation: null, frontier_id: null,
    as_of: null, reference: null, cursor: null, limit: PAGE_SIZE, ...overrides,
  };
}

function scoped(context, overrides = {}) {
  const historical = context.mode === "HISTORICAL";
  return request({
    mode: historical ? "historical" : "current",
    run_id: context.runId, generation: context.generation, ...overrides,
  });
}

export function buildEvidenceRequest(context, criteria = {}, cursor = null) {
  const kind = criteria.kind ?? "context";
  const value = String(criteria.value ?? "").trim();
  if (kind === "context") return scoped(context, { cursor });
  if (kind === "record") return request({
    mode: context.mode === "HISTORICAL" ? "historical" : "current",
    record_id: value || null,
    generation: context.mode === "HISTORICAL" ? context.generation : null,
    run_id: context.mode === "HISTORICAL" ? context.runId : null,
    cursor,
  });
  if (kind === "run") return request({ run_id: value || null, cursor });
  if (kind === "generation") {
    const generation = Number(value);
    return request({
      mode: "historical", run_id: context.runId,
      generation: Number.isSafeInteger(generation) && generation >= 0 ? generation : null,
      cursor,
    });
  }
  if (kind === "reference") {
    return scoped(context, { family: "reference", reference: value || null, cursor });
  }
  const exact = kind === "checkpoint" && value && !value.startsWith("checkpoint:")
    ? `checkpoint:${value}` : value;
  const crossContext = new Set(["source", "semantic", "command"]).has(kind);
  return crossContext
    ? request({ reference: exact || null, cursor })
    : scoped(context, { reference: exact || null, cursor });
}

export function assertEvidencePage(value) {
  if (value?.accepted !== true) {
    const reason = typeof value?.reason === "string" && value.reason
      ? value.reason : "QUERY_RESPONSE_NOT_ACCEPTED";
    const error = new Error(`EVIDENCE_QUERY_REJECTED:${reason}`);
    error.code = reason;
    throw error;
  }
  return value;
}

export async function loadEvidencePage(api, context, criteria, cursor = null) {
  return assertEvidencePage(await api.query(buildEvidenceRequest(context, criteria, cursor)));
}

export async function loadRecordById(api, _context, recordId) {
  const page = assertEvidencePage(await api.query(request({ record_id: recordId })));
  return { page, record: page.records?.[0] ?? null };
}

export async function loadRecordLinks(api, record) {
  const meta = record?.meta ?? {};
  const run = meta.run ?? null;
  return assertEvidencePage(await api.query(request({
    family: "links", mode: run ? "historical" : "current",
    run_id: run?.run_id ?? null, record_id: meta.record_id ?? null,
    generation: run?.generation ?? null, as_of: run ? meta.as_of ?? null : null,
    limit: 32,
  })));
}

const QUERY_STATE_RANK = Object.freeze({
  EMPTY: 0, PRESENT: 1, PARTIAL: 2, STALE: 3,
  MISSING: 4, UNKNOWN: 5, UNAVAILABLE: 6, DENIED: 7,
});

function worseState(left, right) {
  return (QUERY_STATE_RANK[right] ?? -1) > (QUERY_STATE_RANK[left] ?? -1)
    ? right : left;
}

function mergeMarkers(left = [], right = []) {
  const seen = new Map();
  for (const marker of [...left, ...right]) {
    seen.set(marker?.meta?.record_id ?? JSON.stringify(marker), marker);
  }
  return [...seen.values()];
}

export function mergeEvidencePages(previous, next) {
  if (!previous) return next;
  const state = worseState(previous.state, next.state);
  const markers = mergeMarkers(previous.markers, next.markers);
  const coverage = ["MISSING", "UNKNOWN", "UNAVAILABLE", "DENIED"].includes(state)
    ? "UNKNOWN"
    : markers.length || ["PARTIAL", "STALE"].includes(state) || next.next_cursor
      ? "PARTIAL" : next.coverage;
  return {
    ...next, state, coverage, markers,
    returned: (previous.returned ?? 0) + (next.returned ?? 0),
  };
}

export function criteriaForSelection(selection) {
  if (!selection?.id) return { kind: "context", value: "" };
  const kinds = {
    evidence: "record", capability: "capability", episode: "episode",
    semantic: "semantic", memory: "memory", checkpoint: "checkpoint", generation: "record",
    correction: "correction", strategy: "reference", neural: "reference",
    warning: "reference",
  };
  return { kind: kinds[selection.kind] ?? "record", value: selection.id };
}
