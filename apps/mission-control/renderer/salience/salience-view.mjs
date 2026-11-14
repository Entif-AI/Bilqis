import {
  SALIENCE_AXES,
  SALIENCE_PROJECTION,
  SALIENCE_SNAPSHOTS,
} from "./salience-fixture.mjs";
import {
  aggregationForSnapshot,
  aggregationPathForEvent,
  axisPosture,
  constituentObservationIds,
  routingForSnapshot,
  salienceDeepLink,
  snapshotById,
} from "./salience-model.mjs";

let selectedSnapshotId = "current";

const axisLabel = Object.freeze({
  impact: "Impact",
  exigency: "Exigency",
  novelty: "Osmotic Novelty",
});

function badge(text) {
  return `<span class="salience-badge" data-state="${text}">${text}</span>`;
}

function axisCell(event, axis) {
  const value = event.axes[axis];
  const posture = axisPosture(value);
  const missingNote = value.observationState === "EXPECTED_MISSING"
    ? "<small>Expected event absent</small>"
    : value.observationState === "REPORTED_NEGATIVE"
      ? "<small>Observed negative event</small>"
      : value.state === "UNKNOWN"
        ? "<small>Unknown / not reported</small>"
        : "";
  return `<button type="button" class="salience-axis-cell"
    data-salience-inspect="${event.recordId}" data-axis="${axis}" data-posture="${posture}"
    data-focus-key="salience:${event.recordId}:${axis}">
    <span>${axisLabel[axis]}</span>
    ${badge(value.ordinal)}
    ${missingNote}
  </button>`;
}

function eventRows(snapshot) {
  return snapshot.events.map((event) => `<article class="salience-event-row" data-event="${event.recordId}">
    <header>
      <div><small>${event.actionKind} · ${event.capabilityId}</small><strong>${event.salienceId}</strong></div>
      <div><small><b>Observed</b> ${event.observedAt}</small><small><b>Effective</b> ${event.effectiveAt}</small></div>
    </header>
    <div class="salience-lanes">${SALIENCE_AXES.map((axis) => axisCell(event, axis)).join("")}</div>
    <footer>
      <span>scope ${event.scope}</span>
      <span>source ${event.sourceFamily}</span>
      <span>object ${event.associatedObjectRef}</span>
      <a href="${salienceDeepLink(event.recordId)}">stable link</a>
    </footer>
  </article>`).join("");
}

function provenancePanel(snapshot) {
  return `<section class="salience-panel">
    <header><div><span class="eyebrow">Evidence provenance</span><h3>Source, signed policy, basis</h3></div>${badge(snapshot.mode)}</header>
    <div class="salience-provenance-grid">${snapshot.events.map((event) => `<article>
      <h4>${event.capabilityId} · ${event.salienceId}</h4>
      <dl>
        <dt>Policy owner</dt><dd>${event.policy.sourceOwner}</dd>
        <dt>Policy</dt><dd>${event.policy.policyId}/${event.policy.version}</dd>
        <dt>Policy digest</dt><dd>${event.policy.policyDigest}</dd>
        <dt>Window policy</dt><dd>${event.policy.windowPolicyId}/${event.policy.windowPolicyVersion} · size ${event.policy.windowSize}</dd>
        ${SALIENCE_AXES.map((axis) => {
          const value = event.axes[axis];
          return `<dt>${axisLabel[axis]}</dt><dd>${value.sourceRef} · ${value.ruleId}<br><small>${value.basisRefs.join(" · ")}</small></dd>`;
        }).join("")}
      </dl>
    </article>`).join("")}</div>
  </section>`;
}

