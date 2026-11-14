import { evidenceValue, semanticStateInventory, statusBadge } from "./visual-language.mjs";
import { VISUAL_FIXTURES } from "./visual-fixtures.mjs";
import { defensiveCatalogMarkup } from "./foundation/defensive-state.mjs";

function metricTile() {
  return `<article class="metric-tile">
    <header><span>Retained accuracy</span><span class="provenance-chip" data-authority="source">S · source</span></header>
    ${evidenceValue("91.7", "measured", "source", "%")}
    <div class="trend" aria-label="Trend rose from 86 to 92 percent"><span data-height="35"></span><span data-height="48"></span><span data-height="62"></span><span data-height="79"></span></div>
  </article>`;
}

function deltaCard() {
  return `<article class="comparison-card">
    <header><span>Generation comparison</span><span class="provenance-chip" data-authority="derived">D · derived</span></header>
    <strong>+3.2 pp</strong>
    <small>44217 → 44238 · same rubric</small>
  </article>`;
}

function statePanel() {
  const states = semanticStateInventory().map((state) => statusBadge(state)).join("");
  return `<article class="catalog-block"><h3>Semantic status grammar</h3><div class="badge-grid">${states}</div></article>`;
}

function evidencePanel() {
  return `<article class="catalog-block"><h3>Evidence and authority</h3><div class="evidence-grid">
    ${evidenceValue("84.3%", "measured", "source")}
    ${evidenceValue("≈ 86%", "inferred", "source")}
    ${evidenceValue("0.71", "measured", "derived")}
    ${evidenceValue("≈ 0.75", "inferred", "derived")}
  </div></article>`;
}

function stateSurfaces() {
  return `<article class="catalog-block"><h3>Defensive state surfaces</h3><div class="state-surface-grid">${defensiveCatalogMarkup()}</div></article>`;
}

function evidenceRow() {
  return `<details class="evidence-row"><summary><span>receipt:fixture-001</span><span>Verified source chain</span></summary><div><code>generation:44238</code><p>Expandable evidence preserves exact identity and provenance without turning every table row into a wall of metadata.</p></div></details>`;
}

function graphLegend() {
  return `<div class="graph-legend" aria-label="Graph legend">
    <span><i data-edge="source"></i>Source authority</span>
    <span><i data-edge="derived"></i>Derived relation</span>
    <span><i data-edge="held"></i>Held edge</span>
  </div>`;
}

function fixtureStrip() {
  return Object.entries(VISUAL_FIXTURES)
    .map(([name, fixture]) => `<div class="fixture-state" data-fixture="${name}" data-state="${fixture.state}"><strong>${fixture.label}</strong><small>${fixture.mode} · ${fixture.freshness}</small></div>`)
    .join("");
}

export function renderComponentCatalog() {
  return `
    <header class="catalog-heading"><div><span class="eyebrow">GUI02 · reusable system</span><h2>Scientific visual language</h2></div><p>Color reinforces meaning; shape, text, border and pattern carry it first.</p></header>
    <div class="historical-banner" role="status"><strong>◷ HISTORICAL / AS-OF</strong><span>Inspection only · generation 44120 · not live learner state</span></div>
    <div class="catalog-grid">${metricTile()}${deltaCard()}</div>
    ${statePanel()}
    ${evidencePanel()}
    <article class="catalog-block"><h3>Provenance, identity and alerting</h3><div class="identity-row"><span class="run-identity">RUN fixture:prometheus-disposable / GEN 44238</span><span class="provenance-chip" data-authority="source">S · FactoryRelease</span><span class="provenance-chip" data-authority="derived">D · learned projection</span></div><div class="alert" data-state="attention"><strong>! Attention</strong><span>Disk reserve is approaching the configured boundary.</span></div>${evidenceRow()}${graphLegend()}</article>
    ${stateSurfaces()}
    <article class="catalog-block"><h3>Visual-regression fixture states</h3><div class="fixture-strip">${fixtureStrip()}</div></article>
  `;
}
