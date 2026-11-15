export const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";
export const QUERY_PAGE_SCHEMA = "bilqis.bamf.control-plane.query-page/v1";
export const CONCEPT_SCHEMA = "bilqis.bamf.mission-control.semantic-concept-snapshot/v1";
export const STATE_SCHEMA = "bilqis.bamf.mission-control.semantic-generation-state/v1";
export const BANK_SCHEMA = "bilqis.bamf.mission-control.semantic-bank-snapshot/v1";
export const HELD_SCHEMA = "bilqis.bamf.mission-control.semantic-held-mapping/v1";
export const SIMILARITY_SCHEMA = "bilqis.bamf.mission-control.semantic-similarity-snapshot/v1";
export const SUMMARY_SCHEMA = "bilqis.bamf.mission-control.semantic-atlas-snapshot/v1";

const PAGE_STATES = new Set([
  "PRESENT", "EMPTY", "MISSING", "UNAVAILABLE", "PARTIAL", "STALE", "DENIED", "UNKNOWN",
]);

export function invalid(detail) {
  throw new TypeError(`MISSION_CONTROL_SEMANTIC_QUERY_INVALID:${detail}`);
}

export function conceptRecordId(semanticRelease, semanticId) {
  if (typeof semanticRelease !== "string" || !/^[0-9a-f]{64}$/.test(semanticRelease) ||
      typeof semanticId !== "string" || semanticId.length === 0 || semanticId.includes("\n")) {
    invalid("CONCEPT_ID");
  }
  return `semantic-concept:${semanticRelease}:${semanticId}`;
}

export function stateRecordId(context, bank, row) {
  if (!context || typeof context.runId !== "string" || !Number.isSafeInteger(context.generation) ||
      !Number.isSafeInteger(bank) || bank < 0 || !Number.isSafeInteger(row) || row < 0) {
    invalid("STATE_ID");
  }
  return `semantic-state:${context.runId}:${context.generation}:${bank}:${row}`;
}

export function queryRequest({
  family = "semantic", mode = "current", runId = null, recordId = null,
  schemaVersion = null, generation = null, frontierId = null, asOf = null,
  reference = null, cursor = null, limit = 32,
} = {}) {
  return Object.freeze({
    schema: QUERY_SCHEMA,
    family,
    mode,
    run_id: runId,
    record_id: recordId,
    schema_version: schemaVersion,
    generation,
    frontier_id: frontierId,
    as_of: asOf,
    reference,
    cursor,
    limit,
  });
}

function generationSelector(context) {
  if (context.mode === "HISTORICAL") {
    return { mode: "historical", runId: context.runId, generation: context.generation };
  }
  return { mode: "current", runId: context.runId };
}

export function generationQuery(context, options = {}) {
  return queryRequest({ ...generationSelector(context), ...options });
}

export function sourceQuery(options = {}) {
  return queryRequest({ mode: "current", ...options });
}

export function assertQueryPage(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) invalid("PAGE");
  if (raw.accepted === false) {
    if (typeof raw.reason !== "string" || raw.reason.length === 0) invalid("ERROR");
    return raw;
  }
  if (raw.schema !== QUERY_PAGE_SCHEMA || raw.accepted !== true ||
      !PAGE_STATES.has(raw.state) || !Array.isArray(raw.records) ||
      !Array.isArray(raw.markers) || !Array.isArray(raw.links) ||
      !Number.isSafeInteger(raw.total_matches) || raw.total_matches < 0) {
    invalid("PAGE_SHAPE");
  }
  return raw;
}

async function ask(api, request) {
  if (!api || typeof api.query !== "function") invalid("QUERY_CAPABILITY");
  return assertQueryPage(await api.query(request));
}

export function firstRecord(page, schema) {
  return page.accepted === true
    ? page.records.find((record) => record?.schema_version === schema) ?? null
    : null;
}

export async function loadAtlasOverview(api, context) {
  const summary = await ask(api, generationQuery(context, { schemaVersion: SUMMARY_SCHEMA, limit: 1 }));
  const release = firstRecord(summary, SUMMARY_SCHEMA)?.atlas_release_sha256 ?? null;
  const [banks, held, similarities] = await Promise.all([
    ask(api, generationQuery(context, { schemaVersion: BANK_SCHEMA, limit: 32 })),
    heldForRelease(api, release),
    ask(api, generationQuery(context, { schemaVersion: SIMILARITY_SCHEMA, limit: 8 })),
  ]);
  return Object.freeze({ summary, banks, held, similarities });
}

