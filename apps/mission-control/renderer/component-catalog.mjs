import { evidenceValue, semanticStateInventory, statusBadge } from "./visual-language.mjs";
import { VISUAL_FIXTURES } from "./visual-fixtures.mjs";
import { defensiveCatalogMarkup } from "./foundation/defensive-state.mjs";
import { t } from "./foundation/i18n.mjs";
import { disclosureMarkup, panelMarkup } from "./foundation/primitives.mjs";
import { assertUniqueTestIds, testIdAttribute } from "./foundation/test-hooks.mjs";

function metricTile() {
  return `<article class="metric-tile" ${testIdAttribute("foundation", "metric", "retained-accuracy")}>
    <header><span>${t("foundation.catalog.metric.retainedAccuracy")}</span><span class="provenance-chip" data-authority="source">${t("foundation.catalog.metric.sourceAuthority")}</span></header>
    ${evidenceValue("91.7", "measured", "source", "%")}
    <div class="trend" aria-label="${t("foundation.catalog.metric.trend", { from: 86, to: 92 })}"><span data-height="35"></span><span data-height="48"></span><span data-height="62"></span><span data-height="79"></span></div>
  </article>`;
}

function deltaCard() {
  return `<article class="comparison-card" ${testIdAttribute("foundation", "metric", "generation-comparison")}>
    <header><span>${t("foundation.catalog.metric.generationComparison")}</span><span class="provenance-chip" data-authority="derived">${t("foundation.catalog.metric.derivedAuthority")}</span></header>
    <strong>+3.2 pp</strong>
    <small>${t("foundation.catalog.metric.sameRubric", { from: 44217, to: 44238 })}</small>
  </article>`;
}

function statePanel() {
  const states = semanticStateInventory()
    .map((state) => statusBadge(state, "", { testId: `foundation-status-${state}` }))
    .join("");
  return panelMarkup({
    title: t("foundation.catalog.status.title"),
    body: `<div class="badge-grid">${states}</div>`,
    testId: "foundation-status-grammar",
    level: "surface-1",
  });
}

function evidencePanel() {
  return panelMarkup({
    title: t("foundation.catalog.evidence.title"),
    body: `<div class="evidence-grid">
    ${evidenceValue("84.3%", "measured", "source")}
    ${evidenceValue("≈ 86%", "inferred", "source")}
    ${evidenceValue("0.71", "measured", "derived")}
    ${evidenceValue("≈ 0.75", "inferred", "derived")}
  </div>`,
    testId: "foundation-evidence-authority",
    level: "surface-1",
  });
}

function stateSurfaces() {
  return panelMarkup({
    title: t("foundation.catalog.defensive.title"),
    body: `<div class="state-surface-grid">${defensiveCatalogMarkup()}</div>`,
    testId: "foundation-defensive-states",
    level: "surface-1",
  });
}

function evidenceRow() {
  return disclosureMarkup({
    summary: `<span>receipt:fixture-001</span><span>${t("foundation.catalog.evidence.verifiedChain")}</span>`,
    body: `<code>generation:44238</code><p>${t("foundation.catalog.evidence.explanation")}</p>`,
    testId: "foundation-evidence-disclosure",
  });
}

function graphLegend() {
  return `<div class="graph-legend" aria-label="${t("foundation.catalog.legend.label")}" ${testIdAttribute("foundation", "graph", "legend")}>
    <span><i data-edge="source"></i>${t("foundation.catalog.legend.source")}</span>
    <span><i data-edge="derived"></i>${t("foundation.catalog.legend.derived")}</span>
    <span><i data-edge="held"></i>${t("foundation.catalog.legend.held")}</span>
  </div>`;
}

function fixtureStrip() {
  return Object.entries(VISUAL_FIXTURES)
    .map(([name, fixture]) => `<div class="fixture-state" data-fixture="${name}" data-state="${fixture.state}"><strong>${t(fixture.labelKey)}</strong><small>${fixture.mode} · ${fixture.freshness}</small></div>`)
    .join("");
}

export function renderComponentCatalog() {
  const markup = `
    <header class="catalog-heading" ${testIdAttribute("foundation", "catalog", "heading")}><div><span class="eyebrow">${t("foundation.catalog.eyebrow")}</span><h2>${t("foundation.catalog.title")}</h2></div><p>${t("foundation.catalog.summary")}</p></header>
    <div class="historical-banner" role="status" ${testIdAttribute("foundation", "historical", "banner")}><strong>◷ ${t("foundation.catalog.historical.label")}</strong><span>${t("foundation.catalog.historical.detail", { generation: 44120 })}</span></div>
    <div class="catalog-grid">${metricTile()}${deltaCard()}</div>
    ${statePanel()}
    ${evidencePanel()}
    ${panelMarkup({
      title: t("foundation.catalog.provenance.title"),
      body: `<div class="identity-row"><span class="run-identity">RUN fixture:prometheus-disposable / GEN 44238</span><span class="provenance-chip" data-authority="source">S · FactoryRelease</span><span class="provenance-chip" data-authority="derived">${t("foundation.catalog.provenance.learnedProjection")}</span></div><div class="alert" data-state="attention"><strong>! ${t("foundation.catalog.alert.attention")}</strong><span>${t("foundation.catalog.alert.diskReserve")}</span></div>${evidenceRow()}${graphLegend()}`,
      testId: "foundation-provenance-alerting",
      level: "surface-1",
    })}
    ${stateSurfaces()}
    ${panelMarkup({
      title: t("foundation.catalog.fixtures.title"),
      body: `<div class="fixture-strip">${fixtureStrip()}</div>`,
      testId: "foundation-visual-fixtures",
      level: "surface-1",
    })}
  `;
  assertUniqueTestIds(markup);
  return markup;
}
