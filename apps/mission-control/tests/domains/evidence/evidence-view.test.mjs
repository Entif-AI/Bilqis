import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { buildEvidenceRequest } from "../../../renderer/evidence/evidence-query.mjs";
import { renderEvidenceMarkup } from "../../../renderer/evidence/evidence-markup.mjs";
import { renderEvidenceView } from "../../../renderer/evidence/evidence-view.mjs";

import { EVIDENCE_MESSAGES, evidenceT } from "../../../renderer/evidence/evidence-messages.mjs";
import { createTranslator } from "../../../renderer/foundation/i18n.mjs";
import { assertUniqueTestIds } from "../../../renderer/foundation/test-hooks.mjs";

const context = Object.freeze({ mode: "LIVE", runId: "run-7", generation: 7 });

function meta(recordId) {
  return {
    record_id: recordId,
    run: {
      run_id: "run-7", generation: 7,
      run_identity_sha256: "1".repeat(64), generation_manifest_sha256: "2".repeat(64),
      candidate_identity_sha256: "3".repeat(64), factory_release_sha256: "4".repeat(64),
      semantic_release_sha256: "5".repeat(64), topology_sha256: "6".repeat(64),
    },
    materialized_at: 120, observed_at: 118, as_of: 118,
    coverage: "COMPLETE", authority: "MEASURED",
    source_refs: ["source:lesson:1"], evidence_refs: ["evidence:grader:1"],
    receipt_refs: ["receipt:source:1"],
  };
}

function page(request, {
  records = [], links = [], markers = [], state = "PRESENT", coverage = "COMPLETE",
} = {}) {
  return {
    schema: "bilqis.bamf.control-plane.query-page/v1", query_id: "a".repeat(64),
    request, family: request.family, mode: request.mode, state, coverage,
    total_matches: records.length + links.length, returned: records.length + links.length,
    truncated: false, next_cursor: null, records, markers, links, accepted: true,
  };
}

const capability = {
  schema_version: "bilqis.bamf.mission-control.capability-snapshot/v1",
  meta: meta("capability:and"), capability_id: "B.AND",
};
const receipt = {
  schema_version: "bilqis.bamf.mission-control.operator-action-receipt/v2",
  meta: meta("cp05:operation-1:completed"), request_id: "req-1",
  operation_id: "operation-1", state: "COMPLETED", acknowledged_at: 120,
  target_ref: "run:run-7", postcondition_ref: "postcondition:1", error_ref: null,
};

function container() {
  return { innerHTML: "", querySelector() { return null; }, querySelectorAll() { return []; } };
}

function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}

test("selected-object bootstrap issues one query and does not race context", async () => {
  const seen = [];
  const api = { async query(request) { seen.push(request); return page(request, { records: [capability] }); } };
  const host = container();
  renderEvidenceView(host, api, { ...context, generation: 71 }, { kind: "capability", id: "B.AND" });
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(seen.length, 1);
  assert.equal(seen[0].reference, "B.AND");
  assert.equal(seen[0].generation, 71);
});

test("older async query cannot overwrite a newer evidence identity", async () => {
  const andResult = deferred();
  const orResult = deferred();
  const api = { query(request) {
    return request.reference === "B.AND" ? andResult.promise : orResult.promise;
  } };
  const host = container();
  renderEvidenceView(host, api, { ...context, generation: 74 }, { kind: "capability", id: "B.AND" });
  renderEvidenceView(host, api, { ...context, generation: 74 }, { kind: "capability", id: "B.OR" });
  const orRecord = { ...capability, meta: meta("capability:or"), capability_id: "B.OR" };
  orResult.resolve(page(buildEvidenceRequest(context, { kind: "capability", value: "B.OR" }), { records: [orRecord] }));
  await new Promise((resolve) => setTimeout(resolve, 0));
  andResult.resolve(page(buildEvidenceRequest(context, { kind: "capability", value: "B.AND" }), { records: [capability] }));
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.ok(host.innerHTML.includes("capability:or"));
  assert.equal(host.innerHTML.includes("capability:and"), false);
  assert.ok(host.innerHTML.includes('value="B.OR"'));
});

