import test from "node:test";
import assert from "node:assert/strict";

import {
  BANK_SCHEMA,
  CONCEPT_SCHEMA,
  HELD_SCHEMA,
  SIMILARITY_SCHEMA,
  STATE_SCHEMA,
  SUMMARY_SCHEMA,
  conceptRecordId,
  lensEdges,
  loadAbiRow,
  loadAtlasOverview,
  loadSemanticIdentity,
  renderAtlasMarkup,
  stateRecordId,
} from "../../renderer/atlas/semantic-atlas.mjs";
import { duplicateTestIds } from "../../renderer/foundation/test-hooks.mjs";

const RELEASE = "1".repeat(64);
const ROOT_ID = "https://github.com/Entif-AI/Bilqis-MLX/id/root/NI-LEXICON-CURRICULUM/LEXROOT-007a2c39cfe74c";
const SENSE_1 = ROOT_ID.replace("/id/root/", "/id/sense/") + "/STEM%201/BSC";
const SENSE_2 = ROOT_ID.replace("/id/root/", "/id/sense/") + "/STEM%202/BSC";
const context = Object.freeze({
  runId: "run-semantic",
  generation: 7,
  mode: "LIVE",
  semanticRelease: RELEASE,
});

function requestBase(overrides = {}) {
  return {
    schema: "bilqis.bamf.control-plane.query/v1",
    family: "semantic",
    mode: "current",
    run_id: null,
    record_id: null,
    schema_version: null,
    generation: null,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor: null,
    limit: 32,
    ...overrides,
  };
}

