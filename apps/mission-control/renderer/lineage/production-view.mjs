import { escapeText as esc } from "../frames/frame-model.mjs";
import { contextHelpMarkup, controlClass } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";
import { lineageT } from "./lineage-messages.mjs";

export const PRODUCTION_LINEAGE_TABS = Object.freeze([
  ["generations", "lineage.tab.generations"],
  ["selected", "lineage.tab.selected"],
  ["comparison", "lineage.tab.comparison"],
  ["rejected", "lineage.tab.rejected"],
]);

function compact(value) {
  const text = String(value ?? "");
  return /^[0-9a-f]{64}$/.test(text)
    ? text.slice(0, 9) + "…" + text.slice(-9)
    : text;
}

function help(t, id, labelKey, bodyKey) {
  return contextHelpMarkup({
    label: t(labelKey),
    description: t(bodyKey),
    testId: "lineage-help-" + id,
  });
}

function stateText(t, state) {
  try { return t("lineage.production.state." + (state ?? "UNKNOWN")); }
  catch (error) {
    if (!(error instanceof RangeError)) throw error;
    return t("lineage.production.state.UNKNOWN");
  }
}

function timeFact(t, labelKey, unixSeconds, id) {
  if (!Number.isSafeInteger(unixSeconds)) return "";
  return "<div><dt>" + esc(t(labelKey)) + "</dt><dd>" +
    temporalMarkup({
      unixSeconds,
      testId: "lineage-production-time-" + id,
    }) + "</dd></div>";
}

function compactFact(t, labelKey, value) {
  const actual = value ?? t("lineage.value.unavailable");
  return '<div><dt>' + esc(t(labelKey)) + '</dt><dd><code title="' +
    esc(actual) + '">' + esc(compact(actual)) + "</code></dd></div>";
}

function exactIdentityDisclosure(record, t) {
  if (!record) return "";
  const run = record.meta?.run ?? {};
  const rows = [
    ["lineage.production.manifest", run.generation_manifest_sha256],
    ["lineage.production.parentManifest", record.parent_manifest_sha256 ?? t("lineage.graph.genesis")],
    ["lineage.production.checkpoint", record.checkpoint_sha256],
    ["lineage.production.student", record.student_sha256],
    ["lineage.production.optimizer", record.optimizer_state_sha256],
    ["lineage.production.runIdentity", run.run_identity_sha256],
    ["lineage.production.candidate", run.candidate_identity_sha256],
    ["lineage.production.factoryRelease", run.factory_release_sha256],
    ["lineage.production.semanticRelease", run.semantic_release_sha256],
    ["lineage.production.topology", run.topology_sha256],
  ];
  return '<details class="ui-disclosure lineage-production-identities" ' +
    testIdAttribute("lineage", "production", "identities") +
    '><summary>' + esc(t("lineage.production.exactIdentities")) + "</summary><dl>" +
    rows.map(([key, value]) => "<div><dt>" + esc(t(key)) +
      "</dt><dd><code>" + esc(value) + "</code></dd></div>").join("") +
    "</dl></details>";
}

