import {
  ATTNRES_FIXTURE,
  CCGQA_FIXTURE,
  CURRENT_NEURAL_SAMPLE,
  CURRENT_TOPOLOGY,
  HISTORICAL_NEURAL_SAMPLE,
  HISTORICAL_TOPOLOGY,
  REFINEMENT_RECEIPTS,
} from "./neural-fixture.mjs";

export function topologyFor(mode) {
  return mode === "historical" ? HISTORICAL_TOPOLOGY : CURRENT_TOPOLOGY;
}

export function neuralSampleFor(mode) {
  return mode === "historical" ? HISTORICAL_NEURAL_SAMPLE : CURRENT_NEURAL_SAMPLE;
}

export function topologyPath(topology) {
  if (topology.schema === "bilqis.mlx.model-topology/v1") {
    return Object.freeze([
      "input / learned position",
      topology.layers + " causal attention blocks",
      "typed output",
    ]);
  }
  return Object.freeze([
    "input / frame encoder",
    "CCGQA layers 1–4",
    "Block AttnRes group 1",
    "CCGQA layers 5–8",
    "Block AttnRes group 2",
    "CCGQA layers 9–12",
    "Block AttnRes group 3",
    "typed output / local refinement hooks",
  ]);
}

export function ccgqaEvidenceState(sample) {
  if (!sample) return "UNAVAILABLE";
  if (sample.maskInvalidViolations > 0 || sample.finite !== true) return "INVALID";
  return "PRESENT";
}

export function depthWeightRows() {
  return ATTNRES_FIXTURE.map((entry) => {
    const sum = entry.weights.reduce((value, weight) => value + weight, 0);
    return {
      ...entry,
      weightSum: Number(sum.toFixed(6)),
      pairs: entry.sourceOrder.map((source, index) => Object.freeze({
        source,
        weight: entry.weights[index],
      })),
    };
  });
}

export function refinementHistogram(receipts = REFINEMENT_RECEIPTS) {
  const bins = { 0: 0, 1: 0, 2: 0 };
  for (const receipt of receipts) bins[receipt.passes] += 1;
  return Object.freeze({
    none: bins[0],
    one: bins[1],
    multiple: bins[2],
    total: receipts.length,
  });
}

export function refinementCostSummary(receipts = REFINEMENT_RECEIPTS) {
  const active = receipts.filter((item) => item.passes > 0);
  const totalCost = active.reduce((sum, item) => sum + item.resourceCostMs, 0);
  const averageDensity = active.length
    ? active.reduce((sum, item) => sum + item.frameDensity, 0) / active.length
    : 0;
  return Object.freeze({
    activeFrames: active.length,
    totalCostMs: Number(totalCost.toFixed(3)),
    averageFrameDensity: Number(averageDensity.toFixed(3)),
  });
}

export function neuralFixture(mode = "current") {
  const historical = mode === "historical";
  return Object.freeze({
    mode,
    topology: topologyFor(mode),
    telemetry: neuralSampleFor(mode),
    path: topologyPath(topologyFor(mode)),
    ccgqa: historical ? null : CCGQA_FIXTURE,
    attnres: historical ? null : depthWeightRows(),
    refinementReceipts: historical ? null : REFINEMENT_RECEIPTS,
  });
}
