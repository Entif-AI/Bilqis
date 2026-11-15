import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { CORRECTION_FIXTURE } from "../../renderer/corrections/corrections-fixture.mjs";
import {
  assertReceiptBackedTerminalStates,
  evidencedDescendants,
  historyFor,
  impactRows,
  requalificationQueue,
  unknownInfluenceRows,
} from "../../renderer/corrections/corrections-model.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../../..");

test("impact closure includes only explicit evidenced descendants", () => {
  const ids = new Set(evidencedDescendants().map((node) => node.id));
  assert.equal(ids.has(CORRECTION_FIXTURE.correction.currentRevision), true);
  for (const excluded of CORRECTION_FIXTURE.nonDescendants) assert.equal(ids.has(excluded), false, excluded);
  for (const edge of CORRECTION_FIXTURE.edges) {
    assert.equal(ids.has(edge.from), true, edge.from);
    assert.equal(ids.has(edge.to), true, edge.to);
  }
});

test("known exposure invalidation requalification and unknown remain distinct states", () => {
  const states = new Set([
    ...impactRows().map((row) => row.state),
    ...CORRECTION_FIXTURE.history.flatMap((entry) => Object.values(entry.states)),
  ]);
  for (const state of ["KNOWN_EXPOSURE", "INVALIDATED", "REQUALIFICATION_REQUIRED", "REQUALIFIED", "UNAVAILABLE_UNKNOWN"]) {
    assert.equal(states.has(state), true, state);
  }
});

test("requalification queue binds exact source revision generation checkpoint and receipts", () => {
  const completed = requalificationQueue().find((task) => task.status === "REQUALIFIED");
  assert.ok(completed);
  assert.equal(completed.sourceRevision, CORRECTION_FIXTURE.correction.currentRevision);
  assert.equal(completed.generation, 44_238);
  assert.match(completed.checkpoint, /^[0-9a-f]{64}$/);
  assert.equal(completed.implicatedRefs.includes("capability:C.SUCCESSOR"), true);
  assert.equal(completed.receiptRefs.length >= 2, true);
});

test("append-only correction history preserves pre-correction state and later receipt", () => {
  const history = historyFor("capability:C.SUCCESSOR");
  assert.deepEqual(history.map((entry) => entry.state), ["REQUALIFICATION_REQUIRED", "REQUALIFIED"]);
  assert.notEqual(history[0].receipt, history[1].receipt);
  assert.equal(history[0].generation < history[1].generation, true);
});

test("untracked downstream neural influence is explicit instead of omitted", () => {
  assert.deepEqual(unknownInfluenceRows().map((row) => row.id), ["neural-influence:untracked:44238"]);
  assert.equal(unknownInfluenceRows()[0].evidenceRefs.length, 0);
});

test("graph and table share one identity-state projection", () => {
  const rows = impactRows();
  const source = fs.readFileSync(path.join(repoRoot, "apps/mission-control/renderer/corrections/corrections-view.mjs"), "utf8");
  assert.match(source, /evidencedDescendants\(\)/);
  assert.match(source, /impactRows\(\)/);
  for (const edge of CORRECTION_FIXTURE.edges) assert.equal(source.includes(edge.relation), false);
  assert.match(source, /const edges = CORRECTION_FIXTURE\.edges/);
  assert.equal(new Set(rows.map((row) => `${row.id}:${row.state}`)).size, rows.length);
});

test("requalified and recomputed UI states cannot exist without evidence receipts", () => {
  assert.equal(assertReceiptBackedTerminalStates(), true);
  for (const row of impactRows().filter((item) => ["REQUALIFIED", "RECOMPUTED"].includes(item.state))) {
    assert.equal(row.evidenceRefs.length > 0, true, row.id);
  }
});

