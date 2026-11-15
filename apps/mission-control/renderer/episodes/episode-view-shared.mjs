import { escapeText as esc } from "../frames/frame-model.mjs";
import { formatMessage, t as baseT } from "../foundation/i18n.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";
import { EPISODE_FIXTURE_MESSAGES } from "./episode-fixture-messages.mjs";

const STATE_MARKERS = Object.freeze({
  PRESENT: "✓",
  RETAINED: "✓",
  REJECTED: "×",
  UNKNOWN: "?",
  PENDING: "…",
  PARTIAL: "◐",
  MISSING: "∅",
  UNAVAILABLE: "∅",
  MEASURED: "✓",
});

export function stateLabel(state) {
  const key = `learning.state.${state}`;
  try {
    return t(key);
  } catch {
    return String(state);
  }
}

export function stateBadge(state, testId = null) {
  const normalized = String(state).toLowerCase();
  const marker = STATE_MARKERS[state] ?? "?";
  const testHook = testId ? ` ${testIdAttribute(testId)}` : "";
  return `<span class="episode-state" data-state="${esc(normalized)}"${testHook}>
    <span aria-hidden="true">${marker}</span><span>${esc(stateLabel(state))}</span>
  </span>`;
}

export function valueOrUnavailable(value) {
  if (value === null || value === undefined || value === "UNAVAILABLE") {
    return t("learning.value.unavailable");
  }
  if (value === "UNKNOWN") return t("learning.value.unknown");
  return String(value);
}

export function retentionReasonLabel(reason) {
  try {
    return t(`learning.reason.${reason}`);
  } catch {
    return String(reason);
  }
}

export function displayComparisonValue(value) {
  if (value === "UNAVAILABLE") return t("learning.value.unavailable");
  return String(value);
}

export function learningHelpMarkup(key, testId) {
  return contextHelpMarkup({
    label: t(`learning.help.${key}.label`),
    description: t(`learning.help.${key}.description`),
    testId,
  });
}

export function t(key, parameters = {}) {
  const fixtureTemplate = EPISODE_FIXTURE_MESSAGES[key];
  return fixtureTemplate === undefined
    ? baseT(key, parameters)
    : formatMessage(fixtureTemplate, parameters);
}

export { esc, testIdAttribute };
