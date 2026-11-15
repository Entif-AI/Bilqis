import { EPISODE_FIXTURES, EPISODE_STAGES } from "./episode-fixture.mjs";
import { episodeById } from "./episode-model.mjs";
import { diffPanel, terminalProof } from "./episode-proof-view.mjs";
import { replayPanel } from "./episode-replay-view.mjs";
import { episodeRelations, picker, transactionSummary } from "./episode-summary-view.mjs";
import { esc, t, testIdAttribute } from "./episode-view-shared.mjs";

const ui = {
  selectedId: EPISODE_FIXTURES[0].recordId,
  stageIndex: EPISODE_STAGES.length - 1,
};

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
    if ([selected.recordId, selected.episodeId, selected.candidateId].includes(selectedId)) {
      ui.selectedId = selected.recordId;
    }
  }
  const episode = episodeById(ui.selectedId);
  container.innerHTML = episodeMarkupForTest(episode.recordId, ui.stageIndex);
  bind(container, inspectEvidence, inspectCandidate, episode);
}

export function episodeMarkupForTest(
  selectedId = EPISODE_FIXTURES[0].recordId,
  stageIndex = EPISODE_STAGES.length - 1,
) {
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
