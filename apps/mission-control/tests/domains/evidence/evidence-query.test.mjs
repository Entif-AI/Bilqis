import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceRequest,
  criteriaForSelection,
  loadEvidencePage,
  loadRecordById,
  loadRecordLinks,
  mergeEvidencePages,
} from "../../../renderer/evidence/evidence-query.mjs";

const context = Object.freeze({ mode: "LIVE", runId: "run-7", generation: 7 });
const historical = Object.freeze({ mode: "HISTORICAL", runId: "run-7", generation: 6 });

function meta(recordId, generation = 7) {
  return {
    record_id: recordId, run: { run_id: "run-7", generation },
    materialized_at: 120, observed_at: 118, as_of: 118,
    coverage: "COMPLETE", authority: "MEASURED",
    source_refs: ["source:lesson:1"], evidence_refs: ["evidence:grader:1"],
    receipt_refs: ["receipt:source:1"],
  };
}

function page(request, {
  records = [], links = [], markers = [], state = "PRESENT",
  coverage = "COMPLETE", next = null,
} = {}) {
  return {
    schema: "bilqis.bamf.control-plane.query-page/v1", query_id: "a".repeat(64),
    request, family: request.family, mode: request.mode, state, coverage,
    total_matches: records.length + links.length, returned: records.length + links.length,
    truncated: next !== null, next_cursor: next, records, markers, links, accepted: true,
  };
}

const capability = {
  schema_version: "bilqis.bamf.mission-control.capability-snapshot/v1",
  meta: meta("capability:and"), capability_id: "B.AND",
};
const episode = {
  schema_version: "bilqis.bamf.mission-control.learning-episode/v1",
  meta: meta("episode:and"), episode_id: "ep-1", capability_id: "B.AND",
};

test("current context search is exact run/generation and bounded", () => {
  const request = buildEvidenceRequest(context, { kind: "context", value: "" });
  assert.equal(request.family, "record");
  assert.equal(request.run_id, "run-7");
  assert.equal(request.generation, 7);
  assert.equal(request.limit, 16);
});

test("historical exact record never falls back to current", () => {
  const request = buildEvidenceRequest(historical, { kind: "record", value: "receipt:g6" });
  assert.equal(request.mode, "historical");
  assert.equal(request.run_id, "run-7");
  assert.equal(request.generation, 6);
  assert.equal(request.record_id, "receipt:g6");
});

test("domain identities reuse generic forensic record queries", () => {
  const capabilityRequest = buildEvidenceRequest(context, { kind: "capability", value: "B.AND" });
  const commandRequest = buildEvidenceRequest(context, { kind: "command", value: "operation-1" });
  assert.equal(capabilityRequest.reference, "B.AND");
  assert.equal(commandRequest.reference, "operation-1");
  assert.equal(capabilityRequest.family, "record");
  assert.equal(commandRequest.family, "record");
});

test("owning selections map directly into evidence criteria", () => {
  assert.deepEqual(criteriaForSelection({ kind: "capability", id: "B.AND" }), {
    kind: "capability", value: "B.AND",
  });
  assert.deepEqual(criteriaForSelection({ kind: "evidence", id: "receipt:one" }), {
    kind: "record", value: "receipt:one",
  });
  assert.deepEqual(criteriaForSelection({ kind: "generation", id: "generation:44239" }), {
    kind: "record", value: "generation:44239",
  });
  assert.equal(
    buildEvidenceRequest(context, criteriaForSelection({
      kind: "generation", id: "generation:44239",
    })).record_id,
    "generation:44239",
  );
});

test("accepted-false query responses fail closed", async () => {
  const api = { async query() { return { accepted: false, reason: "QUERY_DENIED" }; } };
  await assert.rejects(
    loadEvidencePage(api, context, { kind: "context", value: "" }),
    /EVIDENCE_QUERY_REJECTED:QUERY_DENIED/,
  );
});

test("capability to episode to evidence chain follows CP03 links", async () => {
  const seen = [];
  const api = {
    async query(request) {
      seen.push(request);
      if (request.family === "record" && request.reference === "B.AND") {
        return page(request, { records: [capability] });
      }
      if (request.family === "links" && request.record_id === "capability:and") {
        return page(request, { links: [{
          relation: "EPISODE", source_record_id: "capability:and",
          target_ref: "episode:and", target_record_id: "episode:and",
        }] });
      }
      if (request.family === "record" && request.record_id === "episode:and") {
        return page(request, { records: [episode] });
      }
      if (request.family === "links" && request.record_id === "episode:and") {
        return page(request, { links: [{
          relation: "EVIDENCE", source_record_id: "episode:and",
          target_ref: "evidence:grader:1", target_record_id: null,
        }] });
      }
      throw new Error("unexpected query");
    },
  };
  const first = await loadEvidencePage(api, context, { kind: "capability", value: "B.AND" });
  const capabilityLinks = await loadRecordLinks(api, first.records[0]);
  const exact = await loadRecordById(api, context, capabilityLinks.links[0].target_record_id);
  const episodeLinks = await loadRecordLinks(api, exact.record);
  assert.equal(episodeLinks.links[0].target_ref, "evidence:grader:1");
  assert.deepEqual(seen.map((item) => item.family), ["record", "links", "record", "links"]);
});

test("exact linked hydration ignores shell generation", async () => {
  const seen = [];
  const api = { async query(request) { seen.push(request); return page(request, { records: [episode] }); } };
  await loadRecordById(api, historical, "episode:and");
  assert.equal(seen[0].record_id, "episode:and");
  assert.equal(seen[0].run_id, null);
  assert.equal(seen[0].generation, null);
});

test("bounded pagination preserves degraded markers and clears truncation-only partial", () => {
  const request = buildEvidenceRequest(context, { kind: "context", value: "" });
  const marker = {
    schema_version: "bilqis.bamf.mission-control.partial/v1",
    meta: meta("partial:first"), partial_record_id: "episode:and",
    missing_fields: ["grader_receipt"],
  };
  const degraded = mergeEvidencePages(
    page(request, { records: [episode], markers: [marker], state: "PARTIAL", coverage: "PARTIAL", next: "next" }),
    page({ ...request, cursor: "next" }, { records: [capability] }),
  );
  assert.equal(degraded.state, "PARTIAL");
  assert.equal(degraded.coverage, "PARTIAL");
  assert.deepEqual(degraded.markers, [marker]);

  const complete = mergeEvidencePages(
    page(request, { records: [episode], coverage: "PARTIAL", next: "next" }),
    page({ ...request, cursor: "next" }, { records: [capability] }),
  );
  assert.equal(complete.state, "PRESENT");
  assert.equal(complete.coverage, "COMPLETE");
});

test("cursor pagination is passed back to CP03 unchanged", () => {
  const cursor = `cp03:${"1".repeat(64)}:${"2".repeat(64)}:16`;
  const request = buildEvidenceRequest(context, { kind: "context", value: "" }, cursor);
  assert.equal(request.cursor, cursor);
  assert.equal(request.limit, 16);
});
