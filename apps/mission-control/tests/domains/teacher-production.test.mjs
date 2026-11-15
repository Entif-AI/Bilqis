import test from "node:test";
import assert from "node:assert/strict";
import {
  loadTeacherSnapshot, teacherQuery, teacherSnapshotFromRecord,
} from "../../renderer/teacher/teacher-live.mjs";
import { productionTeacherMarkup } from "../../renderer/teacher/teacher-production-view.mjs";

const baseRecord = Object.freeze({
  schema_version: "bilqis.bamf.mission-control.teacher-snapshot/v1",
  teacher_identity: "teacher:accepted",
  teacher_epoch: 12,
  strategy_id: "strategy:accepted",
  attempts: { state: "PRESENT", value: 9 },
  accepted: { state: "PRESENT", value: 6 },
  rejected: { state: "PRESENT", value: 3 },
});

function record(recordId, observedAt, materializedAt) {
  return {
    ...baseRecord,
    meta: {
      record_id: recordId, coverage: "COMPLETE",
      observed_at: observedAt, materialized_at: materializedAt,
      source_refs: ["source:teacher"], evidence_refs: ["evidence:teacher"],
      receipt_refs: ["receipt:teacher"],
    },
  };
}

test("production Teacher query is context-bound and preserves authoritative observation time", () => {
  const current = teacherQuery({ runId: "run:accepted", mode: "LIVE", generation: 7 });
  assert.equal(current.family, "teacher");
  assert.equal(current.mode, "current");
  assert.equal(current.run_id, "run:accepted");
  assert.equal(current.generation, null);
  const historical = teacherQuery({ runId: "run:accepted", mode: "HISTORICAL", generation: 5 });
  assert.equal(historical.mode, "historical");
  assert.equal(historical.generation, 5);

  const snapshot = teacherSnapshotFromRecord(record("teacher:accepted:7", 1794700118, 1794700120));
  assert.equal(snapshot.observedAt, 1794700118);
  const markup = productionTeacherMarkup({ snapshot }, {
    activeTab: "roster", temporal: { nowMs: 1794700125000 },
  });
  assert.match(markup, /data-source-unix-seconds="1794700118"/);
  assert.doesNotMatch(markup, /1794700120/);
  assert.doesNotMatch(markup, /fixture:/i);
});

test("historical Teacher pagination selects the latest accepted observation in the exact generation", async () => {
  const requests = [];
  const api = {
    query: async (request) => {
      requests.push(request);
      const newer = request.cursor === "next";
      return {
        accepted: true, state: "PRESENT", coverage: "COMPLETE",
        records: [record(newer ? "teacher:new" : "teacher:old",
          newer ? 1794700118 : 1794700000, newer ? 1794700120 : 1794700002)],
        next_cursor: newer ? null : "next",
      };
    },
  };
  const result = await loadTeacherSnapshot(api, {
    runId: "run:accepted", mode: "HISTORICAL", generation: 4,
  });
  assert.equal(requests.length, 2);
  assert.equal(requests[0].generation, 4);
  assert.equal(requests[1].cursor, "next");
  assert.equal(result.snapshot.recordId, "teacher:new");
  assert.equal(result.snapshot.observedAt, 1794700118);
});
