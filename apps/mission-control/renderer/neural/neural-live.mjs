const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";
export const NEURAL_RUNTIME_SCHEMA = "bilqis.bamf.mission-control.neural-runtime-sample/v1";
const PAGE_LIMIT = 32;
const MAX_PAGES = 64;

function runtimeDatum(datum) {
  if (!datum || typeof datum !== "object") return null;
  return Object.freeze({
    state: datum.state ?? "UNKNOWN",
    origin: datum.origin ?? "UNKNOWN",
    value: datum.state === "PRESENT" ? datum.value : null,
    units: datum.units ?? null,
  });
}

export function neuralRuntimeQuery(context, cursor = null) {
  const historical = context?.mode === "HISTORICAL";
  return Object.freeze({
    schema: QUERY_SCHEMA,
    family: "neural",
    mode: historical ? "historical" : "current",
    run_id: context?.runId ?? null,
    record_id: null,
    schema_version: NEURAL_RUNTIME_SCHEMA,
    generation: context?.generation ?? null,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor,
    limit: PAGE_LIMIT,
  });
}

export function neuralRuntimeFromRecord(record) {
  if (record?.schema_version !== NEURAL_RUNTIME_SCHEMA) return null;
  return Object.freeze({
    recordId: record.meta?.record_id ?? "",
    optimizerStep: record.optimizer_step,
    stepDurationMs: runtimeDatum(record.step_duration_ms),
    activeParameters: runtimeDatum(record.active_parameters),
    refinementFraction: runtimeDatum(record.refinement_fraction),
    observedAt: record.meta?.observed_at ?? null,
    materializedAt: record.meta?.materialized_at ?? null,
    coverage: record.meta?.coverage ?? "UNKNOWN",
    authority: record.meta?.authority ?? "UNKNOWN",
    sourceRefs: Object.freeze([...(record.meta?.source_refs ?? [])]),
    evidenceRefs: Object.freeze([...(record.meta?.evidence_refs ?? [])]),
    receiptRefs: Object.freeze([...(record.meta?.receipt_refs ?? [])]),
  });
}

export async function loadNeuralRuntime(api, context) {
  if (!api || typeof api.query !== "function") {
    return Object.freeze({ state: "UNAVAILABLE", coverage: "UNKNOWN", snapshot: null });
  }
  const records = [];
  let cursor = null;
  let state = "EMPTY";
  let coverage = "UNKNOWN";
  for (let pageIndex = 0; pageIndex < MAX_PAGES; pageIndex += 1) {
    const page = await api.query(neuralRuntimeQuery(context, cursor));
    if (page?.accepted !== true) {
      return Object.freeze({ state: page?.state ?? "UNAVAILABLE", coverage: page?.coverage ?? "UNKNOWN", snapshot: null });
    }
    state = page.state;
    coverage = page.coverage ?? "UNKNOWN";
    records.push(...(page.records ?? []).map(neuralRuntimeFromRecord).filter(Boolean));
    cursor = page.next_cursor ?? null;
    if (cursor === null) break;
    if (pageIndex === MAX_PAGES - 1) throw new RangeError("NEURAL_QUERY_PAGE_LIMIT");
  }
  records.sort((left, right) => (
    (left.observedAt ?? -1) - (right.observedAt ?? -1)
    || (left.materializedAt ?? -1) - (right.materializedAt ?? -1)
    || left.recordId.localeCompare(right.recordId)
  ));
  const snapshot = records.at(-1) ?? null;
  return Object.freeze({ state: snapshot ? state : state === "PRESENT" ? "EMPTY" : state, coverage, snapshot });
}
