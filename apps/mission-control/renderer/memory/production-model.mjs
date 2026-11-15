const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";
const MEMORY_SCHEMA = "bilqis.bamf.mission-control.memory-snapshot/v1";
const PRESENT = "PRESENT";

function datum(value) {
  if (value?.state !== PRESENT) {
    return Object.freeze({ state: value?.state ?? "UNAVAILABLE", value: null, units: value?.units ?? null, origin: value?.origin ?? null });
  }
  return Object.freeze({ state: PRESENT, value: value.value, units: value.units ?? null, origin: value.origin ?? "MEASURED" });
}

function memoryRecords(page) {
  return page?.accepted === true && Array.isArray(page.records)
    ? page.records.filter(record => record?.schema_version === MEMORY_SCHEMA)
    : [];
}

export function memoryQuery(context, overrides = {}) {
  const historical = context?.mode === "HISTORICAL";
  return Object.freeze({
    schema: QUERY_SCHEMA,
    family: "memory",
    mode: historical ? "historical" : "current",
    run_id: context?.runId ?? null,
    record_id: null,
    schema_version: MEMORY_SCHEMA,
    generation: historical ? context?.generation ?? null : null,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor: null,
    limit: 64,
    ...overrides,
  });
}

export function historicalMemoryQuery(context, generation) {
  if (!Number.isSafeInteger(generation) || generation < 0) {
    throw new TypeError("GUI10_HISTORICAL_GENERATION_REQUIRED");
  }
  return memoryQuery({ ...context, mode: "HISTORICAL", generation }, {
    mode: "historical",
    generation,
  });
}

export function memoryProfileFromPage(page, context) {
  const records = memoryRecords(page);
  const record = records.at(-1) ?? null;
  if (!record) return null;
  return Object.freeze({
    provenance: "LIVE_QUERY",
    pageState: page?.accepted === true ? page.state : "UNAVAILABLE",
    generation: context?.generation ?? record.meta?.run?.generation ?? null,
    recordId: record.meta?.record_id ?? null,
    observedAt: record.meta?.observed_at ?? null,
    sourceRefs: Object.freeze([...(record.meta?.source_refs ?? [])]),
    evidenceRefs: Object.freeze([...(record.meta?.evidence_refs ?? [])]),
    receiptRefs: Object.freeze([...(record.meta?.receipt_refs ?? [])]),
    metrics: Object.freeze({
      used: datum(record.used_bytes),
      budget: datum(record.budget_bytes),
      hits: datum(record.hits),
      misses: datum(record.misses),
      requalifications: datum(record.requalifications),
    }),
  });
}

export function memoryComparison(before, after) {
  return Object.freeze(Object.keys(after?.metrics ?? {}).map(key => {
    const left = before?.metrics?.[key] ?? null;
    const right = after?.metrics?.[key] ?? null;
    const comparable = left?.state === PRESENT && right?.state === PRESENT &&
      Number.isFinite(left.value) && Number.isFinite(right.value) && left.units === right.units;
    return Object.freeze({ key, before: left, after: right, delta: comparable ? right.value - left.value : null });
  }));
}
