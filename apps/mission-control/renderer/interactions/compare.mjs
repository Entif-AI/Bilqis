import { t } from "../foundation/i18n.mjs";

function row(key, label, left, right, state = null, reason = null) {
  const leftText = left ?? t("investigation.state.unavailable");
  const rightText = right ?? t("investigation.state.unavailable");
  return Object.freeze({
    key,
    label,
    left: String(leftText),
    right: String(rightText),
    state: state ?? (String(leftText) === String(rightText) ? "SAME" : "DIFFERENT"),
    reason,
  });
}

function result(kind, left, right, rows, {
  state = "PRESENT",
  note = t("investigation.compare.literalOnly"),
} = {}) {
  return Object.freeze({
    state,
    kind,
    left,
    right,
    rows: Object.freeze(rows),
    note,
  });
}

function contextRows(left, right) {
  return [
    row("run", t("investigation.compare.row.run"), left.runId, right.runId),
    row("generation", t("investigation.compare.row.generation"), left.generation, right.generation),
  ];
}

function withContextRows(comparison, left, right) {
  return result(comparison.kind, left, right, [
    ...contextRows(left, right),
    ...comparison.rows,
  ], {
    state: comparison.state,
    note: comparison.note,
  });
}

function compareCapabilityRefs(left, right) {
  const leftDetails = left.details ?? {};
  const rightDetails = right.details ?? {};
  const keys = [...new Set([...Object.keys(leftDetails), ...Object.keys(rightDetails)])].sort();
  if (!keys.length) {
    return result("capability", left, right, [], {
      state: "UNAVAILABLE",
      note: t("investigation.compare.capabilityUnavailable"),
    });
  }
  return result("capability", left, right, [
    row("capability-id", t("investigation.compare.row.capabilityId"), left.id, right.id),
    ...keys.map((key, index) => row(
      `detail-${index}`,
      key,
      leftDetails[key],
      rightDetails[key],
      Object.hasOwn(leftDetails, key) && Object.hasOwn(rightDetails, key) ? null : "UNAVAILABLE",
      Object.hasOwn(leftDetails, key) && Object.hasOwn(rightDetails, key)
        ? null : t("investigation.compare.factUnavailable"),
    )),
  ]);
}

function compareIdentityRefs(left, right) {
  const keys = [...new Set([
    ...Object.keys(left.details ?? {}),
    ...Object.keys(right.details ?? {}),
  ])].sort();
  return result(left.kind, left, right, [
    row("identity", t("investigation.compare.row.identity"), left.id, right.id),
    ...keys.map((key, index) => row(
      `detail-${index}`,
      key,
      left.details?.[key],
      right.details?.[key],
      Object.hasOwn(left.details ?? {}, key) && Object.hasOwn(right.details ?? {}, key)
        ? null : "UNAVAILABLE",
    )),
  ], { note: t("investigation.compare.identityOnly") });
}

export function compareStableRefs(left, right) {
  if (!left || !right) {
    return result("none", left, right, [], {
      state: "EMPTY",
      note: t("investigation.compare.empty"),
    });
  }
  if (left.kind !== right.kind) {
    return result("mixed", left, right, [
      ...contextRows(left, right),
      row("object-class", t("investigation.compare.row.objectClass"), left.kind, right.kind, "INCOMPATIBLE"),
    ], {
      state: "INCOMPATIBLE",
      note: t("investigation.compare.mixed"),
    });
  }
  if (left.runId !== right.runId) {
    return result(left.kind, left, right, contextRows(left, right), {
      state: "INCOMPATIBLE",
      note: t("investigation.compare.contextMismatch"),
    });
  }
  let comparison;
  if (left.kind === "capability") {
    comparison = compareCapabilityRefs(left, right);
  } else if (["source", "semantic"].includes(left.kind)) {
    comparison = compareIdentityRefs(left, right);
  } else {
    comparison = result(left.kind, left, right, [
      row("identity", t("investigation.compare.row.identity"), left.id, right.id),
    ], {
      state: "UNAVAILABLE",
      note: t("investigation.compare.adapterUnavailable"),
    });
  }
  return withContextRows(comparison, left, right);
}
