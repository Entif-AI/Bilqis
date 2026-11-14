import {
  FIDELITY_FIXTURES,
  STRATEGY_FIXTURES,
} from "./teacher-fixture.mjs";
import {
  comparisonScopes,
  roleCounts,
  strategyComparison,
  strategyEpisodes,
  teacherProjectionBoundary,
} from "./teacher-model.mjs";
import { objectDomAttributes } from "../interactions/dom-ref.mjs";

const ui = {
  selectedStrategyIds: Object.freeze([
    "strategy:fixture:incumbent-deep-contrast",
    "strategy:fixture:retired-shallow",
  ]),
  scope: Object.freeze({ kind: "capability", value: "B.IFF" }),
};

function badge(value) {
  return `<span class="teacher-state" data-state="${String(value).toLowerCase()}">${value}</span>`;
}

function strategyRelations(strategy) {
  return [
    ...strategy.activeCapabilityScope.map((id) => ({
      kind: "capability", id, relation: "active-capability",
    })),
    ...strategy.sourceFamilies.map((id) => ({
      kind: "source", id, relation: "source-family",
    })),
    ...strategy.episodeRecordIds.map((id) => ({
      kind: "episode", id, relation: "episode",
    })),
  ];
}

function rosterCard(strategy, inspectStrategy) {
  const episodes = strategyEpisodes(strategy);
  const average = strategy.wallSeconds.length
    ? strategy.wallSeconds.reduce((sum, value) => sum + value, 0) / strategy.wallSeconds.length
    : null;
  const ordered = [...strategy.wallSeconds].sort((left, right) => left - right);
  const median = ordered.length
    ? ordered.length % 2
      ? ordered[Math.floor(ordered.length / 2)]
      : (ordered[ordered.length / 2 - 1] + ordered[ordered.length / 2]) / 2
    : null;
  return `<article class="strategy-card" data-role="${strategy.role}" ${objectDomAttributes({
    kind: "strategy", id: strategy.id, relations: strategyRelations(strategy),
  })}>
    <header>
      <div><span class="eyebrow">${strategy.role}</span><h4>${strategy.label}</h4></div>
      ${badge(strategy.status)}
    </header>
    <div class="strategy-metrics">
      <div><small>Attempts / visits</small><strong>${strategy.attempts}</strong></div>
      <div><small>Retained candidates</small><strong>${strategy.retained}</strong></div>
      <div><small>Actual capability gain</small><strong>+${strategy.actualCapabilityGain}</strong></div>
      <div><small>No-gain outcomes</small><strong>${strategy.noGain}</strong></div>
      <div><small>Interference outcomes</small><strong>${strategy.interference}</strong></div>
      <div><small>Avg / median wall s</small><strong>${average?.toFixed(2) ?? "UNAVAILABLE"} / ${median?.toFixed(2) ?? "UNAVAILABLE"}</strong></div>
    </div>
    <div class="strategy-scope">
      <span><strong>Capabilities:</strong> ${strategy.activeCapabilityScope.join(", ")}</span>
      <span><strong>Source families:</strong> ${strategy.sourceFamilies.join(", ")}</span>
      <span><strong>Last used:</strong> ${strategy.lastUsedCheckpoint}</span>
      <span><strong>Retired at:</strong> ${strategy.retiredCheckpoint ?? "ACTIVE"}</span>
      <span><strong>Canary state:</strong> ${strategy.canaryStatus}</span>
      <span><strong>Resource coverage:</strong> ${strategy.resourceState}</span>
    </div>
    <div class="strategy-episode-links">
      ${episodes.length
        ? episodes.map((episode) => `<a href="${episode.href}" ${objectDomAttributes({
          kind: "episode", id: episode.recordId,
        })}>${episode.capabilityId} · ${episode.terminalState} · ${episode.retentionReason}</a>`).join("")
        : '<span class="episode-evidence-empty">No literal Learning Episode fixture linked.</span>'}
    </div>
    <div class="strategy-history">
      ${strategy.history.map((item) => `<div><small>${item.checkpoint}</small><span>${item.role} · ${item.state}</span></div>`).join("")}
    </div>
    <button type="button" data-strategy-inspect="${strategy.id}">Inspect strategy identity</button>
  </article>`;
}

