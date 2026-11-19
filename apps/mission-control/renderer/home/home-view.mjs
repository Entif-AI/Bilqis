import { t } from "../foundation/i18n.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { assertUniqueTestIds, testIdAttribute } from "../foundation/test-hooks.mjs";
import { renderObservedWork } from "./home-observed.mjs";
import { homeStatus } from "./home-model.mjs";

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function metric(value, { percent = false, integer = false } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return t("home.common.unavailable");
  if (typeof value === "string") return value;
  if (percent) return `${(value * 100).toFixed(1)}%`;
  if (integer) return Math.round(value).toLocaleString();
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 3 });
}

function learningCopy(status) {
  const suffix = ({
    IMPROVING: "improving",
    REGRESSION: "regression",
    THROUGHPUT_ONLY: "throughputOnly",
    NO_FRESH_GAIN: "noFreshGain",
  })[status] ?? "noFreshGain";
  return { label: t(`home.learning.${suffix}`), detail: t(`home.learning.${suffix}Detail`) };
}

function booleanState(value, positive, negative) {
  if (value === null || value === undefined) return t("home.common.unavailable");
  return t(value ? positive : negative);
}

function help(labelKey, bodyKey, id) {
  return contextHelpMarkup({
    label: t(labelKey),
    description: t(bodyKey),
    testId: id,
  });
}

function pulseCopy(event) {
  if (event.kind === "gain") return {
    label: t("home.pulse.gainLabel", { capability: event.capabilityId }),
    detail: t("home.pulse.gainDetail", { before: event.before, after: event.after }),
  };
  if (event.kind === "regress") return {
    label: t("home.pulse.regressionLabel", { capability: event.capabilityId }), detail: event.detail,
  };
  if (event.kind === "retain") return {
    label: t("home.pulse.retainLabel", { capability: event.capabilityId }), detail: event.reasonCode,
  };
  if (event.kind === "reject") return {
    label: t("home.pulse.rejectLabel", { capability: event.capabilityId }), detail: event.reasonCode,
  };
  if (event.kind === "source") return {
    label: t("home.pulse.sourceLabel"), detail: t("home.pulse.sourceDetail", { family: event.family }),
  };
  if (event.kind === "correction") return {
    label: t("home.pulse.correctionLabel"), detail: t("home.pulse.correctionDetail", { count: event.count }),
  };
  return { label: event.kind, detail: event.reasonCode ?? event.detail ?? t("home.common.unavailable") };
}

function attentionCopy(item) {
  if (item.kind === "correction") return {
    label: t("home.attention.correctionLabel"), detail: t("home.attention.correctionDetail", { count: item.count }),
  };
  if (item.kind === "stalled") return {
    label: t("home.attention.stalledLabel"), detail: t("home.attention.stalledDetail", { capabilities: item.capabilities }),
  };
  if (item.kind === "held") return {
    label: t("home.attention.heldLabel"), detail: t("home.attention.heldDetail", { capability: item.capabilityId }),
  };
  if (item.kind === "recovery") return {
    label: t("home.attention.recoveryLabel"), detail: t("home.attention.recoveryDetail", { capability: item.capabilityId }),
  };
  return { label: item.kind, detail: item.detail ?? t("home.common.unavailable") };
}

