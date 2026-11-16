import test from "node:test";
import assert from "node:assert/strict";

import { activateDomainViews } from "../../../renderer/foundation/domain-controller.mjs";
import { renderEvidenceMarkup } from "../../../renderer/evidence/evidence-markup.mjs";
import {
  prepareEvidenceSearch,
  renderEvidenceView,
} from "../../../renderer/evidence/evidence-view.mjs";

const context = Object.freeze({ mode: "LIVE", runId: "run-7", generation: 901 });

function meta(recordId) {
  return {
    record_id: recordId,
    run: { run_id: "run-7", generation: 901 },
    materialized_at: 120,
    observed_at: 118,
    as_of: 118,
    coverage: "COMPLETE",
    authority: "MEASURED",
    source_refs: [],
    evidence_refs: [],
    receipt_refs: [],
  };
}

const capability = Object.freeze({
  schema_version: "bilqis.bamf.mission-control.capability-snapshot/v1",
  meta: meta("capability:and"),
  capability_id: "B.AND",
});

function page(request, records = []) {
  return {
    schema: "bilqis.bamf.control-plane.query-page/v1",
    query_id: "a".repeat(64),
    request,
    family: request.family,
    mode: request.mode,
    state: "PRESENT",
    coverage: "COMPLETE",
    total_matches: records.length,
    returned: records.length,
    truncated: false,
    next_cursor: null,
    records,
    markers: [],
    links: [],
    accepted: true,
  };
}

function host() {
  return {
    innerHTML: "",
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
}

function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}

test("new exact search clears prior evidence before showing the loading criterion", () => {
  const oldState = {
    status: "ready",
    criteria: { kind: "capability", value: "B.AND" },
    page: page({ family: "record", mode: "current" }, [capability]),
    records: [capability],
    links: [],
    selected: capability,
    selectedLinks: null,
    raw: false,
    error: null,
    traversalError: null,
    returnAvailable: false,
  };
  const next = prepareEvidenceSearch(
    oldState, { kind: "capability", value: "B.OR" }, false,
  );
  const markup = renderEvidenceMarkup(next);
  assert.deepEqual(next.records, []);
  assert.equal(next.page, null);
  assert.ok(markup.includes("Loading"));
  assert.ok(markup.includes("Awaiting bounded evidence page"));
  assert.ok(markup.includes('value="B.OR"'));
  assert.equal(markup.includes("capability:and"), false);
});

test("leaving Evidence invalidates pending work before another domain reuses the host", async () => {
  const pending = deferred();
  let request;
  const api = {
    query(value) {
      request = value;
      return pending.promise;
    },
  };
  const container = host();
  renderEvidenceView(
    container, api, context, { kind: "capability", id: "B.AND" },
  );
  activateDomainViews({
    state: { view: "school", context },
    getState: () => ({ view: "school", context }),
    defense: {},
    api,
    homeController: { deactivate() {} },
    onInspect() {},
  });
  container.innerHTML = "OWNER SENTINEL";
  pending.resolve(page(request, [capability]));
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(container.innerHTML, "OWNER SENTINEL");
});

test("pagination preserves the selected record traversal failure until a retry", () => {
  const next = prepareEvidenceSearch({selected: capability, selectedLinks: null,
    traversalError: "QUERY_DENIED", records: [capability], links: []}, {kind:"context",value:""}, true);
  assert.equal(next.traversalError, "QUERY_DENIED");
});
