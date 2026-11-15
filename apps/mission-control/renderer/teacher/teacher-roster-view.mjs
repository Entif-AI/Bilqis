import { STRATEGY_FIXTURES } from "./teacher-fixture.mjs";
import { aggregateContext, roleCounts, strategyEpisodes } from "./teacher-model.mjs";
import { objectDomAttributes } from "../interactions/dom-ref.mjs";
import { esc, stateBadge, t, testIdAttribute, unavailable } from "./teacher-view-shared.mjs";

export function strategyRelations(strategy) {
  return [
    ...strategy.activeCapabilityScope.map((id) => ({ kind: "capability", id, relation: "active-capability" })),
    ...strategy.sourceFamilies.map((id) => ({ kind: "source", id, relation: "source-family" })),
    ...strategy.episodeRecordIds.map((id) => ({ kind: "episode", id, relation: "episode" })),
  ];
}

function rosterRow(strategy, selectedId) {
  return `<tr data-selected="${strategy.id === selectedId}" data-role="${esc(strategy.role)}">
    <th scope="row">
      <button type="button" class="teacher-strategy-select" data-strategy-select="${esc(strategy.id)}"
        aria-pressed="${strategy.id === selectedId}" ${testIdAttribute("teacher", "roster", "select", strategy.effectiveKey)}>
        <span>${esc(strategy.label)}</span><code>${esc(strategy.effectiveKey)}</code>
      </button>
    </th>
    <td class="machine-value">${esc(strategy.role)}</td>
    <td>${stateBadge(strategy.status)}</td>
    <td data-align="numeric">${strategy.attempts}</td>
    <td data-align="numeric">${strategy.retained}</td>
    <td data-align="numeric">${strategy.noGain}</td>
    <td data-align="numeric">${strategy.interference}</td>
    <td>${esc(strategy.activeCapabilityScope.join(", "))}</td>
  </tr>`;
}

function episodeLinks(strategy) {
  const episodes = strategyEpisodes(strategy);
  if (!episodes.length) return `<p class="teacher-empty">${esc(t("teacher.detail.noEpisodes"))}</p>`;
  return `<ul class="teacher-episode-links">${episodes.map((episode) =>
    `<li><a href="${episode.href}" ${objectDomAttributes({ kind: "episode", id: episode.recordId })}>
      <span>${esc(episode.capabilityId)}</span><span class="machine-value">${esc(episode.terminalState)} · ${esc(episode.retentionReason)}</span>
    </a></li>`).join("")}</ul>`;
}

function history(strategy) {
  return `<ol class="teacher-history">${strategy.history.map((item) => `<li>
    <code>${esc(item.checkpoint)}</code><span>${esc(t("teacher.detail.historyEntry", { role: item.role, state: item.state }))}</span>
  </li>`).join("")}</ol>`;
}