function rosterPanel(inspectStrategy) {
  const counts = roleCounts();
  return `<section class="teacher-panel">
    <header>
      <div><span class="eyebrow">Strategy roster</span><h3>Current and checkpoint-local evidence</h3></div>
      <span>${counts.INCUMBENT ?? 0} incumbent · ${counts.CHALLENGER ?? 0} challenger · ${counts.CANARY ?? 0} canary · ${counts.RETIRED ?? 0} retired</span>
    </header>
    <div class="strategy-roster">${STRATEGY_FIXTURES.map((strategy) => rosterCard(strategy, inspectStrategy)).join("")}</div>
  </section>`;
}

function comparisonButtons() {
  const selected = ui.selectedStrategyIds.map((id) =>
    STRATEGY_FIXTURES.find((strategy) => strategy.id === id),
  ).filter(Boolean);
  const scopes = comparisonScopes(selected);
  const buttons = [
    Object.freeze({ kind: "whole-school", value: "ALL", label: "Whole-school retained outcomes" }),
    ...scopes.capabilities.map((value) => Object.freeze({
      kind: "capability", value, label: "Capability · " + value,
    })),
    ...scopes.sourceFamilies.map((value) => Object.freeze({
      kind: "source-family", value, label: "Source family · " + value,
    })),
  ];
  return buttons.map((scope) => `<button type="button"
    data-compare-kind="${scope.kind}"
    data-compare-value="${scope.value}"
    aria-pressed="${scope.kind === ui.scope.kind && scope.value === ui.scope.value}">${scope.label}</button>`).join("");
}

function strategySelector() {
  return STRATEGY_FIXTURES.map((strategy) => {
    const selected = ui.selectedStrategyIds.includes(strategy.id);
    return `<button type="button" data-compare-strategy="${strategy.id}" aria-pressed="${selected}">${strategy.role} · ${strategy.label}</button>`;
  }).join("");
}

function comparisonPanel() {
  const comparison = strategyComparison(ui.selectedStrategyIds, ui.scope);
  return `<section class="teacher-panel">
    <header>
      <div><span class="eyebrow">Evidence comparison</span><h3>Common scope, explicit denominators</h3></div>
      ${badge(comparison.coverage)}
    </header>
    <div class="teacher-compare-controls">${strategySelector()}</div>
    <div class="teacher-compare-controls">${comparisonButtons()}</div>
    <p class="coverage-note">Comparison scope: <strong>${comparison.scope.kind}</strong> · ${comparison.scope.value}. Shared-scope observation floor: ${comparison.commonCoverageFloor}. Each strategy keeps its literal observed denominator; equal counts do not imply an identical observation cohort, and unequal coverage remains partial rather than being silently normalized.</p>
    <div class="comparison-wrap"><table class="comparison-table">
      <thead><tr><th>Strategy</th><th>Observed N</th><th>Retained</th><th>Actual gain</th><th>No gain</th><th>Harmful / interference</th><th>Avg / median wall s</th><th>Attempted steps</th><th>Coverage</th></tr></thead>
      <tbody>${comparison.rows.map(({ strategy, metrics }) => `<tr>
        <th>${strategy.role} · ${strategy.label}</th>
        <td>${metrics.observations}</td>
        <td>${metrics.retained} / ${metrics.observations || 0}</td>
        <td>+${metrics.actualGain}</td>
        <td class="no-gain">${metrics.noGain} / ${metrics.observations || 0}</td>
        <td class="harmful">${metrics.interference} / ${metrics.observations || 0}</td>
        <td>${metrics.averageWallSeconds ?? "UNAVAILABLE"} / ${metrics.medianWallSeconds ?? "UNAVAILABLE"}</td>
        <td>${metrics.attemptedSteps}</td>
        <td>${badge(metrics.coverage)}</td>
      </tr>`).join("")}</tbody>
    </table></div>
    <p class="teacher-doctrine">Descriptive evidence only. The view does not convert correlations into strategy priority, quota, scheduler action, or a synthetic winner.</p>
  </section>`;
}

function fidelityPanel() {
  return `<section class="teacher-panel">
    <header><div><span class="eyebrow">Fidelity ladder</span><h3>2 / 4 / 8 / 16 shadow observations</h3></div>${badge("OBSERVATIONAL")}</header>
    <div class="fidelity-grid">${FIDELITY_FIXTURES.map((review) => {
      const strategy = STRATEGY_FIXTURES.find((item) => item.id === review.strategyId);
      return `<article class="fidelity-card">
        <header><div><small>${review.schema}</small><h4>${strategy?.label ?? review.strategyId}</h4></div>${badge(review.mode)}</header>
        <div class="fidelity-rungs">${review.rungs.map((rung, index) => `<div><small>Step ${rung}</small><strong>Δ ${review.targetDeltas[index]}</strong></div>`).join("")}</div>
        <div class="strategy-scope">
          <span><strong>Would stop:</strong> ${review.firstWouldStopStep ?? "NO"}</span>
          <span><strong>Final retained:</strong> ${review.finalRetained}</span>
          <span><strong>Actual steps spent:</strong> ${review.actualStepsSpent}</span>
          <span><strong>Shadow steps saved:</strong> ${review.shadowStepsSaved}</span>
          <span><strong>False kill:</strong> ${review.falseKill}</span>
        </div>
        <div class="fidelity-authority">actual_authority_changed = ${review.actualAuthorityChanged}. These observations do not authorize early termination by themselves.</div>
      </article>`;
    }).join("")}</div>
  </section>`;
}

