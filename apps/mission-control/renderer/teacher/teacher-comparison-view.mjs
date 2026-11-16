import { STRATEGY_FIXTURES } from "./teacher-fixture.mjs";
import { comparisonScopes, strategyComparison } from "./teacher-model.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";
import { esc, scopeLabel, stateBadge, t, testIdAttribute, unavailable } from "./teacher-view-shared.mjs";

export function availableScopes(strategyIds) {
  const selected = strategyIds.map((id) => STRATEGY_FIXTURES.find((strategy) => strategy.id === id)).filter(Boolean);
  const scopes = comparisonScopes(selected);
  return [
    Object.freeze({ kind: "whole-school", value: "ALL" }),
    ...scopes.capabilities.map((value) => Object.freeze({ kind: "capability", value })),
    ...scopes.sourceFamilies.map((value) => Object.freeze({ kind: "source-family", value })),
  ];
}

function strategyControls(selectedStrategyIds) {
  return `<div class="teacher-strategy-controls" role="group" aria-label="${esc(t("teacher.comparison.strategies"))}">
    ${STRATEGY_FIXTURES.map((strategy) => {
      const selected = selectedStrategyIds.includes(strategy.id);
      return `<button type="button" class="teacher-compare-strategy" data-compare-strategy="${esc(strategy.id)}"
        aria-pressed="${selected}" ${testIdAttribute("teacher", "compare", "strategy", strategy.effectiveKey)}>
        <span class="machine-value">${esc(strategy.role)}</span><span>${esc(strategy.label)}</span>
      </button>`;
    }).join("")}
  </div>`;
}

function scopeControl(selectedStrategyIds, scope) {
  const scopes = availableScopes(selectedStrategyIds);
  return `<label class="teacher-scope-control"><span>${esc(t("teacher.comparison.scope"))}</span>
    <select data-compare-scope ${testIdAttribute("teacher", "compare", "scope")}>
      ${scopes.map((item) => {
        const key = `${item.kind}:${item.value}`;
        const selected = item.kind === scope.kind && item.value === scope.value;
        return `<option value="${esc(key)}" ${selected ? "selected" : ""}>${esc(scopeLabel(item))}</option>`;
      }).join("")}
    </select></label>`;
}

function coverageLabel(coverage) {
  return coverage === "EQUAL_OBSERVED_DENOMINATORS"
    ? t("teacher.comparison.coverageEqual")
    : t("teacher.comparison.coveragePartial");
}

export function comparisonPanel(selectedStrategyIds, scope) {
  const comparison = strategyComparison(selectedStrategyIds, scope);
  return `<section class="teacher-comparison" aria-labelledby="teacher-comparison-title" ${testIdAttribute("teacher", "comparison")}>
    <header class="teacher-section-heading"><div>
      <span class="eyebrow">${esc(t("teacher.comparison.eyebrow"))}</span><h3 id="teacher-comparison-title">${esc(t("teacher.comparison.title"))}</h3>
    </div><div class="teacher-heading-tools"><span class="teacher-coverage-label"><span aria-hidden="true">${comparison.coverage === "EQUAL_OBSERVED_DENOMINATORS" ? "=" : "◐"}</span>
      ${esc(coverageLabel(comparison.coverage))}</span>${contextHelpMarkup({
        label: t("teacher.help.comparison.label"), description: t("teacher.help.comparison.body"), testId: "teacher-help-comparison",
      })}</div></header>
    <div class="teacher-comparison-controls">${strategyControls(selectedStrategyIds)}${scopeControl(selectedStrategyIds, scope)}</div>
    <p class="teacher-comparison-note">${esc(t("teacher.comparison.note", { floor: comparison.commonCoverageFloor }))}</p>
    <div class="teacher-table-wrap" tabindex="0" ${testIdAttribute("teacher", "comparison", "scroll")}><table class="teacher-comparison-table"
      ${testIdAttribute("teacher", "comparison", "table")}><thead><tr>
      <th scope="col">${esc(t("teacher.comparison.strategy"))}</th><th scope="col">${esc(t("teacher.comparison.observed"))}</th>
      <th scope="col">${esc(t("teacher.comparison.retained"))}</th><th scope="col">${esc(t("teacher.comparison.gain"))}</th>
      <th scope="col">${esc(t("teacher.comparison.noGain"))}</th><th scope="col">${esc(t("teacher.comparison.interference"))}</th>
      <th scope="col">${esc(t("teacher.comparison.wall"))}</th><th scope="col">${esc(t("teacher.comparison.steps"))}</th>
      <th scope="col">${esc(t("teacher.comparison.coverage"))}</th>
    </tr></thead><tbody>${comparison.rows.map(({ strategy, metrics }) => `<tr>
      <th scope="row"><span>${esc(strategy.label)}</span><code>${esc(strategy.role)}</code></th>
      <td data-align="numeric">${metrics.observations}</td><td data-align="numeric">${metrics.retained} / ${metrics.observations}</td>
      <td data-align="numeric">+${metrics.actualGain}</td><td class="teacher-no-gain" data-align="numeric">${metrics.noGain} / ${metrics.observations}</td>
      <td class="teacher-interference" data-align="numeric">${metrics.interference} / ${metrics.observations}</td>
      <td data-align="numeric">${esc(unavailable(metrics.averageWallSeconds))} / ${esc(unavailable(metrics.medianWallSeconds))}</td>
      <td data-align="numeric">${metrics.attemptedSteps}</td><td>${stateBadge(metrics.coverage)}</td>
    </tr>`).join("")}</tbody></table></div>
    <p class="teacher-doctrine">${esc(t("teacher.comparison.descriptive"))}</p>
  </section>`;
}
