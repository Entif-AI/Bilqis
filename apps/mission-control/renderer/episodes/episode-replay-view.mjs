import { EPISODE_STAGES } from "./episode-fixture.mjs";
import { replaySlice } from "./episode-model.mjs";
import { esc, stateBadge, t, testIdAttribute } from "./episode-view-shared.mjs";

function evidenceButtons(stage) {
  if (!stage.evidence.length) {
    return `<p class="episode-evidence-empty" ${testIdAttribute("learning", "stage", "evidence", "empty")}>${esc(t("learning.lifecycle.noEvidence"))}</p>`;
  }
  return stage.evidence.map((item, index) => {
    const typeLabel = t(`learning.evidenceType.${item.type}`);
    return `<button type="button" data-episode-evidence="${esc(item.id)}" data-evidence-type="${esc(item.type)}"
      ${testIdAttribute("learning", "stage", "evidence", stage.id, index)}>
      <span>${esc(t("learning.lifecycle.openEvidence", { type: typeLabel }))}</span><code>${esc(item.id)}</code>
    </button>`;
  }).join("");
}

export function replayPanel(episode, stageIndex) {
  const replay = replaySlice(episode, stageIndex);
  return `<section class="episode-lifecycle" aria-labelledby="learning-lifecycle-title" ${testIdAttribute("learning", "lifecycle")}>
    <header class="episode-section-heading"><div>
      <span class="eyebrow">${esc(t("learning.lifecycle.eyebrow"))}</span>
      <h3 id="learning-lifecycle-title">${esc(t("learning.lifecycle.title"))}</h3>
    </div><span class="episode-stage-counter">${esc(t("learning.lifecycle.counter", {
      current: replay.stageIndex + 1, total: EPISODE_STAGES.length,
    }))}</span></header>
    <div class="episode-replay"><ol class="episode-stage-list" aria-label="${esc(t("learning.lifecycle.title"))}">
      ${episode.stages.map((stage, index) => `<li class="episode-stage" data-state="${esc(stage.state.toLowerCase())}" data-active="${index === replay.stageIndex}">
        <button type="button" data-stage-index="${index}" aria-pressed="${index === replay.stageIndex}"
          ${index === replay.stageIndex ? 'aria-current="step"' : ""} ${testIdAttribute("learning", "stage", stage.id)}>
          <span class="episode-stage-number" aria-hidden="true">${index + 1}</span>
          <span class="episode-stage-copy"><strong>${esc(t(stage.labelKey))}</strong>${stateBadge(stage.state)}</span>
        </button></li>`).join("")}
    </ol><article class="episode-stage-detail" ${testIdAttribute("learning", "stage", "detail")}>
      <span class="eyebrow">${esc(t("learning.lifecycle.selected"))}</span>
      <div class="episode-stage-detail-heading"><h4>${esc(t(replay.active.labelKey))}</h4>
        ${stateBadge(replay.active.state, "learning-active-stage-state")}</div>
      <p>${esc(t(replay.active.detailKey))}</p>
      <details class="episode-evidence-disclosure" ${testIdAttribute("learning", "stage", "evidence")}>
        <summary>${esc(t("learning.lifecycle.evidenceSummary", { count: replay.active.evidence.length }))}</summary>
        <div class="episode-evidence">${evidenceButtons(replay.active)}</div>
      </details>
    </article></div>
  </section>`;
}
