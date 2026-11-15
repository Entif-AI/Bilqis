import { EPISODE_FIXTURES } from "./episode-fixture.mjs";
import { episodeDeepLink } from "./episode-model.mjs";
import { objectDomAttributes } from "../interactions/dom-ref.mjs";
import {
  esc,
  retentionReasonLabel,
  stateBadge,
  stateLabel,
  t,
  testIdAttribute,
  valueOrUnavailable,
} from "./episode-view-shared.mjs";

export function episodeRelations(episode) {
  const sourceRefs = episode.stages.flatMap((stage) =>
    stage.evidence.filter((item) => item.type === "source-revision")
      .map((item) => ({ kind: "source", id: item.id, relation: "source-revision" })));
  return [
    { kind: "capability", id: episode.capabilityId, relation: "target-capability" },
    ...(episode.resultingGeneration !== null
      ? [{ kind: "generation", id: `generation:${episode.resultingGeneration}`, relation: "resulting-generation" }]
      : []),
    ...(episode.checkpointId
      ? [{ kind: "checkpoint", id: episode.checkpointId, relation: "checkpoint" }]
      : []),
    ...sourceRefs,
  ];
}

function transactionNarrative(episode) {
  if (episode.terminalState === "RETAINED") {
    return t("learning.summary.retained", {
      parent: episode.parentGeneration,
      child: episode.resultingGeneration,
    });
  }
  if (episode.terminalState === "REJECTED") {
    return t("learning.summary.rejected", { parent: episode.parentGeneration });
  }
  return t("learning.summary.unknown", { parent: episode.parentGeneration });
}

function retainedStepsText(episode) {
  return episode.retainedOptimizerSteps === null
    ? t("learning.value.unknown")
    : String(episode.retainedOptimizerSteps);
}

function durationText(durationMs) {
  if (durationMs === null) return t("learning.value.unknown");
  return t("learning.value.seconds", { value: (durationMs / 1000).toFixed(1) });
}

export function transactionSummary(episode) {
  return `<section class="episode-summary" ${testIdAttribute("learning", "transaction", "summary")}>
    <header class="episode-summary-heading"><div>
      <span class="eyebrow">${esc(t("learning.summary.eyebrow"))}</span>
      <h3><span class="episode-summary-capability" ${testIdAttribute("learning", "target", "capability")}>${esc(episode.capabilityId)}</span></h3>
      <p ${testIdAttribute("learning", "transaction", "narrative")}>${esc(transactionNarrative(episode))}</p>
    </div>${stateBadge(episode.terminalState, "learning-terminal-state")}</header>
    <div class="episode-summary-grid">
      <dl class="episode-summary-primary">
        <div><dt>${esc(t("learning.summary.parentLabel"))}</dt><dd ${testIdAttribute("learning", "parent", "generation")}>${esc(episode.parentGeneration)}</dd></div>
        <div><dt>${esc(t("learning.summary.workLabel"))}</dt><dd>${esc(t("learning.summary.steps", {
          attempted: episode.attemptedOptimizerSteps,
          intended: episode.intendedOptimizerSteps,
          retained: retainedStepsText(episode),
        }))}</dd></div>
      </dl>
      <dl class="episode-summary-secondary">
        <div><dt>${esc(t("learning.summary.strategyLabel"))}</dt><dd class="machine-value">${esc(episode.strategy)}</dd></div>
        <div><dt>${esc(t("learning.summary.sourceLabel"))}</dt><dd class="machine-value">${esc(episode.sourceFamily)}</dd></div>
        <div><dt>${esc(t("learning.summary.lessonLabel"))}</dt><dd class="machine-value">${esc(episode.lessonFamily)}</dd></div>
      </dl>
      <div class="episode-resource-posture"><span class="episode-subheading">${esc(t("learning.summary.resourcesLabel"))}</span><dl>
        <div><dt>${esc(t("learning.summary.durationLabel"))}</dt><dd>${esc(durationText(episode.durationMs))}</dd></div>
        <div><dt>${esc(t("learning.summary.peakMemoryLabel"))}</dt><dd>${esc(valueOrUnavailable(episode.resourceCost.peakMemoryBytes))}</dd></div>
        <div><dt>${esc(t("learning.summary.stepRateLabel"))}</dt><dd>${esc(valueOrUnavailable(episode.resourceCost.stepRatePerMinute))}</dd></div>
        <div><dt>${esc(t("learning.summary.coverageLabel"))}</dt><dd>${stateBadge(episode.resourceCost.state)}</dd></div>
      </dl></div>
    </div>
    <details class="episode-custody" ${testIdAttribute("learning", "forensics")}><summary>${esc(t("learning.custody.summary"))}</summary><dl>
      <div><dt>${esc(t("learning.custody.candidateId"))}</dt><dd class="machine-value">${esc(episode.candidateId)}</dd></div>
      <div><dt>${esc(t("learning.custody.recordId"))}</dt><dd class="machine-value">${esc(episode.recordId)}</dd></div>
      <div><dt>${esc(t("learning.custody.episodeId"))}</dt><dd class="machine-value">${esc(episode.episodeId)}</dd></div>
      <div><dt>${esc(t("learning.custody.commandState"))}</dt><dd class="machine-value">${esc(episode.commandState)}</dd></div>
      <div><dt>${esc(t("learning.custody.retentionCode"))}</dt><dd class="machine-value">${esc(episode.retentionReason)}</dd></div>
      <div><dt>${esc(t("learning.custody.deepLink"))}</dt><dd class="machine-value">${esc(episodeDeepLink(episode.recordId))}</dd></div>
    </dl><button type="button" class="episode-inspect-candidate" data-candidate-inspect="${esc(episode.candidateId)}"
      ${testIdAttribute("learning", "candidate", "inspect")} ${objectDomAttributes({
        kind: "candidate", id: episode.candidateId, relations: episodeRelations(episode),
      })}>${esc(t("learning.custody.inspect"))}</button></details>
  </section>`;
}

export function picker(episode) {
  return `<div class="episode-picker" ${testIdAttribute("learning", "episode", "picker")}><label for="learning-episode-selector">
    <span>${esc(t("learning.selector.label"))}</span><small>${esc(t("learning.selector.help"))}</small>
  </label><select id="learning-episode-selector" data-episode-selector ${testIdAttribute("learning", "episode", "selector")}>
    ${EPISODE_FIXTURES.map((item) => `<option value="${esc(item.recordId)}" ${item.recordId === episode.recordId ? "selected" : ""}>
      ${esc(item.capabilityId)} · ${esc(stateLabel(item.terminalState))} · ${esc(retentionReasonLabel(item.retentionReason))}
    </option>`).join("")}
  </select></div>`;
}
