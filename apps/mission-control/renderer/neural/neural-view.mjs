import { modelFixtureT as t } from "../foundation/model-fixture-i18n.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";
import { INSTRUMENTATION_STATES } from "./neural-fixture.mjs";
import {
  ccgqaEvidenceState,
  neuralFixture,
  refinementCostSummary,
  refinementHistogram,
} from "./neural-model.mjs";

const ui = { selected: "fixture:ccgqa:g7:l3" };
const esc = value => String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const pct = value => `${(100 * value).toFixed(1)}%`;
const unavailable = () => t("model.neural.unavailable");

function stateBadge(state, ...hook) {
  const normalized = String(state).toLowerCase().replaceAll("_", "-");
  return `<span class="neural-state" data-neural-state="${esc(normalized)}" ${testIdAttribute("model", ...hook)}>${esc(state)}</span>`;
}

function topologyFields(topology) {
  if (topology.schema.endsWith("/v2")) return [
    [t("model.neural.architecture"), topology.architectureId], [t("model.neural.layers"), topology.layers],
    [t("model.neural.width"), topology.width], [t("model.neural.ffn"), topology.ffnDimension],
    [t("model.neural.qHeads"), topology.queryHeads], [t("model.neural.kvHeads"), topology.kvHeads],
    [t("model.neural.headDim"), topology.headDimension], [t("model.neural.context"), topology.context],
    [t("model.neural.convolution"), `${topology.convolution} k=${topology.convolutionKernel}`],
    [t("model.neural.depthGroups"), topology.depthGroups],
  ];
  return [
    [t("model.neural.layers"), topology.layers], [t("model.neural.heads"), topology.heads],
    [t("model.neural.width"), topology.width], [t("model.neural.ffn"), topology.ffnDimension],
    [t("model.neural.context"), topology.context],
  ];
}

function topologyPathLabel(fixture, index) {
  if (fixture.topology.schema.endsWith("/v1")) {
    return [
      t("model.neural.path.v1.input"),
      t("model.neural.path.v1.attention", { layers: fixture.topology.layers }),
      t("model.neural.path.v1.output"),
    ][index];
  }
  return [
    "input", "ccgqa14", "attn1", "ccgqa58", "attn2", "ccgqa912", "attn3", "output",
  ].map(key => t(`model.neural.path.v2.${key}`))[index];
}

