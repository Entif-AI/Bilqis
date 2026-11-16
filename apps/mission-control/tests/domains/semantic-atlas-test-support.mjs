import {
  BANK_SCHEMA, CONCEPT_SCHEMA, HELD_SCHEMA, SIMILARITY_SCHEMA, STATE_SCHEMA, SUMMARY_SCHEMA,
  conceptRecordId,
} from "../../renderer/atlas/semantic-atlas.mjs";

export const RELEASE = "1".repeat(64);
export const ROOT_ID = "https://github.com/Entif-AI/Bilqis-MLX/id/root/NI-LEXICON-CURRICULUM/LEXROOT-007a2c39cfe74c";
export const SENSE_1 = ROOT_ID.replace("/id/root/", "/id/sense/") + "/STEM%201/BSC";
export const SENSE_2 = ROOT_ID.replace("/id/root/", "/id/sense/") + "/STEM%202/BSC";
export const MATERIALIZED_AT = 1794744000;
export const OBSERVED_AT = 1794743940;
export const CONCEPT_MATERIALIZED_AT = 1794743700;
export const SUMMARY_MATERIALIZED_AT = 1794743800;
export const context = Object.freeze({
  runId: "run-semantic",
  generation: 7,
  mode: "LIVE",
  semanticRelease: RELEASE,
});

export function page(request, records = [], links = [], total = records.length + links.length) {
  return {
    schema: "bilqis.bamf.control-plane.query-page/v1",
    query_id: "a".repeat(64),
    request,
    family: request.family,
    mode: request.mode,
    state: total ? "PRESENT" : "EMPTY",
    coverage: "COMPLETE",
    total_matches: total,
    returned: records.length + links.length,
    truncated: false,
    next_cursor: null,
    records,
    markers: [],
    links,
    accepted: true,
  };
}

export function concept(semanticId = SENSE_1) {
  return {
    schema_version: CONCEPT_SCHEMA,
    meta: { materialized_at: CONCEPT_MATERIALIZED_AT, observed_at: OBSERVED_AT, authority: "SOURCE_AUTHORITATIVE" },
    semantic_id: semanticId,
    kind: "sense",
    atlas_release_sha256: RELEASE,
    types: ["skos:Concept"],
    labels: [],
    realizations: [],
    source_loci: ["New Ithkuil Lexicon §4.3 p.179"],
    source_rows: [],
    relations: [{ predicate: "skos:broader", target_semantic_id: ROOT_ID }],
    abi_index: 1,
    abi_bank: 0,
    abi_row: 1,
    implementation_status: "ADMITTED",
    teaching_candidate: true,
    teaching_reason: "SOURCE_ELIGIBLE",
    frame_schema_refs: ["frame:copular/v1"],
    capability_ids: ["D.COPULAR_IDENTITY"],
  };
}

export function generationState(admission = "ACTIVE") {
  return {
    schema_version: STATE_SCHEMA,
    meta: { materialized_at: MATERIALIZED_AT, observed_at: OBSERVED_AT, authority: "DERIVED" },
    semantic_id: SENSE_1,
    concept_record_id: conceptRecordId(RELEASE, SENSE_1),
    abi_index: 1,
    abi_bank: 0,
    abi_row: 1,
    admission_state: admission,
    newly_admitted: false,
    recently_exercised: true,
    requalification_affected: false,
  };
}

export function similarity() {
  return {
    schema_version: SIMILARITY_SCHEMA,
    source_semantic_id: SENSE_1,
    target_semantic_id: SENSE_2,
    basis_ref: "embedding:fixture",
    similarity: { state: "PRESENT", origin: "DERIVED", value: 0.97, units: "similarity" },
    canonical_equivalence: false,
  };
}
