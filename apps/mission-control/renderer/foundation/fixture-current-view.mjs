import { correctionsT } from "../corrections/corrections-messages.mjs";
import { renderNeuralView } from "../neural/neural-view.mjs";
import { renderEpisodesView } from "../episodes/episode-view.mjs";
import { renderMemoryView } from "../memory/memory-view.mjs";
import { renderTeacherView } from "../teacher/teacher-view.mjs";
import { renderCorrectionsView } from "../corrections/corrections-view.mjs";
import { renderSalienceView } from "../salience/salience-view.mjs";
import { renderLineageView } from "../lineage/lineage-view.mjs";
import { t } from "./i18n.mjs";

export function renderFixtureCurrentView({ state, domain, summary, onInspect }) {
  if (state.view === "model" && state.modelSection !== "frames") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.model.purpose");
    renderNeuralView(domain, (id, kind) => onInspect({
      kind: "neural",
      id,
      details: {
        [t("model.inspector.diagnosticClass")]: kind,
        [t("model.inspector.interpretationBoundary")]: t("model.inspector.telemetryOnly"),
      },
    }));
    return true;
  }
  if (state.view === "learning") {
    domain.hidden = false;
    summary.textContent = t("learning.currentView.summary");
    renderEpisodesView(domain, (id, kind) => onInspect({
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
    return true;
  }
  if (state.view === "memory") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.memory.purpose");
    renderMemoryView(domain, (id, slot) => onInspect({
      kind: "memory",
      id,
      label: id,
      relations: [
        ...slot.capabilities.map((relatedId) => ({ kind: "capability", id: relatedId, relation: "capability" })),
        ...slot.episodes.map((relatedId) => ({ kind: "episode", id: relatedId, relation: "episode" })),
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
    return true;
  }
  if (state.view === "teacher") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.teacher.purpose");
    renderTeacherView(domain, (id, strategy, relations) => onInspect({
      kind: "strategy",
      id,
      label: strategy?.label ?? id,
      relations,
      details: {
        [t("teacher.inspector.role")]: strategy?.role ?? "UNKNOWN",
        [t("teacher.inspector.attempts")]: strategy?.attempts ?? "UNKNOWN",
        [t("teacher.inspector.retained")]: strategy?.retained ?? "UNKNOWN",
        [t("teacher.inspector.noGain")]: strategy?.noGain ?? "UNKNOWN",
        [t("teacher.inspector.interference")]: strategy?.interference ?? "UNKNOWN",
        [t("teacher.inspector.comparisonPosture")]: t("teacher.inspector.descriptiveOnly"),
        [t("teacher.inspector.policyMutation")]: t("teacher.inspector.none"),
      },
    }), state.selected?.kind === "strategy" ? state.selected.id : null);
    return true;
  }
  if (state.view === "corrections") {
    domain.hidden = false;
    summary.textContent = correctionsT("corrections.summary");
    renderCorrectionsView(domain, (id, node) => onInspect({
      kind: "correction", id, fixtureBacked: true,
      details: {
        [correctionsT("corrections.evidence.details")]: node.kind,
        [correctionsT("corrections.evidence.state")]: node.state,
        [correctionsT("corrections.evidence.refs")]:
          node.evidenceRefs.length ? node.evidenceRefs : [correctionsT("corrections.evidence.none")],
        [correctionsT("corrections.evidence.projection")]: correctionsT("corrections.fixture.title"),
      },
    }), { onReference: (ref, kind) => onInspect({
      kind: "correction", id: ref, fixtureBacked: true,
      details: {
        [correctionsT("corrections.evidence.reference")]: ref,
        [correctionsT("corrections.evidence.referenceKind")]: correctionsT(`corrections.reference.${kind}`),
        [correctionsT("corrections.evidence.projection")]: correctionsT("corrections.fixture.title"),
      },
    }) });
    return true;
  }
  if (state.view === "salience") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.salience.purpose");
    renderSalienceView(domain, (id, details) => onInspect({
      kind: "salience-observation",
      id,
      details,
    }), state.selected?.kind === "salience-observation" ? state.selected.id : null);
    return true;
  }
  if (state.view === "lineage") {
    domain.hidden = false;
    summary.textContent = t("shell.destination.lineage.purpose");
    renderLineageView(domain, (id, node) => onInspect({
      kind: "generation",
      id,
      label: t("shell.inspector.generationLabel", { generation: node.generation }),
      relations: [{ kind: "checkpoint", id: `checkpoint:${node.checkpointSha256}`, relation: "checkpoint" }],
      details: {
        [t("shell.inspector.generation")]: node.generation,
        [t("shell.inspector.detail.manifestSha256")]: node.manifestSha256,
        [t("shell.inspector.detail.parentManifest")]:
          node.parentManifestSha256 ?? t("shell.inspector.value.genesis"),
        [t("shell.inspector.detail.transition")]: node.transitionClass,
        [t("shell.inspector.detail.checkpointSha256")]: node.checkpointSha256,
      },
    }), ["generation", "checkpoint"].includes(state.selected?.kind) ? state.selected.id : null, state.context);
    return true;
  }
  return false;
}
