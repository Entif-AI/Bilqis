import test from "node:test";
import assert from "node:assert/strict";
import { buildLearningQuery } from "../../../renderer/learning/query.mjs";
import {
  productionLearningMarkup,
  PRODUCTION_LEARNING_TABS,
} from "../../../renderer/learning/view.mjs";

const context = Object.freeze({
  runId: "accepted-run-7",
  generation: 7,
  mode: "LIVE",
  fixture: false,
});

const episode = Object.freeze({
  schema_version: "bilqis.bamf.mission-control.learning-episode/v1",
  meta: Object.freeze({
    record_id: "episode-record-7",
    authority: "DERIVED",
    coverage: "COMPLETE",
    materialized_at: 1794725520,
    observed_at: 1794725515,
    as_of: 1794725515,
    source_refs: ["source:a"],
    evidence_refs: ["evidence:a"],
    receipt_refs: ["receipt:a"],
  }),
  episode_id: "episode-7",
  capability_id: "B.AND",
  visit_id: "visit-7",
  state: "COMPLETED",
  started_at: 1794725400,
  completed_at: 1794725500,
});

const decision = Object.freeze({
  schema_version: "bilqis.bamf.mission-control.candidate-decision/v1",
  meta: Object.freeze({
    record_id: "decision-record-7",
    authority: "DERIVED",
    coverage: "COMPLETE",
    materialized_at: 1794725521,
    observed_at: 1794725516,
    as_of: 1794725516,
    source_refs: [],
    evidence_refs: ["evidence:b"],
    receipt_refs: ["receipt:b"],
  }),
  candidate_id: "candidate-7",
  capability_id: "B.AND",
  outcome: "ACCEPTED",
  reason_code: "SOURCE_GOLD_PASS",
});

test("production Learning query binds the accepted run and exact generation", () => {
  assert.deepEqual(buildLearningQuery(context), {
    schema: "bilqis.bamf.control-plane.query/v1",
    family: "episode",
    mode: "current",
    run_id: "accepted-run-7",
    record_id: null,
    schema_version: null,
    generation: 7,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor: null,
    limit: 32,
  });
});

test("production Learning has exactly four peer tabs and renders accepted temporal fields", () => {
  const markup = productionLearningMarkup({
    context,
    records: [episode, decision],
    selectedId: episode.meta.record_id,
    activeTab: "transaction",
  });
  assert.deepEqual(PRODUCTION_LEARNING_TABS.map(([id]) => id), [
    "transaction", "lifecycle", "comparison", "outcome",
  ]);
  assert.equal((markup.match(/role="tablist"/g) ?? []).length, 1);
  assert.equal((markup.match(/role="tab"/g) ?? []).length, 4);
  assert.match(markup, /data-source-unix-seconds="1794725520"/);
  assert.match(markup, /data-source-unix-seconds="1794725400"/);
  assert.match(markup, /data-source-unix-seconds="1794725500"/);
  assert.match(markup, /Current accepted run/);
  assert.doesNotMatch(markup, /fixture/i);
});

test("production Learning preserves exact selected record and candidate outcome fields", () => {
  const markup = productionLearningMarkup({
    context: { ...context, mode: "HISTORICAL" },
    records: [episode, decision],
    selectedId: decision.meta.record_id,
    activeTab: "outcome",
  });
  assert.match(markup, /decision-record-7/);
  assert.match(markup, /ACCEPTED/);
  assert.match(markup, /SOURCE_GOLD_PASS/);
  assert.match(markup, /Historical generation 7/);
  assert.match(markup, /data-learning-production-tab="outcome"[^>]*aria-selected="true"/);
});
