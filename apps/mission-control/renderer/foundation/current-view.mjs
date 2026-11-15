import { evidenceT } from "../evidence/evidence-messages.mjs";
import { escapeText as esc } from "../frames/frame-model.mjs";
import { renderEvidenceView } from "../evidence/evidence-view.mjs";
import { t } from "./i18n.mjs";

const FIXTURE_ROUTES = new Set(["model", "learning", "memory", "teacher", "corrections", "salience", "lineage"]);
let fixtureViewPromise = null;

function destinationPurpose(view) {
  return t(`shell.destination.${view}.purpose`);
}

function productionUnavailable(domain) {
  domain.innerHTML = `<section class="ui-state ui-state--empty" role="status" data-test-id="production-data-unavailable"><strong>${esc(t("foundation.defensive.unavailable.label"))}</strong><span>${esc(t("foundation.defensive.unavailable.description"))}</span></section>`;
}

function renderFixtureRoute(args) {
  const expectedView = args.state.view;
  fixtureViewPromise ??= import("./fixture-current-view.mjs");
  void fixtureViewPromise.then(({ renderFixtureCurrentView }) => {
    if (document.querySelector("#shell")?.dataset.view !== expectedView) return;
    renderFixtureCurrentView(args);
  });
}

export function renderCurrentView(
  state, defense, onInspect, api, onEvidenceSelect, onEvidenceReturn, bootstrap = null,
  launchMode = "production",
) {
  const domain = document.querySelector("#domain-view");
  const summary = document.querySelector("#view-summary");
  document.querySelector("#shell").dataset.view = state?.view ?? "mission-control";
  if (!state) {
    domain.hidden = false;
    const connection = bootstrap?.connection ?? null;
    const serviceState = connection?.serviceReady
      ? t("shell.bootstrap.service.ready")
      : connection?.serviceLive ? t("shell.bootstrap.service.connected") : t("shell.bootstrap.service.connecting");
    const learnerState = connection?.learnerReady
      ? t("shell.bootstrap.learner.ready")
      : {
          healthy: t("shell.bootstrap.learner.healthy"),
          "learner-unavailable": t("shell.bootstrap.learner.unavailable"),
        }[connection?.learnerState] ?? t("shell.bootstrap.learner.discovering");
    const telemetryState = bootstrap?.phase === "telemetry-pending"
      ? t("shell.bootstrap.telemetry.waiting")
      : bootstrap?.phase === "failed" ? t("shell.bootstrap.telemetry.failed") : t("shell.bootstrap.telemetry.starting");
    const learnerIdentity = connection?.runId
      ? Number.isSafeInteger(connection.generation)
        ? t("shell.bootstrap.learnerIdentityGeneration", { state: learnerState, runId: connection.runId, generation: connection.generation })
        : t("shell.bootstrap.learnerIdentity", { state: learnerState, runId: connection.runId })
      : learnerState;
    summary.textContent = t("shell.destination.mission-control.bootstrapPurpose");
    domain.innerHTML = `<section class="bootstrap-panel" data-phase="${esc(bootstrap?.phase ?? "connecting")}">
      <span class="eyebrow">${esc(t("shell.bootstrap.eyebrow"))}</span><h2>${esc(bootstrap?.phase === "telemetry-pending" ? t("shell.bootstrap.heading.telemetryPending") : t("shell.bootstrap.heading.starting"))}</h2>
      <p>${esc(t("shell.bootstrap.explanation"))}</p>
      <ol class="bootstrap-steps">
        <li data-state="${connection?.serviceLive ? "done" : "active"}"><strong>${esc(t("shell.bootstrap.step.controlPlane"))}</strong><span>${esc(serviceState)}</span></li>
        <li data-state="${connection?.learnerReady ? "done" : connection?.serviceLive ? "active" : "waiting"}"><strong>${esc(t("shell.bootstrap.step.learner"))}</strong><span>${esc(learnerIdentity)}</span></li>
        <li data-state="${bootstrap?.phase === "ready" ? "done" : bootstrap?.phase === "telemetry-pending" ? "active" : "waiting"}"><strong>${esc(t("shell.bootstrap.step.telemetry"))}</strong><span>${esc(telemetryState)}</span></li>
        <li data-state="${connection?.learnerActive === true ? "done" : "waiting"}"><strong>${esc(t("shell.bootstrap.step.trainer"))}</strong><span>${esc(connection?.learnerActive === true ? t("shell.bootstrap.trainer.running") : t("shell.bootstrap.trainer.notRunning"))}</span></li>
      </ol>
      ${bootstrap?.error ? `<details><summary>${esc(t("shell.bootstrap.technicalDetail"))}</summary><code>${esc(bootstrap.error.code ?? bootstrap.error.message ?? String(bootstrap.error))}</code></details>` : ""}
    </section>`;
    return;
  }
  if (state.view === "school") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.school.purpose");
    domain.innerHTML = `<section class="school-loading" role="status" data-test-id="school-loading">${esc(t("school.production.loading"))}</section>`;
    return;
  }
  if (state.view === "mission-control") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.mission-control.purpose");
    return;
  }
  if (state.view === "atlas") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.atlas.purpose");
    return;
  }
  if (state.view === "capability") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.capability.purpose");
    return;
  }
  if (state.view === "model") {
    domain.hidden = state.modelSection === "frames";
    if (state.modelSection === "frames") {
      summary.textContent = t("shell.destination.model.framesPurpose");
      return;
    }
    domain.hidden = false;
  }
  if (FIXTURE_ROUTES.has(state.view)) {
    domain.hidden = false;
    summary.textContent = destinationPurpose(state.view);
    if (launchMode === "fixtures") {
      domain.innerHTML = `<section class="ui-state ui-state--empty" role="status">${esc(t("shell.bootstrap.telemetry.starting"))}</section>`;
      renderFixtureRoute({ state, domain, summary, onInspect });
    } else {
      productionUnavailable(domain);
    }
    return;
  }
  if (state.view === "evidence") {
    domain.hidden = false;
    summary.textContent = evidenceT("evidence.summary");
    renderEvidenceView(
      domain, api, state.context, state.selected, onEvidenceSelect,
      state.evidenceOrigin ? onEvidenceReturn : null, state.evidenceOrigin,
    );
    return;
  }
  if (state.view === "resources") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.resources.purpose");
    return;
  }
  if (state.view === "operate") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.operate.purpose");
    return;
  }
  domain.hidden = false;
  domain.innerHTML = "";
  summary.textContent = t("shell.destination.fallback.ready");
}
