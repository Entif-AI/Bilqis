import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  SCHOOL_TERMINAL_COLUMNS,
  makeLargeSchoolFixture,
  schoolFixtureRows,
} from "../../renderer/school/school-fixture.mjs";
import {
  equalSchedulingSemantics,
  evidenceTotals,
  exportSchoolCsv,
  paginateRows,
  projectRows,
  scoreQuad,
  selectionNeighborhood,
} from "../../renderer/school/school-model.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../../renderer");
const rows = schoolFixtureRows();

test("literal fixture preserves the terminal-class metric contract", () => {
  assert.deepEqual(SCHOOL_TERMINAL_COLUMNS, [
    "grade", "prerequisites", "was", "top", "now", "total", "growth", "debt",
    "pRet", "visits", "retainedSteps", "lastGain", "lastRegression", "strategy",
    "sourceFamilies", "sourceState", "implementationState", "qualificationState",
  ]);
  const andRow = rows.find((row) => row.id === "B.AND");
  assert.equal(scoreQuad(andRow), "  7/ 11/ 10/ 12");
  assert.equal(andRow.debt, 2);
  assert.equal(andRow.pRet, 0.72);
  assert.equal(andRow.retainedSteps, 472);
});

test("WAS TOP NOW and debt remain distinct evidence dimensions", () => {
  const iff = rows.find((row) => row.id === "B.IFF");
  assert.equal(iff.was, 6);
  assert.equal(iff.top, 10);
  assert.equal(iff.now, 9);
  assert.equal(iff.total, 12);
  assert.equal(iff.debt, 3);
  assert.notEqual(iff.top, iff.now);
});

test("source-held and implementation-uncovered are separate states", () => {
  const held = rows.find((row) => row.id === "D.EVENT");
  const uncovered = rows.find((row) => row.id === "C.SUCCESSOR");
  assert.equal(held.sourceState, "SOURCE_HELD");
  assert.equal(uncovered.sourceState, "SOURCE_READY");
  assert.equal(uncovered.implementationState, "IMPLEMENTATION_UNCOVERED");
  const css = fs.readFileSync(path.join(rendererRoot, "school", "school.css"), "utf8");
  assert.match(css, /SOURCE_HELD/);
  assert.match(css, /IMPLEMENTATION_UNCOVERED/);
  assert.match(css, /border-style:\s*double/);
  assert.match(css, /border-style:\s*dashed/);
});

test("selection highlights exact prerequisite and dependent identities", () => {
  assert.deepEqual(selectionNeighborhood(rows, "B.AND"), {
    selected: "B.AND",
    prerequisites: ["B.NOT"],
    dependents: ["B.OR", "B.IFF"],
  });
});

test("grade labels do not change equal scheduling or promotion semantics", () => {
  const a = rows.find((row) => row.id === "A.IDENTITY");
  const c = rows.find((row) => row.id === "C.COUNT");
  assert.notEqual(a.grade, c.grade);
  assert.equal(a.qualificationState, "QUALIFIED");
  assert.equal(c.qualificationState, "QUALIFIED");
  assert.equal(equalSchedulingSemantics(a, c), true);
  assert.equal("quota" in a, false);
  assert.equal("priority" in c, false);
});

test("sort and filter preserve source evidence values and denominators", () => {
  const before = JSON.stringify(rows);
  const totals = evidenceTotals(rows);
  const projected = projectRows(rows, {
    filters: ["imperfect", "regression"],
    sortKey: "debt",
    direction: "desc",
    groupByFamily: true,
  });
  assert.equal(JSON.stringify(rows), before);
  assert.deepEqual(evidenceTotals(rows), totals);
  for (const row of projected) {
    const source = rows.find((candidate) => candidate.id === row.id);
    assert.equal(row.now, source.now);
    assert.equal(row.total, source.total);
    assert.equal(row.debt, source.debt);
  }
});

test("all required filters retain exact identities", () => {
  const expectations = {
    imperfect: "B.AND",
    regression: "B.AND",
    "stale-debt": "B.IFF",
    "recent-gain": "B.NOT",
    held: "D.EVENT",
    uncovered: "C.SUCCESSOR",
    qualified: "A.IDENTITY",
  };
  for (const [filter, identity] of Object.entries(expectations)) {
    const projected = projectRows(rows, { filters: [filter] });
    assert.equal(projected.some((row) => row.id === identity), true, filter);
  }
});

test("large fixtures paginate without losing total coverage", () => {
  const large = makeLargeSchoolFixture(243);
  const page = paginateRows(large, 5, 50);
  assert.equal(page.total, 243);
  assert.equal(page.pages, 5);
  assert.equal(page.start, 200);
  assert.equal(page.end, 243);
  assert.equal(page.rows.length, 43);
  assert.equal(new Set(large.map((row) => row.id)).size, 243);
});

test("filtered export uses the same displayed capability identities", () => {
  const qualified = projectRows(rows, { filters: ["qualified"], sortKey: "id" });
  const csv = exportSchoolCsv(qualified);
  for (const row of qualified) assert.match(csv, new RegExp(row.id.replace(".", "\\.")));
  assert.equal(csv.split("\n").length, qualified.length + 1);
});

test("graph lifecycle fixtures span ready through qualified plus held", () => {
  const states = new Set(rows.map((row) => row.lifecycleState));
  for (const state of ["READY", "STAGED", "ADMITTED", "EXPOSED", "QUALIFIED", "HELD"]) {
    assert.equal(states.has(state), true, state);
  }
});

test("matrix orientation and peer dependency representations are explicit", () => {
  const source = fs.readFileSync(path.join(rendererRoot, "school", "school-view.mjs"), "utf8");
  const css = fs.readFileSync(path.join(rendererRoot, "school", "school.css"), "utf8");
  assert.match(source, /school\.matrix\.group\.score/);
  assert.match(source, /secondaryColumns/);
  assert.match(source, /data-toggle-columns/);
  assert.match(source, /dependency-peers/);
  assert.match(source, /dependency-fallback/);
  assert.match(source, /aria-label="\$\{esc\(accessibleName\)\}"/);
  assert.match(source, /school\.pagination\.status/);
  assert.match(source, /data-eligibility=/);
  assert.match(source, /data-mastery=/);
  assert.match(source, /data-observed-debt=/);
  assert.match(source, /school\.fixture\.title/);
  assert.match(css, /\.matrix-scroll[^}]*overflow:\s*auto/s);
  assert.match(css, /\.school-matrix \.capability-cell[^}]*position:\s*sticky/s);
  assert.match(css, /\.dependency-peers[^}]*grid-template-columns/s);
});
