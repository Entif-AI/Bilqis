import {
  BANK_SCHEMA,
  CONCEPT_SCHEMA,
  HELD_SCHEMA,
  QUERY_PAGE_SCHEMA,
  SIMILARITY_SCHEMA,
  STATE_SCHEMA,
  SUMMARY_SCHEMA,
  conceptRecordId,
  stateRecordId,
} from "./semantic-atlas.mjs";

const RUN_ID = "fixture-run";
const GENERATION = 7;
const RELEASE = "3".repeat(64);
const ROOT = "https://example.test/id/root/atlas-fixture";
const SEMANTIC = "https://example.test/id/sense/atlas-fixture/primary";
const NEIGHBOR = "https://example.test/id/sense/atlas-fixture/neighbor";
const MATERIALIZED = 1794700120;
const OBSERVED = 1794700118;

function meta(recordId, authority, { run = true, observedAt = OBSERVED } = {}) {
  return {
    record_id: recordId,
    run: run ? {
      run_id: RUN_ID,
      run_identity_sha256: "4".repeat(64),
      generation: GENERATION,
      generation_manifest_sha256: "1".repeat(64),
      candidate_identity_sha256: "2".repeat(64),
      factory_release_sha256: "2".repeat(64),
      semantic_release_sha256: RELEASE,
      topology_sha256: "4".repeat(64),
    } : null,
    materialized_at: MATERIALIZED,
    observed_at: observedAt,
    as_of: observedAt,
    coverage: "COMPLETE",
    authority,
    source_refs: [],
    evidence_refs: [],
    receipt_refs: [],
  };
}

const concept = Object.freeze({
  schema_version: CONCEPT_SCHEMA,
  meta: meta(conceptRecordId(RELEASE, SEMANTIC), "SOURCE_AUTHORITATIVE", { run: false }),
  atlas_release_sha256: RELEASE,
  semantic_id: SEMANTIC,
  kind: "sense",
  types: ["skos:Concept"],
  labels: [],
  realizations: [],
  source_loci: ["Reference fixture · semantic source row 12"],
  source_rows: [],
  relations: [{ predicate: "skos:broader", target_semantic_id: ROOT }],
  abi_index: 1,
  abi_bank: 0,
  abi_row: 1,
  implementation_status: "ADMITTED",
  teaching_candidate: true,
  teaching_reason: "SOURCE_ELIGIBLE",
  frame_schema_refs: ["frame:relation/v2"],
  capability_ids: ["B.EXAMPLE"],
});

const generationState = Object.freeze({
  schema_version: STATE_SCHEMA,
  meta: meta(stateRecordId({ runId: RUN_ID, generation: GENERATION }, 0, 1), "DERIVED"),
  semantic_id: SEMANTIC,
  concept_record_id: conceptRecordId(RELEASE, SEMANTIC),
  abi_index: 1,
  abi_bank: 0,
  abi_row: 1,
  admission_state: "ACTIVE",
  newly_admitted: false,
  recently_exercised: true,
  requalification_affected: false,
});

const similarity = Object.freeze({
  schema_version: SIMILARITY_SCHEMA,
  meta: meta("semantic-similarity:fixture:primary-neighbor", "DERIVED"),
  source_semantic_id: SEMANTIC,
  target_semantic_id: NEIGHBOR,
  basis_ref: "embedding:fixture:g7",
  similarity: { state: "PRESENT", origin: "DERIVED", value: 0.91, units: "similarity" },
  canonical_equivalence: false,
});

const held = Object.freeze({
  schema_version: HELD_SCHEMA,
  meta: meta("semantic-held:fixture:ambiguous", "SOURCE_AUTHORITATIVE", { run: false }),
  atlas_release_sha256: RELEASE,
  domain: "mapping",
  table: "fixture_mapping",
  key: "ambiguous-fixture",
  semantic_id: null,
  source_disposition: "HELD",
  implementation_status: "UNRESOLVED",
  reason_code: "AMBIGUOUS_MAPPING",
  teaching_reason: "HOLD_FOR_REVIEW",
  owner: "REFERENCE_FIXTURE",
});

function page(request, records = [], links = []) {
  const total = records.length + links.length;
  return Object.freeze({
    schema: QUERY_PAGE_SCHEMA,
    query_id: "f".repeat(64),
    request: structuredClone(request),
    family: request.family,
    mode: request.mode,
    state: total ? "PRESENT" : "EMPTY",
    coverage: "COMPLETE",
    total_matches: total,
    returned: total,
    truncated: false,
    next_cursor: null,
    records: structuredClone(records),
    markers: [],
    links: structuredClone(links),
    accepted: true,
  });
}

export function createAtlasFixtureApi() {
  return Object.freeze({
    async query(request) {
      if ((request.run_id !== null && request.run_id !== RUN_ID) ||
          (request.generation !== null && request.generation !== GENERATION)) {
        return page(request);
      }
      if (request.schema_version === SUMMARY_SCHEMA) {
        return page(request, [{
          schema_version: SUMMARY_SCHEMA,
          meta: meta("semantic-atlas:fixture-run:7", "DERIVED"),
          atlas_bundle_id: "5".repeat(64),
          atlas_release_sha256: RELEASE,
          source_bundle_id: "6".repeat(64),
          active_concepts: { state: "PRESENT", origin: "MEASURED", value: 742 },
          source_eligible: { state: "PRESENT", origin: "SOURCE_AUTHORITATIVE", value: 801 },
          source_held: { state: "PRESENT", origin: "SOURCE_AUTHORITATIVE", value: 1 },
        }]);
      }
      if (request.schema_version === BANK_SCHEMA) {
        return page(request, [{
          schema_version: BANK_SCHEMA,
          meta: meta("semantic-bank:fixture-run:7:0", "DERIVED"),
          bank: 0,
          row_capacity: 8192,
          allocated_rows: 500,
          active_rows: 482,
          masked_rows: 18,
          newly_admitted_rows: 6,
          recently_exercised_rows: 41,
          requalification_affected_rows: 3,
        }]);
      }
      if (request.schema_version === HELD_SCHEMA) return page(request, [held]);
      if (request.schema_version === SIMILARITY_SCHEMA) return page(request, [similarity]);
      if (request.record_id === conceptRecordId(RELEASE, SEMANTIC)) return page(request, [concept]);
      if (request.record_id === stateRecordId({ runId: RUN_ID, generation: GENERATION }, 0, 1)) {
        return page(request, [generationState]);
      }
      if (request.record_id === similarity.meta.record_id) return page(request, [similarity]);
      if (request.family === "reference" && request.reference === SEMANTIC) {
        return page(request, [], [{
          relation: "LEARNED_SIMILARITY_SOURCE",
          source_record_id: similarity.meta.record_id,
          target_ref: SEMANTIC,
          target_record_id: similarity.meta.record_id,
        }]);
      }
      return page(request);
    },
  });
}

export const ATLAS_FIXTURE_IDENTITY = Object.freeze({
  runId: RUN_ID,
  generation: GENERATION,
  semanticRelease: RELEASE,
  semanticId: SEMANTIC,
});
