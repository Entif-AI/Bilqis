import { SALIENCE_AXES } from "./salience-fixture.mjs";
import { axisPosture, salienceDeepLink } from "./salience-model.mjs";
import { esc, slug, stateBadge, t, testIdAttribute } from "./salience-view-shared.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";

const AXIS_KEYS = Object.freeze({
  impact: "salience.observations.impact",
  exigency: "salience.observations.exigency",
  novelty: "salience.observations.novelty",
});

function help(labelKey, descriptionKey, testId) {
  return contextHelpMarkup({ label: t(labelKey), description: t(descriptionKey), testId });
}

function postureNote(value) {
  const posture = axisPosture(value);
  if (posture === "UNKNOWN") return t("salience.axis.UNKNOWN");
  if (posture === "EXPECTED_MISSING") return t("salience.axis.EXPECTED_MISSING");
  if (posture === "REPORTED_NEGATIVE") return t("salience.axis.REPORTED_NEGATIVE");
  return "";
}

function axisReading(event, axis) {
  const value = event.axes[axis];
  const posture = axisPosture(value);
  const note = postureNote(value);
  return `<span class="salience-axis-reading" data-posture="${esc(posture)}">
    <strong>${esc(value.ordinal)}</strong>${note ? `<small>${esc(note)}</small>` : ""}
  </span>`;
}

function provenance(event) {
  const suffix = slug(event.recordId);
  return `<tr class="salience-provenance-row"><td colspan="7">
    <details class="salience-provenance" ${testIdAttribute("salience", "provenance", suffix)}>
      <summary>${esc(t("salience.provenance.summary", {id: event.salienceId}))}</summary>
      <div class="salience-provenance-body">
        <div class="salience-panel-help">${help("salience.help.provenance.label", "salience.help.provenance.fixtureBody", `salience-help-provenance-${suffix}`)}</div>
        <dl class="salience-provenance-meta">
          <div><dt>${esc(t("salience.provenance.owner"))}</dt><dd class="machine-value">${esc(event.policy.sourceOwner)}</dd></div>
          <div><dt>${esc(t("salience.provenance.policy"))}</dt><dd class="machine-value">${esc(event.policy.policyId)}/${esc(event.policy.version)}</dd></div>
          <div><dt>${esc(t("salience.provenance.digest"))}</dt><dd class="machine-value">${esc(event.policy.policyDigest)}</dd></div>
          <div><dt>${esc(t("salience.provenance.window"))}</dt><dd class="machine-value">${esc(event.policy.windowPolicyId)}/${esc(event.policy.windowPolicyVersion)} · ${event.policy.windowSize}</dd></div>
          <div><dt>${esc(t("salience.provenance.observed"))}</dt><dd>${temporalMarkup({ unixSeconds: event.observedAt, testId: `salience-observed-${suffix}` })}</dd></div>
          <div><dt>${esc(t("salience.provenance.effective"))}</dt><dd>${temporalMarkup({ unixSeconds: event.effectiveAt, testId: `salience-effective-${suffix}` })}</dd></div>
          <div><dt>${esc(t("salience.provenance.object"))}</dt><dd class="machine-value">${esc(event.associatedObjectRef)}</dd></div>
        </dl>
        <div class="salience-provenance-table-wrap"><table class="salience-provenance-table"><thead><tr>
          <th scope="col">${esc(t("salience.provenance.axis"))}</th>
          <th scope="col">${esc(t("salience.provenance.source"))}</th>
          <th scope="col">${esc(t("salience.provenance.rule"))}</th>
          <th scope="col">${esc(t("salience.provenance.basis"))}</th>
        </tr></thead><tbody>${SALIENCE_AXES.map((axis) => {
          const value = event.axes[axis];
          return `<tr><th scope="row">${esc(t(AXIS_KEYS[axis]))}</th>
            <td class="machine-value">${esc(value.sourceRef)}</td>
            <td class="machine-value">${esc(value.ruleId)}</td>
            <td class="machine-value">${esc(value.basisRefs.join(" · "))}</td></tr>`;
        }).join("")}</tbody></table></div>
        <a class="salience-stable-link" href="${esc(salienceDeepLink(event.recordId))}">${esc(t("salience.provenance.link"))}</a>
      </div>
    </details>
  </td></tr>`;
}

