export const DESTINATIONS = Object.freeze([
  ["mission-control", "Mission Control"],
  ["school", "School"],
  ["capability", "Capability Explorer"],
  ["learning", "Learning"],
  ["atlas", "Atlas"],
  ["model", "Model"],
  ["memory", "Memory"],
  ["teacher", "Teacher"],
  ["salience", "SÍ SÉ SON"],
  ["corrections", "Corrections"],
  ["lineage", "Lineage"],
  ["resources", "Resources"],
  ["evidence", "Evidence"],
  ["operate", "Operate"],
]);

export const DESTINATION_GROUPS = Object.freeze([
  Object.freeze({
    id: "overview-learning",
    labelKey: "shell.nav.group.overviewLearning",
    destinations: Object.freeze(["mission-control", "school", "capability", "learning"]),
  }),
  Object.freeze({
    id: "representation-mechanisms",
    labelKey: "shell.nav.group.representationMechanisms",
    destinations: Object.freeze(["atlas", "model", "memory"]),
  }),
  Object.freeze({
    id: "decision-correction",
    labelKey: "shell.nav.group.decisionCorrection",
    destinations: Object.freeze(["teacher", "salience", "corrections"]),
  }),
  Object.freeze({
    id: "provenance-operations",
    labelKey: "shell.nav.group.provenanceOperations",
    destinations: Object.freeze(["lineage", "resources", "evidence", "operate"]),
  }),
]);

export const INSPECTOR_OWNERS = Object.freeze({
  capability: "capability",
  episode: "learning",
  semantic: "atlas",
  frame: "model",
  memory: "memory",
  checkpoint: "lineage",
  evidence: "evidence",
  source: "evidence",
  correction: "corrections",
  generation: "lineage",
  warning: "resources",
  resource: "resources",
  neural: "model",
  strategy: "teacher",
  operation: "operate",
  "salience-observation": "salience",
});

export const OPERATOR_VIEW_SCHEMA = "bilqis.bamf.mission-control.operator-view/v1";

const COVERAGE_STATES = new Set(["COMPLETE", "PARTIAL", "UNKNOWN", "NOT_APPLICABLE"]);
const AUTHORITY_CLASSES = new Set(["SOURCE_AUTHORITATIVE", "MEASURED", "DERIVED", "INFERRED"]);
const OPERATOR_KEYS = [
  "schema_version", "meta", "learner_state", "stage",
  "active_capability_id", "related_record_ids",
];
const META_KEYS = [
  "record_id", "run", "materialized_at", "observed_at", "as_of",
  "coverage", "authority", "source_refs", "evidence_refs", "receipt_refs",
];
const RUN_KEYS = [
  "run_id", "run_identity_sha256", "generation", "generation_manifest_sha256",
  "candidate_identity_sha256", "factory_release_sha256",
  "semantic_release_sha256", "topology_sha256",
];
// Python str.isspace()/strip whitespace used by mission_control.model.is_name.
// ECMAScript String.trim() differs for U+0085 and U+001C-U+001F, so keep the
// shared wire-domain rule explicit instead of delegating to either runtime.
const PYTHON_WHITESPACE_ONLY = /^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$/u;

function sameKeys(value, expected) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const actual = Object.keys(value).sort();
  return actual.length === expected.length &&
    actual.every((key, index) => key === [...expected].sort()[index]);
}

function isUnicodeScalarText(value) {
  if (typeof value !== "string") return false;
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    if (code >= 0xD800 && code <= 0xDBFF) {
      if (index + 1 >= value.length) return false;
      const next = value.charCodeAt(index + 1);
      if (next < 0xDC00 || next > 0xDFFF) return false;
      index += 1;
    } else if (code >= 0xDC00 && code <= 0xDFFF) {
      return false;
    }
  }
  return true;
}

function isName(value) {
  return isUnicodeScalarText(value) && value.length > 0 &&
    !PYTHON_WHITESPACE_ONLY.test(value) && !value.includes("\n");
}

function isDigest(value) {
  return typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
}

function isTime(value) {
  return Number.isSafeInteger(value) && value >= 0;
}

function isNames(value) {
  return Array.isArray(value) && value.every(isName) && new Set(value).size === value.length;
}

function invalidOperatorView(detail) {
  throw new TypeError(`MISSION_CONTROL_OPERATOR_VIEW_INVALID:${detail}`);
}

export function assertOperatorView(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) invalidOperatorView("root");
  if (raw.schema_version !== OPERATOR_VIEW_SCHEMA) {
    throw new TypeError("MISSION_CONTROL_OPERATOR_VIEW_SCHEMA_UNSUPPORTED");
  }
  if (!sameKeys(raw, OPERATOR_KEYS)) invalidOperatorView("fields");
  if (!sameKeys(raw.meta, META_KEYS)) invalidOperatorView("meta.fields");
  if (!sameKeys(raw.meta.run, RUN_KEYS)) invalidOperatorView("run.fields");

  const run = raw.meta.run;
  if (!isName(run.run_id)) invalidOperatorView("run.run_id");
  if (!Number.isSafeInteger(run.generation) || run.generation < 0) {
    invalidOperatorView("run.generation");
  }
  for (const field of RUN_KEYS.filter((name) => name.endsWith("_sha256"))) {
    if (!isDigest(run[field])) invalidOperatorView(`run.${field}`);
  }

  if (!isName(raw.meta.record_id)) invalidOperatorView("meta.record_id");
  if (!isTime(raw.meta.materialized_at)) invalidOperatorView("meta.materialized_at");
  for (const field of ["observed_at", "as_of"]) {
    const value = raw.meta[field];
    if (value !== null && (!isTime(value) || value > raw.meta.materialized_at)) {
      invalidOperatorView(`meta.${field}`);
    }
  }
  if (!COVERAGE_STATES.has(raw.meta.coverage)) invalidOperatorView("meta.coverage");
  if (!AUTHORITY_CLASSES.has(raw.meta.authority)) invalidOperatorView("meta.authority");
  for (const field of ["source_refs", "evidence_refs", "receipt_refs"]) {
    if (!isNames(raw.meta[field])) invalidOperatorView(`meta.${field}`);
  }

  if (!isName(raw.learner_state)) invalidOperatorView("learner_state");
  if (!isName(raw.stage)) invalidOperatorView("stage");
  if (raw.active_capability_id !== null && !isName(raw.active_capability_id)) {
    invalidOperatorView("active_capability_id");
  }
  if (!isNames(raw.related_record_ids)) invalidOperatorView("related_record_ids");
  return raw;
}

