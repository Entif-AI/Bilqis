import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { assertFramePage, assertFrameRequest } from "../../renderer/frames/frame-contract.mjs";
import { packingMetrics, visiblePosition } from "../../renderer/frames/frame-model.mjs";
import { FrameQueryController, renderFrameExample } from "../../renderer/frames/frame-explorer.mjs";
import { duplicateTestIds } from "../../renderer/foundation/test-hooks.mjs";

const pages = JSON.parse(readFileSync(new URL("../../fixtures/frame-inspections-v1.json", import.meta.url)));
const page = () => structuredClone(pages[1]);

test("four source-addressed atoms expand from one position with exact identities", () => {
  const current = assertFramePage(page());
  const example = current.examples[0];
  assert.deepEqual(packingMetrics([example]), {
    atoms: 4, positions: 1, ratio: 4, fastFraction: 1,
    partial: 0, extended: 0, atomic: 0, expansions: 0, passes: 0,
    sidecarBytes: 0, preparationMs: null,
  });
  const shown = visiblePosition(example.positions[0], 4);
  assert.deepEqual(shown.constituents, example.positions[0].constituents);
  assert.deepEqual(shown.constituents.map(x => [x.sourceOrder, x.role, x.semanticId, x.occurrenceIndex]), [
    [0, "subject", "fixture:entity:0", 0], [1, "relation", "fixture:entity:1", 0],
    [2, "object", "fixture:entity:2", 0], [3, "qualifier", "fixture:entity:3", 0],
  ]);
  const html = renderFrameExample(example, 4);
  for (const atom of shown.constituents) {
    assert.ok(html.includes(atom.atom));
    assert.ok(html.includes(atom.sourceRef));
  }
  assert.match(html, /<details/);
});

test("literal paths and reasons remain distinct and aggregate metrics reconcile", () => {
  const examples = page().examples.slice(0, 2);
  const metrics = packingMetrics(examples);
  assert.equal(metrics.atoms, 8);
  assert.equal(metrics.positions, 4);
  assert.equal(metrics.ratio, 2);
  assert.equal(metrics.fastFraction, 0.25);
  assert.deepEqual([metrics.partial, metrics.extended, metrics.atomic], [1, 1, 1]);
  assert.equal(metrics.expansions, 2);
  assert.equal(metrics.passes, 1);
  assert.equal(metrics.sidecarBytes, 96);
  const html = renderFrameExample(examples[1], 4);
  for (const position of examples[1].positions) {
    assert.ok(html.includes(position.path));
    assert.ok(html.includes(position.reason));
  }
});

test("causal lens hides future and unknown constituents, codec fields and references", () => {
  const example = page().examples[0];
  const html = renderFrameExample(example, 2);
  assert.match(html, /Future-illegal/);
  assert.ok(html.includes("alpha"));
  assert.ok(html.includes("beta"));
  for (const forbidden of ["gamma", "delta", "fixture:entity:2", "fixture:source:quad:3", "frame:quad/v1", "quad-occurrence", "codec_word"]) {
    assert.ok(!html.includes(forbidden), forbidden);
  }
  example.positions[0].visibleAt = null;
  example.positions[0].constituents[0].visibleAt = null;
  assert.ok(!renderFrameExample(example, 4).includes("alpha"));
  assert.match(renderFrameExample(example, 4), /Unknown/);
  example.positions[0].visibleAt = 4;
  example.positions[0].fields[0].visibleAt = null;
  assert.ok(!renderFrameExample(example, 4).includes("codec_word"));
});

test("missing detail, missing measured cost, zero denominator and incomplete totals stay unavailable", () => {
  const examples = page().examples;
  assert.equal(packingMetrics(examples).ratio, null);
  assert.equal(packingMetrics(examples).sidecarBytes, null);
  assert.equal(packingMetrics([examples[0]]).preparationMs, null);
  assert.match(renderFrameExample(examples[2], 0), /Unavailable/);
  assert.equal(packingMetrics([]).ratio, null);
});

