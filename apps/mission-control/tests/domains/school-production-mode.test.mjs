import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  capabilityQuery,
  loadSchoolRows,
  schoolRowFromRecord,
} from "../../renderer/school/school-live.mjs";
import { renderFixtureModePosture } from "../../renderer/foundation/fixture-mode.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../../renderer");

const datum = (value) => ({ state: "PRESENT", origin: "MEASURED", value, units: null });

function capability(id, generation = 7) {
  return {
    schema_version: "bilqis.bamf.mission-control.capability-snapshot/v1",
    meta: {
      record_id: "capability:" + id,
      run: { run_id: "run-7", generation },
      observed_at: 1_799_000_100 + generation,
      materialized_at: 1_799_000_110 + generation,
      source_refs: ["source:" + id],
      evidence_refs: [],
      receipt_refs: [],
    },
    capability_id: id,
    grade_id: "B",
    status: "ADMITTED",
    score_correct: datum(8),
    score_total: datum(12),
    debt: datum(4),
  };
}

test("production capability projection preserves exact evidence and leaves unexposed School fields empty", () => {
  const row = schoolRowFromRecord(capability("B.AND"));
  assert.equal(row.id, "B.AND");
  assert.equal(row.now, 8);
  assert.equal(row.total, 12);
  assert.equal(row.debt, 4);
  assert.equal(row.observedAt, 1_799_000_107);
  assert.equal(row.materializedAt, 1_799_000_117);
  for (const field of ["was", "top", "pRet", "visits", "retainedSteps", "lastGain", "lastRegression", "strategy", "sourceState", "implementationState"]) {
    assert.equal(row[field], null, field);
  }
  assert.deepEqual(row.prerequisites, []);
  assert.deepEqual(row.sourceRefs, ["source:B.AND"]);
});

test("production School query binds exact current or historical context and paginates without fixture fallback", async () => {
  const live = capabilityQuery({ runId: "run-7", generation: 7, mode: "LIVE" });
  assert.equal(live.mode, "current");
  assert.equal(live.run_id, "run-7");
  assert.equal(live.generation, null);

  const historical = capabilityQuery({ runId: "run-7", generation: 6, mode: "HISTORICAL" });
  assert.equal(historical.mode, "historical");
  assert.equal(historical.generation, 6);

  const requests = [];
  const api = {
    async query(request) {
      requests.push(request);
      const second = request.cursor === "next";
      return {
        accepted: true,
        state: "PRESENT",
        coverage: "COMPLETE",
        records: [capability(second ? "B.OR" : "B.AND")],
        next_cursor: second ? null : "next",
      };
    },
  };
  const result = await loadSchoolRows(api, { runId: "run-7", generation: 7, mode: "LIVE" });
  assert.deepEqual(result.rows.map((row) => row.id), ["B.AND", "B.OR"]);
  assert.equal(requests.length, 2);
  assert.equal(requests[1].cursor, "next");

  const rejected = await loadSchoolRows({
    async query() {
      return { accepted: false, state: "DENIED", coverage: "UNKNOWN", records: [] };
    },
  }, { runId: "run-7", generation: 7, mode: "LIVE" });
  assert.equal(rejected.state, "DENIED");
  assert.deepEqual(rejected.rows, []);
});

test("production School modules have no static fixture import", () => {
  const schoolView = fs.readFileSync(path.join(rendererRoot, "school", "school-view.mjs"), "utf8");
  const schoolController = fs.readFileSync(path.join(rendererRoot, "school", "school-domain-controller.mjs"), "utf8");
  const currentView = fs.readFileSync(path.join(rendererRoot, "foundation", "current-view.mjs"), "utf8");
  assert.doesNotMatch(schoolView, /from\s+["'][^"']*fixture/);
  assert.doesNotMatch(schoolController, /from\s+["'][^"']*fixture/);
  assert.doesNotMatch(currentView, /school-fixture|curriculum-atlas-fixture/);
  assert.match(schoolController, /await import\("\.\/school-fixture\.mjs"\)/);
  assert.match(schoolController, /await import\("\.\/curriculum-atlas-view\.mjs"\)/);
});

test("fixture launch posture is persistent and never labels the context as plain LIVE", () => {
  const elements = {
    "#shell": { dataset: {} },
    "#launch-mode-banner": {
      hidden: true,
      attributes: {},
      innerHTML: "",
      setAttribute(name, value) { this.attributes[name] = value; },
    },
    "#mode-badge": { textContent: "LIVE" },
  };
  const document = {
    documentElement: { lang: "en-US" },
    querySelector(selector) { return elements[selector] ?? null; },
  };
  renderFixtureModePosture(document);
  assert.equal(elements["#shell"].dataset.launchMode, "fixtures");
  assert.equal(elements["#launch-mode-banner"].hidden, false);
  assert.match(elements["#launch-mode-banner"].innerHTML, /Reference mode/);
  assert.equal(elements["#mode-badge"].textContent, "REFERENCE · LIVE");
  renderFixtureModePosture(document);
  assert.equal(elements["#mode-badge"].textContent, "REFERENCE · LIVE");
});
