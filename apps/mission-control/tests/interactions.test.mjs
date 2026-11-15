import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

import {
  createInteractionState,
  explicitHighlightRefs,
  historicalContext,
  setCompareSide,
  stableObjectRef,
  withHistoricalLens,
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
import { renderInvestigationMarkup } from "../renderer/interactions/view.mjs";
import { inspectorEvidenceLabelKey } from "../renderer/foundation/renderer-ui.mjs";

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
  const state = {
    context,
    selected: { kind: "capability", id: "B.AND" },
    inspectorOpen: true,
    mutationAvailable: true,
  };
  const next = withHistoricalLens(state, 44238);
  assert.equal(next.selected, null);
  assert.equal(next.inspectorOpen, false);
  assert.equal(next.context.generation, 44238);
  assert.equal(next.mutationAvailable, false);
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

test("compare exposes exact context and refuses cross-run coercion", () => {
  const left = stableObjectRef({ kind: "capability", id: "B.AND", details: { Debt: 1 } }, context);
  const later = stableObjectRef(
    { kind: "capability", id: "B.AND", details: { Debt: 2 } },
    { ...context, generation: 44240 },
  );
  const sameRun = compareStableRefs(left, later);
  assert.deepEqual(
    sameRun.rows.slice(0, 2).map(({ key, left: before, right: after, state }) => ({ key, before, after, state })),
    [
      { key: "run", before: context.runId, after: context.runId, state: "SAME" },
      { key: "generation", before: "44239", after: "44240", state: "DIFFERENT" },
    ],
  );

  const otherRun = stableObjectRef(
    { kind: "capability", id: "B.AND", details: { Debt: 2 } },
    { ...context, runId: "other-run", generation: 44240 },
  );
  const crossRun = compareStableRefs(left, otherRun);
  assert.equal(crossRun.state, "INCOMPATIBLE");
  assert.match(crossRun.note, /Different runs/);
  assert.equal(crossRun.rows[0].key, "run");
  assert.equal(crossRun.rows[0].state, "DIFFERENT");
});

test("investigation composition keeps tools terse and deep links out of permanent shell chrome", () => {
  const currentRef = stableObjectRef({ kind: "capability", id: "B.AND" }, context);
  const markup = renderInvestigationMarkup({
    state: { context },
    interaction: createInteractionState(),
    metadata: emptyOperatorMetadata(),
    currentRef,
    comparison: compareStableRefs(null, null),
    currentAvailable: true,
  });
  assert.match(markup, /data-test-id="investigation-time-toggle"/);
  assert.match(markup, /data-test-id="investigation-open-compare"/);
  assert.match(markup, /data-test-id="investigation-open-pins"/);
  assert.match(markup, /data-test-id="investigation-open-notes"/);
  assert.doesNotMatch(markup, /bilqis:\/\//);
  assert.doesNotMatch(markup, /Exact app URI/);
});

test("note form exposes exact target context before save", () => {
  const currentRef = stableObjectRef({ kind: "capability", id: "B.AND" }, context);
  const markup = renderInvestigationMarkup({
    state: { context },
    interaction: { ...createInteractionState(), panel: "annotations" },
    metadata: emptyOperatorMetadata(),
    currentRef,
    comparison: compareStableRefs(null, null),
    currentAvailable: true,
  });
  assert.match(markup, /data-test-id="investigation-note-target-context"/);
  assert.match(markup, /capability · B\.AND · fixture:prometheus-disposable · generation 44239/);
});

test("compare markup states incompatibility explicitly without comparison cards", () => {
  const left = stableObjectRef({ kind: "capability", id: "B.AND" }, context);
  const right = stableObjectRef({ kind: "strategy", id: "strategy:fixture:challenger-balanced" }, context);
  const interaction = setCompareSide(setCompareSide(createInteractionState(), "left", left), "right", right);
  const markup = renderInvestigationMarkup({
    state: { context }, interaction, metadata: emptyOperatorMetadata(), currentRef: right,
    comparison: compareStableRefs(left, right), currentAvailable: true,
  });
  assert.match(markup, /data-test-id="investigation-compare-state"/);
  assert.match(markup, />Incompatible</);
  assert.match(markup, /data-test-id="investigation-compare-row-object-class"/);
  assert.doesNotMatch(markup, /<article/);
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
  const operation = stableObjectRef({ kind: "operation", id: "operation:fixture:1" }, context);
  assert.equal(
    buildAppUri(operation),
    "bilqis://run/fixture%3Aprometheus-disposable/generation/44239/operation/operation%3Afixture%3A1?fixture=1",
  );
  assert.equal(parseAppUri(buildAppUri(operation)).view, "operate");
});

test("inspector evidence posture follows the exact historical lens rather than stale live defense", () => {
  assert.equal(
    inspectorEvidenceLabelKey({ context }, { historical: false }),
    "shell.inspector.currentEvidence",
  );
  assert.equal(
    inspectorEvidenceLabelKey(
      { context: { ...context, mode: "HISTORICAL", historicalPinned: true } },
      { historical: false },
    ),
    "shell.inspector.historicalEvidence",
  );
  assert.equal(
    inspectorEvidenceLabelKey({ context }, { historical: false }, true),
    "shell.inspector.fixture",
  );
});

test("Corrections browser fixture carries the shared inspector anatomy", () => {
  const fixture = fs.readFileSync(new URL("./browser/corrections-check.cjs", import.meta.url), "utf8");
  for (const id of [
    "inspector-summary",
    "inspector-details",
    "inspector-deep-link-value",
    "copy-deep-link",
    "open-owner",
    "open-evidence",
  ]) {
    assert.match(fixture, new RegExp(`id=\\"${id}\\"`));
  }
  const journey = fs.readFileSync(new URL("./browser/corrections-journey.mjs", import.meta.url), "utf8");
  assert.match(journey, /fixture-inspector-summary/);
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
    { key: "target-committed", label: "Target committed", left: "12/12", right: "8/12", state: "DIFFERENT", reason: null },
  );
  assert.deepEqual(
    candidate.rows.find((item) => item.label === "Protected committed"),
    { key: "protected-committed", label: "Protected committed", left: "48/48", right: "48/48", state: "SAME", reason: null },
  );
});

test("mixed object classes stay explicitly incompatible", () => {
  const compared = compareStableRefs(
    { kind: "capability", id: "B.AND", runId: "r", generation: 1 },
    { kind: "strategy", id: "strategy:fixture:challenger-balanced", runId: "r", generation: 1 },
  );
  assert.equal(compared.state, "INCOMPATIBLE");
  assert.deepEqual(compared.rows.find((item) => item.key === "object-class"), {
    key: "object-class",
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
    { key: "observations", label: "Observations", left: "14", right: "11", state: "DIFFERENT", reason: null },
  );
  assert.deepEqual(
    compared.rows.find((item) => item.label === "Interference"),
    { key: "interference", label: "Interference", left: "2", right: "4", state: "DIFFERENT", reason: null },
  );
  assert.match(compared.note, /No strategy ranking is synthesized/);
});