test("historical compiler and manifest identity cannot be substituted", () => {
  const past = assertFramePage(structuredClone(pages[0]));
  const current = assertFramePage(page());
  assert.notEqual(past.examples[0].compiler.digest, current.examples[0].compiler.digest);
  assert.notEqual(past.examples[0].compiler.version, current.examples[0].compiler.version);
  const wrong = page();
  wrong.examples[0].generationManifest = past.operatorView.meta.run.generation_manifest_sha256;
  assert.throws(() => assertFramePage(wrong), /FRAME_INSPECTION_INVALID/);
});

test("bounded wire validation rejects malformed identities, counters and visibility", () => {
  for (const mutate of [
    p => { p.request.generation = 6; },
    p => { p.examples[0].positions[0].index = 1; },
    p => { p.examples[0].positions[0].constituents[0].sourceOrder = 1; },
    p => { p.examples[0].expansionCount = -1; },
    p => { p.examples[0].positions[0].visibleAt = "4"; },
    p => { p.examples[0].compiler.digest = "unknown"; },
    p => { p.examples[0].positions[0].fields[0].value = "x".repeat(513); },
    p => { p.state = "DENIED"; },
    p => { p.state = "MISSING"; p.examples = []; },
    p => { p.state = "EMPTY"; p.examples = []; p.operatorView = null; },
    p => { p.examples.push(p.examples[0]); },
  ]) {
    const invalid = page(); mutate(invalid);
    assert.throws(() => assertFramePage(invalid), /FRAME_INSPECTION_INVALID/);
  }
  assert.throws(() => assertFrameRequest({ ...page().request, path: "/tmp" }), /FRAME_INSPECTION_INVALID/);
});

test("empty frame collections still carry the exact requested context", () => {
  const empty = page(); empty.state = "EMPTY"; empty.examples = [];
  assert.equal(assertFramePage(empty).operatorView.meta.run.generation, 7);
});

test("expansion reconstructs source order when a receipt lists roles in a different order", () => {
  const example = page().examples[0];
  example.positions[0].constituents.reverse();
  const html = renderFrameExample(example, 4);
  assert.ok(html.indexOf("alpha") < html.indexOf("beta"));
  assert.ok(html.indexOf("gamma") < html.indexOf("delta"));
});

test("aggregate overflow stays unavailable instead of fabricating rounded totals", () => {
  const example = page().examples[0];
  example.sidecarBytes = Number.MAX_SAFE_INTEGER;
  example.preparationMs = Number.MAX_VALUE;
  const metrics = packingMetrics([example, example]);
  assert.equal(metrics.sidecarBytes, null);
  assert.equal(metrics.preparationMs, null);
});

test("receipt strings are escaped in text and attribute contexts", () => {
  const example = page().examples[0];
  example.positions[0].constituents[0].atom = '<img src=x onerror="alert(1)">';
  const html = renderFrameExample(example, 4);
  assert.ok(!html.includes("<img"));
  assert.ok(html.includes("&lt;img"));
});

test("frame detail markup exposes stable unique hooks with progressive receipt detail", () => {
  const example = page().examples[0];
  const html = renderFrameExample(example, 4);
  assert.deepEqual(duplicateTestIds(html), []);
  for (const id of ["model-frame-receipt-provenance", "model-frame-position-0", "model-frame-position-0-table-wrap"]) {
    assert.match(html, new RegExp(`data-test-id="${id}"`), id);
  }
  assert.match(html, /<details class="frame-disclosure"/);
  assert.match(html, /Canonical semantic ID/);
});

test("query epochs discard superseded and unmounted responses; errors clear details", async () => {
  const pending = []; const states = [];
  const controller = new FrameQueryController(request => new Promise(resolve => pending.push({ request, resolve })), state => states.push(state));
  const old = controller.load(pages[0].request);
  const current = controller.load(pages[1].request);
  pending[1].resolve(page()); await current;
  pending[0].resolve(structuredClone(pages[0])); await old;
  assert.equal(states.at(-1).page.request.generation, 7);
  const late = controller.load(pages[0].request);
  controller.dispose(); pending[2].resolve(pages[0]); await late;
  assert.equal(states.at(-1).state, "LOADING");
  const failing = new FrameQueryController(async () => pages[0], state => states.push(state));
  await failing.load(pages[1].request);
  assert.equal(states.at(-1).state, "ERROR");
  assert.equal(states.at(-1).page, null);
});