function recursivePanel(snapshot) {
  const aggregation = aggregationForSnapshot(snapshot);
  if (!aggregation) {
    return `<section class="salience-panel">
      <header><div><span class="eyebrow">Recursive aggregation</span><h3>Selected as-of evidence</h3></div>${badge("UNAVAILABLE")}</header>
      <p class="salience-doctrine">No retained aggregation fixture is available inside this historical as-of boundary. Current clusters, patterns, and trends are not backfilled into the past.</p>
    </section>`;
  }
  const { windows, clusters, pattern, trend } = aggregation;
  return `<section class="salience-panel">
    <header><div><span class="eyebrow">Recursive aggregation</span><h3>Observation → cluster → pattern → trend</h3></div>${badge("CONJECTURE")}</header>
    <p class="salience-doctrine">Aggregation is inspectable and reversible. It does not convert conjecture into source truth or teaching qualification.</p>
    ${windows.map((window) => {
      const cluster = clusters.find((item) => item.windowId === window.id);
      if (!cluster) return "";
      const present = cluster.eventIds.filter((id) => snapshot.events.some((event) => event.recordId === id));
      return `<details open><summary>Window · ${window.id}</summary>
        <div class="salience-scope"><span>size ${window.size}</span><span>accepted append count ${window.acceptedAppendCount}</span><span>bounds ${window.observedBounds.join("–")}</span><span>late ${window.lateObservations}</span></div>
        <details open><summary>Cluster · ${cluster.id}</summary>
          <p>partition ${cluster.partition}</p>
          <p>rule ${cluster.ruleId} · defect present · LOW impact · LOW exigency · ${cluster.lineageIds.length} independent lineages</p>
          <div class="salience-links">${present.map((id) => `<button type="button" data-salience-inspect="${id}" data-focus-key="salience:aggregate:${id}">${id}</button>`).join("")}</div>
        </details>
      </details>`;
    }).join("")}
    <details open><summary>Pattern · ${pattern.id}</summary>
      <p>${pattern.status} · ${pattern.nomination} · source_gold=${pattern.sourceGold} · qualified_for_teaching=${pattern.qualifiedForTeaching}</p>
      <details open><summary>Trend · ${trend.id}</summary>
        <p>supported=${trend.supported} · rule ${trend.ruleId}</p>
        <ol>${trend.points.map((point) => `<li>${point.windowId}: +${point.newLineages} new lineage(s), ${point.cumulativeLineages} cumulative</li>`).join("")}</ol>
        <div class="salience-links">${constituentObservationIds("trend", trend.id).map((id) => {
          const available = snapshot.events.some((event) => event.recordId === id);
          return available
            ? `<button type="button" data-salience-inspect="${id}" data-focus-key="salience:trend:${id}">observation · ${id}</button>`
            : `<span>observation · ${id} · outside selected as-of fixture</span>`;
        }).join("")}</div>
      </details>
    </details>
  </section>`;
}

function routingPanel(snapshot) {
  const routes = routingForSnapshot(snapshot);
  if (!routes.length) {
    return `<section class="salience-panel">
      <header><div><span class="eyebrow">Routing visibility</span><h3>Selected as-of evidence</h3></div>${badge("UNAVAILABLE")}</header>
      <p class="salience-doctrine">No retained routing-rationale fixture is available inside this historical as-of boundary. Current dispatch evidence is not projected backward.</p>
    </section>`;
  }
  return `<section class="salience-panel">
    <header><div><span class="eyebrow">Routing visibility</span><h3>Admitted rationale only</h3></div>${badge("NO_SCALAR")}</header>
    ${routes.map((route) => `<article class="routing-record">
      <h4>${route.id}</h4>
      <p><strong>${route.tier}</strong> because <code>${route.rule}</code>.</p>
      <p>Ordering keys: ${route.ordering.join(" → ")}. Hidden weighting: ${route.hiddenWeighting}.</p>
      <div class="salience-links">${route.citedObservationIds.map((id) => {
        const available = snapshot.events.some((event) => event.recordId === id);
        return available
          ? `<button type="button" data-salience-inspect="${id}" data-focus-key="salience:routing:${id}">cited observation · ${id}</button>`
          : `<span>cited observation · ${id} · outside selected as-of fixture</span>`;
      }).join("")}</div>
    </article>`).join("")}
    <p class="salience-doctrine">This panel exposes recorded dispatch tier and ordering rationale. It does not infer private weights from the selected outcome.</p>
  </section>`;
}

