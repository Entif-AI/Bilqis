import test from "node:test";
import assert from "node:assert/strict";

import {
  BANK_SCHEMA, HELD_SCHEMA, SIMILARITY_SCHEMA, SUMMARY_SCHEMA,
  conceptRecordId, loadAbiRow, loadAtlasOverview, loadSemanticIdentity, renderAtlasMarkup, stateRecordId,
} from "../../renderer/atlas/semantic-atlas.mjs";
import {
  ATLAS_FIXTURE_IDENTITY, createAtlasFixtureApi,
} from "../../renderer/atlas/atlas-fixture.mjs";
import {
  RELEASE, SENSE_1, SENSE_2, SUMMARY_MATERIALIZED_AT, OBSERVED_AT,
  context, page, concept, generationState, similarity,
} from "./semantic-atlas-test-support.mjs";

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

test("historical semantic lookup resolves through the exact generation identity link", async () => {
  const historical = {
    ...context, mode: "HISTORICAL", generation: 6, semanticRelease: "UNKNOWN",
  };
  const stateId = stateRecordId(historical, 0, 1);
  const conceptId = conceptRecordId(RELEASE, SENSE_1);
  const seen = [];
  const api = {
    async query(request) {
      seen.push(request);
      if (request.family === "reference" && request.mode === "historical") {
        return page(request, [], [{
          relation: "SEMANTIC_IDENTITY",
          source_record_id: stateId,
          target_ref: SENSE_1,
          target_record_id: conceptId,
        }]);
      }
      if (request.record_id === stateId) return page(request, [generationState("RESERVED_MASKED")]);
      if (request.record_id === conceptId) return page(request, [concept()]);
      return page(request);
    },
  };
  const result = await loadSemanticIdentity(api, historical, SENSE_1);
  assert.equal(result.concept.semantic_id, SENSE_1);
  assert.equal(result.state.admission_state, "RESERVED_MASKED");
  const reference = seen.find((request) => request.family === "reference");
  assert.equal(reference.mode, "historical");
  assert.equal(reference.run_id, "run-semantic");
  assert.equal(reference.generation, 6);
  assert.equal(seen.some((request) => request.record_id?.includes("UNKNOWN")), false);
});

test("fixture Atlas uses explicit route-local semantic records", async () => {
  const api = createAtlasFixtureApi();
  const fixtureContext = {
    runId: ATLAS_FIXTURE_IDENTITY.runId,
    generation: ATLAS_FIXTURE_IDENTITY.generation,
    semanticRelease: ATLAS_FIXTURE_IDENTITY.semanticRelease,
    mode: "LIVE",
    fixture: true,
  };
  const [overview, selection] = await Promise.all([
    loadAtlasOverview(api, fixtureContext),
    loadSemanticIdentity(api, fixtureContext, ATLAS_FIXTURE_IDENTITY.semanticId),
  ]);
  const markup = renderAtlasMarkup({ status: "ready", overview, selection, context: fixtureContext });
  assert.ok(markup.includes(ATLAS_FIXTURE_IDENTITY.semanticId));
  assert.ok(markup.includes("REFERENCE FIXTURES"));
  assert.ok(markup.includes("Generation 7"));
});

test("fixture Atlas returns no generation data for an unsupported historical generation", async () => {
  const api = createAtlasFixtureApi();
  const historical = {
    runId: ATLAS_FIXTURE_IDENTITY.runId,
    generation: 6,
    semanticRelease: "UNKNOWN",
    mode: "HISTORICAL",
    fixture: true,
  };
  const overview = await loadAtlasOverview(api, historical);
  assert.equal(overview.summary.records.length, 0);
  assert.equal(overview.banks.records.length, 0);
  const selection = await loadSemanticIdentity(api, historical, ATLAS_FIXTURE_IDENTITY.semanticId);
  assert.equal(selection.concept, null);
  assert.equal(selection.state, null);
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

test("held semantic lookup refuses a held record from another semantic release", async () => {
  const foreignId = "held:foreign";
  const currentId = "held:current";
  const api = {
    async query(request) {
      if (request.record_id === conceptRecordId(RELEASE, SENSE_1)) return page(request);
      if (request.family === "reference") return page(request, [], [
        { relation: "HELD_SEMANTIC_IDENTITY", source_record_id: foreignId,
          target_ref: SENSE_1, target_record_id: foreignId },
        { relation: "HELD_SEMANTIC_IDENTITY", source_record_id: currentId,
          target_ref: SENSE_1, target_record_id: currentId },
      ]);
      if (request.record_id === foreignId) return page(request, [{
        schema_version: HELD_SCHEMA, atlas_release_sha256: "2".repeat(64),
        key: "foreign", reason_code: "FOREIGN_RELEASE",
      }]);
      if (request.record_id === currentId) return page(request, [{
        schema_version: HELD_SCHEMA, atlas_release_sha256: RELEASE,
        key: "current", reason_code: "CURRENT_RELEASE",
      }]);
      return page(request);
    },
  };
  const result = await loadSemanticIdentity(api, context, SENSE_1);
  assert.equal(result.held.key, "current");
  assert.equal(result.held.reason_code, "CURRENT_RELEASE");
});

test("overview aggregates bank state while held mappings remain a separate source pool", async () => {
  const api = {
    async query(request) {
      if (request.schema_version === SUMMARY_SCHEMA) return page(request, [{
        schema_version: SUMMARY_SCHEMA,
        meta: { materialized_at: SUMMARY_MATERIALIZED_AT, observed_at: OBSERVED_AT, authority: "DERIVED" },
        atlas_release_sha256: RELEASE,
        active_concepts: { value: 2 }, source_eligible: { value: 3 }, source_held: { value: 1 },
      }]);
      if (request.schema_version === BANK_SCHEMA) return page(request, [{
        schema_version: BANK_SCHEMA, bank: 0, row_capacity: 8192,
        allocated_rows: 3, active_rows: 2, masked_rows: 1,
        newly_admitted_rows: 1, recently_exercised_rows: 1,
        requalification_affected_rows: 0,
      }]);
      if (request.schema_version === HELD_SCHEMA) return page(request, [
        { schema_version: HELD_SCHEMA, atlas_release_sha256: "2".repeat(64),
          key: "foreign-release", reason_code: "FOREIGN_RELEASE" },
        { schema_version: HELD_SCHEMA, atlas_release_sha256: RELEASE,
          key: "ambiguous-1", reason_code: "AMBIGUOUS_MAPPING" },
      ], [], 2);
      if (request.schema_version === SIMILARITY_SCHEMA) return page(request, [similarity()]);
      throw new Error("unexpected query");
    },
  };
  const overview = await loadAtlasOverview(api, context);
  const markup = renderAtlasMarkup({ status: "ready", overview, lens: "canonical" });
  assert.ok(markup.includes(">2</strong>"));
  assert.ok(markup.includes(">1</td>"));
  assert.ok(markup.includes("AMBIGUOUS_MAPPING"));
  assert.equal(markup.includes("FOREIGN_RELEASE"), false);
  assert.ok(markup.includes("Held mappings"));
  assert.ok(markup.includes(`data-source-unix-seconds="${SUMMARY_MATERIALIZED_AT}"`));
});