test("GUI13 source preserves epistemic limits and contains no mutating correction controls", () => {
  const files = ["corrections-fixture.mjs", "corrections-model.mjs", "corrections-view.mjs", "corrections-messages.mjs"];
  const source = files.map((name) => fs.readFileSync(path.join(repoRoot, "apps/mission-control/renderer/corrections", name), "utf8")).join("\n").toLowerCase();
  assert.equal(source.includes("known exposure is not proof of invalidity"), true);
  assert.equal(source.includes("perfect neural unlearning"), true);
  for (const forbidden of ["apply correction now", "mark requalified", "erase learned influence", "automatic source correction"]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
});

test("fixture is grounded in executable correction and CP03 contracts", () => {
  const runtimeEvidence = fs.readFileSync(path.join(repoRoot, "bilqis_mlx/runtime/_correction/atlas_revalidation_evidence.py"), "utf8");
  const runtimeQueue = fs.readFileSync(path.join(repoRoot, "bilqis_mlx/runtime/_correction/atlas_revalidation_queue.py"), "utf8");
  const runtimeRequal = fs.readFileSync(path.join(repoRoot, "bilqis_mlx/runtime/_correction/atlas_requalification_contracts.py"), "utf8");
  const querySupport = fs.readFileSync(path.join(repoRoot, "bilqis_mlx/mission_control/query_support.py"), "utf8");
  assert.match(runtimeEvidence, /class CorrectionEvent/);
  assert.match(runtimeEvidence, /class StateTransition/);
  assert.match(runtimeQueue, /history: tuple\[StateTransition/);
  assert.match(runtimeRequal, /REQUALIFICATION_REQUIRED/);
  assert.match(querySupport, /QueryFamily\.CORRECTION: \(CorrectionEvent,\)/);
});

test("redesigned Corrections owns distinct context, impact, queue and complete history", async () => {
  const { renderCorrectionsMarkup } = await import("../../renderer/corrections/corrections-view.mjs");
  const { assertUniqueTestIds } = await import("../../renderer/foundation/test-hooks.mjs");
  const markup = renderCorrectionsMarkup();
  assertUniqueTestIds(markup);
  for (const id of ["corrections-workspace", "corrections-context", "corrections-impact", "corrections-impact-table", "corrections-graph-toggle", "corrections-queue-table", "corrections-history", "corrections-fixture-notice"]) assert.ok(markup.includes(`data-test-id="${id}"`),id);
  for (const node of evidencedDescendants()) assert.ok(markup.includes(node.id));
  for (const event of CORRECTION_FIXTURE.history) {
    assert.ok(markup.includes(event.id)); assert.ok(markup.includes(event.receipt));
    for (const id of Object.keys(event.states)) assert.ok(markup.includes(id));
  }
  assert.doesNotMatch(markup, /ui-glossary/);
  assert.match(markup, /Not requalified/);
  assert.match(markup, /Fixture projection/);
  assert.match(markup, /perfect neural unlearning/);
});

test("Corrections translation expansion preserves exact source values", async () => {
  const { renderCorrectionsMarkup } = await import("../../renderer/corrections/corrections-view.mjs");
  const { correctionsT } = await import("../../renderer/corrections/corrections-messages.mjs");
  const markup = renderCorrectionsMarkup((key,parameters)=>`Expanded wording ${correctionsT(key,parameters)}`);
  assert.match(markup, /Expanded wording/);
  assert.ok(markup.includes(CORRECTION_FIXTURE.correction.id));
  assert.ok(markup.includes(CORRECTION_FIXTURE.queue[0].checkpoint));
});

test("graph endpoints carry their own identity, kind and state", async () => {
  const { renderCorrectionsMarkup } = await import("../../renderer/corrections/corrections-view.mjs");
  const markup=renderCorrectionsMarkup();
  const endpoints=[...markup.matchAll(/data-test-id="corrections-graph-endpoint-[^"]+"[^>]*>([\s\S]*?)<\/article>/g)].map(match=>match[1]);
  assert.equal(endpoints.length,CORRECTION_FIXTURE.edges.length*2);
  for(const node of evidencedDescendants()) assert.ok(endpoints.some(endpoint=>endpoint.includes(node.id) && endpoint.includes(`>${node.kind}<`) && endpoint.includes(`data-correction-state="${node.state}"`)),node.id);
});

test("reference inspection supplies the declared reference type", async () => {
  const { renderCorrectionsView } = await import("../../renderer/corrections/corrections-view.mjs");
  const seen=[];
  const buttons=["receipt","reference"].map(kind=>({dataset:{correctionRef:`${kind}:exact`,correctionRefKind:kind},addEventListener(_event,handler){this.click=handler;}}));
  const host={innerHTML:"",querySelectorAll(selector){return selector==="[data-correction-ref]"?buttons:[];}};
  renderCorrectionsView(host,()=>{}, {onReference:(...args)=>seen.push(args)});
  buttons.forEach(button=>button.click());
  assert.deepEqual(seen,[["receipt:exact","receipt"],["reference:exact","reference"]]);
});
