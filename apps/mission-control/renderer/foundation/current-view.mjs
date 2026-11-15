import { escapeText as esc } from "../frames/frame-model.mjs";
import { renderSchoolView } from "../school/school-view.mjs";
import { renderNeuralView } from "../neural/neural-view.mjs";
import { renderEpisodesView } from "../episodes/episode-view.mjs";
import { renderMemoryView } from "../memory/memory-view.mjs";
import { renderTeacherView } from "../teacher/teacher-view.mjs";
import { renderCorrectionsView } from "../corrections/corrections-view.mjs";
import { renderSalienceView } from "../salience/salience-view.mjs";
import { renderLineageView } from "../lineage/lineage-view.mjs";
import { renderEvidenceView } from "../evidence/evidence-view.mjs";
import { t } from "./i18n.mjs";

export function renderCurrentView(
  state, defense, onInspect, api, onEvidenceSelect, onEvidenceReturn, bootstrap = null,
) {
  const domain = document.querySelector("#domain-view");
  const fixture = document.querySelector("#domain-context-boundary");
  const catalog = document.querySelector("#visual-catalog");
  const summary = document.querySelector("#view-summary");
  document.querySelector("#shell").dataset.view = state?.view ?? "mission-control";
  if (!state) {
    fixture.hidden = true;
    catalog.hidden = true;
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
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.school.purpose");
    if (state.context.mode === "HISTORICAL") {
      domain.innerHTML = `<section class="fixture-card"><span class="eyebrow">Historical School lens</span><h2>UNAVAILABLE</h2>
        <p>The checked-in School matrix has no exact snapshot for generation ${state.context.generation}. The global historical lens remains unchanged.</p></section>`;
      return;
    }
    renderSchoolView(domain, (id, row, neighborhood) => onInspect({
      kind: "capability",
      id,
      label: id,
      relations: [
        ...neighborhood.prerequisites.map((relatedId) => ({
          kind: "capability", id: relatedId, relation: "prerequisite",
        })),
        ...neighborhood.dependents.map((relatedId) => ({
          kind: "capability", id: relatedId, relation: "dependent",
        })),
      ],
      details: {
        "WAS/TOP/NOW/ALL": row.was + "/" + row.top + "/" + row.now + "/" + row.total,
        Debt: row.debt,
        "P(RET)": row.pRet ?? "NOT MEASURED",
        Prerequisites: row.prerequisites.length ? row.prerequisites : ["none"],
        "Source state": row.sourceState,
        "Implementation state": row.implementationState,
        "Qualification state": row.qualificationState,
      },
    }), state.selected?.kind === "capability" ? state.selected.id : null);
    return;
  }
  if (state.view === "mission-control") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.mission-control.purpose");
    return;
  }
  if (state.view === "atlas") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.atlas.purpose");
    return;
  }
  if (state.view === "capability") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.capability.purpose");
    return;
  }
  if (state.view === "model") {
    domain.hidden = state.modelSection === "frames";
    if (state.modelSection === "frames") {
      fixture.hidden = true; catalog.hidden = true;
      summary.textContent = t("shell.destination.model.framesPurpose");
      return;
    }
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.model.purpose");
    renderNeuralView(domain, (id, kind) => onInspect({
      kind: "neural",
      id,
      details: {
        "Diagnostic class": kind,
        "Interpretation boundary": "Measured routing/runtime telemetry only",
      },
    }));
    return;
  }
  if (state.view === "learning") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.learning.purpose");
    renderEpisodesView(domain, (id, kind) => onInspect({
      kind: "evidence",
      id,
      details: { "Evidence type": kind, "Interpretation boundary": "Durable episode evidence only" },
    }), ["episode", "candidate"].includes(state.selected?.kind) ? state.selected.id : null,
    (id, episode, relations) => onInspect({
      kind: "candidate",
      id,
      label: id,
      relations,
      details: {
        "Target capability": episode.capabilityId,
        "Parent generation": episode.parentGeneration,
        "Terminal state": episode.terminalState,
        "Retention reason": episode.retentionReason,
      },
    }));
    return;
  }
  if (state.view === "memory") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.memory.purpose");
    renderMemoryView(domain, (id, slot) => onInspect({
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
        "Slot address": `motif.page.${slot.pageIndex}[${slot.rowIndex}]`,
        "Creation generation": slot.createdGeneration,
        "Source eligibility": slot.sourceEligibility,
        "Correction state": slot.correctionState,
        "Parameter bank": slot.parameterBank,
        "Related capabilities": slot.capabilities,
        "Related episodes": slot.episodes,
      },
    }), state.selected?.kind === "memory" ? state.selected.id : null, state.context);
    return;
  }
  if (state.view === "teacher") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.teacher.purpose");
    renderTeacherView(domain, (id, strategy, relations) => onInspect({
      kind: "strategy",
      id,
      label: strategy?.label ?? id,
      relations,
      details: {
        Role: strategy?.role ?? "UNKNOWN",
        Attempts: strategy?.attempts ?? "UNKNOWN",
        Retained: strategy?.retained ?? "UNKNOWN",
        "No gain": strategy?.noGain ?? "UNKNOWN",
        Interference: strategy?.interference ?? "UNKNOWN",
        "Comparison posture": "Descriptive evidence only",
        "Policy mutation": "None",
      },
    }));
    return;
  }
  if (state.view === "corrections") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.corrections.purpose");
    renderCorrectionsView(domain, (id, node) => onInspect({
      kind: "correction",
      id,
      details: {
        "Artifact class": node.kind,
        "Impact state": node.state,
        "Evidence refs": node.evidenceRefs.length ? node.evidenceRefs : ["UNTRACKED / UNKNOWN"],
        "Interpretation boundary": "Known exposure and requalification evidence only",
      },
    }));
    return;
  }
  if (state.view === "salience") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.salience.purpose");
    renderSalienceView(domain, (id, details) => onInspect({
      kind: "salience-observation",
      id,
      details,
    }));
    return;
  }
  if (state.view === "lineage") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.lineage.purpose");
    renderLineageView(domain, (id, node) => onInspect({
      kind: "generation",
      id,
      label: `Generation ${node.generation}`,
      relations: [
        { kind: "checkpoint", id: `checkpoint:${node.checkpointSha256}`, relation: "checkpoint" },
      ],
      details: {
        Generation: node.generation,
        "Manifest SHA-256": node.manifestSha256,
        "Parent manifest": node.parentManifestSha256 ?? "GENESIS",
        Transition: node.transitionClass,
        "Checkpoint SHA-256": node.checkpointSha256,
      },
    }), ["generation", "checkpoint"].includes(state.selected?.kind) ? state.selected.id : null, state.context);
    return;
  }
  if (state.view === "evidence") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.evidence.purpose");
    renderEvidenceView(
      domain, api, state.context, state.selected, onEvidenceSelect,
      state.evidenceOrigin ? onEvidenceReturn : null,
    );
    return;
  }
  if (state.view === "resources") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = t("shell.destination.resources.purpose");
    return;
  }
  fixture.hidden = false;
  catalog.hidden = false;
  domain.hidden = true;
  domain.innerHTML = "";
  summary.textContent = defense.historical
    ? t("shell.destination.fallback.historical")
    : t("shell.destination.fallback.ready");
  catalog.innerHTML = renderComponentCatalog();
}
