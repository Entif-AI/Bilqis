import { HOME_FAMILIES, classifyLearning } from "./home-model.mjs";
import { schoolFixtureRows } from "../school/school-fixture.mjs";
import { EPISODE_FIXTURES } from "../episodes/episode-fixture.mjs";

function ratio(numerator, denominator) {
  return Number.isFinite(numerator) && Number.isFinite(denominator) && denominator > 0
    ? numerator / denominator : null;
}

export function referenceHomeProjection() {
  const rows = schoolFixtureRows();
  const current = rows.reduce((sum, row) => sum + row.now, 0);
  const best = rows.reduce((sum, row) => sum + row.top, 0);
  const was = rows.reduce((sum, row) => sum + row.was, 0);
  const total = rows.reduce((sum, row) => sum + row.total, 0);
  const retainedSteps = rows.reduce((sum, row) => sum + row.retainedSteps, 0);
  const pRetRows = rows.filter((row) => row.pRet !== null);
  const retainedEpisode = EPISODE_FIXTURES.find((episode) => episode.terminalState === "RETAINED");
  const pending = EPISODE_FIXTURES.find((episode) => episode.terminalState === "UNKNOWN");
  const rejected = EPISODE_FIXTURES.filter((episode) => episode.terminalState === "REJECTED");
  const regression = rows.find((row) => row.lastRegression !== "none");
  return Object.freeze({
    provenance: "FIXTURE",
    startup: null,
    state: Object.freeze(Object.fromEntries(HOME_FAMILIES.map((family) => [family, "PRESENT"]))),
    learningStatus: classifyLearning({ retained: 1, freshRetainedImprovements: 1, regressions: 1 }),
    learning: Object.freeze({
      latestSchoolScore: ratio(current, total), bestSchoolScore: ratio(best, total),
      wholeSchoolGrowth: ratio(current - was, total), gRtn: null,
      pRet: pRetRows.reduce((sum, row) => sum + row.pRet, 0) / pRetRows.length,
      retainedOptimizerSteps: retainedSteps,
    }),
    curriculum: Object.freeze({
      qualifiedCapabilities: rows.filter((row) => row.qualificationState === "QUALIFIED").length,
      observedDebt: rows.reduce((sum, row) => sum + row.debt, 0), activeConcepts: 30,
      ready: rows.filter((row) => row.qualificationState === "READY").length,
      held: rows.filter((row) => row.sourceState === "SOURCE_HELD").length,
      uncovered: rows.filter((row) => row.implementationState === "IMPLEMENTATION_UNCOVERED").length,
    }),
    runtime: Object.freeze({ running: true, elapsed: "42 m fixture window", visits: rows.reduce((sum, row) => sum + row.visits, 0),
      visitRate: null, retainedCandidates: 1, rejectedCandidates: rejected.length, acceptedStepsHour: null }),
    system: Object.freeze({ memoryPressure: null, peakMemory: null, diskReserve: null, correctionDebt: 1, hardWarnings: 0 }),
    currentWork: Object.freeze({
      capabilityId: pending.capabilityId, strategy: pending.strategy, candidateIntent: pending.retentionReason,
      sourceFamily: pending.sourceFamily, targetAssessment: "PENDING", protectedAssessment: "PENDING",
      recordId: pending.recordId,
    }),
    schoolRows: Object.freeze(rows.slice(0, 7).map((row) => Object.freeze({
      id: row.id, now: row.now, total: row.total, best: row.top, delta: row.growth, debt: row.debt,
      pRet: row.pRet, status: row.qualificationState, lastVisit: row.lastGain,
      strategy: row.strategy, recordId: row.id,
    }))),
    pulse: Object.freeze([
      { kind: "gain", observedAt: null, materializedAt: null, capabilityId: retainedEpisode.capabilityId, before: "10/12", after: "12/12", target: { kind: "episode", id: retainedEpisode.recordId } },
      { kind: "regress", observedAt: null, materializedAt: null, capabilityId: regression.id, detail: regression.lastRegression, target: { kind: "capability", id: regression.id } },
      { kind: "retain", observedAt: null, materializedAt: null, capabilityId: retainedEpisode.capabilityId, reasonCode: retainedEpisode.retentionReason, target: { kind: "episode", id: retainedEpisode.recordId } },
      { kind: "reject", observedAt: null, materializedAt: null, capabilityId: rejected[0].capabilityId, reasonCode: rejected[0].retentionReason, target: { kind: "episode", id: rejected[0].recordId } },
      { kind: "source", observedAt: null, materializedAt: null, family: "future-source", target: { kind: "capability", id: "D.EVENT" } },
      { kind: "correction", observedAt: null, materializedAt: null, count: 1, target: { kind: "correction", id: "correction:fixture:1" } },
    ].map(Object.freeze)),
    attention: Object.freeze([
      Object.freeze({ kind: "stalled", severity: "attention", capabilities: "B.IFF · C.NUMBER", id: "B.IFF", target: { kind: "capability", id: "B.IFF" } }),
      Object.freeze({ kind: "held", severity: "attention", capabilityId: "D.EVENT", id: "D.EVENT", target: { kind: "capability", id: "D.EVENT" } }),
      Object.freeze({ kind: "recovery", severity: "blocker", capabilityId: pending.capabilityId, id: pending.recordId, target: { kind: "episode", id: pending.recordId } }),
    ]),
  });
}