function generationsPanel(record, status, context, t) {
  if (!record) {
    const key = context?.mode === "HISTORICAL"
      ? "lineage.production.generationMissingHistorical"
      : "lineage.production.generationUnavailable";
    return '<section class="lineage-production-state" role="status" ' +
      testIdAttribute("lineage", "production", "generation", "state") +
      "><strong>" + esc(stateText(t, status)) + "</strong><span>" +
      esc(t(key, { generation: context?.generation })) + "</span></section>";
  }
  const run = record.meta.run;
  const parent = record.parent_manifest_sha256
    ? compact(record.parent_manifest_sha256)
    : t("lineage.graph.genesis");
  const row = '<tr><th scope="row" data-sticky="identity">' + esc(run.generation) +
    "</th><td><code>" + esc(compact(run.generation_manifest_sha256)) +
    "</code></td><td><code>" + esc(parent) + "</code></td><td><code>" +
    esc(compact(record.checkpoint_sha256)) + "</code></td><td>" +
    esc(record.status) + "</td></tr>";
  return '<section class="lineage-section lineage-lineage production-lineage-generations">' +
    '<header class="lineage-section-heading"><div><span class="eyebrow">' +
    esc(t("lineage.graph.eyebrow")) + "</span><h3>" +
    esc(t("lineage.production.contextGeneration")) + "</h3><p>" +
    esc(t("lineage.production.contextGenerationSummary")) + "</p></div>" +
    help(t, "accepted", "lineage.help.accepted.label", "lineage.help.accepted.body") +
    '</header><div class="lineage-graph-scroll" tabindex="0" role="region" aria-label="' +
    esc(t("lineage.graph.region")) + '"><ol class="lineage-tree production-lineage-tree">' +
    '<li class="lineage-tree-item"><article class="lineage-node production-lineage-node" aria-current="true">' +
    '<span class="lineage-node-generation">' +
    esc(t("lineage.graph.generation", { generation: run.generation })) +
    "</span><strong>" + esc(record.status) + '</strong><span class="lineage-node-parent">' +
    esc(t("lineage.production.parentManifestShort", { parent })) +
    '</span><span class="lineage-node-id"><span>' + esc(t("lineage.graph.manifest")) +
    "</span><code>" + esc(compact(run.generation_manifest_sha256)) +
    '</code></span><span class="lineage-node-id"><span>' +
    esc(t("lineage.graph.checkpoint")) + "</span><code>" +
    esc(compact(record.checkpoint_sha256)) +
    "</code></span></article></li></ol></div>" +
    '<div class="lineage-table-wrap" tabindex="0" role="region" aria-label="' +
    esc(t("lineage.graph.tableCaption")) + '"><table class="ui-table lineage-table"><caption>' +
    esc(t("lineage.graph.tableCaption")) +
    '</caption><thead><tr><th scope="col" data-sticky="identity">' +
    esc(t("lineage.graph.column.generation")) + '</th><th scope="col">' +
    esc(t("lineage.graph.column.manifest")) + '</th><th scope="col">' +
    esc(t("lineage.graph.column.parent")) + '</th><th scope="col">' +
    esc(t("lineage.graph.column.checkpoint")) + '</th><th scope="col">' +
    esc(t("lineage.production.status")) + "</th></tr></thead><tbody>" +
    row + "</tbody></table></div></section>";
}

function selectedPanel(record, status, t) {
  if (!record) {
    return '<section class="lineage-production-state" role="status"><strong>' +
      esc(stateText(t, status)) + "</strong></section>";
  }
  const run = record.meta.run;
  const receipts = record.meta?.receipt_refs ?? [];
  return '<section class="lineage-section lineage-dossier production-lineage-selected">' +
    '<header class="lineage-section-heading"><div><span class="eyebrow">' +
    esc(t("lineage.dossier.eyebrow")) + "</span><h3>" +
    esc(t("lineage.dossier.title", { generation: run.generation })) + "</h3><p>" +
    esc(t("lineage.production.selectedSummary")) +
    '</p></div><div class="lineage-heading-help">' +
    help(t, "transition", "lineage.help.transition.label", "lineage.help.transition.body") +
    help(t, "custody", "lineage.help.custody.label", "lineage.help.custody.body") +
    '</div></header><dl class="lineage-dossier-facts"><div><dt>' +
    esc(t("lineage.dossier.generation")) + "</dt><dd>" + esc(run.generation) +
    "</dd></div><div><dt>" + esc(t("lineage.production.status")) +
    "</dt><dd>" + esc(record.status) + "</dd></div>" +
    compactFact(t, "lineage.production.manifest", run.generation_manifest_sha256) +
    compactFact(t, "lineage.production.parentManifest",
      record.parent_manifest_sha256 ?? t("lineage.graph.genesis")) +
    compactFact(t, "lineage.production.checkpoint", record.checkpoint_sha256) +
    "<div><dt>" + esc(t("lineage.dossier.transition")) + "</dt><dd>" +
    esc(t("lineage.production.transitionNotRecorded")) + "</dd></div><div><dt>" +
    esc(t("lineage.production.authority")) + "</dt><dd>" +
    esc(record.meta?.authority) + "</dd></div><div><dt>" +
    esc(t("lineage.production.coverage")) + "</dt><dd>" +
    esc(record.meta?.coverage) + "</dd></div>" +
    timeFact(t, "lineage.production.observed", record.meta?.observed_at, "observed") +
    timeFact(t, "lineage.production.materialized", record.meta?.materialized_at, "materialized") +
    timeFact(t, "lineage.production.asOf", record.meta?.as_of, "as-of") +
    "<div><dt>" + esc(t("lineage.production.receipts")) + "</dt><dd>" +
    esc(receipts.length) + "</dd></div></dl>" + exactIdentityDisclosure(record, t) +
    '<button type="button" class="' + controlClass("inspect") +
    '" data-lineage-production-inspect ' +
    testIdAttribute("lineage", "production", "inspect") + ">" +
    esc(t("lineage.production.inspect")) + "</button></section>";
}

