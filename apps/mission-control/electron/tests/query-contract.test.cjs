"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { validateQuery, validatePage } = require("../query-contract.cjs");
const request = () => ({ schema: "bilqis.bamf.control-plane.query/v1", family: "capability",
  mode: "historical", run_id: "fixture:gui05", record_id: null, schema_version: null,
  generation: 3, frontier_id: null, as_of: null, reference: null, cursor: null, limit: 8 });
test("CP03 request enforces exact identities, fields and bounded paging", () => {
  assert.deepEqual(validateQuery(request()), request());
  for (const delta of [{ generation: -1 }, { generation: null }, { limit: 33 },
    { family: "source" }, { run_id: "latest" }, { path: "/tmp/run" },
    { family: "reference", reference: null }]) {
    assert.throws(() => validateQuery({ ...request(), ...delta }));
  }
});
test("CP03 public pages preserve state and reject transport/session data", () => {
  const page = { schema: "bilqis.bamf.control-plane.query-page/v1", query_id: "a".repeat(64),
    request: request(), family: "capability", mode: "historical", state: "MISSING",
    coverage: "COMPLETE", total_matches: 0, returned: 0, truncated: false,
    next_cursor: null, records: [], markers: [], links: [] };
  assert.deepEqual(validatePage(page), page);
  assert.throws(() => validatePage({ ...page, session: {} }));
  assert.throws(() => validatePage({ ...page, returned: 1 }));
});

test("public page validation rejects malformed CP02 records", () => {
  const q = request();
  const page = { schema: "bilqis.bamf.control-plane.query-page/v1", query_id: "a".repeat(64),
    request: q, family: q.family, mode: q.mode, state: "PRESENT", coverage: "COMPLETE",
    total_matches: 1, returned: 1, truncated: false, next_cursor: null,
    records: [{schema_version: "bilqis.bamf.mission-control.capability-dossier/v1", meta: {record_id: "bare"}}],
    markers: [], links: [] };
  assert.throws(() => validatePage(page));
});
