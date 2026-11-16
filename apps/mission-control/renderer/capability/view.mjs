import { contextHelpMarkup, controlClass } from "../foundation/primitives.mjs";
import { t } from "../foundation/i18n.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { SECTIONS, RECORD_FAMILIES, escapeHtml as e, historyEntries, metricText } from "./model.mjs";

const SECTION_DETAIL_KEYS = Object.freeze({
  performance: "capability.section.performanceDetail",
  teaching: "capability.section.teachingDetail",
  sources: "capability.section.sourcesDetail",
  dependencies: "capability.section.dependenciesDetail",
  history: "capability.section.historyDetail",
});

function metricValue(metric, total, score = false) {
  if (!score || metric?.state !== "PRESENT" || total?.state !== "PRESENT") return metricText(metric);
  if (typeof metric.value !== "number" || typeof total.value !== "number") return metricText(metric);
  return t("capability.metric.score", { value: metric.value, total: total.value });
}

function metric(labelKey, id, value, total, score = false) {
  return `<div class="dossier-metric" ${testIdAttribute("capability", "metric", id)}>
    <dt>${e(t(labelKey))}</dt><dd>${e(metricValue(value, total, score))}
    <small>${e(value?.origin ?? value?.state ?? t("capability.common.notMeasured"))}</small></dd></div>`;
}

function help(labelKey, bodyKey, id) {
  return contextHelpMarkup({ label: t(labelKey), description: t(bodyKey), testId: id });
}

function entryRow(entry, section, index, fixture) {
  const values = entry.values ?? [];
  const refs = entry.refs ?? [];
  const entryHook = ["capability", "entry", section, index];
  const facts = values.map((item, factIndex) => `<div ${testIdAttribute(...entryHook, "fact", factIndex)}>
    <dt>${e(item.name)}</dt><dd>${e(metricText(item.value))}
    <small>${e(item.value?.origin ?? item.value?.state ?? "UNMEASURED")}</small></dd></div>`).join("");
  const refButtons = refs.map((ref, refIndex) => `<button type="button" class="${controlClass("link")}"
    data-evidence="${e(ref)}" data-entry="${e(entry.entry_id)}"
    ${testIdAttribute("capability", "evidence", "ref", section, index, refIndex)}>${e(ref)}</button>`).join("");
  const related = entry.related_id ? `<button type="button" class="${controlClass("link")}"
    data-related-kind="${e(entry.related_kind)}" data-related-id="${e(entry.related_id)}"
    ${testIdAttribute("capability", "related", section, index)}>${e(t("capability.entry.openRelated", {
      kind: entry.related_kind, id: entry.related_id,
    }))}</button>` : "";
  const observed = temporalMarkup({
    unixSeconds: fixture ? null : entry.observed_at,
    testId: `capability-entry-${section}-${index}-time`,
  });
  return `<article class="dossier-entry" data-kind="${e(entry.kind)}" ${testIdAttribute(...entryHook)}>
    <header><div><span class="eyebrow">${e(entry.kind)}</span><h3>${e(entry.label)}</h3></div>
      <span class="dossier-stamp"><span>${e(t("capability.entry.generation", { generation: entry.generation }))}</span>${observed}</span></header>
    ${facts ? `<dl class="dossier-facts">${facts}</dl>` : ""}
    <details class="dossier-entry-evidence" ${testIdAttribute(...entryHook, "evidence")}>
      <summary ${testIdAttribute(...entryHook, "evidence", "toggle")}>${e(t("capability.entry.evidence", { count: refs.length }))}</summary>
      <div class="dossier-links">${refButtons}${related}</div>
    </details></article>`;
}

function contextMarkup(state) {
  const source = t(state.fixture ? "capability.context.fixture" : "capability.context.service");
  return `<div class="dossier-context" ${testIdAttribute("capability", "context")}>
    <span>${e(t("capability.context.identity", {
      source, mode: state.lens?.mode, runId: state.lens?.runId, generation: state.lens?.generation,
    }))}</span>
    <strong>${e(t("capability.context.posture", {
      status: state.status, coverage: state.coverage ?? "UNKNOWN",
    }))}</strong>${help("capability.help.identity.label", "capability.help.identity.body", "capability-help-identity")}</div>`;
}

