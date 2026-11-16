import { diffRows, rejectionClass, retainedTransition, rollbackInvariant } from "./episode-model.mjs";
import {
  displayComparisonValue,
  esc,
  learningHelpMarkup,
  retentionReasonLabel,
  stateBadge,
  t,
  testIdAttribute,
} from "./episode-view-shared.mjs";

export function diffPanel(episode) {
  return `<section class="episode-comparison" aria-labelledby="learning-comparison-title" ${testIdAttribute("learning", "comparison")}>
    <header class="episode-section-heading"><div>
      <span class="eyebrow">${esc(t("learning.comparison.eyebrow"))}</span>
      <h3 id="learning-comparison-title">${esc(t("learning.comparison.title"))}</h3>
    </div>${learningHelpMarkup("comparison", "learning-help-comparison")}</header>
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
  return `<tr data-pass="${passed}"><th scope="row">${esc(t(labelKey))}</th>
    <td><span class="episode-proof-marker" aria-hidden="true">${passed ? "✓" : "×"}</span> ${esc(result)}</td></tr>`;
}

function retainedProof(transition) {
  return `<section class="episode-outcome" data-outcome="retained" aria-live="polite" ${testIdAttribute("learning", "outcome", "proof")}>
    <header class="episode-section-heading"><div>
      <span class="eyebrow">${esc(t("learning.outcome.eyebrow"))}</span>
      <h3>${esc(t("learning.outcome.retainedTitle"))}</h3><p>${esc(t("learning.outcome.retainedDetail"))}</p>
    </div><div class="episode-heading-tools">
      ${learningHelpMarkup("retention", "learning-help-retention")}
      ${stateBadge("RETAINED")}
    </div></header>
    <dl class="episode-transition">
      <div><dt>${esc(t("learning.outcome.parentGeneration"))}</dt><dd>${esc(transition.parentGeneration)}</dd></div>
      <span class="episode-transition-arrow" aria-hidden="true">→</span>
      <div><dt>${esc(t("learning.outcome.childGeneration"))}</dt><dd>${esc(transition.childGeneration)}</dd></div>
      <div class="episode-transition-checkpoint"><dt>${esc(t("learning.outcome.checkpoint"))}</dt><dd class="machine-value">${esc(transition.checkpointId)}</dd></div>
    </dl>
  </section>`;
}

function pendingProof() {
  return `<section class="episode-outcome" data-outcome="unknown" aria-live="polite" ${testIdAttribute("learning", "outcome", "proof")}>
    <header class="episode-section-heading"><div>
      <span class="eyebrow">${esc(t("learning.outcome.eyebrow"))}</span>
      <h3>${esc(t("learning.outcome.pendingTitle"))}</h3><p>${esc(t("learning.outcome.pendingDetail"))}</p>
    </div><div class="episode-heading-tools">
      ${learningHelpMarkup("retention", "learning-help-retention")}
      ${stateBadge("UNKNOWN")}
    </div></header>
  </section>`;
}

function rejectedProof(episode, rollback) {
  const classification = rejectionClass(episode);
  return `<section class="episode-outcome" data-outcome="rejected" data-class="${classification}" aria-live="polite" ${testIdAttribute("learning", "outcome", "proof")}>
    <header class="episode-section-heading"><div>
      <span class="eyebrow">${esc(t("learning.outcome.eyebrow"))}</span>
      <h3>${esc(t("learning.outcome.rejectedTitle"))}</h3>
      <p><strong>${esc(t(classification === "INTERFERENCE" ? "learning.outcome.interference" : "learning.outcome.noGain"))}</strong>
        · ${esc(retentionReasonLabel(episode.retentionReason))}</p>
    </div><div class="episode-heading-tools">
      ${learningHelpMarkup("retention", "learning-help-retention")}
      ${stateBadge("REJECTED")}
    </div></header>
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

export function terminalProof(episode) {
  const transition = retainedTransition(episode);
  if (transition) return retainedProof(transition);
  const rollback = rollbackInvariant(episode);
  if (!rollback) return pendingProof();
  return rejectedProof(episode, rollback);
}
