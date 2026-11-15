const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";
const CORRECTION_SCHEMA = "bilqis.bamf.mission-control.correction-event/v1";
const TERMINAL_EVIDENCE_STATES = new Set(["RECOMPUTED", "REQUALIFIED"]);

export function correctionQuery(context) {
  const historical = context?.mode === "HISTORICAL";
  return Object.freeze({
    schema: QUERY_SCHEMA, family: "correction", mode: historical ? "historical" : "current",
    run_id: context?.runId ?? null, record_id: null, schema_version: CORRECTION_SCHEMA,
    generation: historical ? context?.generation ?? null : null, frontier_id: null,
    as_of: null, reference: null, cursor: null, limit: 32,
  });
}

export function productionProjectionFromPage(page, context, selectedId = null) {
  const records = page?.accepted === true && Array.isArray(page.records)
    ? page.records.filter(record => record?.schema_version === CORRECTION_SCHEMA) : [];
  const selected = records.find(record => record.correction_id === selectedId || record.meta?.record_id === selectedId)
    ?? records.at(-1) ?? null;
  if (!selected) return Object.freeze({
    posture: context?.mode === "HISTORICAL" ? "historical" : "live",
    generation: context?.mode === "HISTORICAL" ? context?.generation ?? null : null,
    pageState: page?.accepted === true ? page.state : "UNAVAILABLE", correction: null,
    nodes: Object.freeze([]), edges: Object.freeze([]), queue: Object.freeze([]), history: Object.freeze([]),
  });
  const history = records.map(record => Object.freeze({
    id: record.meta?.record_id ?? record.correction_id,
    phase: "CORRECTION_RECORDED", atGeneration: record.meta?.run?.generation ?? null,
    observedAt: record.meta?.observed_at ?? null,
    receipt: record.meta?.receipt_refs?.[0] ?? null,
    states: Object.freeze({ [record.target_ref]: record.state }),
  }));
  return Object.freeze({
    posture: context?.mode === "HISTORICAL" ? "historical" : "live",
    generation: context?.mode === "HISTORICAL" ? context?.generation ?? null : null,
    pageState: page.state,
    correction: Object.freeze({
      id: selected.correction_id, recordId: selected.meta?.record_id ?? selected.correction_id,
      correctionGeneration: selected.correction_generation, sourceRef: selected.target_ref,
      priorRevision: selected.old_digest, currentRevision: selected.new_digest,
      oldDigest: selected.old_digest, newDigest: selected.new_digest,
      observedAt: selected.meta?.observed_at ?? null,
      sourceReference: selected.meta?.source_refs?.[0] ?? null,
      sourceReceipt: null,
      recordedReceipt: selected.meta?.receipt_refs?.[0] ?? null,
    }),
    nodes: Object.freeze([]), edges: Object.freeze([]), queue: Object.freeze([]), history: Object.freeze(history),
  });
}

export function correctionById(projection, id = projection?.correction?.id) {
  if (!projection?.correction || ![projection.correction.id, projection.correction.recordId].includes(id)) {
    throw new RangeError(`CORRECTION_UNKNOWN:${id}`);
  }
  return projection.correction;
}

export function nodeById(projection, id) {
  return projection?.nodes?.find(node => node.id === id) ?? null;
}

export function evidencedDescendants(projection, rootId = projection?.correction?.currentRevision) {
  if (!rootId) return Object.freeze([]);
  const outgoing = new Map();
  for (const edge of projection?.edges ?? []) {
    const list = outgoing.get(edge.from) ?? [];
    list.push(edge.to); outgoing.set(edge.from, list);
  }
  const seen = new Set([rootId]); const queue = [rootId];
  while (queue.length) {
    const from = queue.shift();
    for (const to of outgoing.get(from) ?? []) {
      if (seen.has(to)) continue; seen.add(to); queue.push(to);
    }
  }
  return Object.freeze((projection?.nodes ?? []).filter(node => seen.has(node.id)));
}

export function impactRows(projection) {
  return Object.freeze(evidencedDescendants(projection).map(node => Object.freeze({
    id: node.id, kind: node.kind, state: node.state, evidenceRefs: node.evidenceRefs,
  })));
}

export function unknownInfluenceRows(projection) {
  return Object.freeze(impactRows(projection).filter(row => row.state === "UNAVAILABLE_UNKNOWN"));
}

export function requalificationQueue(projection) { return projection?.queue ?? Object.freeze([]); }

export function historyFor(projection, id) {
  return Object.freeze((projection?.history ?? []).filter(entry => Object.hasOwn(entry.states, id)).map(entry => Object.freeze({
    historyId: entry.id, phase: entry.phase, generation: entry.atGeneration,
    observedAt: entry.observedAt ?? null, state: entry.states[id], receipt: entry.receipt,
  })));
}

export function assertReceiptBackedTerminalStates(projection) {
  for (const row of impactRows(projection)) {
    if (TERMINAL_EVIDENCE_STATES.has(row.state) && !row.evidenceRefs.length) {
      throw new TypeError(`CORRECTION_TERMINAL_STATE_UNRECEIPTED:${row.id}`);
    }
  }
  for (const entry of projection?.history ?? []) {
    for (const [id, state] of Object.entries(entry.states)) {
      if (state === "REQUALIFIED" && !entry.receipt) throw new TypeError(`CORRECTION_REQUALIFIED_UNRECEIPTED:${id}`);
    }
  }
  return true;
}

export function correctionDeepLink(id) { return `#view=corrections&kind=correction&id=${encodeURIComponent(id)}`; }
