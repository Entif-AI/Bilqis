"use strict";

const fs = require("node:fs");
const path = require("node:path");
const repo = path.resolve(__dirname, "../../../..");

const fixtureOperator = JSON.parse(fs.readFileSync(
  path.join(repo, "apps/mission-control/fixtures/operator-view-v1.json"), "utf8",
));
const mime = { ".html": "text/html", ".mjs": "text/javascript", ".js": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };

const schemas = Object.freeze({
  summary: "bilqis.bamf.mission-control.semantic-atlas-snapshot/v1",
  bank: "bilqis.bamf.mission-control.semantic-bank-snapshot/v1",
  held: "bilqis.bamf.mission-control.semantic-held-mapping/v1",
  concept: "bilqis.bamf.mission-control.semantic-concept-snapshot/v1",
  state: "bilqis.bamf.mission-control.semantic-generation-state/v1",
  similarity: "bilqis.bamf.mission-control.semantic-similarity-snapshot/v1",
});
const production = Object.freeze({
  runId: "production-run",
  generation: 7,
  release: "7".repeat(64),
  semantic: "https://production.example/id/sense/atlas/primary-with-a-long-semantic-identity",
  secondary: "https://production.example/id/sense/atlas/secondary-inspector-selection",
  neighbor: "https://production.example/id/sense/atlas/neighbor-with-an-even-longer-semantic-identity",
  root: "https://production.example/id/root/atlas/source-root-with-a-long-identity",
  sourceMaterialized: 1794699000,
  summaryMaterialized: 1794699900,
  materialized: 1794700120,
  observed: 1794700118,
});
const fixtureSemantic = "https://example.test/id/sense/atlas-fixture/primary";

function check(condition, message) {
  if (!condition) throw new Error(message);
}

function runRef() {
  return {
    run_id: production.runId,
    run_identity_sha256: "4".repeat(64),
    generation: production.generation,
    generation_manifest_sha256: "1".repeat(64),
    candidate_identity_sha256: "2".repeat(64),
    factory_release_sha256: "2".repeat(64),
    semantic_release_sha256: production.release,
    topology_sha256: "4".repeat(64),
  };
}

function meta(recordId, authority, {
  run = true, observedAt = production.observed, materializedAt = production.materialized,
} = {}) {
  return {
    record_id: recordId,
    run: run ? runRef() : null,
    materialized_at: materializedAt,
    observed_at: observedAt,
    as_of: observedAt,
    coverage: "COMPLETE",
    authority,
    source_refs: [],
    evidence_refs: [],
    receipt_refs: [],
  };
}

const productionOperator = structuredClone(fixtureOperator);
productionOperator.meta.record_id = `operator-view:${production.runId}:${production.generation}`;
productionOperator.meta.run = runRef();
productionOperator.meta.source_refs = [`run-state:${production.runId}:${production.generation}`];
productionOperator.meta.evidence_refs = [`evidence:${production.runId}:${production.generation}`];
productionOperator.meta.receipt_refs = [`receipt:${production.runId}:${production.generation}`];

