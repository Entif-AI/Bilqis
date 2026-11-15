import { t } from "./foundation/i18n.mjs";
import { testIdAttribute } from "./foundation/test-hooks.mjs";

export const EVIDENCE_KINDS = Object.freeze({
  measured: { labelKey: "foundation.evidence.measured", marker: "M", cue: "solid" },
  inferred: { labelKey: "foundation.evidence.inferred", marker: "≈", cue: "dashed" },
  source: { labelKey: "foundation.authority.source", marker: "S", cue: "double" },
  derived: { labelKey: "foundation.authority.derived", marker: "D", cue: "single" },
});

export const STATUS_GROUPS = Object.freeze({
  health: ["healthy", "attention", "invalid"],
  availability: ["held", "unavailable", "denied", "unknown", "stale", "partial"],
  operation: ["proposed", "accepted", "attempted", "reconciled"],
  time: ["live", "historical"],
});

export const STATUS_META = Object.freeze({
  healthy: ["✓", "foundation.status.healthy"],
  attention: ["!", "foundation.status.attention"],
  invalid: ["×", "foundation.status.invalid"],
  held: ["Ⅱ", "foundation.status.held"],
  unavailable: ["∅", "foundation.status.unavailable"],
  denied: ["⊘", "foundation.status.denied"],
  unknown: ["?", "foundation.status.unknown"],
  stale: ["↻", "foundation.status.stale"],
  partial: ["◐", "foundation.status.partial"],
  proposed: ["◇", "foundation.status.proposed"],
  accepted: ["◆", "foundation.status.accepted"],
  attempted: ["→", "foundation.status.attempted"],
  reconciled: ["✓", "foundation.status.reconciled"],
  live: ["●", "foundation.status.live"],
  historical: ["◷", "foundation.status.historical"],
});

export function statusBadge(status, detail = "", { testId: id = null } = {}) {
  const known = STATUS_META[status];
  const [marker, label] = known ? [known[0], t(known[1])] : ["?", String(status)];
  const testHook = id ? ` ${testIdAttribute(id)}` : "";
  return `<span class="status-badge" data-state="${status}"${testHook}><span aria-hidden="true">${marker}</span><span>${label}</span>${detail ? `<small>${detail}</small>` : ""}</span>`;
}

export function evidenceValue(value, evidenceKind, authorityKind, unit = "") {
  const evidence = EVIDENCE_KINDS[evidenceKind];
  const authority = EVIDENCE_KINDS[authorityKind];
  return `<span class="evidence-value" data-evidence="${evidenceKind}" data-authority="${authorityKind}">
    <span class="value">${value}${unit}</span>
    <small><b aria-hidden="true">${evidence.marker}</b> ${t(evidence.labelKey)} · <b aria-hidden="true">${authority.marker}</b> ${t(authority.labelKey)}</small>
  </span>`;
}

export function semanticStateInventory() {
  return Object.values(STATUS_GROUPS).flat();
}