test("rejected bootstrap clears evidence and announces query unavailability", async () => {
  const api = { async query() { return { accepted: false, reason: "QUERY_DENIED" }; } };
  const host = container();
  renderEvidenceView(host, api, { ...context, generation: 72 }, { kind: "capability", id: "B.AND" });
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.ok(host.innerHTML.includes("Query unavailable"));
  assert.ok(host.innerHTML.includes("QUERY_DENIED"));
  assert.ok(host.innerHTML.includes('role="alert"'));
  assert.equal(host.innerHTML.includes("capability:and"), false);
});

test("deep-linked exact evidence restores detail after hydration", async () => {
  const api = { async query(request) {
    if (request.family === "record") return page(request, { records: [receipt] });
    if (request.family === "links") return page(request);
    throw new Error("unexpected query");
  } };
  const host = container();
  renderEvidenceView(host, api, { ...context, generation: 73 }, { kind: "evidence", id: receipt.meta.record_id });
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.ok(host.innerHTML.includes("Exact record"));
  assert.ok(host.innerHTML.includes(receipt.meta.record_id));
  assert.ok(host.innerHTML.includes("Raw payload"));
});

test("secondary provenance hydration failure is explicit, not reported as no links", async () => {
  const api = { async query(request) {
    if (request.family === "record") return page(request, { records: [receipt] });
    if (request.family === "links") return { accepted: false, reason: "QUERY_UNAVAILABLE" };
    throw new Error("unexpected query");
  } };
  const host = container();
  renderEvidenceView(host, api, { ...context, generation: 75 }, { kind: "evidence", id: receipt.meta.record_id });
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.ok(host.innerHTML.includes("Provenance traversal unavailable"));
  assert.ok(host.innerHTML.includes("QUERY_UNAVAILABLE"));
  assert.ok(host.innerHTML.includes("Provenance traversal unavailable"));
  assert.equal(host.innerHTML.includes("No resolvable links reported."), false);
});

test("readable and raw views expose the same literal receipt values", () => {
  const request = buildEvidenceRequest(context, { kind: "record", value: receipt.meta.record_id });
  const base = {
    status: "ready", criteria: { kind: "record", value: receipt.meta.record_id },
    page: page(request, { records: [receipt] }), records: [receipt], links: [],
    selected: receipt, selectedLinks: null, error: null,
  };
  const readable = renderEvidenceMarkup({ ...base, raw: false });
  const raw = renderEvidenceMarkup({ ...base, raw: true });
  for (const literal of [
    receipt.meta.record_id, receipt.operation_id, receipt.postcondition_ref,
    receipt.meta.run.run_id, receipt.meta.run.generation_manifest_sha256,
    receipt.meta.source_refs[0],
  ]) {
    assert.ok(readable.includes(literal));
    assert.ok(raw.includes(literal));
  }
  assert.ok(readable.includes("Not separately reported"));
});

test("missing denied conflicting and partial evidence remain distinct", () => {
  const request = buildEvidenceRequest(context, { kind: "reference", value: "receipt:x" });
  const missing = renderEvidenceMarkup({
    status: "ready", criteria: { kind: "reference", value: "receipt:x" },
    page: page(request, { state: "MISSING", coverage: "UNKNOWN" }),
    records: [], links: [], selected: null, selectedLinks: null, raw: false, error: null,
  });
  assert.ok(missing.includes("State: MISSING"));
  assert.ok(missing.replaceAll("MISSING", "DENIED").includes("State: DENIED"));

  const partial = {
    schema_version: "bilqis.bamf.mission-control.partial/v1", meta: meta("partial:capability"),
    partial_record_id: "capability:and", missing_fields: ["grader_receipt", "source_revision"],
  };
  const degraded = renderEvidenceMarkup({
    status: "ready", criteria: { kind: "context", value: "" },
    page: page(request, { records: [capability], markers: [partial], state: "PARTIAL", coverage: "PARTIAL" }),
    records: [capability, { ...capability, meta: meta("capability:conflict") }],
    links: [], selected: null, selectedLinks: null, raw: false, error: null,
  });
  assert.ok(degraded.includes("grader_receipt"));
  assert.ok(degraded.includes("capability:conflict"));
  assert.ok(degraded.includes("Coverage: PARTIAL"));
});

