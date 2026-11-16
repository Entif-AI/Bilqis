import { modelFixtureT as t } from "../foundation/model-fixture-i18n.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";
import { FRAME_QUERY, assertFramePage, sameFrameRequest } from "./frame-contract.mjs";
import { escapeText as esc, packingMetrics, visiblePosition, visibility } from "./frame-model.mjs";

const unavailable = () => t("model.frame.unavailable");
const show = value => esc(value ?? unavailable());
const pair = (label, value) => `<dt>${esc(label)}</dt><dd>${show(value)}</dd>`;
const modeLabel = mode => t(`model.frame.mode.${mode}`);

export function renderPackingMetrics(examples, label, hook = "metrics") {
  const metrics = packingMetrics(examples);
  const labels = {
    atoms: t("model.frame.rawAtoms"), positions: t("model.frame.neuralPositions"), ratio: t("model.frame.packingRatio"),
    fastFraction: t("model.frame.fastFraction"), partial: t("model.frame.partialPositions"), extended: t("model.frame.extendedPositions"),
    atomic: t("model.frame.atomicPositions"), expansions: t("model.frame.expansionCount"), passes: t("model.frame.expansionPasses"),
    sidecarBytes: t("model.frame.sidecarBytes"), preparationMs: t("model.frame.preparationMs"),
  };
  return `<section class="frame-metrics" aria-label="${esc(label)}" ${testIdAttribute("model", "frame", hook)}><h3>${esc(label)}</h3>
    <p>${esc(t("model.frame.fullSourceMetrics"))}</p><dl>${Object.entries(metrics)
      .map(([key, value]) => pair(labels[key], value === null ? null : Number(value.toFixed(3)))).join("")}</dl></section>`;
}

export function renderFrameExample(example, frontier) {
  const identity = `<div class="frame-provenance-heading">${contextHelpMarkup({ label: t("model.frame.help.provenance.label"), description: t("model.frame.help.provenance.description"), testId: "model-frame-help-provenance" })}</div><details class="frame-disclosure" ${testIdAttribute("model", "frame", "receipt", "provenance")}><summary ${testIdAttribute("model", "frame", "receipt", "provenance", "toggle")}>${esc(t("model.frame.receiptProvenance", { version: example.compiler?.version ?? unavailable() }))}</summary><dl class="frame-identity">${pair(t("model.frame.receipt"), example.receiptId)}${pair(t("model.neural.frame"), example.frameId)}
    ${pair(t("model.frame.source"), example.sourceId)}${pair(t("model.frame.generationManifest"), example.generationManifest)}
    ${pair(t("model.frame.compilerVersion"), example.compiler?.version)}${pair(t("model.frame.compilerDigest"), example.compiler?.digest)}
    ${pair(t("model.frame.sourceDigest"), example.sourceDigest)}${pair(t("model.frame.compiledDigest"), example.compiledDigest)}</dl></details>`;
  if (example.positions === null) return `${identity}<p class="frame-request-state" role="status" ${testIdAttribute("model", "frame", "sidecar", "unavailable")}>${esc(t("model.frame.sidecarUnavailable"))}</p>`;
  const positions = example.positions.map(position => {
    const view = visiblePosition(position, frontier);
    const metadata = view.metadata;
    const heading = metadata ? `${show(metadata.path)} · ${show(metadata.schema)}` : show(view.state);
    const rows = view.constituents.map(atom => atom.state
      ? `<tr><td>${atom.sourceOrder}</td><td colspan="6">${esc(t("model.frame.contentsHidden", { state: atom.state }))}</td></tr>`
      : `<tr><td>${atom.sourceOrder}</td><td>${esc(atom.atom)}</td><td>${esc(atom.role)}</td>
         <td>${atom.occurrenceIndex}</td><td>${esc(atom.semanticId)}</td><td>${esc(atom.sourceRef)}</td><td>${esc(t("model.frame.legal"))}</td></tr>`).join("");
    const metadataHtml = metadata ? `<dl class="frame-identity">${pair(t("model.frame.schemaTag"), metadata.tag)}
      ${pair(t("model.frame.occurrence"), metadata.occurrenceId)}${pair(t("model.frame.literalReason"), metadata.reason)}${pair(t("model.frame.sidecarReference"), metadata.sidecarRef)}</dl>` : "";
    const fields = metadata ? position.fields?.map(field => visibility(field.visibleAt, frontier) === "Legal"
      ? pair(field.name, field.value) : pair(t("model.frame.codecField"), t("model.frame.codecHidden", { state: visibility(field.visibleAt, frontier) }))).join("") : null;
    return `<details class="frame-disclosure frame-position" ${testIdAttribute("model", "frame", "position", position.index)}><summary>${esc(t("model.frame.position", { index: position.index, heading }))} · ${esc(t("model.frame.expandConstituents"))}</summary>
      ${metadataHtml}<div class="frame-table-scroll" tabindex="0" ${testIdAttribute("model", "frame", "position", position.index, "table", "wrap")}><table><caption>${esc(t("model.frame.constituents", { frontier }))}</caption>
      <thead><tr><th scope="col">${esc(t("model.frame.order"))}</th><th scope="col">${esc(t("model.frame.atom"))}</th><th scope="col">${esc(t("model.frame.role"))}</th><th scope="col">${esc(t("model.frame.occurrenceIndex"))}</th><th scope="col">${esc(t("model.frame.semanticId"))}</th><th scope="col">${esc(t("model.frame.sourceReference"))}</th><th scope="col">${esc(t("model.frame.legality"))}</th></tr></thead>
      <tbody>${rows}</tbody></table></div><dl class="frame-identity">${fields ?? pair(t("model.frame.codecFields"), unavailable())}</dl></details>`;
  }).join("");
  return `${identity}${positions}`;
}

