import { EPISODE_FIXTURES, EPISODE_STAGES } from "./episode-fixture.mjs";

export function episodeById(id) {
  return EPISODE_FIXTURES.find((episode) =>
    episode.recordId === id || episode.episodeId === id || episode.candidateId === id,
  ) ?? EPISODE_FIXTURES[0];
}

export function episodeDeepLink(recordId) {
  const params = new URLSearchParams({ kind: "episode", id: recordId });
  return "#/view/learning?" + params.toString();
}

export function episodesForCapability(capabilityId) {
  return EPISODE_FIXTURES.filter((episode) => episode.capabilityId === capabilityId);
}

export function scoreText(score) {
  return score ? score.correct + "/" + score.total : "UNAVAILABLE";
}

export function episodeDurationText(durationMs) {
  return durationMs === null ? "UNKNOWN" : (durationMs / 1000).toFixed(1) + " s";
}

export function rollbackInvariant(episode) {
  if (episode.terminalState !== "REJECTED") return null;
  const before = episode.parentState.before;
  const after = episode.parentState.after;
  return Object.freeze({
    neuralUnchanged: before.student === after?.student,
    optimizerUnchanged: before.optimizer === after?.optimizer,
    allocationUnchanged: before.allocation === after?.allocation,
    retainedOptimizerStepsZero: episode.retainedOptimizerSteps === 0,
    noChildGeneration: episode.resultingGeneration === null,
  });
}

export function retainedTransition(episode) {
  if (episode.terminalState !== "RETAINED") return null;
  return Object.freeze({
    parentGeneration: episode.parentGeneration,
    childGeneration: episode.resultingGeneration,
    checkpointId: episode.checkpointId,
    committed: Number.isInteger(episode.resultingGeneration) && episode.checkpointId !== null,
  });
}

export function rejectionClass(episode) {
  if (episode.retentionReason === "NO_MEASURABLE_TARGET_GAIN") return "NO_GAIN";
  if (episode.terminalState === "REJECTED") return "INTERFERENCE";
  return "NONE";
}

export function replaySlice(episode, stageIndex) {
  const bounded = Math.min(Math.max(0, stageIndex), EPISODE_STAGES.length - 1);
  return Object.freeze({
    stageIndex: bounded,
    active: episode.stages[bounded],
    visibleStages: episode.stages.slice(0, bounded + 1),
  });
}

export function diffRows(episode) {
  const scalar = (value) => value ?? "UNAVAILABLE";
  return Object.freeze([
    Object.freeze({
      labelKey: "learning.comparison.targetScore",
      before: scoreText(episode.target.before),
      challenger: scoreText(episode.target.candidateAfter),
      committed: scoreText(episode.target.committedAfter),
      state: episode.target.candidateAfter ? "PRESENT" : "PARTIAL",
    }),
    Object.freeze({
      labelKey: "learning.comparison.protectedScore",
      before: scoreText(episode.protected.before),
      challenger: scoreText(episode.protected.candidateAfter),
      committed: scoreText(episode.protected.committedAfter),
      state: episode.protected.state === "NOT_MEASURED"
        ? "MISSING"
        : episode.protected.candidateAfter ? "PRESENT" : "PARTIAL",
    }),
    Object.freeze({
      labelKey: "learning.comparison.wholeSchoolDelta",
      before: "0",
      challenger: episode.wholeSchool.candidateDelta ?? "UNAVAILABLE",
      committed: episode.wholeSchool.committedDelta ?? "UNAVAILABLE",
      state: episode.wholeSchool.state,
    }),
    Object.freeze({
      labelKey: "learning.comparison.capabilityDebt",
      before: episode.debt.before,
      challenger: episode.debt.candidateAfter ?? "UNAVAILABLE",
      committed: episode.debt.committedAfter ?? "UNAVAILABLE",
      state: episode.debt.candidateAfter === null ? "PARTIAL" : "PRESENT",
    }),
    Object.freeze({
      labelKey: "learning.comparison.memoryBytes",
      before: scalar(episode.memory.beforeBytes),
      challenger: scalar(episode.memory.candidateAfterBytes),
      committed: scalar(episode.memory.committedAfterBytes),
      state: episode.memory.state,
    }),
    Object.freeze({
      labelKey: "learning.comparison.allocationSlots",
      before: scalar(episode.allocation.beforeSlots),
      challenger: scalar(episode.allocation.candidateAfterSlots),
      committed: scalar(episode.allocation.committedAfterSlots),
      state: episode.allocation.state,
    }),
  ]);
}

export function lifecycleCoverage(episode) {
  return Object.freeze(episode.stages.reduce((counts, stage) => {
    counts[stage.state] = (counts[stage.state] ?? 0) + 1;
    return counts;
  }, {}));
}
