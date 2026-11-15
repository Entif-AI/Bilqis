import { contextHelpMarkup, stateMarkup } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { teacherTabPanelMarkup, teacherTabsMarkup } from "./teacher-tabs.mjs";
import { esc, t, testIdAttribute, unavailable } from "./teacher-view-shared.mjs";

function help(labelKey, descriptionKey, testId) {
  return contextHelpMarkup({
    label: t(labelKey), description: t(descriptionKey), testId,
  });
}

function refs(snapshot) {
  const groups = [
    [t("teacher.production.sourceRefs"), snapshot.sourceRefs],
    [t("teacher.production.evidenceRefs"), snapshot.evidenceRefs],
    [t("teacher.production.receiptRefs"), snapshot.receiptRefs],
  ];
  return `<dl class="teacher-production-refs">${groups.map(([label, values]) => `<div><dt>${esc(label)}</dt><dd class="machine-value">${esc(values.length ? values.join(", ") : t("teacher.value.none"))}</dd></div>`).join("")}</dl>`;
}

function roster(snapshot, temporal, state) {
  if (!snapshot) {
    const status = state === "LOADING" ? "loading" : state === "UNAVAILABLE" ? "unavailable" : "empty";
    return stateMarkup({
      title: t(`teacher.production.${status}Title`),
      detail: t(`teacher.production.${status}Detail`),
      testId: "teacher-production-empty",
      kind: status === "unavailable" ? "error" : "empty",
    });
  }
  return `<section class="teacher-roster teacher-production-roster" aria-labelledby="teacher-roster-title" ${testIdAttribute("teacher", "roster")}>
    <header class="teacher-section-heading"><div><span class="eyebrow">${esc(t("teacher.roster.eyebrow"))}</span><h3 id="teacher-roster-title">${esc(t("teacher.production.currentTitle"))}</h3></div>
      <div class="teacher-heading-tools">${help("teacher.help.strategy.label", "teacher.help.strategy.body", "teacher-help-strategy")}${help("teacher.help.metrics.label", "teacher.help.metrics.body", "teacher-help-metrics")}</div></header>
    <div class="teacher-table-wrap" tabindex="0" ${testIdAttribute("teacher", "roster", "scroll")}>
      <table class="teacher-roster-table"><caption>${esc(t("teacher.production.caption"))}</caption><thead><tr>
        <th scope="col">${esc(t("teacher.roster.strategy"))}</th><th scope="col">${esc(t("teacher.production.epoch"))}</th>
        <th scope="col">${esc(t("teacher.roster.attempts"))}</th><th scope="col">${esc(t("teacher.production.accepted"))}</th>
        <th scope="col">${esc(t("teacher.production.rejected"))}</th><th scope="col">${esc(t("teacher.production.observed"))}</th>
      </tr></thead><tbody><tr>
        <th scope="row"><button type="button" class="teacher-strategy-select" data-production-strategy-inspect="${esc(snapshot.strategyId)}" ${testIdAttribute("teacher", "production", "strategy")}><span>${esc(snapshot.strategyId)}</span><code>${esc(snapshot.teacherIdentity)}</code></button></th>
        <td data-align="numeric">${snapshot.teacherEpoch}</td><td data-align="numeric">${esc(unavailable(snapshot.attempts))}</td>
        <td data-align="numeric">${esc(unavailable(snapshot.accepted))}</td><td data-align="numeric">${esc(unavailable(snapshot.rejected))}</td>
        <td>${temporalMarkup({ unixSeconds: snapshot.observedAt, ...temporal, testId: "teacher-production-observed" })}</td>
      </tr></tbody></table>
    </div>
    <section class="teacher-production-provenance"><header class="teacher-section-heading"><h4>${esc(t("teacher.production.provenance"))}</h4>
      ${help("teacher.help.provenance.label", "teacher.help.provenance.body", "teacher-help-provenance")}</header>${refs(snapshot)}</section>
  </section>`;
}

function unavailablePanel(kind) {
  return `<section class="teacher-${kind} teacher-production-boundary" ${testIdAttribute("teacher", kind)}>
    <header class="teacher-section-heading"><div><span class="eyebrow">${esc(t(`teacher.${kind}.eyebrow`))}</span><h3>${esc(t(`teacher.${kind}.title`))}</h3></div>
      ${help(`teacher.help.${kind}.label`, `teacher.help.${kind}.body`, `teacher-help-${kind}`)}</header>
    ${stateMarkup({
      title: t(`teacher.production.${kind}Title`),
      detail: t(`teacher.production.${kind}Detail`),
      testId: `teacher-production-${kind}`,
    })}
  </section>`;
}

export function productionTeacherMarkup(model, { activeTab = "roster", temporal = {} } = {}) {
  const snapshot = model?.snapshot ?? null;
  const rosterBody = roster(snapshot, temporal, model?.state ?? "EMPTY");
  const comparisonBody = unavailablePanel("comparison");
  const fidelityBody = unavailablePanel("fidelity");
  return `<div class="teacher-view teacher-production-view" ${testIdAttribute("teacher", "view")}>
    <header class="teacher-heading" ${testIdAttribute("teacher", "heading")}><div>
      <span class="eyebrow">${esc(t("teacher.view.eyebrow"))}</span><h2>${esc(t("teacher.view.title"))}</h2>
    </div><div class="teacher-heading-context"><p>${esc(t("teacher.production.summary"))}</p>
      ${help("teacher.help.mutation.label", "teacher.help.mutation.body", "teacher-help-mutation")}</div></header>
    ${teacherTabsMarkup(activeTab)}
    ${teacherTabPanelMarkup("roster", rosterBody, activeTab)}
    ${teacherTabPanelMarkup("comparison", comparisonBody, activeTab)}
    ${teacherTabPanelMarkup("fidelity", fidelityBody, activeTab)}
  </div>`;
}
