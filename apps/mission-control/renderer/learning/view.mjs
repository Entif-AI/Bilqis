import { escapeText as esc } from "../frames/frame-model.mjs";
import { t } from "../foundation/i18n.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";
import {
  CANDIDATE_DECISION_SCHEMA,
  LEARNING_EPISODE_SCHEMA,
  recordId,
  recordLabel,
} from "./query.mjs";

export const PRODUCTION_LEARNING_TABS = Object.freeze([
  Object.freeze(["transaction", "learning.tab.transaction"]),
  Object.freeze(["lifecycle", "learning.tab.lifecycle"]),
  Object.freeze(["comparison", "learning.tab.comparison"]),
  Object.freeze(["outcome", "learning.tab.outcome"]),
]);

function fact(label, value) {
  return "<div><dt>" + esc(label) + "</dt><dd>" +
    esc(value ?? t("learning.value.unavailable")) + "</dd></div>";
}

function timeFact(label, unixSeconds, testId) {
  if (!Number.isSafeInteger(unixSeconds)) return "";
  return "<div><dt>" + esc(label) + "</dt><dd>" +
    temporalMarkup({ unixSeconds, testId }) + "</dd></div>";
}

function facts(record) {
  const meta = record?.meta ?? {};
  const type = record?.schema_version === LEARNING_EPISODE_SCHEMA
    ? t("learning.production.episode")
    : record?.schema_version === CANDIDATE_DECISION_SCHEMA
      ? t("learning.production.decision")
      : record?.schema_version;
  return [
    fact(t("learning.production.recordType"), type),
    fact(t("learning.production.recordId"), recordId(record)),
    fact(t("learning.production.capability"), record?.capability_id),
    record?.episode_id ? fact(t("learning.production.episodeId"), record.episode_id) : "",
    record?.candidate_id ? fact(t("learning.production.candidateId"), record.candidate_id) : "",
    record?.visit_id ? fact(t("learning.production.visitId"), record.visit_id) : "",
    fact(t("learning.production.authority"), meta.authority),
    fact(t("learning.production.coverage"), meta.coverage),
    timeFact(t("learning.production.materialized"), meta.materialized_at,
      "learning-production-materialized"),
    timeFact(t("learning.production.observed"), meta.observed_at,
      "learning-production-observed"),
    timeFact(t("learning.production.asOf"), meta.as_of,
      "learning-production-as-of"),
  ].join("");
}

function transactionPanel(record) {
  if (!record) return "<p>" + esc(t("learning.production.empty")) + "</p>";
  return [
    '<section class="episode-summary production-learning-panel">',
    '<header class="episode-section-heading"><h3>',
    esc(t("learning.production.transaction.title")),
    "</h3></header><dl class=\"production-learning-facts\">",
    facts(record),
    "</dl></section>",
  ].join("");
}

function lifecyclePanel(record) {
  if (!record) return "<p>" + esc(t("learning.production.empty")) + "</p>";
  return [
    '<section class="episode-lifecycle production-learning-panel">',
    '<header class="episode-section-heading"><h3>',
    esc(t("learning.production.lifecycle.title")),
    "</h3></header><dl class=\"production-learning-facts\">",
    record.started_at !== undefined
      ? timeFact(t("learning.production.started"), record.started_at,
        "learning-production-started") : "",
    record.completed_at !== undefined && record.completed_at !== null
      ? timeFact(t("learning.production.completed"), record.completed_at,
        "learning-production-completed") : "",
    record.completed_at === null
      ? fact(t("learning.production.completed"), t("learning.production.inProgress")) : "",
    record.state ? fact(t("learning.production.state"), record.state) : "",
    record.outcome ? fact(t("learning.production.outcome"), record.outcome) : "",
    timeFact(t("learning.production.materialized"), record.meta?.materialized_at,
      "learning-production-lifecycle-materialized"),
    "</dl></section>",
  ].join("");
}

function comparisonPanel(record) {
  if (!record) return "<p>" + esc(t("learning.production.empty")) + "</p>";
  const meta = record.meta ?? {};
  return [
    '<section class="episode-comparison production-learning-panel">',
    '<header class="episode-section-heading"><h3>',
    esc(t("learning.production.comparison.title")),
    "</h3></header><dl class=\"production-learning-facts\">",
    fact(t("learning.production.authority"), meta.authority),
    fact(t("learning.production.coverage"), meta.coverage),
    fact(t("learning.production.sources"), String(meta.source_refs?.length ?? 0)),
    fact(t("learning.production.evidence"), String(meta.evidence_refs?.length ?? 0)),
    fact(t("learning.production.receipts"), String(meta.receipt_refs?.length ?? 0)),
    "</dl></section>",
  ].join("");
}

