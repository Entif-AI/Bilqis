import test from "node:test";
import assert from "node:assert/strict";
import { buildQuery, chooseDossier, historyEntries } from "../renderer/capability/model.mjs";
import { DossierController } from "../renderer/capability/controller.mjs";
import { renderDossier, renderEvidence } from "../renderer/capability/view.mjs";
import { assertUniqueTestIds, collectTestIds } from "../renderer/foundation/test-hooks.mjs";
const lens = { runId: "fixture:gui05", generation: 3, mode: "HISTORICAL" };
const row = { schema_version: "bilqis.bamf.mission-control.capability-dossier/v1",
  capability_id: "B.AND", name: "Conjunction", meta: { run: { run_id: lens.runId, generation: 3 } },
  entries: [{ entry_id: "recover", section: "history", generation: 3, observed_at: 30 },
    { entry_id: "regress", section: "history", generation: 2, observed_at: 20 }] };
const page = (records = [row], next_cursor = null) => ({ records, markers: [], links: [], state: "PRESENT",
  coverage: "COMPLETE", next_cursor, truncated: next_cursor !== null });
test("exact generation and schema bind every dossier request", () => {
  assert.deepEqual(buildQuery(lens), { schema: "bilqis.bamf.control-plane.query/v1", family: "capability",
    mode: "historical", run_id: "fixture:gui05", generation: 3,
    schema_version: row.schema_version, record_id: null, frontier_id: null,
    as_of: null, reference: null, cursor: null, limit: 8 });
  assert.equal(chooseDossier([row], lens, "B.AND"), row);
  assert.equal(chooseDossier([row], { ...lens, generation: 2 }, "B.AND"), null);
  assert.throws(() => chooseDossier([row, row], lens, "B.AND"), /AMBIGUOUS/);
  assert.deepEqual(historyEntries(row).map((e) => e.entry_id), ["regress", "recover"]);
});
test("pagination accumulates only within one lens; absence remains partial", async () => {
  const calls = [];
  const controller = new DossierController(async (q) => { calls.push(q); return calls.length === 1 ? page([], "next") : page(); });
  await controller.load(lens, "B.AND");
  assert.equal(controller.state.status, "PARTIAL");
  await controller.more();
  assert.equal(controller.state.dossier, row);
  assert.equal(calls[1].cursor, "next");
});
test("late responses cannot replace a newly selected generation", async () => {
  const pending = [];
  const controller = new DossierController((q) => new Promise((resolve) => pending.push({ q, resolve })));
  const first = controller.load(lens, "B.AND");
  const second = controller.load({ ...lens, generation: 2 }, "B.AND");
  pending[1].resolve(page([])); await second;
  pending[0].resolve(page()); await first;
  assert.equal(controller.state.dossier, null);
  assert.equal(controller.state.lens.generation, 2);
});
test("query failures clear data rather than preserve misleading state", async () => {
  const controller = new DossierController(async () => { throw new Error("stale cursor"); });
  await controller.load(lens, "B.AND");
  assert.equal(controller.state.status, "UNAVAILABLE");
  assert.equal(controller.state.dossier, null);
});
test("dossier uses literal facts, escaping and separate chronology", () => {
  const metric = (value) => ({ value, state: "PRESENT", origin: "MEASURED", units: null });
  const full = { ...row, now: metric(8), top: metric(9), total: metric(12), debt: metric(4),
    retention: metric("watch"), eligibility: metric("eligible"), qualification: metric("qualified"),
    source_state: metric("held"), name: '<img src=x onerror="x">', entries: row.entries.map((e) => ({
      ...e, kind: e.entry_id, label: e.entry_id, refs: ["exact:evidence"], values: [], related_id: null,
    })) };
  const html = renderDossier({ dossier: full, status: "PRESENT", lens, cursor: null, markers: [], fixture: true });
  assert.match(html, /&lt;img/); assert.doesNotMatch(html, /<img/);
  assert.match(html, /regress/); assert.match(html, /recover/); assert.match(html, /exact:evidence/);
});