function topologyRuntime(fixture) {
  const sample = fixture.telemetry;
  const metrics = [
    [t("model.neural.optimizerStep"), sample.optimizerStep],
    [t("model.neural.stepDuration"), sample.stepDurationMs === null ? unavailable() : `${sample.stepDurationMs} ms`],
    [t("model.neural.activeParameters"), sample.activeParameters === null ? unavailable() : sample.activeParameters.toLocaleString()],
    [t("model.neural.refinementFraction"), sample.refinementFraction === null ? unavailable() : pct(sample.refinementFraction)],
  ];
  const times = [
    ["model.neural.observed", sample.observedAt, "model-neural-runtime-observed"],
    ["model.neural.materialized", sample.materializedAt, "model-neural-runtime-materialized"],
  ].filter(([, value]) => Number.isSafeInteger(value));
  return `<section class="neural-section neural-primary" ${testIdAttribute("model", "neural", "topology-runtime")}>
    <header class="neural-section-heading"><div><span class="eyebrow">${esc(t("model.neural.topologyEyebrow"))}</span><h3>${esc(t("model.neural.topologyTitle"))}</h3></div><div class="neural-section-tools">${stateBadge(sample.coverage, "neural", "runtime", "state")}${contextHelpMarkup({ label: t("model.neural.help.topology.label"), description: t("model.neural.help.topology.description"), testId: "model-neural-help-topology" })}</div></header>
    <div class="neural-runtime-grid">
      <div><h4>${esc(t("model.neural.topologyManifest"))}</h4><code class="neural-manifest">${esc(fixture.topology.schema)}</code>
        <ol class="topology-path" ${testIdAttribute("model", "neural", "topology", "path")}>${fixture.path.map((_stage, index) => `<li><span>${index + 1}</span><strong>${esc(topologyPathLabel(fixture, index))}</strong></li>`).join("")}</ol>
        <dl class="topology-facts">${topologyFields(fixture.topology).map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl>
      </div>
      <div><h4>${esc(t("model.neural.runtimeProjection"))}</h4><code class="neural-manifest">${esc(sample.schema)}</code>
        <div class="neural-runtime-authority">${contextHelpMarkup({ label: t("model.neural.help.authority.label"), description: t("model.neural.help.authority.description"), testId: "model-neural-help-authority" })}</div>
        <dl class="runtime-metrics">${metrics.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}<small>${esc(sample.authority)} · ${esc(sample.coverage)}</small></dd></div>`).join("")}</dl>
        ${times.length ? `<dl class="neural-time-facts">${times.map(([label, value, hook]) => `<div><dt>${esc(t(label))}</dt><dd>${temporalMarkup({ unixSeconds: value, testId: hook })}</dd></div>`).join("")}</dl>` : ""}
      </div>
    </div>
  </section>`;
}

function quietUnavailable(eyebrow, title, detail, hook) {
  return `<section class="neural-section neural-unavailable" ${testIdAttribute("model", "neural", hook, "unavailable")}>
    <header class="neural-section-heading"><div><span class="eyebrow">${esc(eyebrow)}</span><h3>${esc(title)}</h3></div>${stateBadge("UNAVAILABLE", "neural", hook, "state")}</header>
    <p>${esc(detail)}</p>
  </section>`;
}

function ccgqaPanel(fixture) {
  if (!fixture.ccgqa) return quietUnavailable(t("model.neural.ccgqaEyebrow"), t("model.neural.ccgqaUnavailable"), t("model.neural.ccgqaUnavailableDetail"), "ccgqa");
  return `<section class="neural-section" ${testIdAttribute("model", "neural", "ccgqa")}>
    <header class="neural-section-heading"><div><span class="eyebrow">${esc(t("model.neural.ccgqaEyebrow"))}</span><h3>${esc(t("model.neural.ccgqaTitle"))}</h3></div>${contextHelpMarkup({ label: t("model.neural.help.ccgqa.label"), description: t("model.neural.help.ccgqa.description"), testId: "model-neural-help-ccgqa" })}</header>
    <details class="neural-disclosure" ${testIdAttribute("model", "neural", "ccgqa", "disclosure")}><summary ${testIdAttribute("model", "neural", "ccgqa", "disclosure", "toggle")}>${esc(t("model.neural.disclosure.ccgqa", { count: fixture.ccgqa.length }))}</summary>
    <div class="neural-table-wrap" tabindex="0" ${testIdAttribute("model", "neural", "ccgqa", "table", "wrap")}><table class="neural-table" ${testIdAttribute("model", "neural", "ccgqa", "table")}>
      <thead><tr><th scope="col">${esc(t("model.neural.layer"))}</th><th scope="col">${esc(t("model.neural.evidence"))}</th><th scope="col">${esc(t("model.neural.q"))}</th><th scope="col">${esc(t("model.neural.k"))}</th><th scope="col">${esc(t("model.neural.v"))}</th><th scope="col">${esc(t("model.neural.channel"))}</th><th scope="col">${esc(t("model.neural.convHealth"))}</th><th scope="col">${esc(t("model.neural.entropy"))}</th><th scope="col">${esc(t("model.neural.sequenceFrames"))}</th><th scope="col">${esc(t("model.neural.cache"))}</th><th scope="col">${esc(t("model.neural.finite"))}</th><th scope="col"></th></tr></thead>
      <tbody>${fixture.ccgqa.map(sample => {
        const state = ccgqaEvidenceState(sample);
        return `<tr data-evidence-state="${state.toLowerCase()}" ${testIdAttribute("model", "neural", "ccgqa", "layer", sample.layer)}><th scope="row">${sample.layer}</th><td>${stateBadge(state, "neural", "ccgqa", "layer", sample.layer, "state")}${state === "INVALID" ? `<small class="invalid-evidence-note">${esc(t("model.neural.maskViolations", { count: sample.maskInvalidViolations }))}</small>` : ""}</td><td>${pct(sample.qUtilization)}</td><td>${pct(sample.kUtilization)}</td><td>${pct(sample.vUtilization)}</td><td>${pct(sample.channelUtilization)}</td><td>${esc(sample.convolutionHealth)}</td><td>${sample.entropyMean.toFixed(2)} / ${sample.entropyP95.toFixed(2)}</td><td>${sample.activeSequenceLength} / ${sample.activeFrameLength}</td><td>${esc(sample.cacheState)} · ${pct(sample.cacheUsage)}</td><td>${esc(sample.finite ? "FINITE" : "NONFINITE")}</td><td><button type="button" data-neural-inspect="${esc(sample.evidenceId)}" data-kind="ccgqa" ${testIdAttribute("model", "neural", "ccgqa", "layer", sample.layer, "inspect")}>${esc(t("model.neural.inspectEvidence"))}</button></td></tr>`;
      }).join("")}</tbody>
    </table></div></details>
  </section>`;
}

function attnResPanel(fixture) {
  if (!fixture.attnres) return quietUnavailable(t("model.neural.attnEyebrow"), t("model.neural.attnUnavailable"), t("model.neural.attnUnavailableDetail"), "attnres");
  return `<section class="neural-section" ${testIdAttribute("model", "neural", "attnres")}>
    <header class="neural-section-heading"><div><span class="eyebrow">${esc(t("model.neural.attnEyebrow"))}</span><h3>${esc(t("model.neural.attnTitle"))}</h3></div><div class="neural-section-tools">${stateBadge("PRESENT", "neural", "attnres", "state")}${contextHelpMarkup({ label: t("model.neural.help.attnres.label"), description: t("model.neural.help.attnres.description"), testId: "model-neural-help-attnres" })}</div></header>
    <p class="neural-doctrine">${esc(t("model.neural.attnDoctrine"))}</p>
    <details class="neural-disclosure" ${testIdAttribute("model", "neural", "attnres", "disclosure")}><summary>${esc(t("model.neural.disclosure.attnres", { count: fixture.attnres.length }))}</summary>
    <div class="neural-table-wrap" tabindex="0" ${testIdAttribute("model", "neural", "attnres", "table", "wrap")}><table class="neural-table attnres-table"><thead><tr><th scope="col">${esc(t("model.neural.attnBoundaryColumn"))}</th><th scope="col">${esc(t("model.neural.attnBasis"))}</th><th scope="col">${esc(t("model.neural.attnWeightSum"))}</th><th scope="col">${esc(t("model.neural.attnGate"))}</th><th scope="col"></th></tr></thead><tbody>
      ${fixture.attnres.map(entry => `<tr ${testIdAttribute("model", "neural", "attnres", "boundary", entry.boundaryGroup)}><th scope="row">${esc(t("model.neural.attnBoundary", { group: entry.boundaryGroup, layer: entry.completedLayer }))}</th><td><div class="mixture-bars">${entry.pairs.map(pair => `<div><span>${esc(pair.source)}</span><progress max="1" value="${pair.weight}"></progress><strong>${pair.weight.toFixed(2)}</strong></div>`).join("")}</div></td><td>${entry.weightSum.toFixed(2)}</td><td>${entry.gate.toFixed(3)}</td><td><button type="button" data-neural-inspect="${esc(entry.evidenceId)}" data-kind="attnres" ${testIdAttribute("model", "neural", "attnres", "boundary", entry.boundaryGroup, "inspect")}>${esc(t("model.neural.inspectWeights"))}</button></td></tr>`).join("")}
    </tbody></table></div></details>
  </section>`;
}

function refinementPanel(fixture) {
  if (!fixture.refinementReceipts) return quietUnavailable(t("model.neural.refinementEyebrow"), t("model.neural.refinementUnavailable"), t("model.neural.refinementUnavailableDetail"), "refinement");
  const histogram = refinementHistogram(fixture.refinementReceipts);
  const cost = refinementCostSummary(fixture.refinementReceipts);
  const bins = [[t("model.neural.noExpansion"), histogram.none], [t("model.neural.onePass"), histogram.one], [t("model.neural.multiplePasses"), histogram.multiple]];
  return `<section class="neural-section" ${testIdAttribute("model", "neural", "refinement")}>
    <header class="neural-section-heading"><div><span class="eyebrow">${esc(t("model.neural.refinementEyebrow"))}</span><h3>${esc(t("model.neural.refinementTitle"))}</h3></div><div class="neural-section-tools">${stateBadge("PRESENT", "neural", "refinement", "state")}${contextHelpMarkup({ label: t("model.neural.help.refinement.label"), description: t("model.neural.help.refinement.description"), testId: "model-neural-help-refinement" })}</div></header>
    <div class="refinement-summary"><div class="refinement-histogram">${bins.map(([label, value], index) => `<div ${testIdAttribute("model", "neural", "refinement", "bin", index)}><span>${esc(label)}</span><progress max="${histogram.total}" value="${value}"></progress><strong>${value}</strong></div>`).join("")}</div><p>${esc(t("model.neural.refinementSummary", { total: histogram.total, active: cost.activeFrames, cost: cost.totalCostMs.toFixed(1), density: cost.averageFrameDensity.toFixed(2) }))}</p></div>
    <details class="neural-disclosure" ${testIdAttribute("model", "neural", "refinement", "disclosure")}><summary>${esc(t("model.neural.disclosure.receipts", { count: fixture.refinementReceipts.length }))}</summary>
    <div class="neural-table-wrap" tabindex="0"><table class="neural-table"><thead><tr><th scope="col">${esc(t("model.neural.frame"))}</th><th scope="col">${esc(t("model.neural.episodeReceipt"))}</th><th scope="col">${esc(t("model.neural.eligible"))}</th><th scope="col">${esc(t("model.neural.quota"))}</th><th scope="col">${esc(t("model.neural.passes"))}</th><th scope="col">${esc(t("model.neural.frameDensity"))}</th><th scope="col">${esc(t("model.neural.costMs"))}</th></tr></thead><tbody>
      ${fixture.refinementReceipts.map((row, index) => `<tr ${testIdAttribute("model", "neural", "refinement", "receipt", index)}><td>${esc(row.frameId)}</td><td><button type="button" data-neural-inspect="${esc(row.episodeReceipt)}" data-kind="refinement" ${testIdAttribute("model", "neural", "refinement", "receipt", index, "inspect")}>${esc(row.episodeReceipt)}</button></td><td>${row.eligibleFrames}</td><td>${row.quota}</td><td>${row.passes}</td><td>${row.frameDensity.toFixed(2)}</td><td>${row.resourceCostMs.toFixed(1)}</td></tr>`).join("")}
    </tbody></table></div></details>
  </section>`;
}

function instrumentationPanel(fixture) {
  const states = fixture.mode === "historical"
    ? INSTRUMENTATION_STATES.map(item => ({ ...item, state: "UNAVAILABLE" }))
    : INSTRUMENTATION_STATES;
  return `<section class="neural-section instrumentation-panel" ${testIdAttribute("model", "neural", "instrumentation")}>
    <header class="neural-section-heading"><div><span class="eyebrow">${esc(t("model.neural.instrumentationEyebrow"))}</span><h3>${esc(t("model.neural.instrumentationTitle"))}</h3></div>${contextHelpMarkup({ label: t("model.neural.help.instrumentation.label"), description: t("model.neural.help.instrumentation.description"), testId: "model-neural-help-instrumentation" })}</header>
    <div class="neural-table-wrap" tabindex="0"><table class="neural-table"><thead><tr><th scope="col">${esc(t("model.neural.instrument"))}</th><th scope="col">${esc(t("model.neural.source"))}</th><th scope="col">${esc(t("model.neural.state"))}</th></tr></thead><tbody>
      ${states.map((item, index) => `<tr ${testIdAttribute("model", "neural", "instrument", index)}><th scope="row">${esc(t(`model.neural.instrument.${item.id}.label`))}</th><td>${esc(fixture.mode === "historical" ? t("model.neural.instrument.historicalUnavailable") : t(`model.neural.instrument.${item.id}.source`))}</td><td>${stateBadge(item.state, "neural", "instrument", index, "state")}</td></tr>`).join("")}
    </tbody></table></div>
  </section>`;
}

function bind(container, inspect, mode, onModeChange) {
  container.querySelectorAll("[data-neural-mode]").forEach(button => button.addEventListener("click", () => {
    const nextMode = button.dataset.neuralMode;
    if (nextMode === mode) return;
    if (typeof onModeChange === "function") onModeChange(nextMode);
    else renderNeuralView(container, inspect, { mode: nextMode });
  }));
  container.querySelectorAll("[data-neural-inspect]").forEach(button => button.addEventListener("click", () => {
    ui.selected = button.dataset.neuralInspect;
    inspect(button.dataset.neuralInspect, button.dataset.kind);
  }));
}

export function renderNeuralMarkup(mode = "current") {
  const fixture = neuralFixture(mode);
  return `<div class="neural-view" ${testIdAttribute("model", "neural", "workspace")}>
    <header class="neural-heading"><div><span class="eyebrow">${esc(t("model.neural.eyebrow"))}</span><h2>${esc(t("model.neural.title"))}</h2></div><p>${esc(t("model.neural.summary"))}</p></header>
    <section class="neural-fixture-posture" ${testIdAttribute("model", "neural", "fixture", "posture")}><div><strong>${esc(t("model.neural.fixtureLabel"))}</strong><span>${esc(t("model.neural.fixturePosture", { generation: fixture.telemetry.generation }))}</span></div><div class="neural-fixture-help"><p>${esc(t("model.neural.fixtureDetail"))}</p>${contextHelpMarkup({ label: t("model.neural.help.posture.label"), description: t("model.neural.help.posture.description"), testId: "model-neural-help-posture" })}</div></section>
    <div class="neural-mode-switch" role="group" aria-label="${esc(t("model.neural.fixtureGroup"))}">
      <button type="button" data-neural-mode="current" aria-pressed="${mode === "current"}" ${testIdAttribute("model", "neural", "fixture", "current")}>${esc(t("model.neural.currentFixture"))}</button>
      <button type="button" data-neural-mode="historical" aria-pressed="${mode === "historical"}" ${testIdAttribute("model", "neural", "fixture", "historical")}>${esc(t("model.neural.historicalFixture"))}</button>
    </div>
    ${topologyRuntime(fixture)}
    <div class="neural-mechanism-stack">${ccgqaPanel(fixture)}${attnResPanel(fixture)}${refinementPanel(fixture)}${instrumentationPanel(fixture)}</div>
  </div>`;
}

export function renderNeuralView(container, inspect, { mode = "current", onModeChange = null } = {}) {
  container.innerHTML = renderNeuralMarkup(mode);
  bind(container, inspect, mode, onModeChange);
}

export function neuralViewModeForTest() {
  return "route-owned";
}
