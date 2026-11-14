import { schoolFixtureRows } from "../school/school-fixture.mjs";
import { EPISODE_FIXTURES } from "../episodes/episode-fixture.mjs";

const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";
const PRESENT = "PRESENT";

export const HOME_FAMILIES = Object.freeze([
  "run", "school", "capability", "episode", "semantic", "resource", "correction", "teacher",
]);

export function queryRequest(family, context, overrides = {}) {
  const historical = context?.mode === "HISTORICAL";
  return Object.freeze({
    schema: QUERY_SCHEMA,
    family,
    mode: historical ? "historical" : "current",
    run_id: context?.runId ?? null,
    record_id: null,
    schema_version: null,
    generation: historical ? context.generation : null,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor: null,
    limit: 32,
    ...overrides,
  });
}

export function familyForEvent(event) {
  const family = String(event?.event_family ?? "");
  if (family.startsWith("lesson.") || family.startsWith("candidate.")) return "episode";
  if (family.startsWith("capability.")) return "capability";
  if (family.startsWith("semantic.")) return "semantic";
  if (family.startsWith("teacher.")) return "teacher";
  if (family.startsWith("correction.")) return "correction";
  if (family.startsWith("resource.")) return "resource";
  if (family.startsWith("run.") || family.startsWith("checkpoint.")) return "run";
  return null;
}

function value(record, field) {
  const datum = record?.[field];
  return datum?.state === PRESENT ? datum.value : null;
}

function latest(records, schema) {
  return records.filter((record) => record?.schema_version === schema).at(-1) ?? null;
}

function pageRecords(pages, family) {
  const page = pages[family];
  return page?.accepted === true && Array.isArray(page.records) ? page.records : [];
}

function pageState(pages, family) {
  const page = pages[family];
  return page?.accepted === true ? page.state : "UNAVAILABLE";
}

function ratio(numerator, denominator) {
  return Number.isFinite(numerator) && Number.isFinite(denominator) && denominator > 0
    ? numerator / denominator : null;
}

export function classifyLearning({ retained = 0, freshRetainedImprovements = 0, regressions = 0 } = {}) {
  if (freshRetainedImprovements > 0) return "IMPROVING";
  if (regressions > 0) return "REGRESSION";
  if (retained > 0) return "THROUGHPUT_ONLY";
  return "NO_FRESH_GAIN";
}

