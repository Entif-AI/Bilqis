import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

import {
  createInteractionState,
  explicitHighlightRefs,
  historicalContext,
  setCompareSide,
  stableObjectRef,
} from "../renderer/interactions/model.mjs";
import {
  OPERATOR_METADATA_KEY,
  addAnnotation,
  emptyOperatorMetadata,
  loadOperatorMetadata,
  saveOperatorMetadata,
  togglePin,
} from "../renderer/interactions/operator-metadata.mjs";
import {
  appUriToHash,
  buildAppUri,
  parseAppUri,
} from "../renderer/interactions/app-uri.mjs";
import { compareStableRefs } from "../renderer/interactions/compare.mjs";

const context = Object.freeze({
  runId: "fixture:prometheus-disposable",
  generation: 44239,
  fixture: true,
  mode: "LIVE",
  historicalPinned: false,
  generationManifest: "a".repeat(64),
  topologyId: "b".repeat(64),
  factoryRelease: "c".repeat(64),
  semanticRelease: "d".repeat(64),
  coverage: "COMPLETE",
  freshness: "FRESH",
});

test("time lens pins an exact historical generation and clears generation-dependent identities", () => {
  const historical = historicalContext(context, 44238);
  assert.equal(historical.generation, 44238);
  assert.equal(historical.mode, "HISTORICAL");
  assert.equal(historical.historicalPinned, true);
  assert.equal(historical.generationManifest, "UNKNOWN");
  assert.equal(historical.topologyId, "UNKNOWN");
  assert.equal(historical.coverage, "UNKNOWN");
  assert.throws(() => historicalContext(context, -1), /BAMF_GUI18_GENERATION_INVALID/);
});

test("current lens availability is an explicit renderer concern, not synthesized from history", () => {
  const renderer = fs.readFileSync(
    new URL("../renderer/renderer.mjs", import.meta.url),
    "utf8",
  );
  const bootstrap = fs.readFileSync(
    new URL("../renderer/foundation/bootstrap-controller.mjs", import.meta.url),
    "utf8",
  );
  assert.match(bootstrap, /snapshotSource === "service" && nextDefense\.id === "live"/);
  assert.match(renderer, /onCurrentLens:/);
  assert.match(renderer, /withDefensiveState\(\{ \.\.\.state, context: verifiedLiveContext \}, defense\)/);
});

test("stable refs preserve exact context and only explicit relations become highlight targets", () => {
  const ref = stableObjectRef({
    kind: "capability",
    id: "B.AND",
    details: { Debt: 2 },
    relations: [
      { kind: "capability", id: "B.NOT", relation: "prerequisite" },
      { kind: "episode", id: "episode-record:fixture:retained-44239", relation: "episode" },
    ],
  }, context);
  assert.deepEqual(explicitHighlightRefs(ref).map(({ kind, id, relation }) => [kind, id, relation]), [
    ["capability", "B.AND", "selected"],
    ["capability", "B.NOT", "prerequisite"],
    ["episode", "episode-record:fixture:retained-44239", "episode"],
  ]);
  assert.equal(ref.runId, "fixture:prometheus-disposable");
  assert.equal(ref.generation, 44239);
});

test("compare state records explicit left and right refs", () => {
  const left = stableObjectRef({ kind: "capability", id: "B.AND" }, context);
  const right = stableObjectRef({ kind: "capability", id: "B.NOT" }, context);
  const withLeft = setCompareSide(createInteractionState(), "left", left);
  const complete = setCompareSide(withLeft, "right", right);
  assert.equal(complete.panel, "compare");
  assert.equal(complete.compare.left.id, "B.AND");
  assert.equal(complete.compare.right.id, "B.NOT");
});

test("operator pins and annotations round-trip without becoming authority", () => {
  const memory = new Map();
  const storage = {
    getItem(key) { return memory.get(key) ?? null; },
    setItem(key, value) { memory.set(key, value); },
  };
  const target = stableObjectRef({ kind: "capability", id: "B.AND" }, context);
  let metadata = togglePin(emptyOperatorMetadata(), target);
  metadata = addAnnotation(metadata, target, "Investigate regression source.", { now: 1700000000000 });
  assert.equal(saveOperatorMetadata(storage, metadata), true);
  const loaded = loadOperatorMetadata(storage);
  assert.equal(loaded.pins.length, 1);
  assert.equal(loaded.pins[0].id, "B.AND");
  assert.deepEqual(loaded.annotations[0], {
    annotationId: "annotation:1700000000000:1",
    target: {
      kind: "capability",
      id: "B.AND",
      label: "B.AND",
      runId: "fixture:prometheus-disposable",
      generation: 44239,
      fixture: true,
    },
    author: "LOCAL_OPERATOR",
    createdAt: 1700000000000,
    scope: "OBJECT",
    authority: "OPERATOR_NOTE_NON_AUTHORITATIVE",
    body: "Investigate regression source.",
  });
  memory.set(OPERATOR_METADATA_KEY, '{"schema":"wrong"}');
  assert.equal(loadOperatorMetadata(storage).pins.length, 0);
});

