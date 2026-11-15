const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";
const TEACHER_SCHEMA = "bilqis.bamf.mission-control.teacher-snapshot/v1";
const PAGE_LIMIT = 32;
const MAX_PAGES = 64;

function datumValue(datum) {
  return datum?.state === "PRESENT" ? datum.value : null;
}

export function teacherQuery(context, cursor = null) {
  const historical = context?.mode === "HISTORICAL";
  return Object.freeze({
    schema: QUERY_SCHEMA,
    family: "teacher",
    mode: historical ? "historical" : "current",
    run_id: context?.runId ?? null,
    record_id: null,
    schema_version: TEACHER_SCHEMA,
    generation: historical ? context?.generation ?? null : null,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor,
    limit: PAGE_LIMIT,
  });
}

export function teacherSnapshotFromRecord(record) {
  if (record?.schema_version !== TEACHER_SCHEMA) return null;
  return Object.freeze({
    recordId: record.meta?.record_id ?? record.strategy_id,
    strategyId: record.strategy_id,
    teacherIdentity: record.teacher_identity,
    teacherEpoch: record.teacher_epoch,
    attempts: datumValue(record.attempts),
    accepted: datumValue(record.accepted),
    rejected: datumValue(record.rejected),
    observedAt: record.meta?.observed_at ?? null,
    materializedAt: record.meta?.materialized_at ?? null,
    coverage: record.meta?.coverage ?? "UNKNOWN",
    sourceRefs: Object.freeze([...(record.meta?.source_refs ?? [])]),
    evidenceRefs: Object.freeze([...(record.meta?.evidence_refs ?? [])]),
    receiptRefs: Object.freeze([...(record.meta?.receipt_refs ?? [])]),
  });
}

export async function loadTeacherSnapshot(api, context) {
  if (!api || typeof api.query !== "function") {
    return Object.freeze({ state: "UNAVAILABLE", coverage: "UNKNOWN", snapshot: null });
  }
  const snapshots = [];
  let cursor = null;
  let state = "EMPTY";
  let coverage = "UNKNOWN";
  for (let pageIndex = 0; pageIndex < MAX_PAGES; pageIndex += 1) {
    const page = await api.query(teacherQuery(context, cursor));
    if (page?.accepted !== true) {
      return Object.freeze({
        state: page?.state ?? "UNAVAILABLE",
        coverage: page?.coverage ?? "UNKNOWN",
        snapshot: null,
      });
    }
    state = page.state;
    coverage = page.coverage ?? "UNKNOWN";
    snapshots.push(...(page.records ?? []).map(teacherSnapshotFromRecord).filter(Boolean));
    cursor = page.next_cursor ?? null;
    if (cursor === null) break;
    if (pageIndex === MAX_PAGES - 1) throw new RangeError("TEACHER_QUERY_PAGE_LIMIT");
  }
  snapshots.sort((left, right) => (
    (left.observedAt ?? -1) - (right.observedAt ?? -1)
    || (left.materializedAt ?? -1) - (right.materializedAt ?? -1)
    || left.recordId.localeCompare(right.recordId)
  ));
  const snapshot = snapshots.at(-1) ?? null;
  return Object.freeze({
    state: snapshot ? state : state === "PRESENT" ? "EMPTY" : state,
    coverage,
    snapshot,
  });
}
