import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { createProductionLineageController } from "../../renderer/lineage/production-controller.mjs";
import {
  buildGenerationQuery,
  buildRejectedQuery,
  rejectedDecisions,
  selectGenerationRecord,
} from "../../renderer/lineage/production-query.mjs";
import { productionLineageMarkup } from "../../renderer/lineage/production-view.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "../..");
const digest = character => character.repeat(64);
const context = Object.freeze({
  runId: "run-production",
  generation: 17,
  mode: "LIVE",
  fixture: false,
});

function generationRecord() {
  return {
    schema_version: "bilqis.bamf.mission-control.generation-manifest/v1",
    meta: {
      record_id: "generation:17",
      run: {
        run_id: context.runId,
        run_identity_sha256: digest("1"),
        generation: 17,
        generation_manifest_sha256: digest("2"),
        candidate_identity_sha256: digest("3"),
        factory_release_sha256: digest("4"),
        semantic_release_sha256: digest("5"),
        topology_sha256: digest("6"),
      },
      materialized_at: 1_790_000_120,
      observed_at: 1_790_000_118,
      as_of: 1_790_000_118,
      coverage: "COMPLETE",
      authority: "MEASURED",
      source_refs: ["source:generation:17"],
      evidence_refs: ["evidence:generation:17"],
      receipt_refs: ["receipt:generation:17"],
    },
    checkpoint_sha256: digest("7"),
    student_sha256: digest("8"),
    optimizer_state_sha256: digest("9"),
    parent_manifest_sha256: digest("a"),
    status: "ACCEPTED",
  };
}

function rejectedRecord() {
  return {
    schema_version: "bilqis.bamf.mission-control.candidate-decision/v1",
    meta: {
      record_id: "candidate-decision:17",
      run: { run_id: context.runId, generation: 17 },
      materialized_at: 1_790_000_117,
      observed_at: 1_790_000_116,
    },
    candidate_id: "candidate:rejected:17",
    capability_id: "B.AND",
    outcome: "REJECTED",
    reason_code: "NO_MEASURABLE_TARGET_GAIN",
  };
}

function page(records, state = "PRESENT") {
  return { accepted: true, state, coverage: "COMPLETE", records };
}

function target() {
  return {
    innerHTML: "",
    querySelectorAll() { return []; },
    querySelector() { return null; },
  };
}

test("production Lineage queries exact CP03 run and generation identity", () => {
  assert.deepEqual(buildGenerationQuery(context), {
    schema: "bilqis.bamf.control-plane.query/v1",
    family: "generation",
    mode: "current",
    run_id: "run-production",
    record_id: null,
    schema_version: "bilqis.bamf.mission-control.generation-manifest/v1",
    generation: 17,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor: null,
    limit: 32,
  });
  assert.equal(buildRejectedQuery(context).family, "episode");
  const historical = buildGenerationQuery({ ...context, mode: "HISTORICAL" });
  assert.equal(historical.mode, "historical");
  assert.equal(historical.generation, 17);
});

test("production selection fails closed to the exact GenerationManifest context", () => {
  const exact = generationRecord();
  const other = structuredClone(exact);
  other.meta.run.generation = 16;
  other.meta.record_id = "generation:16";
  assert.equal(selectGenerationRecord(page([other, exact]), context), exact);
  assert.equal(selectGenerationRecord(page([other]), context), null);
  assert.deepEqual(rejectedDecisions(page([rejectedRecord(), exact])), [rejectedRecord()]);
});

test("production Lineage is tabbed, help-rich, temporal, and forensic by disclosure", () => {
  const record = generationRecord();
  const markup = productionLineageMarkup({
    context,
    generation: record,
    generationState: "PRESENT",
    rejected: [rejectedRecord()],
  });
  assert.equal((markup.match(/role="tablist"/g) ?? []).length, 1);
  for (const id of ["generations", "selected", "comparison", "rejected"]) {
    assert.match(markup, new RegExp('data-test-id="lineage-production-tab-' + id + '"'));
  }
  for (const id of ["accepted", "transition", "custody", "comparison", "rejected", "historical"]) {
    assert.match(markup, new RegExp('data-test-id="lineage-help-' + id + '-trigger"'));
  }
  for (const id of ["observed", "materialized", "as-of"]) {
    assert.match(markup, new RegExp('data-test-id="lineage-production-time-' + id + '"'));
  }
  assert.match(markup, /data-test-id="lineage-production-identities"/);
  assert.match(markup, /222222222…222222222/);
  assert.match(markup, new RegExp(digest("2")));
  assert.match(markup, /candidate:rejected:17/);
  assert.doesNotMatch(markup, /FIXTURE|fixture-lineage-run|4424[0-9]/);
});

test("historical production Lineage keeps exact missing state instead of fixture fallback", () => {
  const markup = productionLineageMarkup({
    context: { ...context, mode: "HISTORICAL", generation: 99 },
    generation: null,
    generationState: "MISSING",
  });
  assert.match(markup, /No exact GenerationManifest was returned for historical generation 99/);
  assert.doesNotMatch(markup, /FIXTURE|fixture-lineage-run/);
});

test("production controller uses CP03 only and never falls back to retained fixtures", async () => {
  const calls = [];
  const record = generationRecord();
  const api = {
    async query(request) {
      calls.push(request);
      return request.family === "generation"
        ? page([record])
        : page([rejectedRecord()]);
    },
  };
  const host = target();
  const controller = createProductionLineageController(api);
  await controller.activate(context, { target: host, onInspect() {} });
  assert.deepEqual(calls.map(call => call.family), ["generation", "episode"]);
  assert.match(host.innerHTML, /run-production|Generation 17/);
  assert.doesNotMatch(host.innerHTML, /FIXTURE|fixture-lineage-run/);

  const failed = target();
  const unavailable = createProductionLineageController({
    async query() { throw new Error("CONTROL_PLANE_UNAVAILABLE"); },
  });
  await unavailable.activate(context, { target: failed, onInspect() {} });
  assert.match(failed.innerHTML, /Generation projection unavailable/);
  assert.doesNotMatch(failed.innerHTML, /FIXTURE|fixture-lineage-run/);
});

test("production launch cannot import Lineage fixtures or infer wall clock from generation", () => {
  const renderer = fs.readFileSync(path.join(appRoot, "renderer/renderer.mjs"), "utf8");
  const fixtureSupport = fs.readFileSync(path.join(appRoot, "renderer/fixture-support.mjs"), "utf8");
  const controller = fs.readFileSync(
    path.join(appRoot, "renderer/lineage/production-controller.mjs"), "utf8",
  );
  const view = fs.readFileSync(
    path.join(appRoot, "renderer/lineage/production-view.mjs"), "utf8",
  );
  const packageJson = JSON.parse(fs.readFileSync(path.resolve(appRoot, "../../package.json"), "utf8"));
  assert.match(renderer, /launchMode === "fixtures"[\s\S]*import\("\.\/fixture-support\.mjs"\)/);
  assert.match(fixtureSupport, /lineage\/lineage-view\.mjs/);
  assert.doesNotMatch(controller + view, /lineage-fixture|fixture-lineage-run|LINEAGE_FIXTURE/);
  assert.doesNotMatch(view, /new Date\([^)]*generation|generation\s*\*\s*1000/);
  assert.ok(packageJson.scripts.bamf);
  assert.ok(packageJson.scripts["bamf:fixtures"]);
  assert.notEqual(
    packageJson.scripts.bamf,
    packageJson.scripts["bamf:fixtures"],
  );
});