function comparisonPanel(record, t) {
  const generation = record?.meta?.run?.generation;
  const endpoint = generation === undefined
    ? t("lineage.value.unavailable")
    : t("lineage.graph.generation", { generation });
  return '<section class="lineage-section lineage-compare production-lineage-comparison">' +
    '<header class="lineage-section-heading"><div><span class="eyebrow">' +
    esc(t("lineage.compare.eyebrow")) + "</span><h3>" +
    esc(t("lineage.compare.title")) + "</h3><p>" +
    esc(t("lineage.production.comparisonSummary")) + "</p></div>" +
    help(t, "comparison", "lineage.help.comparison.label", "lineage.help.comparison.body") +
    '</header><dl class="lineage-dossier-facts"><div><dt>' +
    esc(t("lineage.production.selectedEndpoint")) + "</dt><dd>" +
    esc(endpoint) + "</dd></div><div><dt>" +
    esc(t("lineage.production.compareWorkflow")) + "</dt><dd>" +
    esc(t("lineage.production.compareWorkflowValue")) +
    "</dd></div></dl></section>";
}

function rejectedPanel(rejected, t) {
  const body = rejected.length
    ? '<ol class="lineage-production-rejected-list">' +
      rejected.map((record, index) => "<li " +
        testIdAttribute("lineage", "production", "rejected", index) +
        "><strong><code>" + esc(record.candidate_id ?? record.meta?.record_id) +
        "</code></strong><span>" + esc(record.capability_id) + "</span><span>" +
        esc(record.reason_code) + "</span>" +
        temporalMarkup({
          unixSeconds: record.meta?.observed_at ?? record.meta?.materialized_at,
          testId: "lineage-production-rejected-time-" + index,
        }) + "</li>").join("") + "</ol>"
    : '<p class="lineage-production-state" role="status">' +
      esc(t("lineage.production.rejectedEmpty")) + "</p>";
  return '<section class="lineage-section production-lineage-rejected">' +
    '<header class="lineage-section-heading"><div><span class="eyebrow">' +
    esc(t("lineage.rejected.eyebrow")) + "</span><h3>" +
    esc(t("lineage.rejected.title")) + "</h3><p>" +
    esc(t("lineage.production.rejectedSummary")) + "</p></div>" +
    help(t, "rejected", "lineage.help.rejected.label", "lineage.help.rejected.body") +
    "</header>" + body + "</section>";
}

function tabMarkup(activeTab, t) {
  return PRODUCTION_LINEAGE_TABS.map(([id, key]) =>
    '<button type="button" role="tab" class="' + controlClass("peer-tab") +
    '" id="lineage-production-tab-' + id + '" data-lineage-production-tab="' + id +
    '" aria-controls="lineage-production-panel-' + id + '" aria-selected="' +
    String(id === activeTab) + '" tabindex="' + (id === activeTab ? "0" : "-1") +
    '" ' + testIdAttribute("lineage", "production", "tab", id) + ">" +
    esc(t(key)) + "</button>"
  ).join("");
}

export function productionLineageMarkup({
  context,
  generation = null,
  generationState = "UNKNOWN",
  rejected = [],
  activeTab = "generations",
  t = lineageT,
} = {}) {
  const posture = context?.mode === "HISTORICAL"
    ? t("lineage.production.historical", { generation: context.generation })
    : t("lineage.production.current");
  const panels = {
    generations: generationsPanel(generation, generationState, context, t),
    selected: selectedPanel(generation, generationState, t),
    comparison: comparisonPanel(generation, t),
    rejected: rejectedPanel(rejected, t),
  };
  return '<div class="lineage-view production-lineage" ' +
    testIdAttribute("lineage", "production", "view") +
    '><header class="lineage-heading"><div><span class="eyebrow">' +
    esc(t("lineage.production.eyebrow")) + "</span><h2>" +
    esc(t("lineage.title")) + "</h2><p>" +
    esc(t("lineage.production.summary")) +
    '</p></div><div class="lineage-heading-tools"><strong>' +
    esc(posture) + "</strong>" +
    help(t, "historical", "lineage.help.historical.label", "lineage.help.historical.body") +
    '</div></header><div class="lineage-tabs" role="tablist" aria-label="' +
    esc(t("lineage.tabs.aria")) + '" ' +
    testIdAttribute("lineage", "production", "tabs") + ">" +
    tabMarkup(activeTab, t) + "</div>" +
    PRODUCTION_LINEAGE_TABS.map(([id]) =>
      '<section role="tabpanel" id="lineage-production-panel-' + id +
      '" aria-labelledby="lineage-production-tab-' + id +
      '" data-lineage-production-panel="' + id + '" ' +
      (id === activeTab ? "" : "hidden ") +
      testIdAttribute("lineage", "production", "panel", id) + ">" +
      panels[id] + "</section>"
    ).join("") + "</div>";
}
