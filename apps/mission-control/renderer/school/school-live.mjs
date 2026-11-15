const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";
const CAPABILITY_SCHEMA = "bilqis.bamf.mission-control.capability-snapshot/v1";
const PAGE_LIMIT = 32;
const MAX_PAGES = 128;

function value(datum) {
  return datum?.state === "PRESENT" ? datum.value : null;
}

export function capabilityQuery(context, cursor = null) {
  const historical = context?.mode === "HISTORICAL";
  return Object.freeze({
    schema: QUERY_SCHEMA,
    family: "capability",
    mode: historical ? "historical" : "current",
    run_id: context?.runId ?? null,
    record_id: null,
    schema_version: CAPABILITY_SCHEMA,
    generation: historical ? context?.generation ?? null : null,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor,
    limit: PAGE_LIMIT,
  });
}

export function schoolRowFromRecord(record) {
  if (record?.schema_version !== CAPABILITY_SCHEMA) return null;
  return Object.freeze({
    id: record.capability_id,
    grade: record.grade_id,
    family: null,
    prerequisites: Object.freeze([]),
    was: null,
    top: null,
    now: value(record.score_correct),
    total: value(record.score_total),
    growth: null,
    debt: value(record.debt),
    pRet: null,
    visits: null,
    retainedSteps: null,
    lastGain: null,
    lastRegression: null,
    strategy: null,
    sourceFamilies: Object.freeze([]),
    sourceState: null,
    implementationState: null,
    lifecycleState: record.status,
    qualificationState: record.status,
    staleDebt: false,
    recentGain: false,
    observedDebt: value(record.debt) !== null,
    schedulingSemantics: null,
    observedAt: record.meta?.observed_at ?? null,
    materializedAt: record.meta?.materialized_at ?? null,
    recordId: record.meta?.record_id ?? record.capability_id,
    sourceRefs: Object.freeze([...(record.meta?.source_refs ?? [])]),
    evidenceRefs: Object.freeze([...(record.meta?.evidence_refs ?? [])]),
    receiptRefs: Object.freeze([...(record.meta?.receipt_refs ?? [])]),
  });
}

export async function loadSchoolRows(api, context) {
  if (!api || typeof api.query !== "function") {
    return Object.freeze({
      state: "UNAVAILABLE",
      coverage: "UNKNOWN",
      rows: Object.freeze([]),
      reason: "CONTROL_PLANE_QUERY_UNAVAILABLE",
    });
  }
  const rows = [];
  let cursor = null;
  let state = "EMPTY";
  let coverage = "UNKNOWN";
  for (let pageIndex = 0; pageIndex < MAX_PAGES; pageIndex += 1) {
    const page = await api.query(capabilityQuery(context, cursor));
    if (page?.accepted !== true) {
      return Object.freeze({
        state: page?.state ?? "UNAVAILABLE",
        coverage: page?.coverage ?? "UNKNOWN",
        rows: Object.freeze([]),
        reason: "CAPABILITY_QUERY_REJECTED",
      });
    }
    state = page.state;
    coverage = page.coverage;
    for (const record of page.records ?? []) {
      const row = schoolRowFromRecord(record);
      if (row) rows.push(row);
    }
    cursor = page.next_cursor ?? null;
    if (cursor === null) {
      return Object.freeze({
        state,
        coverage,
        rows: Object.freeze(rows),
        reason: null,
      });
    }
  }
  throw new RangeError("SCHOOL_CAPABILITY_QUERY_PAGE_LIMIT");
}