function observationRows(snapshot, selectedId) {
  return snapshot.events.map((event) => {
    const suffix = slug(event.recordId);
    return `<tr class="salience-observation-row" data-selected="${event.recordId === selectedId}" ${testIdAttribute("salience", "observation", "row", suffix)}>
      <th scope="row" data-sticky="identity"><span class="salience-observation-kind">${esc(t(`salience.action.${event.actionKind}`))}</span>
        <code>${esc(event.salienceId)}</code></th>
      <td class="machine-value">${esc(event.capabilityId)}</td>
      <td>${axisReading(event, "impact")}</td>
      <td>${axisReading(event, "exigency")}</td>
      <td>${axisReading(event, "novelty")}</td>
      <td><span class="machine-value">${esc(event.scope)}</span><small>${esc(event.sourceFamily)}</small></td>
      <td><button type="button" class="ui-control ui-control--inspect salience-inspect"
        data-salience-inspect="${esc(event.recordId)}" data-focus-key="salience:${esc(event.recordId)}:inspect"
        ${testIdAttribute("salience", "observation", "inspect", suffix)}
        aria-label="${esc(t("salience.observations.inspectAria", {id: event.salienceId}))}">${esc(t("salience.observations.inspect"))}</button></td>
    </tr>${provenance(event)}`;
  }).join("");
}

export function observationPanel(snapshot, selectedId) {
  return `<section class="salience-observations" aria-labelledby="salience-observations-title" ${testIdAttribute("salience", "observations")}>
    <header class="salience-section-heading"><div><span class="eyebrow">${esc(t("salience.observations.eyebrow"))}</span>
      <h2 id="salience-observations-title">${esc(t("salience.observations.title"))}</h2></div>
      <div class="salience-heading-tools">${stateBadge(snapshot.mode, "salience-snapshot-state")}${help("salience.help.ordinal.label", "salience.help.ordinal.body", "salience-help-ordinal")}</div></header>
    <div class="salience-observation-guidance">
      <p>${esc(t("salience.observations.doctrine"))}</p>
      <details class="salience-axis-guide" ${testIdAttribute("salience", "axis", "guide")}><summary>${esc(t("salience.axisGuide.summary"))}</summary>
        <ul><li>${esc(t("salience.axisGuide.impact"))} ${help("salience.help.axis.impact.label", "salience.help.axis.impact.body", "salience-help-axis-impact")}</li>
          <li>${esc(t("salience.axisGuide.exigency"))} ${help("salience.help.axis.exigency.label", "salience.help.axis.exigency.body", "salience-help-axis-exigency")}</li>
          <li>${esc(t("salience.axisGuide.novelty"))} ${help("salience.help.axis.novelty.label", "salience.help.axis.novelty.body", "salience-help-axis-novelty")}</li>
          <li>${esc(t("salience.axisGuide.independent"))}</li></ul></details>
    </div>
    <div class="salience-table-wrap" tabindex="0" ${testIdAttribute("salience", "observation", "scroll")}>
      <table class="salience-observation-table" ${testIdAttribute("salience", "observation", "table")}>
        <caption>${esc(t("salience.observations.caption"))}</caption><thead><tr>
          <th scope="col">${esc(t("salience.observations.event"))}</th><th scope="col">${esc(t("salience.observations.capability"))}</th>
          <th scope="col">${esc(t("salience.observations.impact"))}</th><th scope="col">${esc(t("salience.observations.exigency"))}</th>
          <th scope="col">${esc(t("salience.observations.novelty"))}</th><th scope="col">${esc(t("salience.observations.scopeSource"))}</th>
          <th scope="col">${esc(t("salience.observations.inspect"))}</th>
        </tr></thead><tbody>${observationRows(snapshot, selectedId)}</tbody>
      </table>
    </div>
  </section>`;
}