function healthGroup(id, titleKey, rows, state) {
  const unavailable = t("home.common.unavailable");
  const available = rows.filter(([_labelKey, value]) => value !== unavailable);
  const body = available.length
    ? `<dl>${available.map(([labelKey, value]) => `<div><dt>${esc(t(labelKey))}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl>`
    : `<p class="home-quiet">${esc(t("home.health.noMeasuredValues"))}</p>`;
  return `<section class="home-health-group" data-state="${esc(state)}" ${testIdAttribute("home", "health", id)}>
    <h3>${esc(t(titleKey))}</h3>${body}
  </section>`;
}

function renderStartup(model) {
  const startup = model.startup;
  const running = startup.running === true;
  const ready = startup.state === "GENERATION_ZERO_READY";
  const title = ready
    ? t("home.startup.readyTitle", { generation: startup.generation })
    : running ? t("home.startup.runningTitle") : t("home.startup.idleTitle");
  const detail = ready
    ? t("home.startup.readyDetail")
    : running ? t("home.startup.runningDetail") : t("home.startup.idleDetail");
  const trainer = startup.running === true ? t("home.trainer.running")
    : startup.running === false ? t("home.trainer.stopped") : t("home.common.unknown");
  const telemetry = running ? t("home.startup.waiting") : t("home.startup.noEvents");
  return `<section class="home-startup" data-state="${esc(startup.state)}" ${testIdAttribute("home", "startup")}>
    <span class="eyebrow">${esc(t("home.startup.eyebrow"))}</span>
    <h2>${esc(title)}</h2><p>${esc(detail)}</p>
    <dl>
      <div><dt>${esc(t("home.startup.acceptedGeneration"))}</dt><dd>${esc(startup.generation)}</dd></div>
      <div><dt>${esc(t("home.startup.optimizerStep"))}</dt><dd>${esc(startup.optimizerStep)}</dd></div>
      <div><dt>${esc(t("home.startup.trainer"))}</dt><dd>${esc(trainer)}</dd></div>
      <div><dt>${esc(t("home.startup.stage"))}</dt><dd>${esc(startup.stage ?? t("home.common.unknown"))}</dd></div>
      <div><dt>${esc(t("home.startup.learningTelemetry"))}</dt><dd>${esc(telemetry)}</dd></div>
    </dl>
    <div class="home-startup-next"><div><strong>${esc(t("home.startup.next"))}</strong><p>${esc(t("home.startup.nextDetail"))}</p></div>
      <button type="button" data-home-view="operate" ${testIdAttribute("home", "startup", "operate")}>${esc(t("home.startup.openOperate"))}</button></div>
  </section>`;
}

function statusBand(model, status, badge) {
  const learning = learningCopy(status.learning);
  const states = [
    ["running", t("home.status.running"), booleanState(status.running, "home.status.yes", "home.status.no")],
    ["learning", t("home.status.learning"), learning.label],
    ["regression", t("home.status.regression"), booleanState(status.regression, "home.status.observed", "home.status.noneObserved")],
    ["blocked", t("home.status.blocked"), booleanState(status.blocked, "home.status.blockedObserved", "home.status.noneObserved")],
    ["invalidity", t("home.status.invalidity"), booleanState(status.invalidity, "home.status.invalidObserved", "home.status.noneObserved")],
  ];
  return `<section class="home-status-band" data-learning="${esc(status.learning)}" aria-label="${esc(t("home.status.aria"))}" ${testIdAttribute("home", "status", "band")}>
    <div class="home-status-context"><div class="home-section-heading"><span class="eyebrow">${esc(badge)}</span>${help("home.help.status.label", "home.help.status.body", "home-help-status")}</div><strong>${esc(learning.label)}</strong><p>${esc(learning.detail)}</p></div>
    <dl>${states.map(([id, label, value]) => `<div data-status="${id}" ${testIdAttribute("home", "status", id)}><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl>
  </section>`;
}

function currentWork(model, { nowMs, locale } = {}) {
  const current = model.currentWork;
  const assessment = t("home.current.assessmentValue", {
    target: current.targetAssessment ?? t("home.common.unavailable"),
    protected: current.protectedAssessment ?? t("home.common.unavailable"),
  });
  const rows = [
    ["home.current.targetCapability", current.capabilityId],
    ["home.current.strategy", current.strategy],
    ["home.current.intent", current.candidateIntent],
    ["home.current.sourceFamily", current.sourceFamily],
    ["home.current.assessmentPosture", assessment],
  ];
  const inspect = current.recordId
    ? `<button type="button" class="home-link" data-home-target-kind="episode" data-home-target-id="${esc(current.recordId)}" ${testIdAttribute("home", "current", "inspect")}>${esc(t("home.current.inspect"))}</button>` : "";
  const observedTime = temporalMarkup({
    unixSeconds: current.observedAt,
    nowMs,
    locale,
    testId: "home-current-time",
  });
  return `<section class="home-surface home-current" ${testIdAttribute("home", "current", "work")}>
    <header><div><span class="eyebrow">${esc(t("home.current.eyebrow"))}</span><h2>${esc(t("home.current.title"))}</h2></div><div class="home-heading-tools"><span>${esc(current.capabilityId ? t("home.current.observed") : t("home.common.unavailable"))}</span>${help("home.help.current.label", "home.help.current.body", "home-help-current")}</div></header>
    ${model.observed?.current ? renderObservedWork(model.observed, esc, { nowMs, locale }) : `<dl>${rows.map(([labelKey, value]) => `<div><dt>${esc(t(labelKey))}</dt><dd>${esc(value ?? t("home.common.unavailable"))}</dd></div>`).join("")}</dl><div class="home-time-row"><span>${esc(t("home.current.observedTime"))}</span>${observedTime}</div>${inspect}`}
  </section>`;
}

function attention(model, priority, { nowMs, locale } = {}) {
  return `<section class="home-surface home-attention" data-priority="${priority}" ${testIdAttribute("home", "attention")}>
    <header><div><span class="eyebrow">${esc(t("home.attention.eyebrow"))}</span><h2>${esc(t("home.attention.title"))}</h2></div><div class="home-heading-tools"><span>${esc(t("home.attention.count", { count: model.attention.length }))}</span>${help("home.help.attention.label", "home.help.attention.body", "home-help-attention")}</div></header>
    <div class="attention-list">${model.attention.map((item, index) => {
      const copy = attentionCopy(item);
      const time = temporalMarkup({ unixSeconds: item.observedAt, nowMs, locale, testId: `home-attention-time-${index}` });
      return `<div class="home-list-item" data-severity="${esc(item.severity ?? "attention")}"><button type="button" data-severity="${esc(item.severity ?? "attention")}" data-home-target-kind="${esc(item.target?.kind ?? item.kind)}" data-home-target-id="${esc(item.target?.id ?? item.id)}" ${testIdAttribute("home", "attention", "item", index)}><span>${esc(item.kind)}</span><strong>${esc(copy.label)}</strong><small>${esc(copy.detail)}</small></button>${time}</div>`;
    }).join("") || `<p class="home-quiet">${esc(t("home.attention.empty"))}</p>`}</div>
  </section>`;
}

function pulse(model, { nowMs, locale } = {}) {
  return `<section class="home-analysis home-pulse" ${testIdAttribute("home", "pulse")}>
    <header><div><span class="eyebrow">${esc(t("home.pulse.eyebrow"))}</span><h2>${esc(t("home.pulse.title"))}</h2></div><div class="home-heading-tools"><span>${esc(t("home.pulse.count", { count: model.pulse.length }))}</span>${help("home.help.pulse.label", "home.help.pulse.body", "home-help-pulse")}</div></header>
    <div class="pulse-list">${model.pulse.map((event, index) => {
      const copy = pulseCopy(event);
      const time = temporalMarkup({ unixSeconds: event.observedAt, nowMs, locale, testId: `home-pulse-time-${index}` });
      return `<div class="home-list-item"><button type="button" data-home-target-kind="${esc(event.target?.kind ?? "evidence")}" data-home-target-id="${esc(event.target?.id ?? `pulse:${index}`)}" ${testIdAttribute("home", "pulse", "item", index)}><span class="pulse-kind">${esc(event.kind)}</span><strong>${esc(copy.label)}</strong><small>${esc(copy.detail)}</small></button>${time}</div>`;
    }).join("") || `<p class="home-empty">${esc(t("home.pulse.empty"))}</p>`}</div>
  </section>`;
}

function school(model) {
  return `<section class="home-analysis home-school" ${testIdAttribute("home", "school")}>
    <header><div><span class="eyebrow">${esc(t("home.school.eyebrow"))}</span><h2>${esc(t("home.school.title"))}</h2></div><div class="home-heading-tools"><span>${esc(t("home.school.rows", { count: model.schoolRows.length }))}</span>${help("home.help.school.label", "home.help.school.body", "home-help-school")}</div></header>
    <div class="home-school-table-wrap" role="region" aria-label="${esc(t("home.school.tableAria"))}" tabindex="0" ${testIdAttribute("home", "school", "scroll")}><table><thead><tr>${["capability", "now", "best", "delta", "debt", "retention", "status"].map((key) => `<th>${esc(t(`home.school.${key}`))}</th>`).join("")}</tr></thead><tbody>${model.schoolRows.map((row, index) => `<tr ${testIdAttribute("home", "school", "row", index)}><th><button type="button" class="home-link" data-home-target-kind="capability" data-home-target-id="${esc(row.id)}" ${testIdAttribute("home", "school", "capability", index)}>${esc(row.id)}</button></th><td>${esc(metric(row.now))}/${esc(metric(row.total))}</td><td>${esc(metric(row.best))}</td><td>${esc(metric(row.delta))}</td><td>${esc(metric(row.debt))}</td><td>${esc(metric(row.pRet,{percent:true}))}</td><td>${esc(row.status ?? t("home.common.unknown"))}</td></tr>`).join("")}</tbody></table></div>
  </section>`;
}

function healthDetails(model) {
  const groups = [
    healthGroup("learning", "home.health.learning", [
      ["home.health.latestSchoolScore", metric(model.learning.latestSchoolScore, { percent: true })],
      ["home.health.bestSchoolScore", metric(model.learning.bestSchoolScore, { percent: true })],
      ["home.health.wholeSchoolGrowth", metric(model.learning.wholeSchoolGrowth, { percent: true })],
      ["home.health.gRtn", metric(model.learning.gRtn)], ["home.health.pRet", metric(model.learning.pRet, { percent: true })],
      ["home.health.retainedOptimizerSteps", metric(model.learning.retainedOptimizerSteps, { integer: true })],
    ], model.state.capability ?? "UNKNOWN"),
    healthGroup("curriculum", "home.health.curriculum", [
      ["home.health.qualifiedCapabilities", metric(model.curriculum.qualifiedCapabilities, { integer: true })],
      ["home.health.observedDebt", metric(model.curriculum.observedDebt, { integer: true })],
      ["home.health.activeConcepts", metric(model.curriculum.activeConcepts, { integer: true })],
      ["home.health.ready", metric(model.curriculum.ready, { integer: true })], ["home.health.held", metric(model.curriculum.held, { integer: true })],
      ["home.health.uncovered", metric(model.curriculum.uncovered, { integer: true })],
    ], model.state.school ?? "UNKNOWN"),
    healthGroup("runtime", "home.health.runtime", [
      ["home.health.elapsed", metric(model.runtime.elapsed)], ["home.health.visits", metric(model.runtime.visits, { integer: true })],
      ["home.health.visitRate", metric(model.runtime.visitRate)], ["home.health.retainedCandidates", metric(model.runtime.retainedCandidates, { integer: true })],
      ["home.health.rejectedCandidates", metric(model.runtime.rejectedCandidates, { integer: true })],
      ["home.health.acceptedStepsHour", metric(model.runtime.acceptedStepsHour, { integer: true })],
    ], model.state.run ?? "UNKNOWN"),
    healthGroup("system", "home.health.system", [
      ["home.health.memoryPressure", metric(model.system.memoryPressure, { percent: true })], ["home.health.peakMemory", metric(model.system.peakMemory)],
      ["home.health.diskReserve", metric(model.system.diskReserve)], ["home.health.correctionDebt", metric(model.system.correctionDebt, { integer: true })],
      ["home.health.hardWarnings", metric(model.system.hardWarnings, { integer: true })],
    ], model.state.resource ?? "UNKNOWN"),
  ].join("");
  return `<div class="home-health-shell"><div class="home-health-help">${help("home.help.health.label", "home.help.health.body", "home-help-health")}</div><details class="home-health" ${testIdAttribute("home", "health", "details")}><summary><span>${esc(t("home.health.title"))}</span><small>${esc(t("home.health.summary"))}</small></summary><div class="home-health-grid">${groups}</div></details></div>`;
}

export function renderHomeMarkup(model, { historical = false, nowMs = Date.now(), locale } = {}) {
  const markup = model.startup ? renderStartup(model) : (() => {
    const status = homeStatus(model);
    const badge = model.provenance === "FIXTURE"
      ? t(historical ? "home.provenance.fixtureHistorical" : "home.provenance.fixture")
      : t(historical ? "home.provenance.historical" : "home.provenance.live");
    const temporal = { nowMs, locale };
    const primary = status.attentionPriority === "primary" ? attention(model, "primary", temporal) + currentWork(model, temporal) : currentWork(model, temporal) + attention(model, "secondary", temporal);
    return `<div class="home-dashboard" data-attention-priority="${status.attentionPriority}" ${testIdAttribute("home", "root")}>
      ${statusBand(model, status, badge)}
      <div class="home-primary-grid">${primary}</div>
      <div class="home-analysis-grid">${pulse(model, temporal)}${school(model)}</div>
      ${healthDetails(model)}
    </div>`;
  })();
  assertUniqueTestIds(markup);
  return markup;
}

export function bindHomeInteractions(host, onInspect, onNavigate = () => {}) {
  host.querySelectorAll("[data-home-target-id]").forEach((button) => {
    button.addEventListener("click", () => onInspect({ kind: button.dataset.homeTargetKind, id: button.dataset.homeTargetId }));
  });
  host.querySelectorAll("[data-home-view]").forEach((button) => {
    button.addEventListener("click", () => onNavigate(button.dataset.homeView));
  });
}
