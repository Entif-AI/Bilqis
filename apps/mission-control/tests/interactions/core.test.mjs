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
} from "../../renderer/interactions/model.mjs";
import {
  OPERATOR_METADATA_KEY,
  addAnnotation,
  emptyOperatorMetadata,
  loadOperatorMetadata,
  saveOperatorMetadata,
  togglePin,
} from "../../renderer/interactions/operator-metadata.mjs";
import {
  appUriToHash,
  buildAppUri,
  parseAppUri,
} from "../../renderer/interactions/app-uri.mjs";
import { compareStableRefs } from "../../renderer/interactions/compare.mjs";
import { renderInvestigationMarkup } from "../../renderer/interactions/view.mjs";
import { inspectorEvidenceLabelKey } from "../../renderer/foundation/renderer-ui.mjs";

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
    new URL("../../renderer/renderer.mjs", import.meta.url),
    "utf8",
  );
  const bootstrap = fs.readFileSync(
    new URL("../../renderer/foundation/bootstrap-controller.mjs", import.meta.url),
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
