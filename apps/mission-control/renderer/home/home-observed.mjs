import { t } from "../foundation/i18n.mjs";
import { formatDurationSeconds, temporalMarkup } from "../foundation/temporal.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";

const SCHEMAS = new Set([
  "bilqis.bamf.mission-control.trainer-observation/v1",
  "bilqis.bamf.mission-control.trainer-observation/v2",
  "bilqis.bamf.mission-control.trainer-observation/v3",
]);

export function observedHomeState(records, context, run) {
  const history = context?.mode === "HISTORICAL" ? [] : records.filter((row) =>
    SCHEMAS.has(row.schema_version) && row.posture === "OBSERVED" &&
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
  const stageDuration = (value) => {
    if (typeof value !== "number" || !Number.isFinite(value)) return null;
    if (value < 1) return new Intl.NumberFormat(
      locale, { maximumFractionDigits: 1 }).format(value * 1000) + " ms";
    if (value < 10) return new Intl.NumberFormat(
      locale, { maximumFractionDigits: 2 }).format(value) + " s";
    return formatDurationSeconds(value, { locale });
  };
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
  const performance = [
    ["home.observed.stepWall", stageDuration(row.candidate_step_wall_seconds)],
    ["home.observed.sourceCompile", stageDuration(row.pre_neural_source_compile_wall_seconds)],
    ["home.observed.currentness", stageDuration(row.currentness_binding_wall_seconds)],
    ["home.observed.b11Preflight", stageDuration(row.b11_preflight_wall_seconds)],
    ["home.observed.b11Autodiff", stageDuration(row.b11_autodiff_wall_seconds)],
    ["home.observed.optimizerAdmission", stageDuration(row.optimizer_admission_wall_seconds)],
    ["home.observed.motifStaging", stageDuration(row.motif_staging_wall_seconds)],
    ["home.observed.evidenceCapture", stageDuration(row.evidence_capture_wall_seconds)],
    ["home.observed.gradientLaunches", row.c08_gradient_launches],
    ["home.observed.vectorizedBatches", row.c08_vectorized_microbatches],
    ["home.observed.scalarFallbackRows", row.c08_scalar_fallback_rows],
    ["home.observed.materializationBarriers", row.c08_materialization_barriers],
    ["home.observed.logicalBatchWall", stageDuration(row.c08_logical_batch_wall_seconds)],
    ["home.observed.rowsPerLaunch", row.c08_rows_per_gradient_launch],
    ["home.observed.logicalRows", row.logical_rows],
    ["home.observed.compiledPositions", row.compiled_positions],
    ["home.observed.b11ProviderDraws", row.b11_provider_draw_count],
    ["home.observed.b11AtlasReloads", row.b11_atlas_reload_count],
    ["home.observed.terminalStep", row.candidate_terminal_step === null
      || row.candidate_terminal_step === undefined
      ? null : t(row.candidate_terminal_step ? "home.observed.yes" : "home.observed.no")],
    ["home.observed.retentionWall", stageDuration(row.retention_wall_seconds)],
    ["home.observed.evidenceFinalization", stageDuration(row.evidence_finalization_wall_seconds)],
    ["home.observed.publishingWall", stageDuration(row.publishing_wall_seconds)],
  ];
  const stepPerformance = (step) => [
    ["home.observed.stepWall", stageDuration(step.candidate_step_wall_seconds)],
    ["home.observed.sourceCompile", stageDuration(step.pre_neural_source_compile_wall_seconds)],
    ["home.observed.currentness", stageDuration(step.currentness_binding_wall_seconds)],
    ["home.observed.b11Preflight", stageDuration(step.b11_preflight_wall_seconds)],
    ["home.observed.b11Autodiff", stageDuration(step.b11_autodiff_wall_seconds)],
    ["home.observed.optimizerAdmission", stageDuration(step.optimizer_admission_wall_seconds)],
    ["home.observed.motifStaging", stageDuration(step.motif_staging_wall_seconds)],
    ["home.observed.evidenceCapture", stageDuration(step.evidence_capture_wall_seconds)],
    ["home.observed.gradientLaunches", step.c08_gradient_launches],
    ["home.observed.vectorizedBatches", step.c08_vectorized_microbatches],
    ["home.observed.scalarFallbackRows", step.c08_scalar_fallback_rows],
    ["home.observed.materializationBarriers", step.c08_materialization_barriers],
    ["home.observed.logicalBatchWall", stageDuration(step.c08_logical_batch_wall_seconds)],
    ["home.observed.rowsPerLaunch", step.c08_rows_per_gradient_launch],
    ["home.observed.logicalRows", step.logical_rows],
    ["home.observed.compiledPositions", step.compiled_positions],
    ["home.observed.b11ProviderDraws", step.b11_provider_draw_count],
    ["home.observed.b11AtlasReloads", step.b11_atlas_reload_count],
  ];
  const completedSteps = Array.isArray(row.candidate_steps) ? row.candidate_steps : [];
  const activeCompleted = completedSteps.some((step) => step.candidate_step === row.candidate_step);
  const activeStep = row.phase === "TRAINING" && row.candidate_step > 0 && !activeCompleted
    ? { ...row } : null;
  const stepRows = [...completedSteps, ...(activeStep ? [activeStep] : [])];
  const stepsMarkup = stepRows.map((step) => {
    const running = activeStep === step;
    const duration = stageDuration(step.candidate_step_wall_seconds) ?? unknown;
    const summary = running
      ? t("home.observed.stepRunning", { step: step.candidate_step, duration })
      : t("home.observed.stepComplete", { step: step.candidate_step, duration });
    const rows = stepPerformance(step);
    return `<details ${testIdAttribute("home", "observed", "step", step.candidate_step)}><summary>${esc(summary)}</summary><table><thead><tr><th scope="col">${esc(t("home.observed.stage"))}</th><th scope="col">${esc(t("home.observed.value"))}</th></tr></thead><tbody>${rows.map(([key, value]) => `<tr><th scope="row">${esc(t(key))}</th><td>${esc(value ?? unknown)}</td></tr>`).join("")}</tbody></table></details>`;
  }).join("");
  return `<div class="home-observed" data-posture="OBSERVED" data-connection="${esc(row.connection_state)}" data-test-id="home-observed">
    <div class="home-observed-head"><strong class="home-observed-badge">${esc(posture)}</strong>${observedTime}</div>
    <p class="home-observed-accepted">${esc(t("home.observed.acceptedGeneration"))}: ${esc(observed.acceptedGeneration ?? unknown)} · ${esc(t("home.observed.acceptedStep"))}: ${esc(observed.acceptedOptimizerStep ?? unknown)}</p>
    <dl>${fields.map(([key, value]) => `<div><dt>${esc(t(key))}</dt><dd>${esc(value ?? unknown)}</dd></div>`).join("")}</dl>
    ${stepRows.length ? `<section data-test-id="home-observed-steps"><h4>${esc(t("home.observed.steps"))}</h4>${stepsMarkup}</section>` : `<details ${testIdAttribute("home", "observed", "performance")}><summary>${esc(t("home.observed.performance"))}</summary><dl>${performance.map(([key, value]) => `<div><dt>${esc(t(key))}</dt><dd>${esc(value ?? unknown)}</dd></div>`).join("")}</dl></details>`}

    <details ${testIdAttribute("home", "observed", "history")}><summary>${esc(t("home.observed.history"))}</summary><ol>${observed.history.map((item, index) => `<li><span>${esc(item.capability_id ?? unknown)} · ${esc(item.phase)} · ${esc(item.outcome)} · ${esc(item.connection_state)}</span>${temporalMarkup({ unixSeconds: item.meta?.observed_at ?? null, nowMs, locale, testId: `home-observed-history-time-${index}` })}</li>`).join("")}</ol></details>
  </div>`;
}
