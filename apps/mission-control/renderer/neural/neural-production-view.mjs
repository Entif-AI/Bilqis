import { t } from "../foundation/i18n.mjs";
import { contextHelpMarkup, stateMarkup } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";

const esc = value => String(value ?? "").replace(/[&<>"']/g, character => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[character]);
const value = input => input === null || input === undefined ? t("model.frame.unavailable") : input;
const help = (label, description, testId) => contextHelpMarkup({ label: t(label), description: t(description), testId });

function datumMarkup(datum) {
  if (!datum || datum.state !== "PRESENT" || datum.value === null || datum.value === undefined) {
    return `<span>${esc(t("model.frame.unavailable"))}</span>`;
  }
  const units = datum.units ? ` ${esc(datum.units)}` : "";
  return `<span>${esc(datum.value)}${units}</span><small>${esc(datum.origin)}</small>`;
}

function unavailable(model) {
  const kind = model?.state === "LOADING" ? "loading" : model?.state === "UNAVAILABLE" ? "unavailable" : "empty";
  return stateMarkup({
    title: t(`model.neural.production.${kind}Title`),
    detail: t(`model.neural.production.${kind}Detail`),
    testId: "model-neural-production-empty",
    kind: kind === "unavailable" ? "error" : "empty",
  });
}

export function productionNeuralMarkup(model, context) {
  const snapshot = model?.snapshot ?? null;
  const mode = context?.mode === "HISTORICAL" ? "historical" : "current";
  const body = snapshot ? `<section class="neural-section neural-primary" ${testIdAttribute("model", "neural", "production", "sample")}>
    <header class="neural-section-heading"><div><span class="eyebrow">${esc(t("model.neural.runtimeProjection"))}</span><h3>${esc(t("model.neural.production.sampleTitle"))}</h3></div><div class="neural-section-tools">${help("model.neural.help.topology.label", "model.neural.help.topology.description", "model-neural-help-topology")}${help("model.neural.help.authority.label", "model.neural.help.authority.description", "model-neural-help-authority")}</div></header>
    <dl class="runtime-metrics">
      <div><dt>${esc(t("model.neural.optimizerStep"))}</dt><dd>${esc(value(snapshot.optimizerStep))}</dd></div>
      <div><dt>${esc(t("model.neural.stepDuration"))}</dt><dd>${datumMarkup(snapshot.stepDurationMs)}</dd></div>
      <div><dt>${esc(t("model.neural.activeParameters"))}</dt><dd>${datumMarkup(snapshot.activeParameters)}</dd></div>
      <div><dt>${esc(t("model.neural.refinementFraction"))}</dt><dd>${datumMarkup(snapshot.refinementFraction)}</dd></div>
    </dl>
    <dl class="neural-time-facts">
      <div><dt>${esc(t("model.neural.observed"))}</dt><dd>${temporalMarkup({ unixSeconds: snapshot.observedAt, testId: "model-neural-production-observed" })}</dd></div>
      <div><dt>${esc(t("model.neural.materialized"))}</dt><dd>${temporalMarkup({ unixSeconds: snapshot.materializedAt, testId: "model-neural-production-materialized" })}</dd></div>
    </dl>
    <details class="neural-disclosure" ${testIdAttribute("model", "neural", "production", "provenance")}><summary>${esc(t("model.neural.production.provenance"))}</summary>
      <dl class="frame-identity"><dt>${esc(t("model.neural.production.record"))}</dt><dd>${esc(snapshot.recordId)}</dd><dt>${esc(t("model.neural.production.coverage"))}</dt><dd>${esc(snapshot.coverage)}</dd><dt>${esc(t("model.neural.production.authority"))}</dt><dd>${esc(snapshot.authority)}</dd><dt>${esc(t("model.neural.production.sourceRefs"))}</dt><dd>${esc(snapshot.sourceRefs.join(", ") || t("model.frame.unavailable"))}</dd></dl>
    </details>
    <button type="button" data-neural-production-inspect="${esc(snapshot.recordId)}" ${testIdAttribute("model", "neural", "production", "inspect")}>${esc(t("model.neural.inspectEvidence"))}</button>
  </section>` : unavailable(model);
  return `<div class="neural-view neural-production-view" ${testIdAttribute("model", "neural", "production", "view")}>
    <header class="neural-heading"><div><span class="eyebrow">${esc(t("model.neural.eyebrow"))}</span><h2>${esc(t("model.neural.title"))}</h2></div><p>${esc(t("model.neural.summary"))}</p></header>
    <section class="frame-production-posture"><strong>${esc(t("model.neural.production.posture", { mode: t(`model.frame.mode.${mode}`), runId: context?.runId ?? t("model.frame.unavailable"), generation: context?.generation ?? t("model.frame.unavailable") }))}</strong></section>
    ${body}
  </div>`;
}
