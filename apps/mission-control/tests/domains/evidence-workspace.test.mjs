import test from "node:test";
import assert from "node:assert/strict";
import { renderEvidenceMarkup } from "../../renderer/evidence/evidence-markup.mjs";
import { EVIDENCE_MESSAGES, evidenceT } from "../../renderer/evidence/evidence-messages.mjs";
import { createTranslator } from "../../renderer/foundation/i18n.mjs";
import { assertUniqueTestIds } from "../../renderer/foundation/test-hooks.mjs";

const record = { schema_version: "receipt/v1", meta: {
  record_id: "receipt:<exact>", authority: "MEASURED", coverage: "COMPLETE",
  run: { run_id: "run:7", generation: 7 }, source_refs: ["source:<literal>", "source:<literal>"],
  evidence_refs: [], receipt_refs: ["receipt:7"], as_of: 7,
}, answer: false, omitted: null, nested: { value: "x".repeat(180) }, attack: '<img src=x onerror="throw 1">' };
const link = { relation: "supports", source_record_id: "receipt:<exact>", target_ref: "source:<literal>", target_record_id: "source:7" };
const state = { status: "ready", criteria: { kind: "record", value: record.meta.record_id },
  records: [record, record], links: [link, link], selected: record,
  selectedLinks: { state: "PARTIAL", coverage: "PARTIAL", links: [link, link], markers: [], returned: 2, total_matches: 9, truncated: true },
  page: { state: "PARTIAL", coverage: "PARTIAL", markers: [], returned: 4, total_matches: 30, truncated: true, next_cursor: "page:2" },
  returnAvailable: true, origin: { view: "capability", selected: {kind: "capability", id: "B.AND"}, context: {runId: "run:7", generation: 7, mode: "HISTORICAL"} },
};

test("workspace has unique stable hooks even with repeated exact identities", () => {
  const markup = renderEvidenceMarkup(state);
  assertUniqueTestIds(markup);
  for (const hook of ["evidence-query-form", "evidence-query-kind", "evidence-query-value", "evidence-query-submit", "evidence-query-status", "evidence-results-heading", "evidence-detail", "evidence-mode-readable", "evidence-mode-raw", "evidence-more", "evidence-return"]) {
    assert.ok(markup.includes(`data-test-id="${hook}"`), hook);
  }
  assert.match(markup, /aria-pressed="true"/);
  assert.doesNotMatch(markup, /ui-glossary/);
});

test("readable and raw preserve literal false, null, metadata and escaped payload", () => {
  for (const raw of [false, true]) {
    const markup = renderEvidenceMarkup({ ...state, raw });
    for (const literal of ["false", "null", "source:&lt;literal&gt;", "x".repeat(180)]) assert.ok(markup.includes(literal));
    assert.doesNotMatch(markup, /<img/);
    assert.ok(markup.includes("&lt;img"));
  }
});

test("provenance groups, bounded selected links and exact origin remain visible", () => {
  const markup = renderEvidenceMarkup(state);
  for (const text of ["Source", "Evidence", "Receipt", "B.AND", "capability", "Truncated", "2 returned / 9 exact matches"]) assert.ok(markup.includes(text), text);
  assert.match(markup, /data-test-id="evidence-selected-links-status"/);
});

test("loading, failure, empty and absent selection are truthful distinct states", () => {
  const loading = renderEvidenceMarkup({ ...state, status: "loading" });
  assert.match(loading, /data-test-id="evidence-more"[^>]*disabled/);
  const pending = renderEvidenceMarkup({ ...state, selectedLinks: null });
  assert.ok(pending.includes(evidenceT("evidence.links.loading")));
  assert.equal(pending.includes(evidenceT("evidence.links.empty")), false);
  const error = renderEvidenceMarkup({ ...state, traversalError: "QUERY_DENIED" });
  assert.ok(error.includes("QUERY_DENIED"));
  assert.ok(error.includes(evidenceT("evidence.links.failure")));
  const empty = renderEvidenceMarkup({ ...state, records: [], links: [], selected: null });
  assert.ok(empty.includes(evidenceT("evidence.selection.empty")));
});

test("all UI copy accepts a supplied translator with explicit parameters", () => {
  const messages = Object.fromEntries(Object.entries(EVIDENCE_MESSAGES["en-US"]).map(([key, value]) => [key, `⟪${value} translated expansion⟫`]));
  const translate = createTranslator({locale: "test", messages: {test: messages}});
  const markup = renderEvidenceMarkup(state, translate);
  assert.ok(markup.includes("⟪Source translated expansion⟫"));
  assert.ok(markup.includes("receipt:&lt;exact&gt;"));
  assert.doesNotMatch(markup, /I18N_|undefined/);
});
