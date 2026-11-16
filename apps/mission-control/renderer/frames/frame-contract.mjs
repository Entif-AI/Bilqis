import { assertOperatorView } from "../shell-state.mjs";

export const FRAME_QUERY = "bamf.gui08.frame-query/v1";
export const FRAME_PAGE = "bamf.gui08.frame-page/v1";
export const FRAME_PATHS = Object.freeze(["FAST", "PARTIAL", "EXTENDED", "ATOMIC"]);
export const FRAME_STATES = Object.freeze([
  "PRESENT", "EMPTY", "MISSING", "UNAVAILABLE", "DENIED", "STALE", "PARTIAL", "UNKNOWN", "ERROR",
]);
const DATA_STATES = new Set(["PRESENT", "STALE", "PARTIAL"]);

function requireValue(condition) {
  if (!condition) throw new TypeError("FRAME_INSPECTION_INVALID");
}

function keys(value, names) {
  requireValue(value && typeof value === "object" && !Array.isArray(value) &&
    Object.keys(value).length === names.length && names.every(name => Object.hasOwn(value, name)));
}
function text(value) {
  requireValue(typeof value === "string" && value.trim().length > 0 &&
    [...value].length <= 512 && !/[\u0000-\u001f\u007f]/.test(value));
}
function count(value) { requireValue(Number.isSafeInteger(value) && value >= 0); }
function digest(value) { requireValue(typeof value === "string" && /^[0-9a-f]{64}$/.test(value)); }
function nullable(value, validator) { if (value !== null) validator(value); }
function list(value, limit, validator) {
  requireValue(Array.isArray(value) && value.length <= limit);
  value.forEach(validator);
}

export function assertFrameRequest(request) {
  keys(request, ["schemaVersion", "runId", "generation", "mode"]);
  requireValue(request.schemaVersion === FRAME_QUERY);
  text(request.runId); count(request.generation);
  requireValue(["current", "historical"].includes(request.mode));
  requireValue(request.mode !== "current" || request.generation === 7);
  return request;
}

export function sameFrameRequest(left, right) {
  return ["schemaVersion", "runId", "generation", "mode"].every(key => left?.[key] === right?.[key]);
}

function constituent(value) {
  keys(value, ["sourceOrder", "atom", "role", "occurrenceIndex", "semanticId", "sourceRef", "visibleAt"]);
  count(value.sourceOrder); count(value.occurrenceIndex); nullable(value.visibleAt, count);
  for (const name of ["atom", "role", "semanticId", "sourceRef"]) text(value[name]);
}

function field(value) {
  keys(value, ["name", "value", "visibleAt"]);
  text(value.name); text(value.value); nullable(value.visibleAt, count);
}

function position(value, index) {
  keys(value, ["index", "path", "schema", "tag", "occurrenceId", "visibleAt", "reason", "sidecarRef", "fields", "constituents"]);
  requireValue(value.index === index && FRAME_PATHS.includes(value.path));
  for (const name of ["schema", "tag", "occurrenceId", "reason", "sidecarRef"]) nullable(value[name], text);
  nullable(value.visibleAt, count);
  nullable(value.fields, fields => list(fields, 32, field));
  list(value.constituents, 64, constituent);
}

function example(value, manifest) {
  keys(value, ["receiptId", "frameId", "sourceId", "generationManifest", "compiler", "sourceDigest", "compiledDigest", "positions", "expansionCount", "expansionPasses", "sidecarBytes", "preparationMs"]);
  for (const name of ["receiptId", "frameId", "sourceId"]) text(value[name]);
  for (const name of ["generationManifest", "sourceDigest", "compiledDigest"]) digest(value[name]);
  requireValue(value.generationManifest === manifest);
  nullable(value.compiler, compiler => {
    keys(compiler, ["version", "digest"]); text(compiler.version); digest(compiler.digest);
  });
  nullable(value.positions, positions => {
    list(positions, 64, position);
    const atoms = positions.flatMap(item => item.constituents);
    const ordered = atoms.map(item => item.sourceOrder).sort((a, b) => a - b);
    requireValue(ordered.every((order, index) => order === index));
    for (const item of [...positions, ...atoms, ...positions.flatMap(p => p.fields ?? [])]) {
      requireValue(item.visibleAt === null || item.visibleAt <= atoms.length);
    }
  });
  for (const name of ["expansionCount", "expansionPasses", "sidecarBytes"]) nullable(value[name], count);
  nullable(value.preparationMs, cost => requireValue(typeof cost === "number" && Number.isFinite(cost) && cost >= 0));
}

export function assertFramePage(page) {
  requireValue(new TextEncoder().encode(JSON.stringify(page)).length <= 256 * 1024);
  keys(page, ["schemaVersion", "request", "state", "coverage", "provenance", "operatorView", "examples"]);
  requireValue(page.schemaVersion === FRAME_PAGE);
  assertFrameRequest(page.request);
  requireValue(FRAME_STATES.includes(page.state) && ["COMPLETE", "PARTIAL", "UNKNOWN"].includes(page.coverage));
  requireValue(page.provenance === "ILLUSTRATIVE_FIXTURE");
  if (["MISSING", "UNAVAILABLE", "DENIED", "UNKNOWN", "ERROR"].includes(page.state)) {
    requireValue(page.operatorView === null);
  }
  if (page.operatorView !== null) {
    try { assertOperatorView(page.operatorView); } catch { requireValue(false); }
    const run = page.operatorView.meta.run;
    requireValue(run.run_id === page.request.runId && run.generation === page.request.generation);
  }
  requireValue(!(DATA_STATES.has(page.state) || page.state === "EMPTY") || page.operatorView !== null);
  list(page.examples, 32, value => example(value, page.operatorView?.meta.run.generation_manifest_sha256));
  requireValue(DATA_STATES.has(page.state) || page.examples.length === 0);
  for (const key of ["frameId", "receiptId"]) {
    requireValue(new Set(page.examples.map(value => value[key])).size === page.examples.length);
  }
  return page;
}