function page(request, records = [], links = [], total = records.length + links.length) {
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

function concept(semanticId = SENSE_1) {
  return {
    schema_version: CONCEPT_SCHEMA,
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

function generationState(admission = "ACTIVE") {
  return {
    schema_version: STATE_SCHEMA,
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

function similarity() {
  return {
    schema_version: SIMILARITY_SCHEMA,
    source_semantic_id: SENSE_1,
    target_semantic_id: SENSE_2,
    basis_ref: "embedding:fixture",
    similarity: { state: "PRESENT", origin: "DERIVED", value: 0.97, units: "similarity" },
    canonical_equivalence: false,
  };
}

test("canonical root and sense record identities stay exact and release-scoped", () => {
  const root = conceptRecordId(RELEASE, ROOT_ID);
  const sense = conceptRecordId(RELEASE, SENSE_1);
  assert.notEqual(root, sense);
  assert.ok(root.endsWith(ROOT_ID));
  assert.ok(sense.endsWith(SENSE_1));
});

test("canonical lens never imports learned similarity as a graph edge", () => {
  const selection = { concept: concept(), state: generationState(), similarities: [similarity()] };
  const canonical = lensEdges(selection, "canonical");
  const learned = lensEdges(selection, "learned");
  assert.deepEqual(canonical, [{
    kind: "canonical", source: SENSE_1, target: ROOT_ID, relation: "skos:broader",
  }]);
  assert.equal(learned[0].target, SENSE_2);
  assert.equal(learned[0].canonicalEquivalence, false);

  const canonicalMarkup = renderAtlasMarkup({ status: "ready", overview: null,
    selection, lens: "canonical" });
  const learnedMarkup = renderAtlasMarkup({ status: "ready", overview: null,
    selection, lens: "learned" });
  assert.ok(canonicalMarkup.includes("skos:broader"));
  assert.equal(canonicalMarkup.includes("0.97"), false);
  assert.ok(learnedMarkup.includes("0.97"));
  assert.ok(learnedMarkup.includes("canonical equivalence false"));
  assert.ok(learnedMarkup.includes('data-authority="derived"'));
  assert.throws(
    () => lensEdges({ ...selection, similarities: [{ ...similarity(), canonical_equivalence: true }] }, "learned"),
    /MISSION_CONTROL_SEMANTIC_QUERY_INVALID:SIMILARITY_CANONICAL_EQUIVALENCE/,
  );
});

test("identity inspector renders source revision and non-color generation-state cues", () => {
  const activeMarkup = renderAtlasMarkup({
    status: "ready",
    overview: null,
    selection: { concept: concept(), state: generationState("ACTIVE"), similarities: [] },
    lens: "canonical",
  });
  const maskedMarkup = renderAtlasMarkup({
    status: "ready",
    overview: null,
    selection: { concept: concept(), state: generationState("RESERVED_MASKED"), similarities: [] },
    lens: "canonical",
  });
  assert.ok(activeMarkup.includes(RELEASE));
  assert.ok(activeMarkup.includes("state-active"));
  assert.ok(activeMarkup.includes(">ACTIVE<"));
  assert.ok(maskedMarkup.includes("state-reserved_masked"));
  assert.ok(maskedMarkup.includes(">RESERVED_MASKED<"));
});

test("held mapping renders the exact source reason without inventing an ABI address", () => {
  const held = {
    schema_version: HELD_SCHEMA,
    semantic_id: "semantic:held:ambiguous-1",
    domain: "mapping",
    table: "lexicon_mapping",
    key: "ambiguous-1",
    reason_code: "AMBIGUOUS_MAPPING",
    teaching_reason: "HOLD_FOR_REVIEW",
  };
  const markup = renderAtlasMarkup({
    status: "ready", overview: null,
    selection: { concept: null, state: null, held, similarities: [] },
    lens: "canonical",
  });
  assert.ok(markup.includes("AMBIGUOUS_MAPPING"));
  assert.ok(markup.includes("HOLD_FOR_REVIEW"));
  assert.equal(markup.includes("ABI address"), false);
});

test("historical ABI lookup requests the selected generation rather than current state", async () => {
  const historical = { ...context, mode: "HISTORICAL", generation: 6 };
  const seen = [];
  const api = {
    async query(request) {
      seen.push(request);
      if (request.record_id === stateRecordId(historical, 0, 1)) {
        return page(request, [generationState("RESERVED_MASKED")]);
      }
      if (request.record_id === conceptRecordId(RELEASE, SENSE_1)) {
        return page(request, [concept()]);
      }
      if (request.family === "reference") return page(request);
      return page(request);
    },
  };
  const result = await loadAbiRow(api, historical, 0, 1);
  assert.equal(result.state.admission_state, "RESERVED_MASKED");
  assert.equal(seen[0].mode, "historical");
  assert.equal(seen[0].run_id, "run-semantic");
  assert.equal(seen[0].generation, 6);
  const sourceRequest = seen.find((request) => request.record_id?.startsWith("semantic-concept:"));
  assert.equal(sourceRequest.mode, "current");
  assert.equal(sourceRequest.run_id, null);
});

test("exact semantic search binds source identity to generation-local ABI state", async () => {
  const seen = [];
  const api = {
    async query(request) {
      seen.push(request);
      if (request.record_id === conceptRecordId(RELEASE, SENSE_1)) {
        return page(request, [concept()]);
      }
      if (request.record_id === stateRecordId(context, 0, 1)) {
        return page(request, [generationState()]);
      }
      if (request.family === "reference") {
        return page(request, [], [{
          relation: "LEARNED_SIMILARITY_SOURCE",
          source_record_id: "sim:one",
          target_ref: SENSE_1,
          target_record_id: "sim:one",
        }]);
      }
      if (request.record_id === "sim:one") return page(request, [similarity()]);
      return page(request);
    },
  };
  const result = await loadSemanticIdentity(api, context, SENSE_1);
  assert.equal(result.concept.semantic_id, SENSE_1);
  assert.equal(result.state.semantic_id, SENSE_1);
  assert.equal(result.state.abi_row, 1);
  assert.equal(result.similarities[0].target_semantic_id, SENSE_2);
  assert.equal(seen[0].run_id, null);
  assert.equal(seen[1].run_id, "run-semantic");
});

test("overview aggregates bank state while held mappings remain a separate source pool", async () => {
  const api = {
    async query(request) {
      if (request.schema_version === SUMMARY_SCHEMA) return page(request, [{
        schema_version: SUMMARY_SCHEMA,
        active_concepts: { value: 2 }, source_eligible: { value: 3 }, source_held: { value: 1 },
      }]);
      if (request.schema_version === BANK_SCHEMA) return page(request, [{
        schema_version: BANK_SCHEMA, bank: 0, row_capacity: 8192,
        allocated_rows: 3, active_rows: 2, masked_rows: 1,
        newly_admitted_rows: 1, recently_exercised_rows: 1,
        requalification_affected_rows: 0,
      }]);
      if (request.schema_version === HELD_SCHEMA) return page(request, [{
        schema_version: HELD_SCHEMA, key: "ambiguous-1", reason_code: "AMBIGUOUS_MAPPING",
      }], [], 1);
      if (request.schema_version === SIMILARITY_SCHEMA) return page(request, [similarity()]);
      throw new Error("unexpected query");
    },
  };
  const overview = await loadAtlasOverview(api, context);
  const markup = renderAtlasMarkup({ status: "ready", overview, lens: "canonical" });
  assert.ok(markup.includes(">2</strong>"));
  assert.ok(markup.includes(">1</td>"));
  assert.ok(markup.includes("AMBIGUOUS_MAPPING"));
  assert.ok(markup.includes("Held mappings"));
});

test("Atlas markup exposes stable unique test hooks and explicit no-projection state", () => {
  const markup = renderAtlasMarkup({
    status: "ready",
    overview: null,
    selection: { concept: concept(), state: null, similarities: [] },
    lens: "canonical",
  });
  assert.deepEqual(duplicateTestIds(markup), []);
  for (const id of [
    "atlas-view", "atlas-lens-canonical", "atlas-lens-learned",
    "atlas-search-form", "atlas-abi-form", "atlas-semantic-dossier",
    "atlas-request-no-projection",
  ]) assert.ok(markup.includes(`data-test-id="${id}"`), id);
  assert.ok(markup.includes("No exact generation projection"));
});
