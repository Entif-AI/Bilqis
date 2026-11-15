import { EPISODE_FIXTURES, EPISODE_STAGES } from "./episode-fixture.mjs";
import {
  diffRows,
  episodeById,
  episodeDeepLink,
  rejectionClass,
  replaySlice,
  retainedTransition,
  rollbackInvariant,
} from "./episode-model.mjs";
import { objectDomAttributes } from "../interactions/dom-ref.mjs";
import { escapeText as esc } from "../frames/frame-model.mjs";
import { t } from "../foundation/i18n.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";

const ui = {
  selectedId: EPISODE_FIXTURES[0].recordId,
  stageIndex: EPISODE_STAGES.length - 1,
};

const STATE_MARKERS = Object.freeze({
  PRESENT: "✓",
  RETAINED: "✓",
  REJECTED: "×",
  UNKNOWN: "?",
  PENDING: "…",
  PARTIAL: "◐",
  MISSING: "∅",
  UNAVAILABLE: "∅",
  MEASURED: "✓",
});

function stateLabel(state) {
  const key = `learning.state.${state}`;
  try {
    return t(key);
  } catch {
    return String(state);
  }
}

function stateBadge(state, testId = null) {
  const normalized = String(state).toLowerCase();
  const marker = STATE_MARKERS[state] ?? "?";
  const testHook = testId ? ` ${testIdAttribute(testId)}` : "";
  return `<span class="episode-state" data-state="${esc(normalized)}"${testHook}>
    <span aria-hidden="true">${marker}</span><span>${esc(stateLabel(state))}</span>
  </span>`;
}

function valueOrUnavailable(value) {
  if (value === null || value === undefined || value === "UNAVAILABLE") return t("learning.value.unavailable");
  if (value === "UNKNOWN") return t("learning.value.unknown");
  return String(value);
}

function retainedStepsText(episode) {
  return episode.retainedOptimizerSteps === null ? t("learning.value.unknown") : String(episode.retainedOptimizerSteps);
}

function durationText(durationMs) {
  if (durationMs === null) return t("learning.value.unknown");
  return t("learning.value.seconds", { value: (durationMs / 1000).toFixed(1) });
}

function retentionReasonLabel(reason) {
  try {
    return t(`learning.reason.${reason}`);
  } catch {
    return String(reason);
  }
}