export function projectionFromPages(pages, context) {
  const capabilities = pageRecords(pages, "capability");
  const episodes = pageRecords(pages, "episode");
  const schoolRecords = pageRecords(pages, "school");
  const runRecords = pageRecords(pages, "run");
  const semanticRecords = pageRecords(pages, "semantic");
  const resources = pageRecords(pages, "resource");
  const corrections = pageRecords(pages, "correction");
  const teachers = pageRecords(pages, "teacher");

  const run = latest(runRecords, "bilqis.bamf.mission-control.run-context/v1");
  const school = latest(schoolRecords, "bilqis.bamf.mission-control.school-snapshot/v1");
  const frontier = latest(schoolRecords, "bilqis.bamf.mission-control.curriculum-frontier/v1");
  const semantic = latest(semanticRecords, "bilqis.bamf.mission-control.semantic-atlas-snapshot/v1");
  const resource = latest(resources, "bilqis.bamf.mission-control.resource-sample/v1");
  const teacher = latest(teachers, "bilqis.bamf.mission-control.teacher-snapshot/v1");
  const capabilityRows = capabilities.filter((record) => record.schema_version === "bilqis.bamf.mission-control.capability-snapshot/v1");
  const episodeRows = episodes.filter((record) => record.schema_version === "bilqis.bamf.mission-control.learning-episode/v1");
  const decisions = episodes.filter((record) => record.schema_version === "bilqis.bamf.mission-control.candidate-decision/v1");
  const currentCorrect = capabilityRows.reduce((sum, record) => sum + (value(record, "score_correct") ?? 0), 0);
  const currentTotal = capabilityRows.reduce((sum, record) => sum + (value(record, "score_total") ?? 0), 0);
  const debt = capabilityRows.reduce((sum, record) => sum + (value(record, "debt") ?? 0), 0);
  const retained = decisions.filter((record) => record.outcome === "ACCEPTED").length;
  const rejected = decisions.filter((record) => record.outcome === "REJECTED").length;
  const activeEpisode = episodeRows.find((record) => record.state !== "COMPLETED") ?? null;
  const correctionDebt = corrections.filter((record) => record.state === "REQUALIFICATION_REQUIRED").length;
  const qualified = capabilityRows.filter((record) => record.status === "QUALIFIED").length;
  const domainRecordCount = (
    capabilities.length + episodes.length + schoolRecords.length + semanticRecords.length +
    resources.length + corrections.length + teachers.length
  );
  const startup = run && context?.mode !== "HISTORICAL" && domainRecordCount === 0
    ? Object.freeze({
      state: context?.operatorActive === true
        ? "WAITING_FOR_FIRST_TRAINING_EVENT"
        : run.optimizer_step === 0 ? "GENERATION_ZERO_READY" : "IDLE_NO_DOMAIN_EVIDENCE",
      generation: run.meta.run.generation,
      optimizerStep: run.optimizer_step,
      stage: run.stage,
      running: typeof context?.operatorActive === "boolean" ? context.operatorActive : null,
    })
    : null;

  return Object.freeze({
    provenance: "LIVE_QUERY",
    startup,
    state: Object.freeze(Object.fromEntries(HOME_FAMILIES.map((family) => [family, pageState(pages, family)]))),
    learningStatus: classifyLearning({ retained, freshRetainedImprovements: 0, regressions: 0 }),
    learning: Object.freeze({
      latestSchoolScore: ratio(currentCorrect, currentTotal),
      bestSchoolScore: null,
      wholeSchoolGrowth: null,
      gRtn: null,
      pRet: null,
      retainedOptimizerSteps: null,
    }),
    curriculum: Object.freeze({
      qualifiedCapabilities: qualified || value(school, "mastered_count"),
      observedDebt: capabilityRows.length ? debt : null,
      activeConcepts: value(semantic, "active_concepts"),
      ready: frontier?.ready_capability_ids?.length ?? null,
      held: frontier?.held_capability_ids?.length ?? null,
      uncovered: null,
    }),
    runtime: Object.freeze({
      running: typeof context?.operatorActive === "boolean" ? context.operatorActive : null,
      elapsed: null,
      visits: episodeRows.length || null,
      visitRate: null,
      retainedCandidates: retained,
      rejectedCandidates: rejected,
      acceptedStepsHour: value(resource, "step_rate_per_minute") === null
        ? null : value(resource, "step_rate_per_minute") * 60,
    }),
    system: Object.freeze({
      memoryPressure: ratio(value(resource, "memory_used_bytes"), value(resource, "memory_budget_bytes")),
      peakMemory: null,
      diskReserve: null,
      correctionDebt,
      hardWarnings: null,
    }),
    currentWork: Object.freeze({
      capabilityId: activeEpisode?.capability_id ?? context?.activeCapabilityId ?? null,
      strategy: teacher?.strategy_id ?? null,
      candidateIntent: activeEpisode?.state ?? run?.stage ?? null,
      sourceFamily: null,
      targetAssessment: null,
      protectedAssessment: null,
      recordId: activeEpisode?.meta?.record_id ?? null,
    }),
    schoolRows: Object.freeze(capabilityRows.slice(0, 8).map((record) => Object.freeze({
      id: record.capability_id,
      now: value(record, "score_correct"),
      total: value(record, "score_total"),
      debt: value(record, "debt"),
      status: record.status,
      recordId: record.meta?.record_id ?? record.capability_id,
    }))),
    pulse: Object.freeze(decisions.slice(-8).reverse().map((record) => Object.freeze({
      kind: record.outcome === "ACCEPTED" ? "retain" : "reject",
      label: `${record.outcome}: ${record.capability_id}`,
      detail: record.reason_code,
      target: Object.freeze({ kind: "capability", id: record.capability_id }),
    }))),
    attention: Object.freeze([
      ...(correctionDebt ? [{ kind: "correction", label: "Correction debt", detail: `${correctionDebt} requalification item(s) require review`, id: corrections[0]?.meta?.record_id }] : []),
    ]),
  });
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
      { kind: "gain", label: `Fresh retained gain · ${retainedEpisode.capabilityId}`, detail: "10/12 → 12/12; child generation committed", target: { kind: "episode", id: retainedEpisode.recordId } },
      { kind: "regress", label: `Regression · ${regression.id}`, detail: regression.lastRegression, target: { kind: "capability", id: regression.id } },
      { kind: "retain", label: "Candidate retained", detail: retainedEpisode.retentionReason, target: { kind: "episode", id: retainedEpisode.recordId } },
      { kind: "reject", label: `Candidate rejected · ${rejected[0].capabilityId}`, detail: rejected[0].retentionReason, target: { kind: "episode", id: rejected[0].recordId } },
      { kind: "source", label: "Source family held", detail: "future-source · policy/evidence hold", target: { kind: "capability", id: "D.EVENT" } },
      { kind: "correction", label: "Correction / requalification", detail: "1 fixture correction requires requalification", target: { kind: "correction", id: "correction:fixture:1" } },
    ].map(Object.freeze)),
    attention: Object.freeze([
      Object.freeze({ kind: "stalled", label: "Stale capability debt", detail: "B.IFF and C.NUMBER carry stale observed debt", id: "B.IFF", target: { kind: "capability", id: "B.IFF" } }),
      Object.freeze({ kind: "held", label: "Held source family", detail: "D.EVENT · future-source remains held", id: "D.EVENT", target: { kind: "capability", id: "D.EVENT" } }),
      Object.freeze({ kind: "recovery", label: "Outcome reconciliation", detail: `${pending.capabilityId} has partial optimizer evidence and no terminal receipt`, id: pending.recordId, target: { kind: "episode", id: pending.recordId } }),
    ]),
  });
}