function projectionMarkup(markers = []) {
  if (!markers.length) return "";
  return `<details class="dossier-projection" ${testIdAttribute("capability", "projection")}>
    <summary>${e(t("capability.projection.summary"))}</summary>
    <pre>${e(JSON.stringify(markers, null, 2))}</pre></details>`;
}

export function renderDossier(state) {
  const { dossier: d, status } = state;
  const context = contextMarkup(state);
  const markers = projectionMarkup(state.markers);
  if (!d) {
    const detail = state.cursor ? t("capability.empty.partial") : t("capability.empty.exact");
    return `<article class="dossier-document dossier-document--empty" ${testIdAttribute("capability", "document")}>
      ${context}<div class="dossier-empty" ${testIdAttribute("capability", "empty")}>
        <h2 ${testIdAttribute("capability", "empty", "status")}>${e(status)}</h2>
        <p>${e(detail)}</p>${state.error ? `<details><summary>${e(t("capability.common.technicalDetail"))}</summary><code>${e(state.error)}</code></details>` : ""}
      </div>${markers}</article>`;
  }

  const metrics = [
    ["capability.metric.now", "now", d.now, true],
    ["capability.metric.top", "top", d.top, true],
    ["capability.metric.total", "total", d.total, false],
    ["capability.metric.debt", "debt", d.debt, false],
    ["capability.metric.retention", "retention", d.retention, false],
    ["capability.metric.eligibility", "eligibility", d.eligibility, false],
    ["capability.metric.qualification", "qualification", d.qualification, false],
    ["capability.metric.source", "source", d.source_state, false],
  ];
  const sections = SECTIONS.map((section) => {
    const entries = section === "history" ? historyEntries(d) : d.entries.filter((entry) => entry.section === section);
    return `<section id="dossier-${section}" class="dossier-section" tabindex="-1"
      aria-labelledby="dossier-${section}-heading" ${testIdAttribute("capability", "section", section)}>
      <header><div class="dossier-section-title"><h2 id="dossier-${section}-heading">${e(t(`capability.section.${section}`))}</h2>
        ${section === "dependencies" ? help("capability.help.dependencies.label", "capability.help.dependencies.body", "capability-help-dependencies") : ""}
        ${section === "history" ? help("capability.help.history.label", "capability.help.history.body", "capability-help-history") : ""}</div>
        <p>${e(t(SECTION_DETAIL_KEYS[section]))}</p></header>
      ${entries.length ? entries.map((entry, index) => entryRow(entry, section, index, state.fixture)).join("") :
        `<p class="dossier-section-empty" ${testIdAttribute("capability", "section", section, "empty")}>${e(t("capability.section.empty"))}</p>`}
    </section>`;
  }).join("");

  return `<article class="dossier-document" ${testIdAttribute("capability", "document")}>
    ${context}
    <header class="dossier-heading" ${testIdAttribute("capability", "heading")}>
      <div><span class="eyebrow">${e(t("capability.heading.eyebrow"))}</span>
        <h2 ${testIdAttribute("capability", "name")}>${e(d.name)}</h2>
        <code ${testIdAttribute("capability", "identity")}>${e(d.capability_id)}</code>
        <p class="dossier-boundary">${e(t("capability.heading.summary"))}</p></div>
      <dl class="dossier-posture">
        <div><dt>${e(t("capability.identity.current"))}</dt><dd>${e(status)}</dd></div>
        <div><dt>${e(t("capability.identity.qualification"))}</dt><dd>${e(metricText(d.qualification))}</dd></div>
        <div><dt>${e(t("capability.identity.source"))}</dt><dd>${e(metricText(d.source_state))}</dd></div>
        <div><dt>${e(t("capability.identity.provenance"))}</dt><dd>${e(`${d.meta?.authority ?? "UNKNOWN"} · ${d.meta?.coverage ?? "UNKNOWN"}`)}</dd></div>
      </dl>
    </header>
    <div class="dossier-metrics-heading"><span>${e(t("capability.metrics.aria"))}</span>
      ${help("capability.help.metrics.label", "capability.help.metrics.body", "capability-help-metrics")}</div>
    <dl class="dossier-metrics" aria-label="${e(t("capability.metrics.aria"))}" ${testIdAttribute("capability", "metrics")}>
      ${metrics.map(([labelKey, id, value, score]) => metric(labelKey, id, value, d.total, score)).join("")}
    </dl>
    <nav class="dossier-tabs" aria-label="${e(t("capability.section.navigation"))}" ${testIdAttribute("capability", "section", "nav")}>
      ${SECTIONS.map((section) => `<button type="button" class="${controlClass("peer-tab")}" data-section="${section}"
        ${testIdAttribute("capability", "section", "nav", section)}>${e(t(`capability.section.${section}`))}</button>`).join("")}
      ${help("capability.help.navigation.label", "capability.help.navigation.body", "capability-help-navigation")}
    </nav>
    <div class="dossier-sections">${sections}</div>
    <div class="dossier-provenance-heading">${help("capability.help.provenance.label", "capability.help.provenance.body", "capability-help-provenance")}</div>
    <details class="dossier-provenance" ${testIdAttribute("capability", "provenance")}>
      <summary>${e(t("capability.provenance.summary"))}</summary><pre>${e(JSON.stringify(d.meta, null, 2))}</pre>
    </details>
    ${markers}
  </article>`;
}

