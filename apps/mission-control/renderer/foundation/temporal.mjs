import { createTranslator, DEFAULT_LOCALE } from "./i18n.mjs";
import { testIdAttribute } from "./test-hooks.mjs";

const SECOND = 1;
const MINUTE = 60;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const WEEK = 7 * DAY;
const MONTH = 30 * DAY;
const YEAR = 365 * DAY;

const RELATIVE_UNITS = Object.freeze([
  ["second", SECOND],
  ["minute", MINUTE],
  ["hour", HOUR],
  ["day", DAY],
  ["week", WEEK],
  ["month", MONTH],
  ["year", YEAR],
]);

function esc(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function sourceDate(unixSeconds) {
  if (!Number.isSafeInteger(unixSeconds)) return null;
  const date = new Date(unixSeconds * 1000);
  return Number.isNaN(date.getTime()) ? null : date;
}

function relativeUnit(deltaSeconds) {
  const absolute = Math.abs(deltaSeconds);
  if (absolute < MINUTE) return RELATIVE_UNITS[0];
  if (absolute < HOUR) return RELATIVE_UNITS[1];
  if (absolute < DAY) return RELATIVE_UNITS[2];
  if (absolute < WEEK) return RELATIVE_UNITS[3];
  if (absolute < MONTH) return RELATIVE_UNITS[4];
  if (absolute < YEAR) return RELATIVE_UNITS[5];
  return RELATIVE_UNITS[6];
}

export function formatRelativeUnixSeconds(
  unixSeconds,
  { nowMs = Date.now(), locale = DEFAULT_LOCALE } = {},
) {
  const translate = createTranslator({ locale });
  const date = sourceDate(unixSeconds);
  if (!date || !Number.isFinite(nowMs)) return translate("foundation.temporal.unavailable");
  const deltaSeconds = (date.getTime() - nowMs) / 1000;
  const [unit, secondsPerUnit] = relativeUnit(deltaSeconds);
  const value = Math.round(deltaSeconds / secondsPerUnit);
  return new Intl.RelativeTimeFormat(locale, { numeric: "always" }).format(value, unit);
}

export function temporalMarkup({
  unixSeconds,
  nowMs = Date.now(),
  locale = DEFAULT_LOCALE,
  testId,
} = {}) {
  const translate = createTranslator({ locale });
  const date = sourceDate(unixSeconds);
  if (!date) {
    return `<span class="ui-temporal ui-temporal--unavailable" ${testIdAttribute(testId)}>${esc(translate("foundation.temporal.unavailable"))}</span>`;
  }
  const iso = date.toISOString();
  const relative = formatRelativeUnixSeconds(unixSeconds, { nowMs, locale });
  const full = new Intl.DateTimeFormat(locale, {
    dateStyle: "full",
    timeStyle: "long",
  }).format(date);
  const detailId = `${testId}-detail`;
  const exact = translate("foundation.temporal.exactUtc", { value: iso });
  return `<time class="ui-temporal" datetime="${esc(iso)}" data-source-unix-seconds="${unixSeconds}" tabindex="0" aria-describedby="${detailId}" ${testIdAttribute(testId)}><span class="ui-temporal__relative">${esc(relative)}</span><span id="${detailId}" class="ui-temporal__detail" role="tooltip" popover="manual" ${testIdAttribute(testId, "detail")}><span>${esc(full)}</span><code>${esc(exact)}</code></span></time>`;
}
