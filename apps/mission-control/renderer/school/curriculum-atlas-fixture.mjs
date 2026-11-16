import { schoolFixtureRows, makeLargeSchoolFixture } from "./school-fixture.mjs";

const DISPLAY = Object.freeze({
  "A.IDENTITY": Object.freeze({ label: "Semantic Identity", semanticId: "fixture-semantic:A.IDENTITY" }),
  "B.NOT": Object.freeze({ label: "Negation", semanticId: "fixture-semantic:B.NOT" }),
  "B.AND": Object.freeze({ label: "Boolean Composition", semanticId: "fixture-semantic:B.AND" }),
  "B.OR": Object.freeze({ label: "Boolean Disjunction", semanticId: "fixture-semantic:B.OR" }),
  "B.IFF": Object.freeze({ label: "Boolean Equivalence", semanticId: "fixture-semantic:B.IFF" }),
  "C.COUNT": Object.freeze({ label: "Counting", semanticId: "fixture-semantic:C.COUNT" }),
  "C.NUMBER": Object.freeze({ label: "Number Semantics", semanticId: "fixture-semantic:C.NUMBER" }),
  "C.SUCCESSOR": Object.freeze({ label: "Successor", semanticId: "fixture-semantic:C.SUCCESSOR" }),
  "D.EVENT": Object.freeze({ label: "Event Semantics", semanticId: "fixture-semantic:D.EVENT" }),
});

const CURRENT_IDS = Object.freeze([
  "A.IDENTITY", "B.NOT", "B.AND", "B.OR", "B.IFF",
  "C.COUNT", "C.NUMBER", "C.SUCCESSOR", "D.EVENT",
]);

const HISTORICAL_IDS = Object.freeze([
  "A.IDENTITY", "B.NOT", "B.AND", "B.OR", "B.IFF", "C.COUNT",
]);

const HISTORICAL_OVERRIDES = Object.freeze({
  "B.NOT": Object.freeze({
    was: 7, top: 10, now: 10, debt: 2, pRet: 0.78,
    lifecycleState: "EXPOSED", qualificationState: "ADMITTED",
    recentGain: true, observedDebt: true, lastGain: "gen 44218 +1",
    lastRegression: "none",
  }),
  "B.AND": Object.freeze({
    was: 5, top: 7, now: 7, debt: 5, pRet: 0.51,
    lifecycleState: "EXPOSED", qualificationState: "ADMITTED",
    recentGain: true, observedDebt: true, lastGain: "gen 44219 +1",
    lastRegression: "none",
  }),
  "B.OR": Object.freeze({
    was: 0, top: 0, now: 0, debt: 12, pRet: null,
    lifecycleState: "READY", qualificationState: "READY",
    recentGain: false, observedDebt: true, lastGain: "none",
    lastRegression: "none",
  }),
  "B.IFF": Object.freeze({
    was: 0, top: 0, now: 0, debt: 12, pRet: null,
    lifecycleState: "STAGED", qualificationState: "STAGED",
    recentGain: false, observedDebt: true, lastGain: "none",
    lastRegression: "none",
  }),
  "C.COUNT": Object.freeze({
    was: 0, top: 0, now: 0, debt: 12, pRet: null,
    lifecycleState: "STAGED", qualificationState: "STAGED",
    recentGain: false, observedDebt: false, lastGain: "none",
    lastRegression: "none",
  }),
});

const SNAPSHOT_SPECS = Object.freeze({
  current: Object.freeze({
    id: "current",
    label: "Current curriculum fixture",
    currentGrade: "C",
    activeId: "C.NUMBER",
    includedIds: CURRENT_IDS,
    overrides: Object.freeze({}),
  }),
  historical: Object.freeze({
    id: "historical",
    label: "Historical curriculum fixture",
    currentGrade: "B",
    activeId: "B.AND",
    includedIds: HISTORICAL_IDS,
    overrides: HISTORICAL_OVERRIDES,
  }),
});

function displayFor(id) {
  return DISPLAY[id] ?? Object.freeze({
    label: id,
    semanticId: "fixture-semantic:" + id,
  });
}

