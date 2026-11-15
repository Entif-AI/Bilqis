import { SALIENCE_AXES, SALIENCE_SNAPSHOTS } from "./salience-fixture.mjs";
import { aggregationPathForEvent, snapshotById } from "./salience-model.mjs";
import { aggregationPanel } from "./salience-aggregation-view.mjs";
import { observationPanel } from "./salience-observation-view.mjs";
import { projectionDisclosure, routingPanel } from "./salience-routing-view.mjs";
import { esc, t, testIdAttribute } from "./salience-view-shared.mjs";

let selectedSnapshotId = "current";
let selectedObservationId = null;

function snapshotOption(snapshot) {
  const key = snapshot.mode === "HISTORICAL" ? "salience.snapshot.historical" : "salience.snapshot.current";
  return `<option value="${esc(snapshot.id)}" ${snapshot.id === selectedSnapshotId ? "selected" : ""}>
    ${esc(t(key, {generation: snapshot.generation}))}
  </option>`;
}

function snapshotControl(snapshot) {
  return `<div class="salience-view-controls" ${testIdAttribute("salience", "controls")}>
    <label class="salience-snapshot-control"><span>${esc(t("salience.snapshot.label"))}</span>
      <select data-snapshot-select ${testIdAttribute("salience", "snapshot", "select")}>
        ${SALIENCE_SNAPSHOTS.map(snapshotOption).join("")}
      </select>
      <small>${esc(t("salience.snapshot.help"))}</small>
    </label>
    <p class="salience-fixture-boundary" role="note" ${testIdAttribute("salience", "fixture", "boundary")}>
      ${esc(t("salience.fixture.boundary"))}
    </p>
  </div>`;
}

function inspectDetails(event, axis) {
  const evidence = axis ? event.axes[axis] : null;
  const path = aggregationPathForEvent(event.recordId);
  return {
    [t("salience.inspector.capability")]: event.capabilityId,
    [t("salience.inspector.action")]: event.actionKind,
    [t("salience.inspector.time")]: `${event.observedAt} / ${event.effectiveAt}`,
    [t("salience.inspector.object")]: event.associatedObjectRef,
    [t("salience.inspector.policyOwner")]: event.policy.sourceOwner,
    [t("salience.inspector.policy")]: `${event.policy.policyId}/${event.policy.version}`,
    [t("salience.inspector.policyDigest")]: event.policy.policyDigest,
    [t("salience.inspector.axis")]: axis ?? t("salience.value.allAxes"),
    [t("salience.inspector.ordinal")]: evidence?.ordinal ??
      SALIENCE_AXES.map((name) => `${name}:${event.axes[name].ordinal}`).join(" · "),
    [t("salience.inspector.observationState")]: evidence?.observationState ?? t("salience.value.mixed"),
    [t("salience.inspector.source")]: evidence?.sourceRef ?? event.sourceFamily,
    [t("salience.inspector.basis")]: evidence?.basisRefs ?? event.evidenceRefs,
    [t("salience.inspector.aggregationPath")]: path ?
      [path.cluster.id, path.pattern.id, path.trend.id] : [t("salience.value.none")],
  };
}

function bind(container, inspect) {
  container.querySelector("[data-snapshot-select]")?.addEventListener("change", (event) => {
    selectedSnapshotId = event.currentTarget.value;
    selectedObservationId = null;
    renderSalienceView(container, inspect);
  });
  container.querySelectorAll("[data-salience-inspect]").forEach((control) => {
    control.addEventListener("click", () => {
      const snapshot = snapshotById(selectedSnapshotId);
      const event = snapshot.events.find((item) => item.recordId === control.dataset.salienceInspect);
      if (!event) return;
      selectedObservationId = event.recordId;
      inspect(event.recordId, inspectDetails(event, control.dataset.axis ?? null));
      container.querySelectorAll(".salience-observation-row").forEach((row) => {
        row.dataset.selected = row.querySelector("[data-salience-inspect]")?.dataset.salienceInspect === selectedObservationId ? "true" : "false";
      });
    });
  });
}

export function salienceMarkupForTest(
  snapshotId = selectedSnapshotId,
  selectedId = selectedObservationId,
) {
  const snapshot = snapshotById(snapshotId);
  selectedSnapshotId = snapshot.id;
  return `<div class="salience-view" ${testIdAttribute("salience", "view")}>
    ${snapshotControl(snapshot)}
    ${observationPanel(snapshot, selectedId)}
    ${aggregationPanel(snapshot)}
    <section class="salience-derived" aria-label="${esc(t("salience.routing.summary"))}">
      ${routingPanel(snapshot)}
      ${projectionDisclosure()}
    </section>
  </div>`;
}

export function renderSalienceView(container, inspect, selectedId = null) {
  if (selectedId) {
    const containing = SALIENCE_SNAPSHOTS.find((snapshot) =>
      snapshot.events.some((event) => event.recordId === selectedId || event.salienceId === selectedId));
    if (containing) selectedSnapshotId = containing.id;
    selectedObservationId = containing?.events.find((event) =>
      event.recordId === selectedId || event.salienceId === selectedId)?.recordId ?? null;
  }
  container.hidden = false;
  container.innerHTML = salienceMarkupForTest(selectedSnapshotId, selectedObservationId);
  bind(container, inspect);
}
