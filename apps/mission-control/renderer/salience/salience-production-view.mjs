import { contextHelpMarkup, stateMarkup } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { salienceTabPanelMarkup, salienceTabsMarkup } from "./salience-tabs.mjs";
import { esc, stateBadge, t, testIdAttribute } from "./salience-view-shared.mjs";

const AXES = Object.freeze(["impact", "exigency", "novelty"]);

function help(labelKey, descriptionKey, testId) {
  return contextHelpMarkup({ label: t(labelKey), description: t(descriptionKey), testId });
}

function originLabel(origin) {
  return t(`salience.origin.${origin ?? "UNKNOWN"}`);
}

function axisReading(axis) {
  if (!axis || axis.state !== "PRESENT") {
    const state = axis?.state ?? "UNKNOWN";
    return `<span class="salience-axis-reading" data-posture="${esc(state)}"><strong>${esc(t(`salience.axisState.${state}`))}</strong></span>`;
  }
  const units = axis.units ? ` · ${axis.units}` : "";
  return `<span class="salience-axis-reading" data-posture="${esc(axis.origin ?? "UNKNOWN")}">
    <strong>${esc(axis.value)}</strong><small>${esc(originLabel(axis.origin))}${esc(units)}</small>
  </span>`;
}

function refs(values) {
  return esc(values.length ? values.join(" · ") : t("salience.value.noneRecorded"));
}

function provenance(event, temporal) {
  const id = event.recordId.replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-|-$/g, "").toLowerCase();
  return `<tr class="salience-provenance-row"><td colspan="8">
    <details class="salience-provenance" ${testIdAttribute("salience", "production", "provenance", id)}>
      <summary>${esc(t("salience.production.provenanceSummary", {id: event.salienceId}))}</summary>
      <div class="salience-provenance-body">
        <div class="salience-panel-help">${help("salience.help.provenance.label", "salience.help.provenance.productionBody", `salience-help-production-provenance-${id}`)}</div>
        <dl class="salience-provenance-meta">
          <div><dt>${esc(t("salience.production.authority"))}</dt><dd>${esc(t(`salience.authority.${event.authority}`))}</dd></div>
          <div><dt>${esc(t("salience.production.coverage"))}</dt><dd>${esc(event.coverage)}</dd></div>
          <div><dt>${esc(t("salience.provenance.observed"))}</dt><dd>${temporalMarkup({ unixSeconds: event.observedAt, ...temporal, testId: `salience-production-observed-${id}` })}</dd></div>
          <div><dt>${esc(t("salience.production.materialized"))}</dt><dd>${temporalMarkup({ unixSeconds: event.materializedAt, ...temporal, testId: `salience-production-materialized-${id}` })}</dd></div>
          <div><dt>${esc(t("salience.production.sourceRefs"))}</dt><dd class="machine-value">${refs(event.sourceRefs)}</dd></div>
          <div><dt>${esc(t("salience.production.evidenceRefs"))}</dt><dd class="machine-value">${refs(event.evidenceRefs)}</dd></div>
          <div><dt>${esc(t("salience.production.receiptRefs"))}</dt><dd class="machine-value">${refs(event.receiptRefs)}</dd></div>
        </dl>
      </div>
    </details>
  </td></tr>`;
}

function axisHeading(axis) {
  return `<span class="salience-column-heading"><span>${esc(t(`salience.observations.${axis}`))}</span>
    ${help(`salience.help.axis.${axis}.label`, `salience.help.axis.${axis}.body`, `salience-help-axis-${axis}`)}</span>`;
}

function observationRows(events, selectedId, temporal) {
  return events.map((event) => {
    const id = event.recordId.replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-|-$/g, "").toLowerCase();
    return `<tr class="salience-observation-row" data-selected="${event.recordId === selectedId}" ${testIdAttribute("salience", "production", "observation", id)}>
      <th scope="row" data-sticky="identity"><span class="salience-observation-kind">${esc(event.actionKind)}</span><code>${esc(event.salienceId)}</code></th>
      <td class="machine-value">${esc(event.capabilityId)}</td>
      <td>${axisReading(event.axes.impact)}</td><td>${axisReading(event.axes.exigency)}</td><td>${axisReading(event.axes.novelty)}</td>
      <td>${esc(event.actionKind)}</td>
      <td>${temporalMarkup({ unixSeconds: event.observedAt, ...temporal, testId: `salience-production-row-time-${id}` })}</td>
      <td><button type="button" class="ui-control ui-control--inspect salience-inspect" data-production-salience-inspect="${esc(event.recordId)}"
        data-focus-key="salience:${esc(event.recordId)}:inspect" ${testIdAttribute("salience", "production", "inspect", id)}
        aria-label="${esc(t("salience.observations.inspectAria", {id: event.salienceId}))}">${esc(t("salience.observations.inspect"))}</button></td>
    </tr>${provenance(event, temporal)}`;
  }).join("");
}