function blocker(row) {
  if (row.sourceState === "SOURCE_HELD") {
    return Object.freeze({
      code: "SOURCE_HELD",
      detail: "Owning source state is SOURCE_HELD.",
      evidence: Object.freeze([...row.sourceFamilies]),
    });
  }
  if (row.implementationState === "IMPLEMENTATION_UNCOVERED") {
    return Object.freeze({
      code: "IMPLEMENTATION_UNCOVERED",
      detail: "Source is known but the implementation surface is uncovered.",
      evidence: Object.freeze([...row.sourceFamilies]),
    });
  }
  if (row.lifecycleState === "HELD") {
    return Object.freeze({
      code: "UNKNOWN",
      detail: "Held state has no more specific blocker in the shared School fixture.",
      evidence: Object.freeze([]),
    });
  }
  return null;
}

function eventGeneration(label) {
  const match = String(label).match(/gen\s+(\d+)/);
  return match ? Number(match[1]) : null;
}

function boundedHistory(row, generation) {
  const events = [];
  if (row.lastGain !== "none") {
    events.push(Object.freeze({
      posture: "HISTORICAL",
      kind: "GAIN",
      generation: eventGeneration(row.lastGain),
      label: row.lastGain,
    }));
  }
  if (row.lastRegression !== "none") {
    events.push(Object.freeze({
      posture: "HISTORICAL",
      kind: "REGRESSION",
      generation: eventGeneration(row.lastRegression),
      label: row.lastRegression,
    }));
  }
const bounded = events
  .filter((event) => event.generation === null || generation === null || event.generation <= generation)
  .sort((a, b) => (a.generation ?? -1) - (b.generation ?? -1));
bounded.push(Object.freeze({
  posture: "CURRENT_AS_OF",
  kind: "STATE",
  generation,
  label: row.lifecycleState + " · NOW " + row.now + "/" + row.total,
}));
return Object.freeze(bounded.slice(-4));
}

function withDisplay(row, currentGrade, generation) {
  const display = displayFor(row.id);
  return Object.freeze({
    ...row,
    prerequisites: Object.freeze([...row.prerequisites]),
    sourceFamilies: Object.freeze([...row.sourceFamilies]),
    label: display.label,
    semanticId: display.semanticId,
    semanticIdentityAuthority: "FIXTURE_DISPLAY_ONLY",
    firstIntroducedGrade: row.grade,
    newThisGrade: row.grade === currentGrade,
    blocker: blocker(row),
    requalificationState: row.lastRegression !== "none"
      ? "REGRESSION_OBSERVED"
      : "NONE_RECORDED",
    sourceRefs: Object.freeze([...row.sourceFamilies]),
    lastRelevantEvent: row.lastRegression !== "none" ? row.lastRegression : row.lastGain,
    historyEvents: boundedHistory(row, generation),
  });
}

export function curriculumFixtureSnapshot(mode = "current", generation = null) {
  const spec = SNAPSHOT_SPECS[mode] ?? SNAPSHOT_SPECS.current;
  const rows = schoolFixtureRows();
  const byId = new Map(rows.map((row) => [row.id, row]));
  const nodes = spec.includedIds.map((id) => {
    const source = byId.get(id);
    if (!source) throw new Error("GUI22_FIXTURE_CAPABILITY_MISSING:" + id);
    const row = { ...source, ...(spec.overrides[id] ?? {}) };
    return withDisplay(row, spec.currentGrade, generation);
  });
  return Object.freeze({
    id: spec.id,
    label: spec.label,
    generation,
    currentGrade: spec.currentGrade,
    activeId: spec.activeId,
    nodes: Object.freeze(nodes),
    fixture: true,
    fixtureBoundary: "SHARED_SCHOOL_ROWS_PLUS_EXPLICIT_AS_OF_OVERRIDES",
  });
}

export function curriculumLargeFixture(size = 243) {
  const base = schoolFixtureRows();
  const baseIndex = new Map(base.map((row, index) => [row.id, index]));
  return makeLargeSchoolFixture(size).map((row, index) => {
    const source = base[index % base.length];
    const cycleStart = index - (index % base.length);
    const prerequisites = source.prerequisites.flatMap((id) => {
      const relative = baseIndex.get(id);
      const target = relative === undefined ? -1 : cycleStart + relative;
      return target >= 0 && target < size
        ? [id + ".F" + String(target + 1).padStart(3, "0")]
        : [];
    });
    return withDisplay({ ...row, prerequisites }, "C", null);
  });
}

export const CURRICULUM_DISPLAY_METADATA = DISPLAY;
