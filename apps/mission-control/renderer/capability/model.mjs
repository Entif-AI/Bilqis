export const DOSSIER_SCHEMA = "bilqis.bamf.mission-control.capability-dossier/v1";
export const SECTIONS = ["performance", "teaching", "sources", "dependencies", "history"];
export const RECORD_FAMILIES = ["run", "school", "capability", "episode", "generation", "semantic",
  "frame", "neural", "memory", "teacher", "salience", "correction", "resource"];

export function buildQuery(lens, overrides = {}) {
  return { schema: "bilqis.bamf.control-plane.query/v1", family: "capability",
    mode: lens.mode === "HISTORICAL" ? "historical" : "current", run_id: lens.runId,
    generation: lens.generation, schema_version: DOSSIER_SCHEMA, record_id: null,
    frontier_id: null, as_of: null, reference: null, cursor: null, limit: 8, ...overrides };
}

export function chooseDossier(records, lens, capabilityId) {
  const found = records.filter((row) => row.schema_version === DOSSIER_SCHEMA &&
    row.capability_id === capabilityId && row.meta?.run?.run_id === lens.runId &&
    row.meta.run.generation === lens.generation);
  if (found.length > 1) throw new Error("DOSSIER_IDENTITY_AMBIGUOUS");
  return found[0] ?? null;
}

export function historyEntries(dossier) {
  return dossier.entries.filter((entry) => entry.section === "history")
    .toSorted((a, b) => a.generation - b.generation || a.observed_at - b.observed_at || a.entry_id.localeCompare(b.entry_id));
}

export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}

export function metricText(metric) {
  if (!metric || metric.state !== "PRESENT") return metric?.state ?? "UNKNOWN";
  return `${metric.value}${metric.units ? ` ${metric.units}` : ""}`;
}