function projectionPanel() {
  const projection = teacherProjectionBoundary();
  return `<section class="teacher-panel">
    <header><div><span class="eyebrow">Mission Control projection boundary</span><h3>${projection.schema}</h3></div>${badge(projection.coverage)}</header>
    <p class="teacher-doctrine">Current CP02 TeacherSnapshot exposes only ${projection.fields.join(", ")}. Rich strategy-role, context, cost, retirement and fidelity evidence in GUI11 is therefore explicit fixture evidence grounded in the Factory teacher-observation and strategy-population contracts.</p>
  </section>`;
}

function bind(container, inspectStrategy) {
  container.querySelectorAll("[data-strategy-inspect]").forEach((button) => button.addEventListener("click", () => {
    const strategy = STRATEGY_FIXTURES.find((item) => item.id === button.dataset.strategyInspect);
    inspectStrategy(button.dataset.strategyInspect, strategy, strategy ? strategyRelations(strategy) : []);
  }));
  container.querySelectorAll("[data-compare-strategy]").forEach((button) => button.addEventListener("click", () => {
    const id = button.dataset.compareStrategy;
    const selected = new Set(ui.selectedStrategyIds);
    if (selected.has(id)) {
      if (selected.size > 2) selected.delete(id);
    } else {
      selected.add(id);
    }
    ui.selectedStrategyIds = Object.freeze([...selected]);
    const strategies = ui.selectedStrategyIds.map((strategyId) =>
      STRATEGY_FIXTURES.find((strategy) => strategy.id === strategyId),
    ).filter(Boolean);
    const scopes = comparisonScopes(strategies);
    if (ui.scope.kind === "capability" && !scopes.capabilities.includes(ui.scope.value)) {
      ui.scope = Object.freeze({ kind: "whole-school", value: "ALL" });
    }
    if (ui.scope.kind === "source-family" && !scopes.sourceFamilies.includes(ui.scope.value)) {
      ui.scope = Object.freeze({ kind: "whole-school", value: "ALL" });
    }
    renderTeacherView(container, inspectStrategy);
  }));
  container.querySelectorAll("[data-compare-kind]").forEach((button) => button.addEventListener("click", () => {
    ui.scope = Object.freeze({
      kind: button.dataset.compareKind,
      value: button.dataset.compareValue,
    });
    renderTeacherView(container, inspectStrategy);
  }));
}

export function renderTeacherView(container, inspectStrategy) {
  container.innerHTML = `<div class="teacher-view">
    <header class="teacher-heading"><div><span class="eyebrow">GUI11 · Teacher / Strategy Lab</span><h2>Measured outcomes, visible uncertainty</h2></div><p>Inspect strategy population, efficacy, no-gain, interference, cost and shadow fidelity without turning observational correlation into policy authority.</p></header>
    <div class="teacher-fixture-notice"><strong>FIXTURE · FACTORY-EVIDENCE SHAPE</strong><span>Strategy-lab detail is representative fixture data because current CP02 TeacherSnapshot is intentionally narrow. Literal Learning Episode links use the landed GUI06 record-ID contract.</span></div>
    <div class="ui-glossary" aria-label="Strategy lab metric definitions"><span><strong>Retained</strong> candidate updates kept by the teacher.</span><span><strong>No gain</strong> attempts without measurable target improvement.</span><span><strong>Interference</strong> attempts that harmed protected capability evidence.</span><span><strong>Wall s</strong> observed elapsed seconds.</span></div>
    ${rosterPanel(inspectStrategy)}
    ${comparisonPanel()}
    ${fidelityPanel()}
    ${projectionPanel()}
  </div>`;
  bind(container, inspectStrategy);
}

export function teacherComparisonStateForTest() {
  return Object.freeze({
    selectedStrategyIds: Object.freeze([...ui.selectedStrategyIds]),
    scope: Object.freeze({ ...ui.scope }),
  });
}
