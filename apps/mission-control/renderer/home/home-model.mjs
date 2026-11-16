import { observedHomeState } from "./home-observed.mjs";

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
  if (regressions > 0) return "REGRESSION";
  if (freshRetainedImprovements > 0) return "IMPROVING";
  if (retained > 0) return "THROUGHPUT_ONLY";
  return "NO_FRESH_GAIN";
}

export function homeStatus(model) {
  const invalidStates = new Set(["INVALID", "INVALIDITY", "CONFLICT", "DENIED", "REVOKED", "INCOMPATIBLE"]);
  const regression = model?.learningStatus === "REGRESSION" ||
    model?.pulse?.some((event) => ["regress", "regression"].includes(event.kind)) === true;
  const blocked = model?.attention?.some((item) => item.severity === "blocker" || item.kind === "blocked") === true;
  const invalidity = Object.values(model?.state ?? {}).some((state) => invalidStates.has(state)) ||
    model?.attention?.some((item) => item.severity === "invalid") === true;
  return Object.freeze({
    running: model?.runtime?.running ?? null,
    learning: model?.learningStatus ?? "NO_FRESH_GAIN",
    regression,
    blocked,
    invalidity,
    attentionPriority: regression || blocked || invalidity ? "primary" : "secondary",
  });
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
  const observed = observedHomeState(runRecords, context, run);
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
  const startup = run && !observed.current && context?.mode !== "HISTORICAL" && domainRecordCount === 0
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
  const health = observed.current?.learning_health;
  const healthRegressions = Array.isArray(health?.regressed_protected_capabilities)
    ? health.regressed_protected_capabilities.length +
      (health.regressed_from_first === true ? 1 : 0) : 0;
  const acceptedGain = Number.isInteger(health?.gain_from_first) &&
    health.gain_from_first > 0 ? 1 : 0;

  return Object.freeze({
    provenance: "LIVE_QUERY",
    observed,
    startup,
    state: Object.freeze(Object.fromEntries(HOME_FAMILIES.map((family) => [family, pageState(pages, family)]))),
    learningStatus: classifyLearning({
      retained, freshRetainedImprovements: acceptedGain, regressions: healthRegressions,
    }),
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
      capabilityId: observed.current?.capability_id ?? activeEpisode?.capability_id ?? context?.activeCapabilityId ?? null,
      strategy: teacher?.strategy_id ?? null,
      candidateIntent: observed.current?.phase ?? activeEpisode?.state ?? run?.stage ?? null,
      sourceFamily: null,
      targetAssessment: null,
      protectedAssessment: null,
      recordId: activeEpisode?.meta?.record_id ?? null,
      observedAt: activeEpisode?.meta?.observed_at ?? null,
      materializedAt: activeEpisode?.meta?.materialized_at ?? null,
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
      capabilityId: record.capability_id,
      reasonCode: record.reason_code,
      observedAt: record.meta?.observed_at ?? null,
      materializedAt: record.meta?.materialized_at ?? null,
      target: Object.freeze({ kind: "capability", id: record.capability_id }),
    }))),
    attention: Object.freeze([
      ...(correctionDebt ? [{
        kind: "correction", severity: "invalid", count: correctionDebt, id: corrections[0]?.meta?.record_id,
        target: { kind: "correction", id: corrections[0]?.meta?.record_id },
        observedAt: corrections[0]?.meta?.observed_at ?? null,
        materializedAt: corrections[0]?.meta?.materialized_at ?? null,
      }] : []),
    ]),
  });
}
