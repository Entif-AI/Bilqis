import { t } from "../foundation/i18n.mjs";

function row(key, label, left, right, state = null) {
  const leftText = left ?? t("investigation.state.unavailable");
  const rightText = right ?? t("investigation.state.unavailable");
  return Object.freeze({
    key,
    label,
    left: String(leftText),
    right: String(rightText),
    state: state ?? (String(leftText) === String(rightText) ? "SAME" : "DIFFERENT"),
    reason: null,
  });
}

function result(kind, left, right, rows, state = "PRESENT", note = null) {
  return Object.freeze({
    state,
    kind,
    left,
    right,
    rows: Object.freeze(rows),
    note: note ?? t("investigation.compare.identityOnly"),
  });
}

function contextRows(left, right) {
  return [
    row("run", t("investigation.compare.row.run"), left.runId, right.runId),
    row("generation", t("investigation.compare.row.generation"), left.generation, right.generation),
  ];
}

export function compareProductionRefs(left, right) {
  if (!left || !right) {
    return result("none", left, right, [], "EMPTY", t("investigation.compare.empty"));
  }
  if (left.fixture || right.fixture) {
    return result(left.kind, left, right, [], "INCOMPATIBLE", t("investigation.compare.contextMismatch"));
  }
  if (left.kind !== right.kind) {
    return result("mixed", left, right, [
      ...contextRows(left, right),
      row("object-class", t("investigation.compare.row.objectClass"), left.kind, right.kind, "INCOMPATIBLE"),
    ], "INCOMPATIBLE", t("investigation.compare.mixed"));
  }
  if (left.runId !== right.runId) {
    return result(left.kind, left, right, contextRows(left, right), "INCOMPATIBLE",
      t("investigation.compare.contextMismatch"));
  }
  const keys = [...new Set([
    ...Object.keys(left.details ?? {}),
    ...Object.keys(right.details ?? {}),
  ])].sort();
  return result(left.kind, left, right, [
    ...contextRows(left, right),
    row("identity", t("investigation.compare.row.identity"), left.id, right.id),
    ...keys.map((key, index) =>
      row(`detail-${index}`, key, left.details?.[key], right.details?.[key])),
  ]);
}