function projectionPanel() {
  return `<section class="salience-panel">
    <header><div><span class="eyebrow">Projection boundary</span><h3>${SALIENCE_PROJECTION.schema}</h3></div>${badge("PARTIAL")}</header>
    <p>CP02/CP03 projects ${SALIENCE_PROJECTION.fields.join(", ")}. Signed policy identity/version, per-axis fact/rule provenance, recursive aggregation, and routing-rationale detail are not first-class SalienceEvent fields, so GUI12’s rich inspection is explicitly fixture-backed from the executable C06 contracts.</p>
  </section>`;
}

function bind(container, inspect) {
  container.querySelectorAll("[data-snapshot]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedSnapshotId = button.dataset.snapshot;
      renderSalienceView(container, inspect);
    });
  });
  container.querySelectorAll("[data-salience-inspect]").forEach((button) => {
    button.addEventListener("click", () => {
      const snapshot = snapshotById(selectedSnapshotId);
      const event = snapshot.events.find((item) => item.recordId === button.dataset.salienceInspect);
      if (!event) return;
      const axis = button.dataset.axis;
      const evidence = axis ? event.axes[axis] : null;
      const path = aggregationPathForEvent(event.recordId);
      inspect(event.recordId, {
        Capability: event.capabilityId,
        "Action kind": event.actionKind,
        "Observed / effective": `${event.observedAt} / ${event.effectiveAt}`,
        "Associated object": event.associatedObjectRef,
        "Policy owner": event.policy.sourceOwner,
        Policy: `${event.policy.policyId}/${event.policy.version}`,
        "Policy digest": event.policy.policyDigest,
        Axis: axis ?? "all",
        Ordinal: evidence?.ordinal ?? SALIENCE_AXES.map((name) => `${name}:${event.axes[name].ordinal}`).join(" · "),
        "Observation state": evidence?.observationState ?? "mixed",
        Source: evidence?.sourceRef ?? event.sourceFamily,
        Basis: evidence?.basisRefs ?? event.evidenceRefs,
        "Aggregation path": path ? [path.cluster.id, path.pattern.id, path.trend.id] : ["none in selected fixture"],
      });
    });
  });
}

export function renderSalienceView(container, inspect) {
  const snapshot = snapshotById(selectedSnapshotId);
  container.hidden = false;
  container.innerHTML = `<div class="salience-view">
    <div class="salience-fixture-notice"><strong>FIXTURE · C06 EVIDENCE SHAPE</strong><span>Rich fact/rule provenance, signed policy identity, recursive aggregation and routing rationale are fixture-backed because current SalienceEvent projection is intentionally narrow.</span></div>
    <section class="salience-toolbar" aria-label="Salience as-of fixture selector">
      ${SALIENCE_SNAPSHOTS.map((item) => `<button type="button" data-snapshot="${item.id}" data-focus-key="salience:snapshot:${item.id}" aria-pressed="${item.id === snapshot.id}">${item.label}</button>`).join("")}
    </section>
    <div class="ui-glossary" aria-label="SÍ SÉ SON definitions"><span><strong>Impact</strong> consequence magnitude.</span><span><strong>Exigency</strong> urgency or time pressure.</span><span><strong>Osmotic Novelty</strong> departure from expectation.</span><span>The three axes remain independent; this view does not compute a universal score.</span></div>
    <section class="salience-panel">
      <header><div><span class="eyebrow">SÍ SÉ SON</span><h3>Three independent evidence lanes</h3></div>${badge(snapshot.mode)}</header>
      <p class="salience-doctrine">Impact, Exigency, and expectation-relative Osmotic Novelty remain separate ordinals. No weighted universal salience score is computed.</p>
      <div class="salience-lane-head">${SALIENCE_AXES.map((axis) => `<strong>${axisLabel[axis]}</strong>`).join("")}</div>
      <div class="salience-events">${eventRows(snapshot)}</div>
    </section>
    ${provenancePanel(snapshot)}
    ${recursivePanel(snapshot)}
    ${routingPanel(snapshot)}
    ${projectionPanel()}
  </div>`;
  bind(container, inspect);
}
