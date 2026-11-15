import { SALIENCE_PROJECTION } from "./salience-fixture.mjs";
import { routingForSnapshot } from "./salience-model.mjs";
import { esc, slug, stateBadge, t, testIdAttribute } from "./salience-view-shared.mjs";

function citedObservation(snapshot, id) {
  const available = snapshot.events.some((event) => event.recordId === id);
  if (!available) return `<span class="salience-observation-ref salience-observation-ref--unavailable">${esc(t("salience.observation.outside", {id}))}</span>`;
  return `<button type="button" class="ui-control ui-control--link salience-observation-ref"
    data-salience-inspect="${esc(id)}" data-focus-key="salience:routing:${esc(id)}"
    ${testIdAttribute("salience", "routing", "observation", slug(id))}>${esc(t("salience.observation.available", {id}))}</button>`;
}

export function routingPanel(snapshot) {
  const routes = routingForSnapshot(snapshot);
  const countKey = routes.length === 1 ? "salience.routing.count" : "salience.routing.countPlural";
  return `<details class="salience-routing ui-disclosure" ${testIdAttribute("salience", "routing")}>
    <summary><span>${esc(t("salience.routing.summary"))}</span>
      <span>${routes.length ? esc(t(countKey, {count: routes.length})) : esc(t("salience.value.unavailable"))}</span></summary>
    <div class="ui-disclosure__body salience-routing-body">${routes.length ? routes.map((route) => `<section class="salience-route"
      ${testIdAttribute("salience", "routing", "record", slug(route.id))}><h3><code>${esc(route.id)}</code></h3>
      <dl><div><dt>${esc(t("salience.routing.tier"))}</dt><dd class="machine-value">${esc(route.tier)}</dd></div>
        <div><dt>${esc(t("salience.routing.rule"))}</dt><dd class="machine-value">${esc(route.rule)}</dd></div>
        <div><dt>${esc(t("salience.routing.ordering"))}</dt><dd class="machine-value">${esc(route.ordering.join(" → "))}</dd></div>
        <div><dt>${esc(t("salience.routing.weighting"))}</dt><dd class="machine-value">${esc(route.hiddenWeighting)}</dd></div></dl>
      <div class="salience-cited-observations"><strong>${esc(t("salience.routing.cited"))}</strong>
        ${route.citedObservationIds.map((id) => citedObservation(snapshot, id)).join("")}</div></section>`).join("")
      : `<p>${esc(t("salience.routing.unavailable"))}</p>`}
      <p class="salience-derived-boundary">${esc(t("salience.routing.boundary"))}</p>
    </div>
  </details>`;
}

export function projectionDisclosure() {
  return `<details class="salience-projection ui-disclosure" ${testIdAttribute("salience", "projection")}>
    <summary><span>${esc(t("salience.projection.summary"))}</span>${stateBadge("PARTIAL")}</summary>
    <div class="ui-disclosure__body"><dl class="salience-projection-grid">
      <div><dt>${esc(t("salience.projection.schema"))}</dt><dd class="machine-value">${esc(SALIENCE_PROJECTION.schema)}</dd></div>
      <div><dt>${esc(t("salience.projection.coverage"))}</dt><dd>${esc(t("salience.value.partial"))}</dd></div>
      <div><dt>${esc(t("salience.projection.fields"))}</dt><dd class="machine-value">${esc(SALIENCE_PROJECTION.fields.join(", "))}</dd></div>
    </dl><p>${esc(t("salience.projection.limit"))}</p></div>
  </details>`;
}