async function heldForRelease(api, release) {
  if (typeof release !== "string" || !/^[0-9a-f]{64}$/.test(release)) {
    return Object.freeze({ accepted: true, records: Object.freeze([]) });
  }
  let cursor = null;
  const records = [];
  do {
    const page = await ask(api, sourceQuery({ schemaVersion: HELD_SCHEMA, cursor, limit: 32 }));
    if (page.accepted !== true) return Object.freeze({ accepted: false, records: Object.freeze([]) });
    records.push(...page.records.filter((record) =>
      record?.schema_version === HELD_SCHEMA && record.atlas_release_sha256 === release));
    cursor = page.next_cursor;
  } while (cursor && records.length < 8);
  return Object.freeze({ accepted: true, records: Object.freeze(records.slice(0, 8)) });
}

async function learnedEdges(api, context, semanticId) {
  const references = await ask(api, generationQuery(context, {
    family: "reference", reference: semanticId, limit: 32,
  }));
  if (references.accepted !== true) return [];
  const recordIds = [...new Set(references.links
    .filter((link) => link.relation === "LEARNED_SIMILARITY_SOURCE" ||
      link.relation === "LEARNED_SIMILARITY_TARGET")
    .map((link) => link.source_record_id))];
  const pages = await Promise.all(recordIds.slice(0, 32).map((recordId) =>
    ask(api, generationQuery(context, { recordId, limit: 1 }))));
  return pages.map((page) => firstRecord(page, SIMILARITY_SCHEMA)).filter(Boolean);
}

async function heldForIdentity(api, semanticId, release) {
  const references = await ask(api, sourceQuery({
    family: "reference", reference: semanticId, limit: 32,
  }));
  if (references.accepted !== true) return null;
  const ids = references.links.filter((link) => link.relation === "HELD_SEMANTIC_IDENTITY")
    .map((link) => link.source_record_id);
  const pages = await Promise.all(ids.slice(0, 32).map((recordId) =>
    ask(api, sourceQuery({ recordId, limit: 1 }))));
  return pages.map((page) => firstRecord(page, HELD_SCHEMA))
    .find((record) => record?.atlas_release_sha256 === release) ?? null;
}

export async function loadSemanticIdentity(api, context, semanticId) {
  if (context.mode === "HISTORICAL") {
    const references = await ask(api, generationQuery(context, {
      family: "reference", reference: semanticId, limit: 32,
    }));
    const identity = references.accepted === true
      ? references.links.find((link) => link.relation === "SEMANTIC_IDENTITY") : null;
    if (!identity) return Object.freeze({ semanticId, concept: null, state: null,
      held: null, similarities: [] });
    const statePage = await ask(api, generationQuery(context, {
      recordId: identity.source_record_id, limit: 1,
    }));
    const state = firstRecord(statePage, STATE_SCHEMA);
    const conceptId = state?.concept_record_id ?? identity.target_record_id;
    const conceptPage = conceptId
      ? await ask(api, sourceQuery({ recordId: conceptId, limit: 1 })) : null;
    const concept = conceptPage ? firstRecord(conceptPage, CONCEPT_SCHEMA) : null;
    const similarities = await learnedEdges(api, context, semanticId);
    return Object.freeze({ semanticId, concept, state, held: null, similarities });
  }
  const conceptPage = await ask(api, sourceQuery({
    recordId: conceptRecordId(context.semanticRelease, semanticId), limit: 1,
  }));
  const concept = firstRecord(conceptPage, CONCEPT_SCHEMA);
  if (!concept) {
    return Object.freeze({ semanticId, concept: null, state: null,
      held: await heldForIdentity(api, semanticId, context.semanticRelease), similarities: [] });
  }
  const statePage = await ask(api, generationQuery(context, {
    recordId: stateRecordId(context, concept.abi_bank, concept.abi_row), limit: 1,
  }));
  const state = firstRecord(statePage, STATE_SCHEMA);
  const similarities = await learnedEdges(api, context, semanticId);
  return Object.freeze({ semanticId, concept, state, held: null, similarities });
}

export async function loadAbiRow(api, context, bank, row) {
  const statePage = await ask(api, generationQuery(context, {
    recordId: stateRecordId(context, bank, row), limit: 1,
  }));
  const state = firstRecord(statePage, STATE_SCHEMA);
  if (!state) return Object.freeze({ bank, row, state: null, concept: null, similarities: [] });
  const conceptPage = state.concept_record_id
    ? await ask(api, sourceQuery({ recordId: state.concept_record_id, limit: 1 }))
    : null;
  const concept = conceptPage ? firstRecord(conceptPage, CONCEPT_SCHEMA) : null;
  const similarities = await learnedEdges(api, context, state.semantic_id);
  return Object.freeze({ bank, row, state, concept, similarities });
}
