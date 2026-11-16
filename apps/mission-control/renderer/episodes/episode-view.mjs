import { EPISODE_FIXTURES, EPISODE_STAGES } from "./episode-fixture.mjs";
import { episodeById } from "./episode-model.mjs";
import { diffPanel, terminalProof } from "./episode-proof-view.mjs";
import { replayPanel } from "./episode-replay-view.mjs";
import { episodeRelations, picker, transactionSummary } from "./episode-summary-view.mjs";
import { esc, learningHelpMarkup, t, testIdAttribute } from "./episode-view-shared.mjs";

export const LEARNING_TABS = Object.freeze([
  Object.freeze({ id: "transaction", labelKey: "learning.tab.transaction" }),
  Object.freeze({ id: "lifecycle", labelKey: "learning.tab.lifecycle" }),
  Object.freeze({ id: "comparison", labelKey: "learning.tab.comparison" }),
  Object.freeze({ id: "outcome", labelKey: "learning.tab.outcome" }),
]);

const ui = {
  selectedId: EPISODE_FIXTURES[0].recordId,
  stageIndex: EPISODE_STAGES.length - 1,
  activeTab: LEARNING_TABS[0].id,
};

function activateTab(container, id, { focus = false } = {}) {
  if (!LEARNING_TABS.some((tab) => tab.id === id)) return;
  ui.activeTab = id;
  container.querySelectorAll("[data-learning-tab]").forEach((button) => {
    const active = button.dataset.learningTab === id;
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
  });
  container.querySelectorAll("[data-learning-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.learningPanel !== id;
  });
  if (focus) container.querySelector(`[data-learning-tab="${id}"]`)?.focus();
}

function bind(container, inspectEvidence, inspectCandidate, episode) {
  container.querySelectorAll("[data-learning-tab]").forEach((button) => {
    button.addEventListener("click", () => activateTab(container, button.dataset.learningTab));
    button.addEventListener("keydown", (event) => {
      const current = LEARNING_TABS.findIndex((tab) => tab.id === button.dataset.learningTab);
      const next = event.key === "ArrowRight" ? (current + 1) % LEARNING_TABS.length
        : event.key === "ArrowLeft" ? (current - 1 + LEARNING_TABS.length) % LEARNING_TABS.length
        : event.key === "Home" ? 0
        : event.key === "End" ? LEARNING_TABS.length - 1
        : null;
      if (next === null) return;
      event.preventDefault();
      activateTab(container, LEARNING_TABS[next].id, { focus: true });
    });
  });
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
  container.innerHTML = episodeMarkupForTest(episode.recordId, ui.stageIndex, ui.activeTab);
  bind(container, inspectEvidence, inspectCandidate, episode);
}

export function episodeMarkupForTest(
  selectedId = EPISODE_FIXTURES[0].recordId,
  stageIndex = EPISODE_STAGES.length - 1,
  activeTab = LEARNING_TABS[0].id,
) {
  const episode = episodeById(selectedId);
  const tabBody = Object.freeze({
    transaction: transactionSummary(episode),
    lifecycle: replayPanel(episode, stageIndex),
    comparison: diffPanel(episode),
    outcome: terminalProof(episode),
  });
  return `<div class="episodes-view" ${testIdAttribute("learning", "view")}>
    <header class="episodes-heading" ${testIdAttribute("learning", "heading")}>
      <div><span class="eyebrow">${esc(t("learning.view.eyebrow"))}</span><h2>${esc(t("learning.view.title"))}</h2></div>
      <p>${esc(t("learning.view.summary"))}</p>
    </header>
    <div class="episodes-fixture-notice" role="note" ${testIdAttribute("learning", "fixture", "notice")}>
      <strong>${esc(t("learning.fixture.label"))}</strong><span>${esc(t("learning.fixture.detail"))}</span>
      ${learningHelpMarkup("provenance", "learning-help-provenance")}
    </div>
    ${picker(episode)}
    <div class="episode-tabs" role="tablist" aria-label="${esc(t("learning.tabs.aria"))}" ${testIdAttribute("learning", "tabs")}>
      ${LEARNING_TABS.map((tab) => {
        const active = tab.id === activeTab;
        return `<button type="button" role="tab" id="learning-tab-${tab.id}" data-learning-tab="${tab.id}"
          aria-controls="learning-panel-${tab.id}" aria-selected="${active}" tabindex="${active ? 0 : -1}"
          ${testIdAttribute("learning", "tab", tab.id)}>${esc(t(tab.labelKey))}</button>`;
      }).join("")}
    </div>
    ${LEARNING_TABS.map((tab) => `<section id="learning-panel-${tab.id}" class="episode-tab-panel"
      role="tabpanel" aria-labelledby="learning-tab-${tab.id}" data-learning-panel="${tab.id}"
      ${tab.id === activeTab ? "" : "hidden"} ${testIdAttribute("learning", "panel", tab.id)}>
      ${tabBody[tab.id]}
    </section>`).join("")}
  </div>`;
}

export function currentEpisodeForTest() {
  return ui.selectedId;
}

export function currentLearningTabForTest() {
  return ui.activeTab;
}
