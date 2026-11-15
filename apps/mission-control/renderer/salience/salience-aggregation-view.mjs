import { aggregationForSnapshot, constituentObservationIds } from "./salience-model.mjs";
import { esc, slug, stateBadge, t, testIdAttribute, yesNo } from "./salience-view-shared.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";

function help(labelKey, descriptionKey, testId) {
  return contextHelpMarkup({ label: t(labelKey), description: t(descriptionKey), testId });
}

function observationRef(snapshot, id, prefix) {
  const available = snapshot.events.some((event) => event.recordId === id);
  if (!available) return `<span class="salience-observation-ref salience-observation-ref--unavailable">${esc(t("salience.observation.outside", {id}))}</span>`;
  return `<button type="button" class="ui-control ui-control--link salience-observation-ref"
    data-salience-inspect="${esc(id)}" data-focus-key="salience:${esc(prefix)}:${esc(id)}"
    ${testIdAttribute("salience", prefix, slug(id))}>${esc(t("salience.observation.available", {id}))}</button>`;
}

function clusterNode(snapshot, cluster) {
  const suffix = slug(cluster.id);
  return `<details class="salience-aggregate-node" data-depth="1" ${testIdAttribute("salience", "aggregation", "cluster", suffix)}>
    <summary><span><strong>${esc(t("salience.aggregation.cluster"))}</strong> <code>${esc(cluster.id)}</code></span>
      <span>${esc(t("salience.aggregation.clusterSummary", {
        observations: cluster.eventIds.length, lineages: cluster.lineageIds.length,
      }))}</span></summary>
    <div class="salience-aggregate-body"><dl>
      <div><dt>${esc(t("salience.aggregation.partition"))}</dt><dd class="machine-value">${esc(cluster.partition)}</dd></div>
      <div><dt>${esc(t("salience.aggregation.rule"))}</dt><dd class="machine-value">${esc(cluster.ruleId)}</dd></div>
      <div><dt>${esc(t("salience.aggregation.structure"))}</dt><dd class="machine-value">${esc(cluster.structureRef)}</dd></div>
      <div><dt>${esc(t("salience.aggregation.defect"))}</dt><dd class="machine-value">${esc(cluster.defectRef)}</dd></div>
    </dl><div class="salience-constituents"><strong>${esc(t("salience.aggregation.constituents"))}</strong>
      ${cluster.eventIds.map((id) => observationRef(snapshot, id, "aggregate")).join("")}</div></div>
  </details>`;
}

function windowNode(snapshot, window, cluster) {
  const suffix = slug(window.id);
  return `<details class="salience-aggregate-node" data-depth="0" ${testIdAttribute("salience", "aggregation", "window", suffix)}>
    <summary><span><strong>${esc(t("salience.aggregation.window"))}</strong> <code>${esc(window.id)}</code></span>
      <span>${esc(t("salience.aggregation.windowSummary", {size: window.acceptedAppendCount, late: window.lateObservations}))}</span></summary>
    <div class="salience-aggregate-body"><dl>
      <div><dt>${esc(t("salience.aggregation.bounds"))}</dt><dd class="machine-value">${esc(window.observedBounds.join("–"))}</dd></div>
      <div><dt>${esc(t("salience.aggregation.window"))}</dt><dd>${window.size}</dd></div>
    </dl>${cluster ? clusterNode(snapshot, cluster) : ""}</div>
  </details>`;
}

function patternNode(snapshot, pattern, trend) {
  const suffix = slug(pattern.id);
  return `<details class="salience-aggregate-node salience-pattern-node" data-depth="0" ${testIdAttribute("salience", "aggregation", "pattern", suffix)}>
    <summary><span><strong>${esc(t("salience.aggregation.pattern"))}</strong> <code>${esc(pattern.id)}</code></span>
      <span>${esc(t("salience.aggregation.patternSummary", {status: pattern.status, lineages: pattern.independentLineages}))}</span></summary>
    <div class="salience-aggregate-body"><dl>
      <div><dt>${esc(t("salience.aggregation.rule"))}</dt><dd class="machine-value">${esc(pattern.ruleId)}</dd></div>
      <div><dt>${esc(t("salience.aggregation.nomination"))}</dt><dd class="machine-value">${esc(pattern.nomination)}</dd></div>
      <div><dt>${esc(t("salience.aggregation.sourceGold"))}</dt><dd>${esc(yesNo(pattern.sourceGold))}</dd></div>
      <div><dt>${esc(t("salience.aggregation.teaching"))}</dt><dd>${esc(yesNo(pattern.qualifiedForTeaching))}</dd></div>
    </dl>
    <details class="salience-aggregate-node" data-depth="1" ${testIdAttribute("salience", "aggregation", "trend", slug(trend.id))}>
      <summary><span><strong>${esc(t("salience.aggregation.trend"))}</strong> <code>${esc(trend.id)}</code></span>
        <span>${esc(t("salience.aggregation.trendSummary", {
          state: trend.supported ? t("salience.aggregation.supported") : t("salience.aggregation.unsupported"),
          points: trend.points.length,
        }))}</span></summary>
      <div class="salience-aggregate-body"><p class="machine-value">${esc(trend.ruleId)}</p>
        <ol class="salience-trend-points">${trend.points.map((point) => `<li>${esc(t("salience.aggregation.point", {
          window: point.windowId, newLineages: point.newLineages, cumulative: point.cumulativeLineages,
        }))}</li>`).join("")}</ol>
        <div class="salience-constituents"><strong>${esc(t("salience.aggregation.constituents"))}</strong>
          ${constituentObservationIds("trend", trend.id).map((id) => observationRef(snapshot, id, "trend")).join("")}</div>
      </div>
    </details></div>
  </details>`;
}

export function aggregationPanel(snapshot) {
  const aggregation = aggregationForSnapshot(snapshot);
  if (!aggregation) return `<section class="salience-analysis salience-aggregation" ${testIdAttribute("salience", "aggregation")}>
    <header class="salience-section-heading"><div><span class="eyebrow">${esc(t("salience.aggregation.eyebrow"))}</span>
      <h2>${esc(t("salience.aggregation.title"))}</h2></div><div class="salience-heading-tools">${stateBadge("UNAVAILABLE")}${help("salience.help.aggregation.label", "salience.help.aggregation.fixtureBody", "salience-help-aggregation")}</div></header>
    <p class="salience-analysis-note">${esc(t("salience.aggregation.unavailable"))}</p></section>`;
  const {windows, clusters, pattern, trend} = aggregation;
  return `<section class="salience-analysis salience-aggregation" ${testIdAttribute("salience", "aggregation")}>
    <header class="salience-section-heading"><div><span class="eyebrow">${esc(t("salience.aggregation.eyebrow"))}</span>
      <h2>${esc(t("salience.aggregation.title"))}</h2></div><div class="salience-heading-tools">${stateBadge("CONJECTURE")}${help("salience.help.aggregation.label", "salience.help.aggregation.fixtureBody", "salience-help-aggregation")}</div></header>
    <p class="salience-analysis-note">${esc(t("salience.aggregation.doctrine"))}</p>
    <div class="salience-aggregation-tree">${windows.map((window) =>
      windowNode(snapshot, window, clusters.find((cluster) => cluster.windowId === window.id))).join("")}
      ${patternNode(snapshot, pattern, trend)}</div>
  </section>`;
}
