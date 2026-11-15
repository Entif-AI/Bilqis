const OWNER = Object.freeze({
  capability: "capability",
  episode: "learning",
  candidate: "learning",
  semantic: "atlas",
  frame: "model",
  neural: "model",
  memory: "memory",
  checkpoint: "lineage",
  generation: "lineage",
  evidence: "evidence",
  source: "evidence",
  correction: "corrections",
  warning: "resources",
  resource: "resources",
  strategy: "teacher",
  operation: "operate",
  "salience-observation": "salience",
});

function segment(value) {
  return encodeURIComponent(String(value));
}

export function buildAppUri(ref) {
  if (!ref || typeof ref.runId !== "string" || !ref.runId ||
      !Number.isSafeInteger(ref.generation) || ref.generation < 0 ||
      !OWNER[ref.kind] || typeof ref.id !== "string" || !ref.id) {
    throw new TypeError("BAMF_GUI18_APP_URI_TARGET_INVALID");
  }
  const base = `bilqis://run/${segment(ref.runId)}/generation/${ref.generation}/${segment(ref.kind)}/${segment(ref.id)}`;
  return ref.fixture === true ? base + "?fixture=1" : base;
}

export function parseAppUri(raw) {
  if (typeof raw !== "string" || raw.length > 8192) return null;
  let value;
  try {
    value = new URL(raw);
  } catch (_error) {
    return null;
  }
  if (value.protocol !== "bilqis:" || value.hostname !== "run" ||
      value.username || value.password || value.port) return null;
  const parts = value.pathname.split("/").filter(Boolean);
  if (parts.length !== 5 || parts[1] !== "generation") return null;
  let runId;
  let kind;
  let id;
  try {
    runId = decodeURIComponent(parts[0]);
    kind = decodeURIComponent(parts[3]);
    id = decodeURIComponent(parts[4]);
  } catch (_error) {
    return null;
  }
  const generation = Number(parts[2]);
  if (!runId || runId.includes("\n") || !id || id.includes("\n") ||
      !Number.isSafeInteger(generation) || generation < 0 || !OWNER[kind]) {
    return null;
  }
  const fixture = value.searchParams.get("fixture") === "1";
  if ([...value.searchParams.keys()].some((key) => key !== "fixture")) return null;
  return Object.freeze({
    view: OWNER[kind],
    selected: Object.freeze({ kind, id }),
    context: Object.freeze({
      runId,
      generation,
      mode: "HISTORICAL",
      fixture,
      historicalPinned: true,
    }),
  });
}

export function appUriToHash(raw) {
  const route = parseAppUri(raw);
  if (!route) return null;
  const params = new URLSearchParams({
    kind: route.selected.kind,
    id: route.selected.id,
    run: route.context.runId,
    generation: String(route.context.generation),
    mode: "HISTORICAL",
  });
  if (route.context.fixture) params.set("fixture", "true");
  return `#/view/${route.view}?${params.toString()}`;
}

export function routeForObjectRef(ref) {
  return parseAppUri(buildAppUri(ref));
}