export function normalizeContext(raw = {}) {
  assertOperatorView(raw);
  const run = raw.meta.run;
  return Object.freeze({
    runId: run.run_id,
    mode: "LIVE",
    generation: run.generation,
    generationManifest: run.generation_manifest_sha256,
    topologyId: run.topology_sha256,
    factoryRelease: run.factory_release_sha256,
    semanticRelease: run.semantic_release_sha256,
    optimizerStep: "UNKNOWN",
    admissionLease: "UNKNOWN",
    correctionFrontier: "UNKNOWN",
    coverage: raw.meta.coverage,
    freshness: "UNKNOWN",
    resourceHealth: "UNKNOWN",
    schemaVersion: raw.schema_version,
    recordId: raw.meta.record_id,
    historicalPinned: false,
  });
}

export function createShellState(context, route = {}) {
  return withRoute({
    context: normalizeContext(context),
    view: "mission-control",
    selected: null,
    evidenceOrigin: null,
    inspectorOpen: false,
    defensiveState: "unknown",
    mutationAvailable: false,
  }, route);
}

export function withRoute(state, route = {}) {
  const destinations = new Set(DESTINATIONS.map(([id]) => id));
  const view = destinations.has(route.view) ? route.view : "mission-control";
  const changedLens = route.context && ["runId", "generation", "mode"].some((key) =>
    route.context[key] !== state.context[key]);
  const origin = route.evidenceOrigin;
  const evidenceOrigin = (
    view === "evidence" && origin && destinations.has(origin.view)
  ) ? origin : null;
  return {
    ...state,
    view,
    context: changedLens ? Object.freeze({ ...state.context, ...route.context,
      generationManifest: "UNKNOWN", topologyId: "UNKNOWN", factoryRelease: "UNKNOWN",
      semanticRelease: "UNKNOWN", coverage: "UNKNOWN", freshness: "UNKNOWN" }) : state.context,
    selected: route.selected ?? null,
    evidenceOrigin,
    inspectorOpen: Boolean(route.selected) && view !== "capability",
  };
}

export function navigate(state, view, selected = null) {
  const destinations = new Set(DESTINATIONS.map(([id]) => id));
  if (!destinations.has(view)) return state;
  return {
    ...state,
    view,
    selected,
    evidenceOrigin: view === "evidence" ? state.evidenceOrigin : null,
    inspectorOpen: selected !== null,
  };
}

export function inspect(state, selected) {
  return { ...state, selected, inspectorOpen: Boolean(selected) };
}

export function selectObject(state, selected) {
  return { ...state, selected, inspectorOpen: false };
}

export function openEvidence(state) {
  const origin = state.view !== "evidence" && state.selected ? {
    view: state.view,
    selected: state.selected,
    inspectorOpen: state.inspectorOpen,
  } : state.evidenceOrigin;
  return {
    ...state,
    view: "evidence",
    selected: state.selected,
    evidenceOrigin: origin ?? null,
    inspectorOpen: false,
  };
}

export function returnFromEvidence(state) {
  if (!state.evidenceOrigin) return state;
  const origin = state.evidenceOrigin;
  return {
    ...state,
    view: origin.view,
    selected: origin.selected,
    evidenceOrigin: null,
    inspectorOpen: origin.inspectorOpen === true,
  };
}

export function openSelectionOwner(state) {
  if (!state.selected) return state;
  const owner = INSPECTOR_OWNERS[state.selected.kind];
  return owner ? navigate(state, owner, state.selected) : state;
}

export function withContext(state, nextContext) {
  return { ...state, context: normalizeContext(nextContext) };
}

export function withDefensiveState(state, profile) {
  if (!profile || typeof profile !== "object" || typeof profile.id !== "string") {
    throw new TypeError("MISSION_CONTROL_DEFENSIVE_STATE_INVALID");
  }
  const context = Object.freeze({
    ...state.context,
    mode: state.context.historicalPinned ||
      (profile.historical && profile.snapshotAvailable) ? "HISTORICAL" : "LIVE",
    freshness: profile.freshness,
  });
  return {
    ...state,
    context,
    defensiveState: profile.id,
    mutationAvailable: profile.mutationAllowed === true && context.mode === "LIVE",
  };
}

export function shellPosture(context) {
  if (context.mode === "HISTORICAL") return "historical";
  if (context.freshness === "STALE" || context.freshness === "DISCONNECTED") return "stale";
  if (context.freshness === "UNKNOWN") return "unknown";
  return "live";
}
