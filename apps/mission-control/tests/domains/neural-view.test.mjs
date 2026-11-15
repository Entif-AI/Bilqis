import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ATTNRES_FIXTURE,
  CCGQA_FIXTURE,
  CURRENT_TOPOLOGY,
  HISTORICAL_TOPOLOGY,
  INSTRUMENTATION_STATES,
  REFINEMENT_RECEIPTS,
} from "../../renderer/neural/neural-fixture.mjs";
import {
  ccgqaEvidenceState,
  depthWeightRows,
  neuralFixture,
  refinementCostSummary,
  refinementHistogram,
  topologyPath,
} from "../../renderer/neural/neural-model.mjs";
import { renderNeuralMarkup } from "../../renderer/neural/neural-view.mjs";
import { duplicateTestIds } from "../../renderer/foundation/test-hooks.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../../..");
const rendererRoot = path.resolve(here, "../../renderer");

test("current topology fixture matches exact BAMF v2 production geometry", () => {
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/runtime/topology_v2/spec.py"),
    "utf8",
  );
  const expected = {
    layers: 12,
    width: 768,
    ffnDimension: 3072,
    queryHeads: 16,
    kvHeads: 8,
    headDimension: 24,
    context: 1024,
    convolutionKernel: 3,
    depthGroups: 3,
  };
  assert.equal(CURRENT_TOPOLOGY.schema, "bilqis.mlx.model-topology/v2");
  assert.equal(CURRENT_TOPOLOGY.architectureId, "bamf-atlas-v2");
  for (const [field, value] of Object.entries(expected)) assert.equal(CURRENT_TOPOLOGY[field], value);
  for (const literal of [
    "layers: int = 12",
    "width: int = 768",
    "ffn_dimension: int = 3072",
    "query_heads: int = 16",
    "kv_heads: int = 8",
    "head_dimension: int = 24",
    "context: int = 1024",
    "convolution_kernel: int = 3",
    "depth_groups: int = 3",
  ]) assert.equal(source.includes(literal), true, literal);
  assert.deepEqual(topologyPath(CURRENT_TOPOLOGY), [
    "input / frame encoder",
    "CCGQA layers 1–4",
    "Block AttnRes group 1",
    "CCGQA layers 5–8",
    "Block AttnRes group 2",
    "CCGQA layers 9–12",
    "Block AttnRes group 3",
    "typed output / local refinement hooks",
  ]);
});

test("historical generation uses its own v1 topology contract and no v2 diagnostic synthesis", () => {
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/runtime/_model/model_topology.py"),
    "utf8",
  );
  assert.equal(HISTORICAL_TOPOLOGY.schema, "bilqis.mlx.model-topology/v1");
  assert.deepEqual(
    [
      HISTORICAL_TOPOLOGY.layers,
      HISTORICAL_TOPOLOGY.heads,
      HISTORICAL_TOPOLOGY.width,
      HISTORICAL_TOPOLOGY.ffnDimension,
      HISTORICAL_TOPOLOGY.context,
    ],
    [6, 24, 384, 1536, 96],
  );
  assert.equal(source.includes("CURRENT_DEFAULT_TOPOLOGY = ModelTopologySpec("), true);
  assert.equal(source.includes("layers=6, heads=24, width=384, ffn_dimension=1536, context=96"), true);
  const fixture = neuralFixture("historical");
  assert.equal(fixture.ccgqa, null);
  assert.equal(fixture.attnres, null);
  assert.equal(fixture.refinementReceipts, null);
});

test("CCGQA fixture exposes literal utilization mask sequence cache and finite metrics", () => {
  const sample = CCGQA_FIXTURE[0];
  for (const field of [
    "qUtilization",
    "kUtilization",
    "vUtilization",
    "channelUtilization",
    "entropyMean",
    "entropyP95",
    "maskInvalidViolations",
    "activeSequenceLength",
    "activeFrameLength",
    "cacheState",
    "cacheUsage",
    "finite",
  ]) assert.notEqual(sample[field], undefined, field);
  assert.equal(ccgqaEvidenceState(sample), "PRESENT");
  assert.equal(sample.contract, "bilqis_mlx.runtime._model.backbone.atlas_attention.ccgqa");
});

