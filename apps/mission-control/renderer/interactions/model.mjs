const PANELS = new Set(["closed", "compare", "pins", "annotations"]);

function nonblank(value) {
  return typeof value === "string" && value.trim().length > 0 && !value.includes("\n");
}

function freezeDetails(details) {
  if (!details || typeof details !== "object" || Array.isArray(details)) return null;
  return Object.freeze({ ...details });
}

export function normalizeRelations(relations = []) {
  if (!Array.isArray(relations)) return Object.freeze([]);
  const seen = new Set();
  const result = [];
  for (const relation of relations) {
    if (!relation || typeof relation !== "object" ||
        !nonblank(relation.kind) || !nonblank(relation.id) ||
        !nonblank(relation.relation)) continue;
    const key = [relation.kind, relation.id, relation.relation].join("\u0000");
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(Object.freeze({
      kind: relation.kind,
      id: relation.id,
      relation: relation.relation,
    }));
  }
  return Object.freeze(result);
}

export function stableObjectRef(selected, context) {
  if (!selected || typeof selected !== "object" ||
      !nonblank(selected.kind) || !nonblank(selected.id) ||
      !context || !nonblank(context.runId) ||
      !Number.isSafeInteger(context.generation) || context.generation < 0) {
    return null;
  }
  return Object.freeze({
    kind: selected.kind,
    id: selected.id,
    label: nonblank(selected.label) ? selected.label : selected.id,
    runId: context.runId,
    generation: context.generation,
    fixture: context.fixture === true,
    details: freezeDetails(selected.details),
    relations: normalizeRelations(selected.relations),
  });
}

export function objectRefKey(ref) {
  if (!ref) return "";
  return [ref.runId, ref.generation, ref.kind, ref.id].join("\u0000");
}

export function sameObjectRef(left, right) {
  return Boolean(left && right && objectRefKey(left) === objectRefKey(right));
}

export function historicalContext(context, generation) {
  if (!context || !Number.isSafeInteger(generation) || generation < 0) {
    throw new RangeError("BAMF_GUI18_GENERATION_INVALID");
  }
  return Object.freeze({
    ...context,
    generation,
    mode: "HISTORICAL",
    historicalPinned: true,
    generationManifest: "UNKNOWN",
    topologyId: "UNKNOWN",
    factoryRelease: "UNKNOWN",
    semanticRelease: "UNKNOWN",
    coverage: "UNKNOWN",
    freshness: "UNKNOWN",
  });
}

export function withHistoricalLens(state, generation) {
  if (!state) return state;
  return Object.freeze({
    ...state,
    context: historicalContext(state.context, generation),
    selected: null,
    inspectorOpen: false,
    mutationAvailable: false,
  });
}

export function createInteractionState() {
  return Object.freeze({
    panel: "closed",
    compare: Object.freeze({ left: null, right: null }),
  });
}

export function setInteractionPanel(interaction, panel) {
  return Object.freeze({
    ...interaction,
    panel: PANELS.has(panel) ? panel : "closed",
  });
}

export function setCompareSide(interaction, side, ref) {
  if (!["left", "right"].includes(side)) {
    throw new TypeError("BAMF_GUI18_COMPARE_SIDE_INVALID");
  }
  return Object.freeze({
    ...interaction,
    compare: Object.freeze({ ...interaction.compare, [side]: ref ?? null }),
    panel: "compare",
  });
}

export function explicitHighlightRefs(ref) {
  if (!ref) return Object.freeze([]);
  return Object.freeze([
    Object.freeze({ kind: ref.kind, id: ref.id, relation: "selected" }),
    ...normalizeRelations(ref.relations),
  ]);
}
