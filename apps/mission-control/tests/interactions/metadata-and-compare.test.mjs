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

test("inspector evidence posture keeps launch-owned fixture custody distinct from production history", () => {
  assert.equal(
    inspectorEvidenceLabelKey({ context }, { historical: false }),
    "shell.inspector.fixture",
  );
  assert.equal(
    inspectorEvidenceLabelKey(
      { context: { ...context, mode: "HISTORICAL", historicalPinned: true } },
      { historical: false },
    ),
    "shell.inspector.fixture",
  );
  assert.equal(
    inspectorEvidenceLabelKey(
      { context: { ...context, fixture: false } },
      { historical: false },
    ),
    "shell.inspector.currentEvidence",
  );
  assert.equal(
    inspectorEvidenceLabelKey(
      { context: { ...context, fixture: false, mode: "HISTORICAL", historicalPinned: true } },
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
  const fixture = fs.readFileSync(new URL("../browser/corrections-check.cjs", import.meta.url), "utf8");
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
  const journey = fs.readFileSync(new URL("../browser/corrections-journey.mjs", import.meta.url), "utf8");
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