export class FrameQueryController {
  constructor(querySnapshot, publish) {
    this.querySnapshot = querySnapshot;
    this.publish = publish;
    this.epoch = 0;
  }
  dispose() { this.epoch += 1; }
  async load(request) {
    const epoch = ++this.epoch;
    this.publish({ state: "LOADING", request, page: null });
    try {
      const page = assertFramePage(await this.querySnapshot(request));
      if (!sameFrameRequest(request, page.request)) throw new TypeError("FRAME_INSPECTION_REQUEST_MISMATCH");
      if (epoch === this.epoch) this.publish({ state: page.state, request, page });
    } catch {
      if (epoch === this.epoch) this.publish({ state: "ERROR", request, page: null });
    }
  }
}

export function mountFrameExplorer(host, { querySnapshot, context, selectedId, onContext, onSelection }) {
  let selected = selectedId;
  host.innerHTML = `<div class="frame-explorer" ${testIdAttribute("model", "frame", "workspace")}>
    <header class="frame-heading"><div><span class="eyebrow">${esc(t("model.frame.eyebrow"))}</span><h2>${esc(t("model.frame.title"))}</h2></div><div class="frame-heading-detail"><p>${esc(t("model.frame.summary"))}</p>${contextHelpMarkup({ label: t("model.frame.help.concepts.label"), description: t("model.frame.help.concepts.description"), testId: "model-frame-help-concepts" })}</div></header>
    <section class="frame-fixture-posture" ${testIdAttribute("model", "frame", "fixture", "posture")}><div><strong>${esc(t("model.frame.fixtureLabel"))}</strong><span>${esc(t("model.frame.fixtureDetail"))}</span>${contextHelpMarkup({ label: t("model.neural.help.posture.label"), description: t("model.neural.help.posture.description"), testId: "model-frame-help-posture" })}</div></section>
    <div class="frame-control-bar" ${testIdAttribute("model", "frame", "controls")}>
      <label>${esc(t("model.frame.generation"))}<select data-frame-generation data-focus-key="frame-generation" ${testIdAttribute("model", "frame", "generation")}>
        <option value="7">${esc(t("model.frame.currentFixture"))}</option><option value="6">${esc(t("model.frame.historicalFixture"))}</option></select></label>
      <div class="frame-request-block"><span>${esc(t("model.frame.requestState"))}${contextHelpMarkup({ label: t("model.frame.help.controls.label"), description: t("model.frame.help.controls.description"), testId: "model-frame-help-controls" })}</span><p data-frame-state role="status" ${testIdAttribute("model", "frame", "request", "state")}></p></div>
    </div>
    <div data-frame-results ${testIdAttribute("model", "frame", "results")}></div>
  </div>`;
  const results = host.querySelector('[data-test-id="model-frame-results"]');
  const generationSelect = host.querySelector('[data-test-id="model-frame-generation"]');
  generationSelect.value = String(context.generation);
  const controller = new FrameQueryController(querySnapshot, result => {
    const state = host.querySelector('[data-test-id="model-frame-request-state"]');
    state.textContent = t("model.frame.requested", { state: result.state, runId: result.request.runId, generation: result.request.generation, mode: modeLabel(result.request.mode) });
    results.replaceChildren();
    const page = result.page;
    if (!page?.operatorView) return;
    onContext(page.operatorView, page.request.mode);
    const examples = page.examples;
    if (!examples.length) return;
    const observed = page.operatorView.meta?.observed_at;
    const materialized = page.operatorView.meta?.materialized_at;
    const temporal = [
      ["model.neural.observed", observed, "model-frame-observed"],
      ["model.neural.materialized", materialized, "model-frame-materialized"],
    ].filter(([, value]) => Number.isSafeInteger(value));
    results.innerHTML = `<section class="frame-result-set" ${testIdAttribute("model", "frame", "result", "set")}><div class="frame-result-status"><p class="frame-coverage" ${testIdAttribute("model", "frame", "coverage")}>${esc(t("model.frame.coverage", { coverage: page.coverage, count: examples.length }))}</p>${temporal.length ? `<dl class="frame-time-facts">${temporal.map(([label, value, hook]) => `<div><dt>${esc(t(label))}</dt><dd>${temporalMarkup({ unixSeconds: value, testId: hook })}</dd></div>`).join("")}</dl>` : ""}</div>
      <div class="frame-example-control"><label>${esc(t("model.frame.compiledExample"))}<select data-frame-example data-focus-key="frame-example" ${testIdAttribute("model", "frame", "example")}><option value="">${esc(t("model.frame.selectExact"))}</option>
      ${examples.map(example => `<option value="${esc(example.frameId)}">${esc(example.frameId)}</option>`).join("")}</select></label></div>
      <div data-frame-detail ${testIdAttribute("model", "frame", "detail")}></div><details class="frame-disclosure frame-aggregate" ${testIdAttribute("model", "frame", "aggregate")}><summary>${esc(t("model.frame.aggregatePacking", { count: examples.length }))}</summary>
      ${renderPackingMetrics(examples, t("model.frame.allReturned"), "aggregate-metrics")}</details></section>`;
    const selector = results.querySelector('[data-test-id="model-frame-example"]');
    const detail = results.querySelector('[data-test-id="model-frame-detail"]');
    function selectExample(id) {
      selected = id;
      const example = examples.find(item => item.frameId === id);
      selector.value = example?.frameId ?? "";
      if (!example) {
        detail.textContent = id ? t("model.frame.missingExact", { id }) : t("model.frame.selectPrompt");
        return;
      }
      const atoms = packingMetrics([example]).atoms;
      detail.innerHTML = `<div class="frame-selected-summary">${renderPackingMetrics([example], t("model.frame.selectedExample"), "selected-metrics")}
        <label>${esc(t("model.frame.predictionFrontier"))}${contextHelpMarkup({ label: t("model.frame.help.frontier.label"), description: t("model.frame.help.frontier.description"), testId: "model-frame-help-frontier" })}<select data-frame-frontier data-focus-key="frame-frontier" ${testIdAttribute("model", "frame", "frontier")} ${atoms === null ? "disabled" : ""}>
        ${atoms === null ? `<option>${esc(unavailable())}</option>` : Array.from({ length: atoms + 1 }, (_, p) => `<option value="${p}">${esc(t("model.frame.frontierOption", { count: p }))}</option>`).join("")}</select></label></div>
        <div data-frame-positions ${testIdAttribute("model", "frame", "positions")}></div>`;
      const frontier = detail.querySelector('[data-test-id="model-frame-frontier"]');
      const draw = () => {
        const positions = detail.querySelector('[data-test-id="model-frame-positions"]');
        const open = [...positions.querySelectorAll("details")].map(node => node.open);
        positions.innerHTML = renderFrameExample(example, Number(frontier.value) || 0);
        positions.querySelectorAll("details").forEach((node, index) => { node.open = open[index] ?? false; });
      };
      if (atoms !== null) frontier.value = String(atoms);
      frontier.addEventListener("change", draw);
      draw();
    }
    selector.addEventListener("change", () => {
      onSelection(selector.value);
      selectExample(selector.value);
    });
    selectExample(selected);
  });
  const load = () => {
    const generation = Number(generationSelect.value);
    void controller.load({ schemaVersion: FRAME_QUERY, runId: context.runId,
      generation, mode: generation === 7 ? "current" : "historical" });
  };
  generationSelect.addEventListener("change", () => {
    selected = null;
    onSelection(null);
    load();
  });
  load();
  return { dispose: () => controller.dispose() };
}