function episodeRelations(episode) {
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

function transactionSummary(episode) {
  return `<section class="episode-summary" ${testIdAttribute("learning", "transaction", "summary")}>
    <header class="episode-summary-heading">
      <div>
        <span class="eyebrow">${esc(t("learning.summary.eyebrow"))}</span>
        <h3><span class="episode-summary-capability" ${testIdAttribute("learning", "target", "capability")}>${esc(episode.capabilityId)}</span></h3>
        <p ${testIdAttribute("learning", "transaction", "narrative")}>${esc(transactionNarrative(episode))}</p>
      </div>
      ${stateBadge(episode.terminalState, "learning-terminal-state")}
    </header>

    <div class="episode-summary-grid">
      <dl class="episode-summary-primary">
        <div>
          <dt>${esc(t("learning.summary.parentLabel"))}</dt>
          <dd ${testIdAttribute("learning", "parent", "generation")}>${esc(episode.parentGeneration)}</dd>
        </div>
        <div>
          <dt>${esc(t("learning.summary.workLabel"))}</dt>
          <dd>${esc(t("learning.summary.steps", {
            attempted: episode.attemptedOptimizerSteps,
            intended: episode.intendedOptimizerSteps,
            retained: retainedStepsText(episode),
          }))}</dd>
        </div>
      </dl>

      <dl class="episode-summary-secondary">
        <div><dt>${esc(t("learning.summary.strategyLabel"))}</dt><dd class="machine-value">${esc(episode.strategy)}</dd></div>
        <div><dt>${esc(t("learning.summary.sourceLabel"))}</dt><dd class="machine-value">${esc(episode.sourceFamily)}</dd></div>
        <div><dt>${esc(t("learning.summary.lessonLabel"))}</dt><dd class="machine-value">${esc(episode.lessonFamily)}</dd></div>
      </dl>

      <div class="episode-resource-posture">
        <span class="episode-subheading">${esc(t("learning.summary.resourcesLabel"))}</span>
        <dl>
          <div><dt>${esc(t("learning.summary.durationLabel"))}</dt><dd>${esc(durationText(episode.durationMs))}</dd></div>
          <div><dt>${esc(t("learning.summary.peakMemoryLabel"))}</dt><dd>${esc(valueOrUnavailable(episode.resourceCost.peakMemoryBytes))}</dd></div>
          <div><dt>${esc(t("learning.summary.stepRateLabel"))}</dt><dd>${esc(valueOrUnavailable(episode.resourceCost.stepRatePerMinute))}</dd></div>
          <div><dt>${esc(t("learning.summary.coverageLabel"))}</dt><dd>${stateBadge(episode.resourceCost.state)}</dd></div>
        </dl>
      </div>
    </div>

    <details class="episode-custody" ${testIdAttribute("learning", "forensics")}>
      <summary>${esc(t("learning.custody.summary"))}</summary>
      <dl>
        <div><dt>${esc(t("learning.custody.candidateId"))}</dt><dd class="machine-value">${esc(episode.candidateId)}</dd></div>
        <div><dt>${esc(t("learning.custody.recordId"))}</dt><dd class="machine-value">${esc(episode.recordId)}</dd></div>
        <div><dt>${esc(t("learning.custody.episodeId"))}</dt><dd class="machine-value">${esc(episode.episodeId)}</dd></div>
        <div><dt>${esc(t("learning.custody.commandState"))}</dt><dd class="machine-value">${esc(episode.commandState)}</dd></div>
        <div><dt>${esc(t("learning.custody.retentionCode"))}</dt><dd class="machine-value">${esc(episode.retentionReason)}</dd></div>
        <div><dt>${esc(t("learning.custody.deepLink"))}</dt><dd class="machine-value">${esc(episodeDeepLink(episode.recordId))}</dd></div>
      </dl>
      <button type="button" class="episode-inspect-candidate" data-candidate-inspect="${esc(episode.candidateId)}"
        ${testIdAttribute("learning", "candidate", "inspect")} ${objectDomAttributes({
          kind: "candidate", id: episode.candidateId, relations: episodeRelations(episode),
        })}>${esc(t("learning.custody.inspect"))}</button>
    </details>
  </section>`;
}

function evidenceButtons(stage) {
  if (!stage.evidence.length) {
    return `<p class="episode-evidence-empty" ${testIdAttribute("learning", "stage", "evidence", "empty")}>${esc(t("learning.lifecycle.noEvidence"))}</p>`;
  }
  return stage.evidence.map((item, index) => {
    const typeLabel = t(`learning.evidenceType.${item.type}`);
    return `<button type="button" data-episode-evidence="${esc(item.id)}" data-evidence-type="${esc(item.type)}"
      ${testIdAttribute("learning", "stage", "evidence", stage.id, index)}>
      <span>${esc(t("learning.lifecycle.openEvidence", { type: typeLabel }))}</span>
      <code>${esc(item.id)}</code>
    </button>`;
  }).join("");
}

function replayPanel(episode, stageIndex = ui.stageIndex) {
  const replay = replaySlice(episode, stageIndex);
  return `<section class="episode-lifecycle" aria-labelledby="learning-lifecycle-title" ${testIdAttribute("learning", "lifecycle")}>
    <header class="episode-section-heading">
      <div>
        <span class="eyebrow">${esc(t("learning.lifecycle.eyebrow"))}</span>
        <h3 id="learning-lifecycle-title">${esc(t("learning.lifecycle.title"))}</h3>
      </div>
      <span class="episode-stage-counter">${esc(t("learning.lifecycle.counter", {
        current: replay.stageIndex + 1,
        total: EPISODE_STAGES.length,
      }))}</span>
    </header>
    <div class="episode-replay">
      <ol class="episode-stage-list" aria-label="${esc(t("learning.lifecycle.title"))}">
        ${episode.stages.map((stage, index) => `<li class="episode-stage" data-state="${esc(stage.state.toLowerCase())}" data-active="${index === replay.stageIndex}">
          <button type="button" data-stage-index="${index}" aria-pressed="${index === replay.stageIndex}"
            ${index === replay.stageIndex ? 'aria-current="step"' : ""}
            ${testIdAttribute("learning", "stage", stage.id)}>
            <span class="episode-stage-number" aria-hidden="true">${index + 1}</span>
            <span class="episode-stage-copy"><strong>${esc(t(stage.labelKey))}</strong>${stateBadge(stage.state)}</span>
          </button>
        </li>`).join("")}
      </ol>
      <article class="episode-stage-detail" ${testIdAttribute("learning", "stage", "detail")}>
        <span class="eyebrow">${esc(t("learning.lifecycle.selected"))}</span>
        <div class="episode-stage-detail-heading">
          <h4>${esc(t(replay.active.labelKey))}</h4>
          ${stateBadge(replay.active.state, "learning-active-stage-state")}
        </div>
        <p>${esc(t(replay.active.detailKey))}</p>
        <details class="episode-evidence-disclosure" ${testIdAttribute("learning", "stage", "evidence")}>
          <summary>${esc(t("learning.lifecycle.evidenceSummary", { count: replay.active.evidence.length }))}</summary>
          <div class="episode-evidence">${evidenceButtons(replay.active)}</div>
        </details>
      </article>
    </div>
  </section>`;
}

function displayComparisonValue(value) {
  if (value === "UNAVAILABLE") return t("learning.value.unavailable");
  return String(value);
}

function diffPanel(episode) {
  return `<section class="episode-comparison" aria-labelledby="learning-comparison-title" ${testIdAttribute("learning", "comparison")}>
    <header class="episode-section-heading">
      <div>
        <span class="eyebrow">${esc(t("learning.comparison.eyebrow"))}</span>
        <h3 id="learning-comparison-title">${esc(t("learning.comparison.title"))}</h3>
      </div>
    </header>
    <div class="episode-diff-wrap" tabindex="0" ${testIdAttribute("learning", "comparison", "scroll")}>
      <table class="episode-diff" ${testIdAttribute("learning", "comparison", "table")}>
        <caption>${esc(t("learning.comparison.caption"))}</caption>
        <thead><tr>
          <th scope="col">${esc(t("learning.comparison.evidence"))}</th>
          <th scope="col">${esc(t("learning.comparison.before"))}</th>
          <th scope="col">${esc(t("learning.comparison.challenger"))}</th>
          <th scope="col">${esc(t("learning.comparison.committed"))}</th>
          <th scope="col">${esc(t("learning.comparison.coverage"))}</th>
        </tr></thead>
        <tbody>${diffRows(episode).map((row) => `<tr data-state="${esc(String(row.state).toLowerCase())}">
          <th scope="row">${esc(t(row.labelKey))}</th>
          <td>${esc(displayComparisonValue(row.before))}</td>
          <td>${esc(displayComparisonValue(row.challenger))}</td>
          <td>${esc(displayComparisonValue(row.committed))}</td>
          <td>${stateBadge(row.state)}</td>
        </tr>`).join("")}</tbody>
      </table>
    </div>
    ${episode.terminalState === "REJECTED"
      ? `<p class="episode-comparison-note">${esc(t("learning.comparison.rejectedNote"))}</p>`
      : ""}
  </section>`;
}

function invariantRow(labelKey, passed, value = null) {
  const result = value ?? (passed ? t("learning.outcome.preserved") : t("learning.outcome.mismatch"));
  return `<tr data-pass="${passed}">
    <th scope="row">${esc(t(labelKey))}</th>
    <td><span class="episode-proof-marker" aria-hidden="true">${passed ? "✓" : "×"}</span> ${esc(result)}</td>
  </tr>`;
}

function terminalProof(episode) {
  const transition = retainedTransition(episode);
  if (transition) {
    return `<section class="episode-outcome" data-outcome="retained" aria-live="polite" ${testIdAttribute("learning", "outcome", "proof")}>
      <header class="episode-section-heading">
        <div>
          <span class="eyebrow">${esc(t("learning.outcome.eyebrow"))}</span>
          <h3>${esc(t("learning.outcome.retainedTitle"))}</h3>
          <p>${esc(t("learning.outcome.retainedDetail"))}</p>
        </div>
        ${stateBadge("RETAINED")}
      </header>
      <dl class="episode-transition">
        <div><dt>${esc(t("learning.outcome.parentGeneration"))}</dt><dd>${esc(transition.parentGeneration)}</dd></div>
        <span class="episode-transition-arrow" aria-hidden="true">→</span>
        <div><dt>${esc(t("learning.outcome.childGeneration"))}</dt><dd>${esc(transition.childGeneration)}</dd></div>
        <div class="episode-transition-checkpoint"><dt>${esc(t("learning.outcome.checkpoint"))}</dt><dd class="machine-value">${esc(transition.checkpointId)}</dd></div>
      </dl>
    </section>`;
  }

  const rollback = rollbackInvariant(episode);
  if (!rollback) {
    return `<section class="episode-outcome" data-outcome="unknown" aria-live="polite" ${testIdAttribute("learning", "outcome", "proof")}>
      <header class="episode-section-heading">
        <div>
          <span class="eyebrow">${esc(t("learning.outcome.eyebrow"))}</span>
          <h3>${esc(t("learning.outcome.pendingTitle"))}</h3>
          <p>${esc(t("learning.outcome.pendingDetail"))}</p>
        </div>
        ${stateBadge("UNKNOWN")}
      </header>
    </section>`;
  }

  const classification = rejectionClass(episode);
  return `<section class="episode-outcome" data-outcome="rejected" data-class="${classification}" aria-live="polite" ${testIdAttribute("learning", "outcome", "proof")}>
    <header class="episode-section-heading">
      <div>
        <span class="eyebrow">${esc(t("learning.outcome.eyebrow"))}</span>
        <h3>${esc(t("learning.outcome.rejectedTitle"))}</h3>
        <p><strong>${esc(t(classification === "INTERFERENCE" ? "learning.outcome.interference" : "learning.outcome.noGain"))}</strong>
          · ${esc(retentionReasonLabel(episode.retentionReason))}</p>
      </div>
      ${stateBadge("REJECTED")}
    </header>
    <table class="episode-rollback-table" ${testIdAttribute("learning", "rollback", "table")}>
      <thead><tr><th scope="col">${esc(t("learning.outcome.invariant"))}</th><th scope="col">${esc(t("learning.outcome.result"))}</th></tr></thead>
      <tbody>
        ${invariantRow("learning.outcome.neural", rollback.neuralUnchanged)}
        ${invariantRow("learning.outcome.optimizer", rollback.optimizerUnchanged)}
        ${invariantRow("learning.outcome.allocation", rollback.allocationUnchanged)}
        ${invariantRow("learning.outcome.retainedSteps", rollback.retainedOptimizerStepsZero, String(episode.retainedOptimizerSteps))}
        ${invariantRow("learning.outcome.child", rollback.noChildGeneration, t("learning.outcome.none"))}
      </tbody>
    </table>
  </section>`;
}

function picker(episode) {
  return `<div class="episode-picker" ${testIdAttribute("learning", "episode", "picker")}>
    <label for="learning-episode-selector">
      <span>${esc(t("learning.selector.label"))}</span>
      <small>${esc(t("learning.selector.help"))}</small>
    </label>
    <select id="learning-episode-selector" data-episode-selector ${testIdAttribute("learning", "episode", "selector")}>
      ${EPISODE_FIXTURES.map((item) => `<option value="${esc(item.recordId)}" ${item.recordId === episode.recordId ? "selected" : ""}>
        ${esc(item.capabilityId)} · ${esc(stateLabel(item.terminalState))} · ${esc(retentionReasonLabel(item.retentionReason))}
      </option>`).join("")}
    </select>
  </div>`;
}

function bind(container, inspectEvidence, inspectCandidate, episode) {
  container.querySelector("[data-episode-selector]")?.addEventListener("change", (event) => {
    ui.selectedId = event.currentTarget.value;
    ui.stageIndex = EPISODE_STAGES.length - 1;
    renderEpisodesView(container, inspectEvidence, ui.selectedId, inspectCandidate);
  });
  container.querySelectorAll("[data-stage-index]").forEach((button) => button.addEventListener("click", () => {
    ui.stageIndex = Number(button.dataset.stageIndex);
    renderEpisodesView(container, inspectEvidence, ui.selectedId, inspectCandidate);
  }));
  container.querySelectorAll("[data-episode-evidence]").forEach((button) => button.addEventListener("click", () => {
    inspectEvidence(button.dataset.episodeEvidence, button.dataset.evidenceType);
  }));
  container.querySelector("[data-candidate-inspect]")?.addEventListener("click", () => {
    inspectCandidate?.(episode.candidateId, episode, episodeRelations(episode));
  });
}

export function renderEpisodesView(container, inspectEvidence, selectedId = null, inspectCandidate = null) {
  if (selectedId) {
    const selected = episodeById(selectedId);
    if (selected.recordId === selectedId || selected.episodeId === selectedId || selected.candidateId === selectedId) {
      ui.selectedId = selected.recordId;
    }
  }
  const episode = episodeById(ui.selectedId);
  container.innerHTML = episodeMarkupForTest(episode.recordId, ui.stageIndex);
  bind(container, inspectEvidence, inspectCandidate, episode);
}

export function episodeMarkupForTest(selectedId = EPISODE_FIXTURES[0].recordId, stageIndex = EPISODE_STAGES.length - 1) {
  const episode = episodeById(selectedId);
  return `<div class="episodes-view" ${testIdAttribute("learning", "view")}>
    <header class="episodes-heading" ${testIdAttribute("learning", "heading")}>
      <div><span class="eyebrow">${esc(t("learning.view.eyebrow"))}</span><h2>${esc(t("learning.view.title"))}</h2></div>
      <p>${esc(t("learning.view.summary"))}</p>
    </header>
    <div class="episodes-fixture-notice" role="note" ${testIdAttribute("learning", "fixture", "notice")}>
      <strong>${esc(t("learning.fixture.label"))}</strong><span>${esc(t("learning.fixture.detail"))}</span>
    </div>
    ${picker(episode)}
    ${transactionSummary(episode)}
    ${replayPanel(episode, stageIndex)}
    ${diffPanel(episode)}
    ${terminalProof(episode)}
  </div>`;
}

export function currentEpisodeForTest() {
  return ui.selectedId;
}
