import { escapeText as esc } from "../frames/frame-model.mjs";
import { t } from "../foundation/i18n.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";

const STATE_MARKERS = Object.freeze({
  ACTIVE: "✓",
  PRESENT: "✓",
  PARTIAL: "◐",
  CHECKPOINT_LOCAL_RETIRED: "×",
  RETIRED: "×",
  OBSERVATIONAL: "○",
  SHADOW: "○",
  EQUAL_OBSERVED_DENOMINATORS: "=",
  PARTIAL_OBSERVED_DENOMINATORS: "◐",
});

export function stateBadge(value, testId = null) {
  const state = String(value);
  const hook = testId ? ` ${testIdAttribute(testId)}` : "";
  return `<span class="teacher-state" data-state="${esc(state.toLowerCase())}"${hook}>
    <span aria-hidden="true">${STATE_MARKERS[state] ?? "•"}</span><span>${esc(state)}</span>
  </span>`;
}

export function unavailable(value) {
  return value === null || value === undefined ? t("teacher.value.unavailable") : String(value);
}

export function yesNo(value) {
  return t(value ? "teacher.value.yes" : "teacher.value.no");
}

export function scopeLabel(scope) {
  if (scope.kind === "capability") return t("teacher.comparison.capability", { value: scope.value });
  if (scope.kind === "source-family") return t("teacher.comparison.sourceFamily", { value: scope.value });
  return t("teacher.comparison.wholeSchool");
}

export { esc, t, testIdAttribute };