function observations(model, selectedId, temporal) {
  const events = model?.events ?? [];
  if (!events.length) {
    const state = model?.state ?? "EMPTY";
    const status = state === "LOADING" ? "loading" : state === "EMPTY" ? "empty" :
      state === "PARTIAL" || state === "STALE" ? "partial" : "unavailable";
    const kind = state === "UNAVAILABLE" || state === "DENIED" ? "error" : "empty";
    return stateMarkup({
      title: t(`salience.production.${status}Title`),
      detail: t(`salience.production.${status}Detail`),
      testId: "salience-production-empty",
      kind,
    });
  }
  return `<section class="salience-observations salience-production-observations" aria-labelledby="salience-production-observations-title" ${testIdAttribute("salience", "observations")}>
    <header class="salience-section-heading"><div><span class="eyebrow">${esc(t("salience.observations.eyebrow"))}</span>
      <h2 id="salience-production-observations-title">${esc(t("salience.observations.title"))}</h2></div>
      <div class="salience-heading-tools">${help("salience.help.ordinal.label", "salience.help.ordinal.body", "salience-help-ordinal")}${help("salience.help.provenance.label", "salience.help.provenance.productionBody", "salience-help-provenance")}</div></header>
    <p class="salience-analysis-note">${esc(t("salience.observations.doctrine"))}</p>
    <div class="salience-table-wrap" tabindex="0" ${testIdAttribute("salience", "observation", "scroll")}>
      <table class="salience-observation-table" ${testIdAttribute("salience", "observation", "table")}>
        <caption>${esc(t("salience.production.caption"))}</caption><thead><tr>
          <th scope="col">${esc(t("salience.observations.event"))}</th><th scope="col">${esc(t("salience.observations.capability"))}</th>
          <th scope="col">${axisHeading("impact")}</th><th scope="col">${axisHeading("exigency")}</th><th scope="col">${axisHeading("novelty")}</th>
          <th scope="col">${esc(t("salience.production.action"))}</th><th scope="col">${esc(t("salience.provenance.observed"))}</th>
          <th scope="col">${esc(t("salience.observations.inspect"))}</th>
        </tr></thead><tbody>${observationRows(events, selectedId, temporal)}</tbody>
      </table>
    </div>
  </section>`;
}

function boundaryPanel(kind) {
  return `<section class="salience-analysis salience-production-boundary" ${testIdAttribute("salience", kind)}>
    <header class="salience-section-heading"><div><span class="eyebrow">${esc(t(`salience.${kind}.eyebrow`))}</span><h2>${esc(t(`salience.${kind}.title`))}</h2></div>
      ${help(`salience.help.${kind}.label`, `salience.help.${kind}.productionBody`, `salience-help-${kind}`)}</header>
    ${stateMarkup({
      title: t(`salience.production.${kind}Title`),
      detail: t(`salience.production.${kind}Detail`),
      testId: `salience-production-${kind}`,
    })}
  </section>`;
}

export function productionSalienceMarkup(model, {
  activeTab = "observations",
  selectedId = null,
  context = null,
  temporal = {},
} = {}) {
  const mode = context?.mode === "HISTORICAL" ? "HISTORICAL" : "CURRENT";
  const generation = context?.generation ?? t("salience.value.unavailable");
  return `<div class="salience-view salience-production-view" ${testIdAttribute("salience", "view")}>
    <header class="salience-heading" ${testIdAttribute("salience", "heading")}><div><span class="eyebrow">${esc(t("salience.title"))}</span><h2>${esc(t("salience.production.title"))}</h2></div>
      <div class="salience-heading-context"><p>${esc(t("salience.production.summary"))}</p><div class="salience-heading-tools">
        ${help("salience.help.concept.label", "salience.help.concept.body", "salience-help-concept")}${help("salience.help.elsewhere.label", "salience.help.elsewhere.body", "salience-help-elsewhere")}
      </div></div></header>
    <div class="salience-view-controls" ${testIdAttribute("salience", "controls")}><div class="salience-snapshot-readout">
      <span>${esc(t("salience.snapshot.label"))}</span><strong>${esc(t("salience.production.snapshot", {mode: t(`salience.value.${mode === "HISTORICAL" ? "historical" : "current"}`), generation}))}</strong>
      ${help("salience.help.snapshot.label", "salience.help.snapshot.productionBody", "salience-help-snapshot")}</div>${stateBadge(mode, "salience-snapshot-state")}</div>
    ${salienceTabsMarkup(activeTab)}
    ${salienceTabPanelMarkup("observations", observations(model, selectedId, temporal), activeTab)}
    ${salienceTabPanelMarkup("aggregation", boundaryPanel("aggregation"), activeTab)}
    ${salienceTabPanelMarkup("routing", boundaryPanel("routing"), activeTab)}
  </div>`;
}
