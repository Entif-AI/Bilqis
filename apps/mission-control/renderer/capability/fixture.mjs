import pages from "./fixture-data.mjs";
export const FIXTURE_RUN = "fixture:gui05";
export async function fixtureQuery(query) {
  if (query.run_id !== FIXTURE_RUN) throw new Error("FIXTURE_RUN_MISMATCH");
  const key = JSON.stringify([query.family, query.generation, query.schema_version,
    query.record_id, query.reference, query.cursor, query.mode]);
  const page = pages[key];
  if (!page) return { schema: "bilqis.bamf.control-plane.query-page/v1", request: query,
    state: "MISSING", coverage: "COMPLETE", records: [], markers: [], links: [],
    next_cursor: null, truncated: false, total_matches: 0, returned: 0 };
  return structuredClone(page);
}
