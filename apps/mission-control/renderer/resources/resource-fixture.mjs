const GiB = 1024 ** 3;

function metric(value, units, semantic = "MEASURED", origin = "MEASURED") {
  return Object.freeze({ state: "PRESENT", value, units, semantic, origin });
}

function unavailable(units = null) {
  return Object.freeze({ state: "UNAVAILABLE", value: null, units, semantic: "UNAVAILABLE", origin: null });
}

const CURRENT = Object.freeze({
  provenance: "FIXTURE",
  generation: 44239,
  window: "fixture-window:44239:10m",
  aggregate: Object.freeze({
    unifiedMemoryUsed: metric(48 * GiB, "bytes"),
    unifiedMemoryBudget: metric(96 * GiB, "bytes", "CONFIGURED_LIMIT", "SOURCE_AUTHORITATIVE"),
    forecastMemoryPeak: metric(58 * GiB, "bytes", "ESTIMATE", "INFERRED"),
    mlxAllocatedMemory: metric(34 * GiB, "bytes"),
    mlxCacheMemory: metric(4 * GiB, "bytes"),
    cpuUtilization: metric(61.4, "percent"),
    preparationWorkers: metric(6, "workers"),
    diskFree: metric(312 * GiB, "bytes"),
    diskReserve: metric(200 * GiB, "bytes", "CONFIGURED_LIMIT", "SOURCE_AUTHORITATIVE"),
    candidateSnapshotFootprint: metric(4 * GiB, "bytes"),
    acceptedStepsHour: metric(420, "steps/hour", "DERIVED", "DERIVED"),
    sequenceDensity: metric(0.73, "fraction"),
    frameDensity: metric(0.61, "fraction"),
    batchSize: metric(12, "examples"),
    actualLengthP50: metric(384, "positions"),
    actualLengthP95: metric(704, "positions"),
    actualLengthMax: metric(768, "positions"),
    preparationCompileMs: metric(418, "ms"),
    mlxWallMs: metric(1642, "ms"),
    monetaryCost: unavailable("USD"),
  }),
  memoryDecomposition: Object.freeze([
    Object.freeze({ id: "model-parameters", label: "Model parameters", value: 3 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "optimizer-state", label: "Optimizer moments/state", value: 8 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "gradients", label: "Gradients", value: 3 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "engram", label: "Engram / motif memory", value: 7 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "activations", label: "Active batch / activations", value: 10 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "candidate-snapshot", label: "Candidate snapshot / staging", value: 4 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "caches", label: "Caches", value: 4 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "frame-sidecars", label: "Frame compiler / sidecars", value: 1 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "other", label: "Other explicitly measured", value: null, state: "UNAVAILABLE" }),
  ]),
  timeline: Object.freeze([
    Object.freeze({
      id: "resource:fixture:44239:0001", observedAt: 1_799_000_100,
      unifiedMemoryUsed: 42 * GiB, mlxAllocated: 29 * GiB, batchSize: 8,
      sequenceDensity: 0.55, acceptedStepsHour: 360, expansionCount: 1,
      episodeId: "episode-record:fixture:retained-44239", batchId: "batch:fixture:44239:01",
      checkpointId: "generation:44238", sourceWorkload: "factory:fixture:compile:01",
    }),
    Object.freeze({
      id: "resource:fixture:44239:0002", observedAt: 1_799_000_220,
      unifiedMemoryUsed: 46 * GiB, mlxAllocated: 32 * GiB, batchSize: 12,
      sequenceDensity: 0.68, acceptedStepsHour: 408, expansionCount: 3,
      episodeId: "episode-record:fixture:retained-44239", batchId: "batch:fixture:44239:02",
      checkpointId: "generation:44238", sourceWorkload: "factory:fixture:compile:02",
    }),
    Object.freeze({
      id: "resource:fixture:44239:0003", observedAt: 1_799_000_340,
      unifiedMemoryUsed: 54 * GiB, mlxAllocated: 39 * GiB, batchSize: 16,
      sequenceDensity: 0.91, acceptedStepsHour: 444, expansionCount: 7,
      episodeId: "episode-record:fixture:interference-44239", batchId: "batch:fixture:44239:03",
      checkpointId: "checkpoint:fixture:candidate-44239", sourceWorkload: "factory:fixture:compile:03",
    }),
    Object.freeze({
      id: "resource:fixture:44239:0004", observedAt: 1_799_000_460,
      unifiedMemoryUsed: 48 * GiB, mlxAllocated: 34 * GiB, batchSize: 12,
      sequenceDensity: 0.73, acceptedStepsHour: 420, expansionCount: 2,
      episodeId: "episode-record:fixture:pending-44239", batchId: "batch:fixture:44239:04",
      checkpointId: "generation:44239", sourceWorkload: "factory:fixture:compile:04",
    }),
  ]),
  throughputInterpretation: "THROUGHPUT_ONLY",
});

const HISTORICAL = Object.freeze({
  ...CURRENT,
  provenance: "FIXTURE",
  generation: 44238,
  window: "fixture-window:44238:10m",
  aggregate: Object.freeze({
    ...CURRENT.aggregate,
    unifiedMemoryUsed: metric(41 * GiB, "bytes"),
    forecastMemoryPeak: metric(46 * GiB, "bytes", "ESTIMATE", "INFERRED"),
    mlxAllocatedMemory: metric(28 * GiB, "bytes"),
    mlxCacheMemory: metric(3 * GiB, "bytes"),
    cpuUtilization: metric(48.2, "percent"),
    preparationWorkers: metric(4, "workers"),
    diskFree: metric(326 * GiB, "bytes"),
    candidateSnapshotFootprint: metric(3 * GiB, "bytes"),
    acceptedStepsHour: metric(330, "steps/hour", "DERIVED", "DERIVED"),
    sequenceDensity: metric(0.58, "fraction"),
    frameDensity: metric(0.49, "fraction"),
    batchSize: metric(8, "examples"),
    actualLengthP50: metric(312, "positions"),
    actualLengthP95: metric(608, "positions"),
    actualLengthMax: metric(704, "positions"),
    preparationCompileMs: metric(362, "ms"),
    mlxWallMs: metric(1328, "ms"),
  }),
  memoryDecomposition: Object.freeze([
    Object.freeze({ id: "model-parameters", label: "Model parameters", value: 3 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "optimizer-state", label: "Optimizer moments/state", value: 8 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "gradients", label: "Gradients", value: 3 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "engram", label: "Engram / motif memory", value: 5 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "activations", label: "Active batch / activations", value: 7 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "candidate-snapshot", label: "Candidate snapshot / staging", value: 3 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "caches", label: "Caches", value: 3 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "frame-sidecars", label: "Frame compiler / sidecars", value: 1 * GiB, state: "PRESENT" }),
    Object.freeze({ id: "other", label: "Other explicitly measured", value: null, state: "UNAVAILABLE" }),
  ]),
  timeline: Object.freeze([]),
});

export const RESOURCE_FIXTURES = Object.freeze([HISTORICAL, CURRENT]);

export function currentResourceFixture() {
  return CURRENT;
}

export function historicalResourceFixture() {
  return HISTORICAL;
}
