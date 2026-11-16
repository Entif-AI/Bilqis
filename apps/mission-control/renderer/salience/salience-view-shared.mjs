import { escapeText as esc } from "../frames/frame-model.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";
import { salienceT as t } from "./salience-messages.mjs";

const STATE_MARKERS = Object.freeze({
  CURRENT: "●",
  HISTORICAL: "◷",
  PARTIAL: "◐",
  UNAVAILABLE: "×",
  CONJECTURE: "◇",
  UNKNOWN: "?",
  EXPECTED_MISSING: "∅",
  REPORTED_NEGATIVE: "−",
});

const STATE_LABEL_KEYS = Object.freeze({
  CURRENT: "salience.value.current",
  HISTORICAL: "salience.value.historical",
  PARTIAL: "salience.value.partial",
  UNAVAILABLE: "salience.value.unavailable",
  CONJECTURE: "salience.value.conjecture",
});

export function slug(value) {
  return String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

export function stateBadge(value, testId = null) {
  const state = String(value);
  const label = STATE_LABEL_KEYS[state] ? t(STATE_LABEL_KEYS[state]) : state;
  const hook = testId ? ` ${testIdAttribute(testId)}` : "";
  return `<span class="salience-state" data-state="${esc(state.toLowerCase())}"${hook}>
    <span aria-hidden="true">${STATE_MARKERS[state] ?? "•"}</span><span>${esc(label)}</span>
  </span>`;
}

export function yesNo(value) {
  return t(value ? "salience.value.yes" : "salience.value.no");
}

export { esc, t, testIdAttribute };