function outcomePanel(record) {
  if (!record) return "<p>" + esc(t("learning.production.empty")) + "</p>";
  return [
    '<section class="episode-outcome production-learning-panel">',
    '<header class="episode-section-heading"><h3>',
    esc(t("learning.production.outcome.title")),
    "</h3></header><dl class=\"production-learning-facts\">",
    record.outcome ? fact(t("learning.production.outcome"), record.outcome) : "",
    record.reason_code ? fact(t("learning.production.reason"), record.reason_code) : "",
    record.state ? fact(t("learning.production.state"), record.state) : "",
    "</dl></section>",
  ].join("");
}

function tabMarkup(activeTab) {
  return PRODUCTION_LEARNING_TABS.map(([id, key]) => [
    '<button type="button" role="tab" id="learning-production-tab-', id,
    '" data-learning-production-tab="', id,
    '" aria-controls="learning-production-panel-', id,
    '" aria-selected="', String(id === activeTab),
    '" tabindex="', id === activeTab ? "0" : "-1", '">',
    esc(t(key)), "</button>",
  ].join("")).join("");
}

function panelMarkup(activeTab, record) {
  const content = {
    transaction: transactionPanel(record),
    lifecycle: lifecyclePanel(record),
    comparison: comparisonPanel(record),
    outcome: outcomePanel(record),
  };
  return PRODUCTION_LEARNING_TABS.map(([id]) => [
    '<section role="tabpanel" id="learning-production-panel-', id,
    '" aria-labelledby="learning-production-tab-', id,
    '" data-learning-production-panel="', id, '" ',
    id === activeTab ? "" : "hidden", ">",
    content[id], "</section>",
  ].join("")).join("");
}

export function productionLearningMarkup({
  context,
  records = [],
  selectedId = null,
  activeTab = "transaction",
  status = "PRESENT",
} = {}) {
  const record = records.find((item) => recordId(item) === selectedId) ?? records[0] ?? null;
  const selected = record ? recordId(record) : "";
  const posture = context?.mode === "HISTORICAL"
    ? t("learning.production.historical", { generation: context.generation })
    : t("learning.production.current");
  const statusMessage = ["EMPTY", "MISSING"].includes(status)
    ? t("learning.production.empty")
    : ["UNAVAILABLE", "DENIED", "UNKNOWN"].includes(status)
      ? t("learning.production.unavailable") : "";
  return [
    '<div class="episodes-view production-learning" ',
    testIdAttribute("learning", "production", "view"), ">",
    '<header class="episodes-heading"><div><span class="eyebrow">',
    esc(t("learning.production.eyebrow")), "</span><h2>",
    esc(t("learning.production.title")), "</h2></div>",
    '<div class="episode-heading-tools"><strong>', esc(posture), "</strong>",
    contextHelpMarkup({
      label: t("learning.production.help.provenance.label"),
      description: t("learning.production.help.provenance.description"),
      testId: "learning-production-help-provenance",
    }),
    "</div></header>",
    '<div class="episode-picker"><label for="learning-production-selector"><span>',
    esc(t("learning.production.record")), "</span>",
    '<select id="learning-production-selector" data-learning-production-selector ',
    testIdAttribute("learning", "production", "selector"), ">",
    records.map((item) => [
      '<option value="', esc(recordId(item)), '" ',
      recordId(item) === selected ? "selected" : "", ">",
      esc(recordLabel(item, t("learning.value.unknown"))), "</option>",
    ].join("")).join(""),
    "</select></label>",
    record ? [
      '<button class="episode-inspect-candidate" type="button" data-learning-production-inspect ',
      testIdAttribute("learning", "production", "inspect"), ">",
      esc(t("learning.production.inspect")), "</button>",
    ].join("") : "",
    "</div>",
    statusMessage ? "<p>" + esc(statusMessage) + "</p>" : "",
    '<div class="episode-tabs" role="tablist" aria-label="',
    esc(t("learning.tabs.aria")), '" ',
    testIdAttribute("learning", "production", "tabs"), ">",
    tabMarkup(activeTab), "</div>",
    panelMarkup(activeTab, record),
    "</div>",
  ].join("");
}
