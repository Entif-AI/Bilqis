import { EPISODE_FIXTURES } from "../episodes/episode-fixture.mjs";
import { episodeDeepLink } from "../episodes/episode-model.mjs";
import {
  FIDELITY_FIXTURES,
  STRATEGY_FIXTURES,
  TEACHER_PROJECTION,
} from "./teacher-fixture.mjs";

export function strategyById(id) {
  return STRATEGY_FIXTURES.find((strategy) => strategy.id === id) ?? STRATEGY_FIXTURES[0];
}

export function strategyEpisodes(strategy) {
  return strategy.episodeRecordIds.map((recordId) => {
    const episode = EPISODE_FIXTURES.find((item) => item.recordId === recordId);
    return Object.freeze({
      recordId,
      capabilityId: episode?.capabilityId ?? "UNKNOWN",
      terminalState: episode?.terminalState ?? "UNKNOWN",
      retentionReason: episode?.retentionReason ?? "UNKNOWN",
      href: episodeDeepLink(recordId),
    });
  });
}

export function median(values) {
  if (!values.length) return null;
  const ordered = [...values].sort((left, right) => left - right);
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2
    ? ordered[middle]
    : (ordered[middle - 1] + ordered[middle]) / 2;
}

export function aggregateContext(rows) {
  if (!rows.length) {
    return Object.freeze({
      observations: 0,
      retained: 0,
      noGain: 0,
      interference: 0,
      actualGain: 0,
      averageWallSeconds: null,
      medianWallSeconds: null,
      attemptedSteps: 0,
      coverage: "MISSING",
    });
  }
  const wall = rows.flatMap((row) => row.wallSeconds);
  const observations = rows.reduce((sum, row) => sum + row.observations, 0);
  return Object.freeze({
    observations,
    retained: rows.reduce((sum, row) => sum + row.retained, 0),
    noGain: rows.reduce((sum, row) => sum + row.noGain, 0),
    interference: rows.reduce((sum, row) => sum + row.interference, 0),
    actualGain: rows.reduce((sum, row) => sum + row.actualGain, 0),
    averageWallSeconds: wall.length
      ? Number((wall.reduce((sum, value) => sum + value, 0) / wall.length).toFixed(2))
      : null,
    medianWallSeconds: wall.length ? Number(median(wall).toFixed(2)) : null,
    attemptedSteps: rows.reduce((sum, row) => sum + row.attemptedSteps, 0),
    coverage: observations > 0 ? "PRESENT" : "MISSING",
  });
}

export function comparisonScopes(strategies) {
  if (!strategies.length) return Object.freeze({ capabilities: [], sourceFamilies: [] });
  const capabilitySets = strategies.map((strategy) =>
    new Set(strategy.contexts.map((row) => row.capabilityId)),
  );
  const familySets = strategies.map((strategy) =>
    new Set(strategy.contexts.map((row) => row.sourceFamily)),
  );
  const intersection = (sets) => [...sets[0]].filter((value) =>
    sets.slice(1).every((set) => set.has(value)),
  ).sort();
  return Object.freeze({
    capabilities: Object.freeze(intersection(capabilitySets)),
    sourceFamilies: Object.freeze(intersection(familySets)),
  });
}

export function strategyComparison(strategyIds, scope) {
  const strategies = strategyIds.map(strategyById);
  const rows = strategies.map((strategy) => {
    const selected = strategy.contexts.filter((row) => {
      if (scope.kind === "capability") return row.capabilityId === scope.value;
      if (scope.kind === "source-family") return row.sourceFamily === scope.value;
      return true;
    });
    return Object.freeze({
      strategy,
      metrics: aggregateContext(selected),
      matchedContexts: Object.freeze(selected.map((row) =>
        row.capabilityId + " · " + row.sourceFamily,
      )),
    });
  });
  const counts = rows.map((row) => row.metrics.observations);
  const commonCoverageFloor = counts.length ? Math.min(...counts) : 0;
  return Object.freeze({
    scope: Object.freeze({ ...scope }),
    rows: Object.freeze(rows),
    commonCoverageFloor,
    coverage: counts.every((count) => count === commonCoverageFloor)
      ? "EQUAL_OBSERVED_DENOMINATORS"
      : "PARTIAL_OBSERVED_DENOMINATORS",
  });
}

export function fidelityForStrategy(strategyId) {
  return FIDELITY_FIXTURES.filter((item) => item.strategyId === strategyId);
}

export function roleCounts() {
  return Object.freeze(STRATEGY_FIXTURES.reduce((result, strategy) => {
    result[strategy.role] = (result[strategy.role] ?? 0) + 1;
    return result;
  }, {}));
}

export function teacherProjectionBoundary() {
  return TEACHER_PROJECTION;
}
