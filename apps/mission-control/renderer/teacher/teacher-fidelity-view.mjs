import { FIDELITY_FIXTURES, STRATEGY_FIXTURES } from "./teacher-fixture.mjs";
import { teacherProjectionBoundary } from "./teacher-model.mjs";
import { esc, stateBadge, t, testIdAttribute, yesNo } from "./teacher-view-shared.mjs";

function delta(value) {
  return value > 0 ? `+${value}` : String(value);
}

function fidelityTable() {
  return `<div class="teacher-table-wrap" tabindex="0" ${testIdAttribute("teacher", "fidelity", "scroll")}><table class="teacher-fidelity-table"
    ${testIdAttribute("teacher", "fidelity", "table")}><caption>${esc(t("teacher.fidelity.caption"))}</caption><thead><tr>
    <th scope="col">${esc(t("teacher.fidelity.strategy"))}</th><th scope="col">${esc(t("teacher.fidelity.step2"))}</th>
    <th scope="col">${esc(t("teacher.fidelity.step4"))}</th><th scope="col">${esc(t("teacher.fidelity.step8"))}</th>
    <th scope="col">${esc(t("teacher.fidelity.step16"))}</th><th scope="col">${esc(t("teacher.fidelity.stop"))}</th>
    <th scope="col">${esc(t("teacher.fidelity.finalRetained"))}</th><th scope="col">${esc(t("teacher.fidelity.actualSteps"))}</th>
    <th scope="col">${esc(t("teacher.fidelity.saved"))}</th><th scope="col">${esc(t("teacher.fidelity.falseKill"))}</th>
  </tr></thead><tbody>${FIDELITY_FIXTURES.map((review) => {
    const strategy = STRATEGY_FIXTURES.find((item) => item.id === review.strategyId);
    return `<tr><th scope="row"><span>${esc(strategy?.label ?? review.strategyId)}</span><code>${esc(review.mode)}</code></th>
      ${review.targetDeltas.map((value) => `<td data-align="numeric">${esc(delta(value))}</td>`).join("")}
      <td data-align="numeric">${esc(review.firstWouldStopStep ?? t("teacher.fidelity.none"))}</td>
      <td>${esc(yesNo(review.finalRetained))}</td><td data-align="numeric">${review.actualStepsSpent}</td>
      <td data-align="numeric">${review.shadowStepsSaved}</td><td>${esc(yesNo(review.falseKill))}</td></tr>`;
  }).join("")}</tbody></table></div>`;
}

function projectionDisclosure() {
  const projection = teacherProjectionBoundary();
  return `<details class="teacher-projection" ${testIdAttribute("teacher", "projection")}>
    <summary>${esc(t("teacher.projection.summary"))} ${stateBadge(projection.coverage)}</summary>
    <dl><div><dt>${esc(t("teacher.projection.schema"))}</dt><dd class="machine-value">${esc(projection.schema)}</dd></div>
      <div><dt>${esc(t("teacher.projection.coverage"))}</dt><dd class="machine-value">${esc(projection.coverage)}</dd></div>
      <div><dt>${esc(t("teacher.projection.fields"))}</dt><dd class="machine-value">${esc(projection.fields.join(", "))}</dd></div></dl>
    <p>${esc(t("teacher.projection.limit"))}</p>
  </details>`;
}

function glossaryDisclosure() {
  return `<details class="teacher-glossary" ${testIdAttribute("teacher", "glossary")}><summary>${esc(t("teacher.glossary.summary"))}</summary>
    <ul><li>${esc(t("teacher.glossary.retained"))}</li><li>${esc(t("teacher.glossary.noGain"))}</li>
      <li>${esc(t("teacher.glossary.interference"))}</li><li>${esc(t("teacher.glossary.wall"))}</li></ul></details>`;
}

export function fidelityPanel() {
  return `<section class="teacher-fidelity" aria-labelledby="teacher-fidelity-title" ${testIdAttribute("teacher", "fidelity")}>
    <header class="teacher-section-heading"><div><span class="eyebrow">${esc(t("teacher.fidelity.eyebrow"))}</span>
      <h3 id="teacher-fidelity-title">${esc(t("teacher.fidelity.title"))}</h3></div>
      <span class="teacher-observational"><span aria-hidden="true">○</span>${esc(t("teacher.fidelity.observational"))}</span></header>
    ${fidelityTable()}<p class="teacher-fidelity-boundary">${esc(t("teacher.fidelity.boundary"))}</p>
    <div class="teacher-disclosures">${projectionDisclosure()}${glossaryDisclosure()}</div>
  </section>`;
}