export function renderEvidence(ref, entry, page, error = null) {
  const state = error ? t("capability.evidence.unavailable") : page?.state ?? t("capability.evidence.loading");
  const activeRecord = page?.records?.[0]?.meta?.record_id ?? ref;
  const links = page?.links ?? [];
  const records = page?.records ?? [];
  return `<div class="capability-evidence" ${testIdAttribute("capability", "evidence", "detail")}>
    <header><div><span class="eyebrow">${e(t("capability.evidence.title"))}</span>
      <h2 ${testIdAttribute("capability", "evidence", "heading")}>${e(ref)}</h2></div>
      <span class="capability-evidence-state">${e(t("capability.evidence.state", { state }))}</span></header>
    <button type="button" class="${controlClass("link")}" data-open-evidence="${e(activeRecord)}"
      ${testIdAttribute("capability", "evidence", "open")}>${e(t("capability.evidence.openFull"))}</button>
    ${error ? `<details><summary>${e(t("capability.common.technicalDetail"))}</summary><code>${e(error)}</code></details>` : ""}
    ${entry ? `<details ${testIdAttribute("capability", "evidence", "entry")}><summary>${e(t("capability.evidence.entryDetail"))}</summary>
      <pre>${e(JSON.stringify(entry, null, 2))}</pre></details>` : ""}
    <div class="capability-evidence-links">
      ${links.map((link, index) => `<article ${testIdAttribute("capability", "evidence", "link", index)}>
        <div><strong>${e(link.relation)}</strong><code>${e(link.target_ref)}</code></div>
        <details><summary>${e(t("capability.evidence.linkDetail"))}</summary><pre>${e(JSON.stringify(link, null, 2))}</pre></details>
        ${link.target_record_id ? `<label>${e(t("capability.evidence.recordFamily"))}
          <select data-family ${testIdAttribute("capability", "evidence", "family", index)}>
            ${RECORD_FAMILIES.map((family) => `<option ${family === "capability" ? "selected" : ""}>${e(family)}</option>`).join("")}
          </select></label>
          <button type="button" class="${controlClass("secondary")}" data-record="${e(link.target_record_id)}"
            ${testIdAttribute("capability", "evidence", "inspect", index)}>${e(t("capability.evidence.inspectRecord", { ref: link.target_ref }))}</button>` :
          `<p>${e(t("capability.evidence.unresolved"))}</p>`}
      </article>`).join("")}
    </div>
    ${page?.next_cursor ? `<button type="button" class="${controlClass("secondary")}" data-evidence-more
      ${testIdAttribute("capability", "evidence", "more")}>${e(t("capability.evidence.more"))}</button>` : ""}
    ${records.map((record, index) => `<details class="capability-evidence-record" ${testIdAttribute("capability", "evidence", "record", index)}>
      <summary>${e(t("capability.evidence.recordDetail"))} · <code>${e(record.meta?.record_id ?? record.schema_version ?? index)}</code></summary>
      <pre>${e(JSON.stringify(record, null, 2))}</pre></details>`).join("")}
  </div>`;
}
