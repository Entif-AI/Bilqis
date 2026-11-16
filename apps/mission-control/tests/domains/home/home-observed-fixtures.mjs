export const context = { runId: "trainer-run", generation: 0, mode: "LIVE", operatorActive: true };
export function observation(changes = {}) {
  return { schema_version: "bilqis.bamf.mission-control.trainer-observation/v1",
    meta: { run: { run_id: "trainer-run", generation: 0 }, observed_at: 1000 },
    observation_id: "visit-1", revision: 3, visit_index: 1, posture: "OBSERVED",
    phase: "RETENTION", outcome: "RUNNING", connection_state: "LIVE", capability_id: "A.IDENTITY",
    candidate_step: 1, candidate_horizon: 1, candidate_optimizer_step: 1,
    retention_completed: 1, retention_total: 4, retention_subject: "A.IDENTITY", retention_role: "parent",
    elapsed_ms: 1500, cpu_seconds: 0.4, peak_rss_bytes: 1048576, disk_free_bytes: 1073741824,
    ...changes };
}
export function runPage(row = observation(), generation = 0) {
  return { accepted: true, state: "PARTIAL", records: [
    { schema_version: "bilqis.bamf.mission-control.run-context/v1",
      meta: { run: { run_id: "trainer-run", generation, generation_manifest_sha256: `manifest-${generation}` } },
      optimizer_step: generation, stage: "FOUNDATION" }, row,
  ] };
}
export const host = () => ({ innerHTML: "", querySelectorAll: () => [] });

export function disclosureHost() {
  let markup = "";
  let details = new Map();
  return {
    hidden: false,
    get innerHTML() { return markup; },
    set innerHTML(value) {
      markup = value;
      details = new Map([...value.matchAll(/<details\b([^>]*)data-test-id="([^"]+)"([^>]*)>/g)].map((match) => [
        match[2], { dataset: { testId: match[2] }, open: /\bopen\b/.test(`${match[1]} ${match[3]}`) },
      ]));
    },
    querySelectorAll(selector) {
      if (selector === "details[data-test-id][open]") return [...details.values()].filter((item) => item.open);
      return [];
    },
    querySelector(selector) {
      const match = selector.match(/^\[data-test-id="([^"]+)"\]$/);
      return match ? details.get(match[1]) ?? null : null;
    },
    disclosure(id) { return details.get(id) ?? null; },
  };
}