test("query state is aria-live and memory producer absence is explicit", () => {
  const request = buildEvidenceRequest(context, { kind: "memory", value: "motif:bool-composition" });
  const markup = renderEvidenceMarkup({
    status: "ready", criteria: { kind: "memory", value: "motif:bool-composition" },
    page: page(request, { state: "EMPTY" }), records: [], links: [],
    selected: null, selectedLinks: null, raw: false, error: null,
  });
  assert.ok(markup.includes('role="status"'));
  assert.ok(markup.includes('aria-live="polite"'));
  assert.ok(markup.includes("This query returned no accepted CP03 memory record"));
  assert.equal(markup.includes("GUI10 display fixtures"), false);
});

test("Evidence keeps one route title and uses grouped shared help", () => {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const html = fs.readFileSync(path.join(here, "../../../renderer/index.html"), "utf8");
  const markup = renderEvidenceMarkup(state);
  assert.equal((html.match(/data-test-id="shell-destination-title"/g) ?? []).length, 1);
  assert.doesNotMatch(markup, /<h[12][^>]*>\s*Evidence\s*<\/h[12]>/);
  assert.doesNotMatch(markup, /role="tablist"/);
  for (const hook of [
    "evidence-help-search", "evidence-help-posture", "evidence-help-results",
    "evidence-help-provenance", "evidence-help-display", "evidence-help-origin",
    "evidence-help-traversal",
  ]) assert.ok(markup.includes(`data-test-id="${hook}"`), hook);
  assert.equal(markup.includes("About exact queries"), false);
});

test("readable Evidence renders authoritative times with shared temporal controls while raw metadata stays literal", () => {
  const readable = renderEvidenceMarkup({ ...state, selected: receipt, raw: false });
  for (const [hook, source] of [
    ["evidence-time-materialized", "120"],
    ["evidence-time-observed", "118"],
    ["evidence-time-as-of", "118"],
    ["evidence-time-field-acknowledged-at", "120"],
  ]) {
    assert.ok(readable.includes(`data-test-id="${hook}"`), hook);
    assert.ok(readable.includes(`data-source-unix-seconds="${source}"`), source);
  }
  assert.ok(readable.includes("evidence-metadata-payload"));
  assert.ok(readable.includes('&quot;materialized_at&quot;: 120'));
  const raw = renderEvidenceMarkup({ ...state, selected: receipt, raw: true });
  assert.ok(raw.includes('&quot;observed_at&quot;: 118'));
  assert.ok(raw.includes('&quot;acknowledged_at&quot;: 120'));
});

test("evidence markup exposes explicit return control when origin is retained", () => {
  const request = buildEvidenceRequest(context, { kind: "context", value: "" });
  const markup = renderEvidenceMarkup({
    status: "ready", criteria: { kind: "context", value: "" },
    page: page(request, { records: [capability] }), records: [capability], links: [],
    selected: null, selectedLinks: null, raw: false, error: null,
    traversalError: null, returnAvailable: true,
  });
  assert.ok(markup.includes("Return to origin"));
  assert.ok(markup.includes("data-evidence-return"));
});

test("forensic renderer has no direct provider filesystem process or network escape", () => {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const source = ["evidence-view.mjs", "evidence-query.mjs", "evidence-markup.mjs"]
    .map((name) => fs.readFileSync(path.join(here, "../../../renderer/evidence", name), "utf8")).join("\n");
  for (const forbidden of ["require(", "node:fs", "process.", "electron", "fetch(", "XMLHttpRequest"]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
});

test("shell inspector exposes evidence navigation beside owning-view navigation", () => {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const html = fs.readFileSync(path.join(here, "../../../renderer/index.html"), "utf8");
  assert.ok(html.includes('data-test-id="inspector-open-evidence"'));
  assert.ok(html.includes('data-test-id="inspector-open-owner"'));
});

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
