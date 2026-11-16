import { normalizeRelations } from "./model.mjs";

function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

export function objectDomAttributes({ kind, id, relations = [] }) {
  const encoded = encodeURIComponent(JSON.stringify(normalizeRelations(relations)));
  return `data-object-kind="${esc(kind)}" data-object-id="${esc(id)}" data-object-relations="${esc(encoded)}"`;
}

export function objectRefFromElement(element, context = {}) {
  if (!element?.dataset?.objectKind || !element?.dataset?.objectId) return null;
  let relations = [];
  try {
    relations = JSON.parse(decodeURIComponent(element.dataset.objectRelations ?? "%5B%5D"));
  } catch (_error) {
    relations = [];
  }
  return Object.freeze({
    kind: element.dataset.objectKind,
    id: element.dataset.objectId,
    label: element.dataset.objectId,
    runId: context.runId ?? "UNKNOWN",
    generation: Number.isSafeInteger(context.generation) ? context.generation : 0,
    fixture: context.fixture === true,
    details: null,
    relations: normalizeRelations(relations),
  });
}
