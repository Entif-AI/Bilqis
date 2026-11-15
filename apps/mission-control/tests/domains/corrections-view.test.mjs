import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { CORRECTION_FIXTURE, CORRECTION_FIXTURE_SUPPORT } from "../../renderer/corrections/corrections-fixture.mjs";
import {
  assertReceiptBackedTerminalStates, correctionQuery, evidencedDescendants, historyFor,
  impactRows, productionProjectionFromPage, requalificationQueue, unknownInfluenceRows,
} from "../../renderer/corrections/corrections-model.mjs";
import { CORRECTION_TABS, renderCorrectionsMarkup } from "../../renderer/corrections/corrections-view.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../../..");
const fixture = CORRECTION_FIXTURE;

test("impact closure includes only explicit evidenced descendants", () => {
  const ids = new Set(evidencedDescendants(fixture).map(node => node.id));
  assert.equal(ids.has(fixture.correction.currentRevision), true);
  for (const excluded of fixture.nonDescendants) assert.equal(ids.has(excluded), false, excluded);
  for (const edge of fixture.edges) {
    assert.equal(ids.has(edge.from), true, edge.from);
    assert.equal(ids.has(edge.to), true, edge.to);
  }
});

test("correction state distinctions remain explicit", () => {
  const states = new Set([...impactRows(fixture).map(row => row.state), ...fixture.history.flatMap(entry => Object.values(entry.states))]);
  for (const state of ["KNOWN_EXPOSURE", "INVALIDATED", "REQUALIFICATION_REQUIRED", "REQUALIFIED", "UNAVAILABLE_UNKNOWN"]) {
    assert.equal(states.has(state), true, state);
  }
});

test("requalification queue retains exact custody and receipts", () => {
  const completed = requalificationQueue(fixture).find(task => task.status === "REQUALIFIED");
  assert.equal(completed.sourceRevision, fixture.correction.currentRevision);
  assert.equal(completed.generation, 44_238);
  assert.match(completed.checkpoint, /^[0-9a-f]{64}$/);
  assert.ok(completed.implicatedRefs.includes("capability:C.SUCCESSOR"));
  assert.ok(completed.receiptRefs.length >= 2);
});

test("append-only fixture history preserves correction then requalification", () => {
  const history = historyFor(fixture, "capability:C.SUCCESSOR");
  assert.deepEqual(history.map(entry => entry.state), ["REQUALIFICATION_REQUIRED", "REQUALIFIED"]);
  assert.notEqual(history[0].receipt, history[1].receipt);
  assert.ok(history[0].generation < history[1].generation);
});

test("unknown downstream influence stays explicit", () => {
  assert.deepEqual(unknownInfluenceRows(fixture).map(row => row.id), ["neural-influence:untracked:44238"]);
  assert.equal(unknownInfluenceRows(fixture)[0].evidenceRefs.length, 0);
});

test("receipt-backed terminal states remain guarded", () => {
  assert.equal(assertReceiptBackedTerminalStates(fixture), true);
});

test("Corrections renders one four-tab hierarchy with contextual help", async () => {
  const { assertUniqueTestIds } = await import("../../renderer/foundation/test-hooks.mjs");
  const markup = renderCorrectionsMarkup(fixture, {
    messages: CORRECTION_FIXTURE_SUPPORT.messages,
    fixtureNotice: CORRECTION_FIXTURE_SUPPORT.notice,
  });
  assertUniqueTestIds(markup);
  assert.equal((markup.match(/role="tablist"/g) ?? []).length, 1);
  assert.equal((markup.match(/role="tab"/g) ?? []).length, 4);
  for (const tab of CORRECTION_TABS) assert.match(markup, new RegExp(`data-test-id="corrections-tab-${tab}"`));
  assert.ok((markup.match(/ui-context-help__trigger/g) ?? []).length >= 7);
  assert.match(markup, /REFERENCE FIXTURES/);
  assert.doesNotMatch(markup, /perfect neural unlearning|not proof|cannot perform/i);
});

test("generation-only reference history does not invent wall-clock timestamps", () => {
  const markup = renderCorrectionsMarkup(fixture, { messages: CORRECTION_FIXTURE_SUPPORT.messages });
  assert.match(markup, /Generation 44238/);
  assert.doesNotMatch(markup, /data-test-id="corrections-context-time"/);
});

test("production correction query is mode-bound and source timestamps render truthfully", () => {
  const context = { runId: "run:real", generation: 9, mode: "HISTORICAL", fixture: false };
  const query = correctionQuery(context);
  assert.equal(query.mode, "historical");
  assert.equal(query.generation, 9);
  assert.equal(query.run_id, "run:real");
  const record = {
    schema_version: "bilqis.bamf.mission-control.correction-event/v1",
    meta: {
      record_id: "correction-record:9", run: { run_id: "run:real", generation: 9 },
      observed_at: 1_799_000_200, source_refs: ["source:r9"], receipt_refs: ["receipt:r9"],
    },
    correction_id: "correction:9", correction_generation: 12, target_ref: "source:numeric",
    old_digest: "8".repeat(64), new_digest: "9".repeat(64), state: "REQUALIFICATION_REQUIRED",
  };
  const projection = productionProjectionFromPage({ accepted: true, state: "PRESENT", records: [record] }, context);
  assert.equal(projection.posture, "historical");
  assert.equal(projection.correction.observedAt, 1_799_000_200);
  const markup = renderCorrectionsMarkup(projection);
  assert.match(markup, /data-source-unix-seconds="1799000200"/);
  assert.match(markup, /HISTORICAL/);
});

test("production projection never backfills fixture impact or queue", () => {
  const projection = productionProjectionFromPage(
    { accepted: true, state: "EMPTY", records: [] },
    { runId: "run:real", mode: "LIVE", fixture: false },
  );
  assert.equal(projection.correction, null);
  assert.deepEqual(projection.nodes, []);
  assert.deepEqual(projection.queue, []);
  const markup = renderCorrectionsMarkup(projection);
  assert.doesNotMatch(markup, /fixture|44238|numeric-source-r8-r9/i);
  assert.match(markup, /Correction detail unavailable/);
});

test("production Corrections modules have no fixture dependency", () => {
  const files = ["corrections-controller.mjs", "corrections-model.mjs", "corrections-view.mjs", "corrections-messages.mjs"];
  const source = files.map(name => fs.readFileSync(path.join(repoRoot, "apps/mission-control/renderer/corrections", name), "utf8")).join("\n");
  assert.doesNotMatch(source, /corrections-fixture|CORRECTION_FIXTURE/);
});

test("fixture remains grounded in executable correction and CP03 contracts", () => {
  const runtimeEvidence = fs.readFileSync(path.join(repoRoot, "bilqis_mlx/runtime/_correction/atlas_revalidation_evidence.py"), "utf8");
  const querySupport = fs.readFileSync(path.join(repoRoot, "bilqis_mlx/mission_control/query_support.py"), "utf8");
  assert.match(runtimeEvidence, /class CorrectionEvent/);
  assert.match(querySupport, /QueryFamily\.CORRECTION: \(CorrectionEvent,\)/);
});
