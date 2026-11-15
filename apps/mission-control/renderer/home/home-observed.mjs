import { t } from "../foundation/i18n.mjs";
import { formatDurationSeconds, temporalMarkup } from "../foundation/temporal.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";

const SCHEMA = "bilqis.bamf.mission-control.trainer-observation/v1";

export function observedHomeState(records, context, run) {
  const history = context?.mode === "HISTORICAL" ? [] : records.filter((row) =>
    row.schema_version === SCHEMA && row.posture === "OBSERVED" &&
    row.meta?.run?.run_id === context?.runId).sort((a, b) =>
    (b.meta.observed_at - a.meta.observed_at) || (b.revision - a.revision)).slice(0, 8)
    .map((row) => Object.freeze(context?.transportDisconnected && row.connection_state === "LIVE"
      ? { ...row, connection_state: "DISCONNECTED" } : row));
  return Object.freeze({ current: history[0] ?? null, history: Object.freeze(history),
    acceptedGeneration: run?.meta?.run?.generation ?? null,
    acceptedOptimizerStep: run?.optimizer_step ?? null });
}

export function renderObservedWork(observed, esc, { nowMs = Date.now(), locale } = {}) {
  const row = observed?.current;
  if (!row) return "";
  const unknown = t("home.common.unavailable");
  const progress = row.retention_total === null ? unknown
    : t("home.observed.assessments", { completed: row.retention_completed, total: row.retention_total });
  const candidate = row.candidate_horizon === null ? unknown : `${row.candidate_step} / ${row.candidate_horizon}`;
  const elapsed = formatDurationSeconds(row.elapsed_ms / 1000, { locale });
  const posture = row.connection_state === "DISCONNECTED" ? t("home.observed.disconnected")
    : t("home.observed.provisional");
  const observedTime = temporalMarkup({
    unixSeconds: row.meta?.observed_at ?? null,
    nowMs,
    locale,
    testId: "home-observed-time",
  });
  const fields = [
    ["home.current.targetCapability", row.capability_id],
    ["home.observed.phase", row.phase], ["home.observed.outcome", row.outcome],
    ["home.observed.candidate", candidate], ["home.observed.candidateOptimizer", row.candidate_optimizer_step],
    ["home.observed.retention", progress],
    ["home.observed.subject", [row.retention_subject, row.retention_role].filter(Boolean).join(" · ") || null],
    ["home.observed.elapsed", elapsed],
    ["home.observed.cpu", row.cpu_seconds === null ? null : formatDurationSeconds(row.cpu_seconds, { locale })],
    ["home.observed.memory", row.peak_rss_bytes === null ? null : `${(row.peak_rss_bytes / 1048576).toFixed(1)} MiB`],
    ["home.observed.disk", row.disk_free_bytes === null ? null : `${(row.disk_free_bytes / 1073741824).toFixed(1)} GiB`],
  ];
  return `<div class="home-observed" data-posture="OBSERVED" data-connection="${esc(row.connection_state)}" data-test-id="home-observed">
    <div class="home-observed-head"><strong class="home-observed-badge">${esc(posture)}</strong>${observedTime}</div>
    <p class="home-observed-accepted">${esc(t("home.observed.acceptedGeneration"))}: ${esc(observed.acceptedGeneration ?? unknown)} · ${esc(t("home.observed.acceptedStep"))}: ${esc(observed.acceptedOptimizerStep ?? unknown)}</p>
    <dl>${fields.map(([key, value]) => `<div><dt>${esc(t(key))}</dt><dd>${esc(value ?? unknown)}</dd></div>`).join("")}</dl>

    <details ${testIdAttribute("home", "observed", "history")}><summary>${esc(t("home.observed.history"))}</summary><ol>${observed.history.map((item, index) => `<li><span>${esc(item.capability_id ?? unknown)} · ${esc(item.phase)} · ${esc(item.outcome)} · ${esc(item.connection_state)}</span>${temporalMarkup({ unixSeconds: item.meta?.observed_at ?? null, nowMs, locale, testId: `home-observed-history-time-${index}` })}</li>`).join("")}</ol></details>
  </div>`;
}