test("projection availability remains literal and never implies healthy data", async () => {
  for (const status of ["DENIED", "PARTIAL", "STALE", "UNKNOWN", "EMPTY", "UNAVAILABLE"]) {
    const controller = new DossierController(async () => ({ ...page([]), state: status }));
    await controller.load(lens, "B.AND");
    assert.equal(controller.state.status, status);
    assert.equal(controller.state.dossier, null);
  }
});

test("fixture evidence comes from exact CP03 pages and preserves chronology", async () => {
  const { fixtureQuery } = await import("../renderer/capability/fixture.mjs");
  const later = await fixtureQuery(buildQuery(lens));
  const earlier = await fixtureQuery(buildQuery({ ...lens, generation: 1 }));
  const current = chooseDossier(later.records, lens, "B.AND");
  assert.equal(current.now.value, 10);
  assert.equal(earlier.records[0].now.value, 9);
  assert.deepEqual(historyEntries(current).slice(0, 3).map((entry) => entry.kind), ["gain", "regression", "recovery"]);
  const ref = "evidence:B.AND:protected:3";
  const links = await fixtureQuery(buildQuery(lens, { family: "reference", reference: ref, schema_version: null }));
  assert.equal(links.links[0].target_record_id, ref);
  const scores = await fixtureQuery(buildQuery(lens, { record_id: ref, schema_version: null }));
  assert.equal(scores.records[0].score_correct.value, 11);
  assert.equal(scores.records[0].meta.run.generation, 3);
});

test("absent dossier still shows literal projection markers", () => {
  const html = renderDossier({ dossier: null, lens, status: "DENIED", markers: [{ reason: "EXACT_REASON" }] });
  assert.match(html, /EXACT_REASON/);
});

test("redesigned dossier uses stable semantic hooks and keeps the no-causality boundary visible", async () => {
  const { fixtureQuery } = await import("../renderer/capability/fixture.mjs");
  const result = await fixtureQuery(buildQuery(lens));
  const dossier = chooseDossier(result.records, lens, "B.AND");
  const html = renderDossier({ dossier, lens, status: result.state, coverage: result.coverage, markers: [], fixture: true });
  assert.equal(assertUniqueTestIds(html), true);
  const ids = new Set(collectTestIds(html));
  for (const id of [
    "capability-document", "capability-heading", "capability-name", "capability-identity",
    "capability-metrics", "capability-metric-now", "capability-metric-top",
    "capability-section-performance", "capability-section-teaching", "capability-section-sources",
    "capability-section-dependencies", "capability-section-history",
    "capability-provenance",
  ]) assert.equal(ids.has(id), true, id);
  assert.match(html, /Measured chronology and declared evidence only/);
  assert.match(html, /does not infer causes/);
  assert.match(html, /10\/12/);
});

test("inline evidence is bounded, uniquely hooked, and offers the full Evidence route", () => {
  const entry = { entry_id: "entry:1", section: "performance", refs: ["evidence:1"] };
  const pageWithEvidence = {
    state: "PRESENT",
    links: [{ relation: "EVIDENCE", target_ref: "evidence:1", target_record_id: "record:1" }],
    records: [{ schema_version: "test/v1", meta: { record_id: "record:1" }, exact: "literal" }],
  };
  const html = renderEvidence("evidence:1", entry, pageWithEvidence);
  assert.equal(assertUniqueTestIds(html), true);
  for (const id of ["capability-evidence-detail", "capability-evidence-heading", "capability-evidence-open",
    "capability-evidence-link-0", "capability-evidence-inspect-0", "capability-evidence-record-0"]) {
    assert.match(html, new RegExp(`data-test-id="${id}"`), id);
  }
  assert.match(html, /Open in Evidence/);
  assert.match(html, /<details[^>]*data-test-id="capability-evidence-entry"/);
});