function selectedDetail(strategy) {
  const metrics = aggregateContext(strategy.contexts);
  return `<section class="teacher-strategy-detail" ${testIdAttribute("teacher", "strategy", "detail")}
    ${objectDomAttributes({ kind: "strategy", id: strategy.id, relations: strategyRelations(strategy) })}>
    <header class="teacher-section-heading"><div>
      <span class="eyebrow">${esc(t("teacher.detail.eyebrow"))}</span><h3>${esc(strategy.label)}</h3>
      <code class="teacher-strategy-id">${esc(strategy.id)}</code>
    </div><div class="teacher-state-pair"><span class="machine-value">${esc(strategy.role)}</span>${stateBadge(strategy.status)}</div></header>

    <div class="teacher-detail-grid">
      <section><h4>${esc(t("teacher.detail.outcomes"))}</h4><dl class="teacher-detail-metrics">
        <div><dt>${esc(t("teacher.detail.attempts"))}</dt><dd>${strategy.attempts}</dd></div>
        <div><dt>${esc(t("teacher.detail.retained"))}</dt><dd>${strategy.retained}</dd></div>
        <div><dt>${esc(t("teacher.detail.actualGain"))}</dt><dd>+${strategy.actualCapabilityGain}</dd></div>
        <div><dt>${esc(t("teacher.detail.noGain"))}</dt><dd>${strategy.noGain}</dd></div>
        <div><dt>${esc(t("teacher.detail.interference"))}</dt><dd>${strategy.interference}</dd></div>
        <div><dt>${esc(t("teacher.detail.wall"))}</dt><dd>${esc(t("teacher.detail.secondsPair", {
          average: unavailable(metrics.averageWallSeconds), median: unavailable(metrics.medianWallSeconds),
        }))}</dd></div>
      </dl></section>
      <section><h4>${esc(t("teacher.detail.scope"))}</h4><dl class="teacher-detail-scope">
        <div><dt>${esc(t("teacher.detail.capabilities"))}</dt><dd>${esc(strategy.activeCapabilityScope.join(", "))}</dd></div>
        <div><dt>${esc(t("teacher.detail.sourceFamilies"))}</dt><dd class="machine-value">${esc(strategy.sourceFamilies.join(", "))}</dd></div>
        <div><dt>${esc(t("teacher.detail.lastUsed"))}</dt><dd class="machine-value">${esc(strategy.lastUsedCheckpoint)}</dd></div>
        <div><dt>${esc(t("teacher.detail.retiredAt"))}</dt><dd class="machine-value">${esc(strategy.retiredCheckpoint ?? t("teacher.value.active"))}</dd></div>
        <div><dt>${esc(t("teacher.detail.canary"))}</dt><dd class="machine-value">${esc(strategy.canaryStatus)}</dd></div>
        <div><dt>${esc(t("teacher.detail.resources"))}</dt><dd>${stateBadge(strategy.resourceState)}</dd></div>
      </dl></section>
    </div>

    <div class="teacher-detail-lower">
      <section><h4>${esc(t("teacher.detail.episodes"))}</h4>${episodeLinks(strategy)}</section>
      <section><h4>${esc(t("teacher.detail.history"))}</h4>${history(strategy)}</section>
    </div>
    <button type="button" class="teacher-inspect" data-strategy-inspect="${esc(strategy.id)}"
      ${testIdAttribute("teacher", "strategy", "inspect")}>${esc(t("teacher.detail.inspect"))}</button>
  </section>`;
}

export function rosterPanel(selectedId) {
  const selected = STRATEGY_FIXTURES.find((strategy) => strategy.id === selectedId) ?? STRATEGY_FIXTURES[0];
  const counts = roleCounts();
  return `<section class="teacher-roster" aria-labelledby="teacher-roster-title" ${testIdAttribute("teacher", "roster")}>
    <header class="teacher-section-heading"><div>
      <span class="eyebrow">${esc(t("teacher.roster.eyebrow"))}</span><h3 id="teacher-roster-title">${esc(t("teacher.roster.title"))}</h3>
    </div><span class="teacher-roster-counts">${esc(t("teacher.roster.counts", {
      incumbent: counts.INCUMBENT ?? 0, challenger: counts.CHALLENGER ?? 0,
      canary: counts.CANARY ?? 0, retired: counts.RETIRED ?? 0,
    }))}</span></header>
    <div class="teacher-table-wrap" tabindex="0" ${testIdAttribute("teacher", "roster", "scroll")}>
      <table class="teacher-roster-table"><caption>${esc(t("teacher.roster.caption"))}</caption><thead><tr>
        <th scope="col">${esc(t("teacher.roster.strategy"))}</th><th scope="col">${esc(t("teacher.roster.role"))}</th>
        <th scope="col">${esc(t("teacher.roster.status"))}</th><th scope="col">${esc(t("teacher.roster.attempts"))}</th>
        <th scope="col">${esc(t("teacher.roster.retained"))}</th><th scope="col">${esc(t("teacher.roster.noGain"))}</th>
        <th scope="col">${esc(t("teacher.roster.interference"))}</th><th scope="col">${esc(t("teacher.roster.scope"))}</th>
      </tr></thead><tbody>${STRATEGY_FIXTURES.map((strategy) => rosterRow(strategy, selected.id)).join("")}</tbody></table>
    </div>
    ${selectedDetail(selected)}
  </section>`;
}