const conceptId = `semantic-concept:${production.release}:${production.semantic}`;
const stateId = `semantic-state:${production.runId}:${production.generation}:0:1`;
const secondaryConceptId = `semantic-concept:${production.release}:${production.secondary}`;
const secondaryStateId = `semantic-state:${production.runId}:${production.generation}:0:2`;
const similarityId = "semantic-similarity:production:primary-neighbor";
const productionData = Object.freeze({
  summary: {
    schema_version: schemas.summary,
    meta: meta(`semantic-atlas:${production.runId}:${production.generation}`, "DERIVED", {
      materializedAt: production.summaryMaterialized,
    }),
    atlas_bundle_id: "5".repeat(64),
    atlas_release_sha256: production.release,
    source_bundle_id: "6".repeat(64),
    active_concepts: { state: "PRESENT", origin: "DERIVED", value: 742, units: null },
    source_eligible: { state: "PRESENT", origin: "SOURCE_AUTHORITATIVE", value: 801, units: null },
    source_held: { state: "PRESENT", origin: "SOURCE_AUTHORITATIVE", value: 1, units: null },
  },
  bank: {
    schema_version: schemas.bank,
    meta: meta(`semantic-bank:${production.runId}:${production.generation}:0`, "DERIVED"),
    bank: 0, row_capacity: 8192, allocated_rows: 500, active_rows: 482, masked_rows: 18,
    newly_admitted_rows: 6, recently_exercised_rows: 41, requalification_affected_rows: 3,
  },
  held: {
    schema_version: schemas.held,
    meta: meta("semantic-held:production:ambiguous", "SOURCE_AUTHORITATIVE", {
      run: false, materializedAt: production.sourceMaterialized,
    }),
    atlas_release_sha256: production.release,
    domain: "mapping", table: "production_mapping", key: "ambiguous-production",
    semantic_id: null, source_disposition: "HELD", implementation_status: "UNRESOLVED",
    reason_code: "AMBIGUOUS_MAPPING", teaching_reason: "HOLD_FOR_REVIEW", owner: "SOURCE_OWNER",
  },
  concept: {
    schema_version: schemas.concept,
    meta: meta(conceptId, "SOURCE_AUTHORITATIVE", {
      run: false, materializedAt: production.sourceMaterialized,
    }),
    atlas_release_sha256: production.release,
    semantic_id: production.semantic,
    kind: "sense",
    types: ["skos:Concept"], labels: [], realizations: [],
    source_loci: ["Production semantic source row 12 with a deliberately long source locus value"],
    source_rows: [],
    relations: Array.from({ length: 14 }, (_, index) => ({
      predicate: index % 2 ? "skos:related" : "skos:broader",
      target_semantic_id: `${production.root}/relation-${String(index).padStart(2, "0")}-with-long-target-identity`,
    })),
    abi_index: 1, abi_bank: 0, abi_row: 1,
    implementation_status: "ADMITTED", teaching_candidate: true,
    teaching_reason: "SOURCE_ELIGIBLE", frame_schema_refs: ["frame:relation/v2"],
    capability_ids: ["B.PRODUCTION.ATLAS"],
  },
  secondaryConcept: {
    schema_version: schemas.concept,
    meta: meta(secondaryConceptId, "SOURCE_AUTHORITATIVE", {
      run: false, materializedAt: production.sourceMaterialized,
    }),
    atlas_release_sha256: production.release,
    semantic_id: production.secondary,
    kind: "sense",
    types: ["skos:Concept"], labels: [], realizations: [],
    source_loci: ["Production semantic source row 13"], source_rows: [],
    relations: [{ predicate: "skos:broader", target_semantic_id: production.root }],
    abi_index: 2, abi_bank: 0, abi_row: 2,
    implementation_status: "ADMITTED", teaching_candidate: true,
    teaching_reason: "SOURCE_ELIGIBLE", frame_schema_refs: ["frame:relation/v2"],
    capability_ids: ["B.PRODUCTION.ATLAS"],
  },
  state: {
    schema_version: schemas.state,
    meta: meta(stateId, "DERIVED"),
    semantic_id: production.semantic,
    concept_record_id: conceptId,
    abi_index: 1, abi_bank: 0, abi_row: 1,
    admission_state: "ACTIVE", newly_admitted: false,
    recently_exercised: true, requalification_affected: false,
  },
  secondaryState: {
    schema_version: schemas.state,
    meta: meta(secondaryStateId, "DERIVED"),
    semantic_id: production.secondary,
    concept_record_id: secondaryConceptId,
    abi_index: 2, abi_bank: 0, abi_row: 2,
    admission_state: "ACTIVE", newly_admitted: false,
    recently_exercised: false, requalification_affected: false,
  },
  similarity: {
    schema_version: schemas.similarity,
    meta: meta(similarityId, "DERIVED"),
    source_semantic_id: production.semantic,
    target_semantic_id: production.neighbor,
    basis_ref: "embedding:production:g7",
    similarity: { state: "PRESENT", origin: "DERIVED", value: 0.91, units: "similarity" },
    canonical_equivalence: false,
  },
});

module.exports = {
  fixtureOperator, productionOperator, productionData, schemas, production, fixtureSemantic,
  conceptId, stateId, secondaryConceptId, secondaryStateId, similarityId, repo,
};