test("app URI round-trips exact run generation object and trusted internal route", () => {
  const target = stableObjectRef({ kind: "capability", id: "B.AND" }, context);
  const uri = buildAppUri(target);
  assert.equal(
    uri,
    "bilqis://run/fixture%3Aprometheus-disposable/generation/44239/capability/B.AND?fixture=1",
  );
  assert.deepEqual(parseAppUri(uri), {
    view: "capability",
    selected: { kind: "capability", id: "B.AND" },
    context: {
      runId: "fixture:prometheus-disposable",
      generation: 44239,
      mode: "HISTORICAL",
      fixture: true,
      historicalPinned: true,
    },
  });
  assert.equal(
    appUriToHash(uri),
    "#/view/capability?kind=capability&id=B.AND&run=fixture%3Aprometheus-disposable&generation=44239&mode=HISTORICAL&fixture=true",
  );
  assert.equal(parseAppUri("https://example.test/run/x/generation/1/capability/B.AND"), null);
});

test("generation compare exposes literal incompatibility and candidate compare keeps challenger separate", () => {
  const leftGeneration = {
    kind: "generation", id: "generation:44238", runId: "fixture-run", generation: 44238,
  };
  const rightGeneration = {
    kind: "generation", id: "generation:44241", runId: "fixture-run", generation: 44241,
  };
  const generation = compareStableRefs(leftGeneration, rightGeneration);
  assert.equal(generation.state, "PRESENT");
  assert.equal(generation.rows.some((item) =>
    item.label === "Resource profile" && item.state === "UNAVAILABLE"), true);

  const leftCandidate = {
    kind: "candidate", id: "candidate:fixture:retained-44239",
    runId: "fixture-run", generation: 44238,
  };
  const rightCandidate = {
    kind: "candidate", id: "candidate:fixture:interference-reject",
    runId: "fixture-run", generation: 44238,
  };
  const candidate = compareStableRefs(leftCandidate, rightCandidate);
  assert.deepEqual(
    candidate.rows.find((item) => item.label === "Target committed"),
    { label: "Target committed", left: "12/12", right: "8/12", state: "DIFFERENT", reason: null },
  );
  assert.deepEqual(
    candidate.rows.find((item) => item.label === "Protected committed"),
    { label: "Protected committed", left: "48/48", right: "48/48", state: "SAME", reason: null },
  );
});

test("mixed object classes stay explicitly incompatible", () => {
  const compared = compareStableRefs(
    { kind: "capability", id: "B.AND", runId: "r", generation: 1 },
    { kind: "strategy", id: "strategy:fixture:challenger-balanced", runId: "r", generation: 1 },
  );
  assert.equal(compared.state, "INCOMPATIBLE");
  assert.deepEqual(compared.rows[0], {
    label: "Object class",
    left: "capability",
    right: "strategy",
    state: "INCOMPATIBLE",
    reason: null,
  });
});

test("strategy compare presents the two literal metric sets side by side", () => {
  const compared = compareStableRefs(
    {
      kind: "strategy",
      id: "strategy:fixture:incumbent-deep-contrast",
      runId: "fixture-run",
      generation: 44239,
    },
    {
      kind: "strategy",
      id: "strategy:fixture:challenger-balanced",
      runId: "fixture-run",
      generation: 44239,
    },
  );
  assert.deepEqual(
    compared.rows.find((item) => item.label === "Observations"),
    { label: "Observations", left: "14", right: "11", state: "DIFFERENT", reason: null },
  );
  assert.deepEqual(
    compared.rows.find((item) => item.label === "Interference"),
    { label: "Interference", left: "2", right: "4", state: "DIFFERENT", reason: null },
  );
  assert.match(compared.note, /No strategy ranking is synthesized/);
});
