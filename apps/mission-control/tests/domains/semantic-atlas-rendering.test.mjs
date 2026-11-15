import test from "node:test";
import assert from "node:assert/strict";

import {
  HELD_SCHEMA, conceptRecordId, lensEdges, renderAtlasMarkup,
} from "../../renderer/atlas/semantic-atlas.mjs";
import { ATLAS_TABS } from "../../renderer/atlas/atlas-view-parts.mjs";
import { duplicateTestIds } from "../../renderer/foundation/test-hooks.mjs";
import {
  RELEASE, ROOT_ID, SENSE_1, SENSE_2, MATERIALIZED_AT, OBSERVED_AT, CONCEPT_MATERIALIZED_AT,
  context, concept, generationState, similarity,
} from "./semantic-atlas-test-support.mjs";

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
  assert.ok(learnedMarkup.includes("distinct source identities"));
  assert.ok(learnedMarkup.includes('data-authority="derived"'));
  assert.ok(learnedMarkup.includes("Derived similarity"));
  assert.ok(learnedMarkup.includes("Source truth"));
  assert.ok(learnedMarkup.includes("Derived generation state"));
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
  assert.ok(activeMarkup.includes(`data-source-unix-seconds="${CONCEPT_MATERIALIZED_AT}"`));
  assert.ok(activeMarkup.includes(`data-source-unix-seconds="${MATERIALIZED_AT}"`));
  assert.ok(activeMarkup.includes(`data-source-unix-seconds="${OBSERVED_AT}"`));
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

test("historical Atlas posture names the exact selected generation", () => {
  const markup = renderAtlasMarkup({
    status: "ready",
    overview: null,
    selection: null,
    context: { ...context, mode: "HISTORICAL", generation: 6 },
  });
  assert.ok(markup.includes("Historical generation 6"));
  assert.ok(markup.includes('data-test-id="atlas-help-posture-trigger"'));
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
    "atlas-request-no-projection", "atlas-tabs", "atlas-tab-lookup", "atlas-tab-abi",
    "atlas-tab-dossier", "atlas-help-overview-trigger", "atlas-help-lookup-trigger",
    "atlas-help-abi-trigger", "atlas-help-dossier-trigger", "atlas-help-relations-trigger",
  ]) assert.ok(markup.includes(`data-test-id="${id}"`), id);
  assert.ok(markup.includes("Generation projection unavailable"));
  assert.equal((markup.match(/role="tablist"/g) ?? []).length, 1);
  assert.equal((markup.match(/role="tab"/g) ?? []).length, ATLAS_TABS.length);
  assert.equal(ATLAS_TABS.length, 3);
  assert.ok(markup.includes(`data-source-unix-seconds="${CONCEPT_MATERIALIZED_AT}"`));
  assert.equal(/\bnever\b|does not|No exact generation projection/.test(markup), false);
});
