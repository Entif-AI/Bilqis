"use strict";

const Ajv2020 = require("ajv/dist/2020");
const bundle = require("../../../bilqis_mlx/mission_control/schemas/mission-control-v1.schema.json");
const ajv = new Ajv2020({ strict: false });
const recordValidators = new Map(Object.entries(bundle.records).map(([id, schema]) => [id, ajv.compile(schema)]));

const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";
const PAGE_SCHEMA = "bilqis.bamf.control-plane.query-page/v1";
const FAMILIES = ["record", "run", "school", "capability", "episode", "generation", "semantic",
  "frame", "neural", "memory", "teacher", "salience", "correction", "resource", "reference", "links"];
const QUERY_KEYS = ["schema", "family", "mode", "run_id", "record_id", "schema_version",
  "generation", "frontier_id", "as_of", "reference", "cursor", "limit"];
const PAGE_KEYS = ["schema", "query_id", "request", "family", "mode", "state", "coverage",
  "total_matches", "returned", "truncated", "next_cursor", "records", "markers", "links"];
const name = (v) => typeof v === "string" && v.trim().length > 0 && !v.includes("\n");
const integer = (v) => Number.isSafeInteger(v) && v >= 0;
const exact = (v, keys) => v && typeof v === "object" && !Array.isArray(v) &&
  Object.keys(v).length === keys.length && keys.every((k) => Object.hasOwn(v, k));
function invalid() { throw new TypeError("BAMF_GUI05_QUERY_CONTRACT_INVALID"); }

function validateQuery(q) {
  if (!exact(q, QUERY_KEYS) || q.schema !== QUERY_SCHEMA || !FAMILIES.includes(q.family) ||
      !["current", "historical"].includes(q.mode) || !integer(q.limit) || q.limit < 1 || q.limit > 32) invalid();
  for (const key of ["run_id", "record_id", "schema_version", "frontier_id", "reference", "cursor"]) {
    if (q[key] !== null && (!name(q[key]) || q[key] === "latest")) invalid();
  }
  for (const key of ["generation", "as_of"]) if (q[key] !== null && !integer(q[key])) invalid();
  if (q.mode === "historical" && [q.generation, q.frontier_id, q.as_of, q.record_id].every((v) => v === null)) invalid();
  if (q.family === "reference" && q.reference === null) invalid();
  if (q.family === "links" && q.record_id === null) invalid();
  return q;
}

function validatePage(p) {
  if (!exact(p, PAGE_KEYS) || p.schema !== PAGE_SCHEMA ||
      typeof p.query_id !== "string" || !/^[a-f0-9]{64}$/.test(p.query_id)) invalid();
  validateQuery(p.request);
  if (p.family !== p.request.family || p.mode !== p.request.mode ||
      !["PRESENT", "EMPTY", "MISSING", "UNAVAILABLE", "PARTIAL", "STALE", "DENIED", "UNKNOWN"].includes(p.state) ||
      !["COMPLETE", "PARTIAL", "UNKNOWN", "NOT_APPLICABLE"].includes(p.coverage) ||
      !integer(p.total_matches) || !integer(p.returned) || typeof p.truncated !== "boolean" ||
      !(p.next_cursor === null || name(p.next_cursor)) || p.truncated !== (p.next_cursor !== null)) invalid();
  if (![p.records, p.markers, p.links].every(Array.isArray) || p.returned !== p.records.length + p.links.length ||
      p.returned > p.request.limit || p.total_matches < p.returned) invalid();
  for (const row of [...p.records, ...p.markers]) {
    if (!recordValidators.get(row?.schema_version)?.(row)) invalid();
  }
  for (const link of p.links) {
    if (!exact(link, ["relation", "source_record_id", "target_ref", "target_record_id"]) ||
        ![link.relation, link.source_record_id, link.target_ref].every(name) ||
        !(link.target_record_id === null || name(link.target_record_id))) invalid();
  }
  return p;
}
module.exports = { QUERY_SCHEMA, PAGE_SCHEMA, validateQuery, validatePage };