test("mask-invalid violation is invalid evidence, not a normal warning", () => {
  const invalid = CCGQA_FIXTURE.find((sample) => sample.maskInvalidViolations > 0);
  assert.ok(invalid);
  assert.equal(ccgqaEvidenceState(invalid), "INVALID");
  const markup = renderNeuralMarkup("current");
  assert.match(markup, /data-evidence-state="invalid"/);
  assert.match(markup, /Mask-invalid violations: 2/);
  assert.match(markup, /data-neural-state="invalid"/);
});

test("neural workspace uses stable unique hooks and mechanism-first hierarchy", () => {
  const markup = renderNeuralMarkup("current");
  assert.deepEqual(duplicateTestIds(markup), []);
  for (const id of [
    "model-neural-workspace", "model-neural-fixture-posture", "model-neural-topology-runtime",
    "model-neural-ccgqa", "model-neural-attnres", "model-neural-refinement", "model-neural-instrumentation",
  ]) assert.match(markup, new RegExp(`data-test-id="${id}"`), id);
  assert.ok(markup.indexOf('data-test-id="model-neural-topology-runtime"') < markup.indexOf('data-test-id="model-neural-ccgqa"'));
  assert.ok(markup.indexOf('data-test-id="model-neural-ccgqa"') < markup.indexOf('data-test-id="model-neural-refinement"'));
});

test("historical neural fixture keeps unsupported instrumentation explicitly unavailable", () => {
  const markup = renderNeuralMarkup("historical");
  for (const id of ["ccgqa", "attnres", "refinement"]) {
    assert.match(markup, new RegExp(`data-test-id="model-neural-${id}-unavailable"`));
  }
  assert.doesNotMatch(markup, /0\.0%/);
});

test("AttnRes display uses only directly recorded alpha source order and normalized weights", () => {
  const depthSource = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/runtime/_depth/depth_contracts.py"),
    "utf8",
  );
  const selectionSource = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/runtime/_depth/depth_selection.py"),
    "utf8",
  );
  assert.equal(depthSource.includes('SOURCE_ORDER = ("h0", "g1", "g2", "g3")'), true);
  assert.equal(selectionSource.includes("class DepthSelectionDiagnostics:"), true);
  assert.equal(selectionSource.includes("alpha: mx.array"), true);
  for (const row of depthWeightRows()) {
    assert.equal(row.weightSum, 1);
    assert.deepEqual(row.sourceOrder, ATTNRES_FIXTURE[row.boundaryGroup - 1].sourceOrder);
  }
});

test("local-refinement histogram reconciles exactly with frame and episode receipts", () => {
  const histogram = refinementHistogram();
  assert.equal(histogram.none + histogram.one + histogram.multiple, REFINEMENT_RECEIPTS.length);
  assert.deepEqual(REFINEMENT_RECEIPTS.map((row) => row.passes), [0, 1, 2, 1, 0]);
  for (const receipt of REFINEMENT_RECEIPTS) {
    assert.equal(receipt.frameId.startsWith("frame:"), true);
    assert.equal(receipt.episodeReceipt.startsWith("episode:"), true);
    assert.equal(receipt.selectionSchema, "bilqis.mlx.refinement-selection/v1");
  }
  assert.deepEqual(refinementCostSummary(), {
    activeFrames: 3,
    totalCostMs: 7.8,
    averageFrameDensity: 0.577,
  });
});

test("missing instrumentation is explicit unavailable or partial, never a synthetic zero", () => {
  const missing = INSTRUMENTATION_STATES.filter((item) => item.state !== "PRESENT");
  assert.equal(missing.length >= 2, true);
  for (const item of missing) {
    assert.equal(["UNAVAILABLE", "PARTIAL"].includes(item.state), true);
    assert.equal("value" in item, false);
  }
});

test("neural UI avoids anthropomorphic activation labels", () => {
  const source = ["neural/neural-view.mjs", "neural/neural-model.mjs", "neural/neural-fixture.mjs"]
    .map((name) => fs.readFileSync(path.join(rendererRoot, name), "utf8"))
    .join("\n")
    .toLowerCase();
  for (const forbidden of ["thought", "rationale", "natural-language reasoning"]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
});
