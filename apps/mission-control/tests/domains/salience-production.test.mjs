import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  loadSalienceSnapshot,
  salienceEventFromRecord,
  salienceQuery,
} from "../../renderer/salience/salience-live.mjs";
import { productionSalienceMarkup } from "../../renderer/salience/salience-production-view.mjs";
import { assertUniqueTestIds, collectTestIds } from "../../renderer/foundation/test-hooks.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../../renderer");

function datum(value, origin, units = "ordinal") {
  return { state: "PRESENT", origin, value, units };
}

function record(id = "salience-record:live:1", observedAt = 1_800_000_000) {
  return {
    schema_version: "bilqis.bamf.mission-control.salience-event/v1",
    meta: {
      record_id: id,
      materialized_at: observedAt + 4,
      observed_at: observedAt,
      as_of: observedAt,
      coverage: "COMPLETE",
      authority: "MEASURED",
      source_refs: ["source:salience:live"],
      evidence_refs: ["evidence:salience:live"],
      receipt_refs: ["receipt:salience:live"],
    },
    salience_id: "salience:live:1",
    capability_id: "B.AND",
    impact: datum("HIGH", "SOURCE_AUTHORITATIVE"),
    exigency: datum("MODERATE", "DERIVED"),
    novelty: datum("LOW", "INFERRED"),
    action_kind: "TEACHING",
  };
}

test("production salience query binds current and historical context exactly", () => {
  const current = salienceQuery({ runId: "bamf-live", mode: "LIVE", generation: 9 });
  assert.equal(current.family, "salience");
  assert.equal(current.mode, "current");
  assert.equal(current.run_id, "bamf-live");
  assert.equal(current.generation, null);

  const historical = salienceQuery({ runId: "bamf-live", mode: "HISTORICAL", generation: 8 });
  assert.equal(historical.mode, "historical");
  assert.equal(historical.generation, 8);
  assert.equal(historical.schema_version, "bilqis.bamf.mission-control.salience-event/v1");
});

test("production salience record keeps authority, times, and evidence references literal", () => {
  const event = salienceEventFromRecord(record());
  assert.equal(event.recordId, "salience-record:live:1");
  assert.equal(event.observedAt, 1_800_000_000);
  assert.equal(event.materializedAt, 1_800_000_004);
  assert.equal(event.authority, "MEASURED");
  assert.equal(event.axes.impact.value, "HIGH");
  assert.equal(event.axes.impact.origin, "SOURCE_AUTHORITATIVE");
  assert.equal(event.axes.exigency.origin, "DERIVED");
  assert.equal(event.axes.novelty.origin, "INFERRED");
  assert.deepEqual(event.sourceRefs, ["source:salience:live"]);
  assert.deepEqual(event.evidenceRefs, ["evidence:salience:live"]);
  assert.deepEqual(event.receiptRefs, ["receipt:salience:live"]);
  assert.equal(event.effectiveAt, null);
});

test("production salience loader paginates and preserves the selected generation contract", async () => {
  const requests = [];
  const pages = [
    { accepted: true, state: "PRESENT", coverage: "PARTIAL", records: [record("salience-record:live:1", 20)], next_cursor: "next" },
    { accepted: true, state: "PRESENT", coverage: "COMPLETE", records: [record("salience-record:live:2", 10)], next_cursor: null },
  ];
  const api = { query: async (request) => { requests.push(request); return pages.shift(); } };
  const result = await loadSalienceSnapshot(api, { runId: "bamf-live", mode: "HISTORICAL", generation: 8 });
  assert.equal(requests.length, 2);
  assert.equal(requests[0].generation, 8);
  assert.equal(requests[1].cursor, "next");
  assert.deepEqual(result.events.map((event) => event.recordId), ["salience-record:live:2", "salience-record:live:1"]);
  assert.equal(result.coverage, "COMPLETE");
});

test("production observations use one top-level tab layer with contextual help and shared time", () => {
  const event = salienceEventFromRecord(record());
  const model = { state: "PRESENT", coverage: "COMPLETE", events: [event] };
  const markup = productionSalienceMarkup(model, {
    activeTab: "observations",
    selectedId: event.recordId,
    context: { mode: "LIVE", generation: 9 },
    temporal: { nowMs: 1_800_000_010_000 },
  });
  assert.equal(assertUniqueTestIds(markup), true);
  const ids = new Set(collectTestIds(markup));
  for (const id of [
    "salience-tabs", "salience-tab-observations", "salience-tab-aggregation", "salience-tab-routing",
    "salience-help-concept", "salience-help-elsewhere", "salience-help-snapshot", "salience-help-ordinal",
    "salience-help-axis-impact", "salience-help-axis-exigency", "salience-help-axis-novelty",
    "salience-observation-table",
  ]) assert.equal(ids.has(id), true, id);
  assert.match(markup, /aria-selected="true"[\s\S]*>Observations<\/button>/);
  assert.match(markup, /data-selected="true"/);
  assert.match(markup, /data-source-unix-seconds="1800000000"/);
  assert.match(markup, /Exact UTC:/);
  assert.match(markup, /Source-authoritative/);
  assert.match(markup, /Derived/);
  assert.match(markup, /Inferred/);
});

test("production aggregation and routing tabs state the contract boundary without fixture substitution", () => {
  const model = { state: "PRESENT", coverage: "COMPLETE", events: [salienceEventFromRecord(record())] };
  const aggregation = productionSalienceMarkup(model, { activeTab: "aggregation", context: { mode: "HISTORICAL", generation: 8 } });
  const routing = productionSalienceMarkup(model, { activeTab: "routing", context: { mode: "HISTORICAL", generation: 8 } });
  assert.match(aggregation, /Aggregation detail unavailable/);
  assert.match(aggregation, /salience-help-aggregation/);
  assert.match(routing, /Routing detail unavailable/);
  assert.match(routing, /salience-help-routing/);
  for (const markup of [aggregation, routing]) {
    assert.doesNotMatch(markup, /fixture:/i);
    assert.doesNotMatch(markup, /cluster:fixture|routing:fixture|pattern:fixture/);
  }
});

test("production salience dependency graph has no fixture import", () => {
  for (const name of ["salience-controller.mjs", "salience-live.mjs", "salience-production-view.mjs", "salience-tabs.mjs"]) {
    const source = fs.readFileSync(path.join(rendererRoot, "salience", name), "utf8");
    assert.doesNotMatch(source, /salience-fixture|events-fixture/);
  }
});
