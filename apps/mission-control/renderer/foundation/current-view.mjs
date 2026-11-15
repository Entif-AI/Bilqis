import { correctionsT } from "../corrections/corrections-messages.mjs";
import { evidenceT } from "../evidence/evidence-messages.mjs";
import { escapeText as esc } from "../frames/frame-model.mjs";
import { renderEvidenceView } from "../evidence/evidence-view.mjs";
import { t } from "./i18n.mjs";

export function renderCurrentView(
  state, defense, onInspect, api, onEvidenceSelect, onEvidenceReturn, bootstrap = null,
  fixtureViews = null,
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
    if (state.context.mode === "HISTORICAL") {
      domain.innerHTML = `<section class="fixture-card" data-test-id="school-historical-unavailable"><span class="eyebrow">${esc(t("shell.school.historical.eyebrow"))}</span><h2>${esc(t("shell.school.historical.title"))}</h2>
        <p>${esc(t("shell.school.historical.summary", { generation: state.context.generation }))}</p></section>`;
      return;
    }
    domain.innerHTML = fixtureViews && state.context.fixture === true
      ? ""
      : productionProjectionMarkup("school");
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
    summary.textContent = t("shell.destination.model.purpose");
    if (!fixtureViews?.renderNeuralView || state.context.fixture !== true) {
      domain.innerHTML = productionProjectionMarkup("model");
      return;
    }
    fixtureViews.renderNeuralView(domain, (id, kind) => onInspect({
      kind: "neural",
      id,
      details: {
        [t("model.inspector.diagnosticClass")]: kind,
        [t("model.inspector.interpretationBoundary")]: t("model.inspector.telemetryOnly"),
      },
    }));
    return;
  }
  if (state.view === "learning") {
    domain.hidden = false;
    summary.textContent = t("learning.currentView.summary");
    if (!fixtureViews?.renderEpisodesView || state.context.fixture !== true) {
      domain.innerHTML = "";
      return;
    }
    fixtureViews.renderEpisodesView(domain, (id, kind) => onInspect({
      kind: "evidence",
      id,
      details: {
        [t("learning.inspector.evidenceType")]: kind,
        [t("learning.inspector.interpretationBoundary")]: t("learning.inspector.durableEvidenceOnly"),
      },
    }), ["episode", "candidate"].includes(state.selected?.kind) ? state.selected.id : null,
    (id, episode, relations) => onInspect({
      kind: "candidate",
      id,
      label: id,
      relations,
      details: {
        [t("learning.inspector.targetCapability")]: episode.capabilityId,
        [t("learning.inspector.parentGeneration")]: episode.parentGeneration,
        [t("learning.inspector.terminalState")]: episode.terminalState,
        [t("learning.inspector.retentionReason")]: episode.retentionReason,
      },
    }));
    return;
  }
  if (state.view === "memory") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.memory.purpose");
    if (!fixtureViews?.renderMemoryView || state.context.fixture !== true) {
      domain.innerHTML = productionProjectionMarkup("memory");
      return;
    }
    fixtureViews.renderMemoryView(domain, (id, slot) => onInspect({
      kind: "memory",
      id,
      label: id,
      relations: [
        ...slot.capabilities.map((relatedId) => ({
          kind: "capability", id: relatedId, relation: "capability",
        })),
        ...slot.episodes.map((relatedId) => ({
          kind: "episode", id: relatedId, relation: "episode",
        })),
      ],
      details: {
        [t("shell.inspector.detail.slotAddress")]: `motif.page.${slot.pageIndex}[${slot.rowIndex}]`,
        [t("shell.inspector.detail.creationGeneration")]: slot.createdGeneration,
        [t("shell.inspector.detail.sourceEligibility")]: slot.sourceEligibility,
        [t("shell.inspector.detail.correctionState")]: slot.correctionState,
        [t("shell.inspector.detail.parameterBank")]: slot.parameterBank,
        [t("shell.inspector.detail.relatedCapabilities")]: slot.capabilities,
        [t("shell.inspector.detail.relatedEpisodes")]: slot.episodes,
      },
    }), state.selected?.kind === "memory" ? state.selected.id : null, state.context);
    return;
  }
  if (state.view === "teacher") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.teacher.purpose");
    domain.innerHTML = "";
    return;
  }
  if (state.view === "corrections") {
    domain.hidden = false;
    summary.textContent = correctionsT("corrections.summary");
    if (!fixtureViews?.renderCorrectionsView || state.context.fixture !== true) {
      domain.innerHTML = productionProjectionMarkup("corrections");
      return;
    }
    fixtureViews.renderCorrectionsView(domain, (id, node) => onInspect({
      kind: "correction", id, fixtureBacked: true,
      details: {
        [correctionsT("corrections.evidence.details")]: node.kind,
        [correctionsT("corrections.evidence.state")]: node.state,
        [correctionsT("corrections.evidence.refs")]: node.evidenceRefs.length ? node.evidenceRefs : [correctionsT("corrections.evidence.none")],
        [correctionsT("corrections.evidence.projection")]: correctionsT("corrections.fixture.title"),
      },
    }), {onReference: (ref, kind) => onInspect({
      kind: "correction", id: ref, fixtureBacked: true,
      details: {
        [correctionsT("corrections.evidence.reference")]: ref,
        [correctionsT("corrections.evidence.referenceKind")]: correctionsT(`corrections.reference.${kind}`),
        [correctionsT("corrections.evidence.projection")]: correctionsT("corrections.fixture.title"),
      },
    })});
    return;
  }
  if (state.view === "salience") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.salience.purpose");
    domain.innerHTML = "";
    return;
  }
  if (state.view === "lineage") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.lineage.purpose");
    if (!fixtureViews?.renderLineageView || state.context.fixture !== true) {
      domain.innerHTML = productionProjectionMarkup("lineage");
      return;
    }
    fixtureViews.renderLineageView(domain, (id, node) => onInspect({
      kind: "generation",
      id,
      label: t("shell.inspector.generationLabel", { generation: node.generation }),
      relations: [
        { kind: "checkpoint", id: `checkpoint:${node.checkpointSha256}`, relation: "checkpoint" },
      ],
      details: {
        [t("shell.inspector.generation")]: node.generation,
        [t("shell.inspector.detail.manifestSha256")]: node.manifestSha256,
        [t("shell.inspector.detail.parentManifest")]: node.parentManifestSha256 ?? t("shell.inspector.value.genesis"),
        [t("shell.inspector.detail.transition")]: node.transitionClass,
        [t("shell.inspector.detail.checkpointSha256")]: node.checkpointSha256,
      },
    }), ["generation", "checkpoint"].includes(state.selected?.kind) ? state.selected.id : null, state.context);
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

function productionProjectionMarkup(destination) {
  return `<section class="fixture-card" data-test-id="production-projection-required-${esc(destination)}">
    <span class="eyebrow">${esc(t("shell.productionProjection.eyebrow"))}</span>
    <h2>${esc(t("shell.productionProjection.title"))}</h2>
    <p>${esc(t("shell.productionProjection.description", {
      destination: t(`shell.destination.${destination}`),
    }))}</p>
  </section>`;
}
