const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";
const SALIENCE_SCHEMA = "bilqis.bamf.mission-control.salience-event/v1";
const PAGE_LIMIT = 32;
const MAX_PAGES = 64;

function dataValue(value) {
  return Object.freeze({
    state: value?.state ?? "UNKNOWN",
    origin: value?.origin ?? null,
    value: value?.state === "PRESENT" ? value.value : null,
    units: value?.units ?? null,
  });
}

export function salienceQuery(context, cursor = null) {
  const historical = context?.mode === "HISTORICAL";
  return Object.freeze({
    schema: QUERY_SCHEMA,
    family: "salience",
    mode: historical ? "historical" : "current",
    run_id: context?.runId ?? null,
    record_id: null,
    schema_version: SALIENCE_SCHEMA,
    generation: historical ? context?.generation ?? null : null,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor,
    limit: PAGE_LIMIT,
  });
}

export function salienceEventFromRecord(record) {
  if (record?.schema_version !== SALIENCE_SCHEMA) return null;
  return Object.freeze({
    recordId: record.meta?.record_id ?? record.salience_id,
    salienceId: record.salience_id,
    capabilityId: record.capability_id,
    actionKind: record.action_kind,
    axes: Object.freeze({
      impact: dataValue(record.impact),
      exigency: dataValue(record.exigency),
      novelty: dataValue(record.novelty),
    }),
    observedAt: record.meta?.observed_at ?? null,
    effectiveAt: null,
    materializedAt: record.meta?.materialized_at ?? null,
    asOf: record.meta?.as_of ?? null,
    coverage: record.meta?.coverage ?? "UNKNOWN",
    authority: record.meta?.authority ?? "UNKNOWN",
    sourceRefs: Object.freeze([...(record.meta?.source_refs ?? [])]),
    evidenceRefs: Object.freeze([...(record.meta?.evidence_refs ?? [])]),
    receiptRefs: Object.freeze([...(record.meta?.receipt_refs ?? [])]),
  });
}

export async function loadSalienceSnapshot(api, context) {
  if (!api || typeof api.query !== "function") {
    return Object.freeze({ state: "UNAVAILABLE", coverage: "UNKNOWN", events: Object.freeze([]) });
  }
  const events = [];
  let cursor = null;
  let state = "EMPTY";
  let coverage = "UNKNOWN";
  for (let pageIndex = 0; pageIndex < MAX_PAGES; pageIndex += 1) {
    const page = await api.query(salienceQuery(context, cursor));
    if (page?.accepted !== true) {
      return Object.freeze({
        state: page?.state ?? "UNAVAILABLE",
        coverage: page?.coverage ?? "UNKNOWN",
        events: Object.freeze([]),
      });
    }
    state = page.state;
    coverage = page.coverage ?? "UNKNOWN";
    events.push(...(page.records ?? []).map(salienceEventFromRecord).filter(Boolean));
    cursor = page.next_cursor ?? null;
    if (cursor === null) break;
    if (pageIndex === MAX_PAGES - 1) throw new RangeError("SALIENCE_QUERY_PAGE_LIMIT");
  }
  events.sort((left, right) => (
    (left.observedAt ?? -1) - (right.observedAt ?? -1)
    || (left.materializedAt ?? -1) - (right.materializedAt ?? -1)
    || left.recordId.localeCompare(right.recordId)
  ));
  return Object.freeze({
    state: events.length ? state : state === "PRESENT" ? "EMPTY" : state,
    coverage,
    events: Object.freeze(events),
  });
}
