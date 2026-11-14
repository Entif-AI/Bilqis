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

export function renderCurrentView(
  state, defense, onInspect, api, onEvidenceSelect, onEvidenceReturn, bootstrap = null,
) {
  const domain = document.querySelector("#domain-view");
  const fixture = document.querySelector(".fixture-card");
  const catalog = document.querySelector("#visual-catalog");
  const summary = document.querySelector("#view-summary");
  document.querySelector("#shell").dataset.view = state?.view ?? "mission-control";
  if (!state) {
    fixture.hidden = true;
    catalog.hidden = true;
    domain.hidden = false;
    const connection = bootstrap?.connection ?? null;
    const serviceState = connection?.serviceReady ? "Ready" : connection?.serviceLive ? "Connected" : "Connecting";
    const learnerState = connection?.learnerReady ? "Accepted learner ready" : connection?.learnerState ?? "Discovering learner";
    const telemetryState = bootstrap?.phase === "telemetry-pending"
      ? "Waiting for first accepted Mission Control projection"
      : bootstrap?.phase === "failed" ? "Bootstrap failed" : "Starting";
    summary.textContent = "Mission Control is establishing the local learner and telemetry pipeline.";
    domain.innerHTML = `<section class="bootstrap-panel" data-phase="${esc(bootstrap?.phase ?? "connecting")}">
      <span class="eyebrow">Startup diagnostics</span><h2>${esc(bootstrap?.phase === "telemetry-pending" ? "Learner connected. Telemetry is still bootstrapping." : "Starting Mission Control")}</h2>
      <p>This view reports each startup boundary separately. Missing telemetry is not rendered as learner failure and fixture data is never substituted for live state.</p>
      <ol class="bootstrap-steps">
        <li data-state="${connection?.serviceLive ? "done" : "active"}"><strong>Local control plane</strong><span>${esc(serviceState)}</span></li>
        <li data-state="${connection?.learnerReady ? "done" : connection?.serviceLive ? "active" : "waiting"}"><strong>Learner discovery</strong><span>${esc(connection?.runId ? `${learnerState} · ${connection.runId}${Number.isSafeInteger(connection.generation) ? ` · generation ${connection.generation}` : ""}` : learnerState)}</span></li>
        <li data-state="${bootstrap?.phase === "ready" ? "done" : bootstrap?.phase === "telemetry-pending" ? "active" : "waiting"}"><strong>Mission Control telemetry</strong><span>${esc(telemetryState)}</span></li>
        <li data-state="${connection?.learnerActive === true ? "done" : "waiting"}"><strong>Trainer</strong><span>${connection?.learnerActive === true ? "Running" : "Not running"}</span></li>
      </ol>
      ${bootstrap?.error ? `<details><summary>Technical detail</summary><code>${esc(bootstrap.error.code ?? bootstrap.error.message ?? String(bootstrap.error))}</code></details>` : ""}
    </section>`;
    return;
  }
  if (state.view === "school") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = "Exact capability comparison and declared prerequisite topology. Grade labels organize only.";
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
    summary.textContent = "Outcome-first learner health, current work, learning pulse and actionable attention.";
    return;
  }
  if (state.view === "atlas") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = "Source-authoritative semantic identity and generation-scoped ABI state, with learned similarity isolated behind a separate lens.";
    return;
  }
  if (state.view === "capability") {
    domain.hidden = false;
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = "Measured chronology, source support, and literal evidence. No inferred causes.";
    return;
  }
  if (state.view === "model") {
    domain.hidden = state.modelSection === "frames";
    if (state.modelSection === "frames") {
      fixture.hidden = true; catalog.hidden = true;
      summary.textContent = "Frame Compiler Explorer · inspect exact packing receipts and causal visibility.";
      return;
    }
    fixture.hidden = true;
    catalog.hidden = true;
    summary.textContent = "Topology, attention health, depth routing and local refinement as measured telemetry only.";
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
    summary.textContent = "Durable candidate transaction replay with explicit retention, rollback and evidence boundaries.";
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
    summary.textContent = "Retained Engram allocation, retrieval telemetry, correction state, and generation deltas without promoting memory hits into semantic or capability authority.";
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
    summary.textContent = "Teacher strategy population, measured outcomes, cost and fidelity observations without unsupported ranking.";
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
    summary.textContent = "Evidenced correction blast radius, append-only correction history, and receipt-backed requalification state without implying perfect neural unlearning.";
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
    summary.textContent = "Independent Impact, Exigency and Osmotic Novelty evidence with reversible aggregation and admitted routing rationale.";
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
    summary.textContent = "Immutable accepted-generation lineage, exact manifest provenance, and literal structured generation differences without winner synthesis.";
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
    summary.textContent = "Exact Mission Control records, provenance links, bounded pagination and literal raw payloads.";
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
    summary.textContent = "Measured resource budgets, decomposed where instrumented, with exact historical comparison and spike correlation.";
    return;
  }
  fixture.hidden = false;
  catalog.hidden = false;
  domain.hidden = true;
  domain.innerHTML = "";
  summary.textContent = defense.historical
    ? "Inspection-only evidence retained while the live command context is unavailable."
    : "Shell foundation ready for provider-neutral BAMF views.";
  catalog.innerHTML = renderComponentCatalog();
}
