import { DossierController } from "./controller.mjs";
import { buildQuery, escapeHtml as e } from "./model.mjs";
import { fixtureQuery, FIXTURE_RUN } from "./fixture.mjs";
import { renderDossier, renderEvidence } from "./view.mjs";
import { controlClass } from "../foundation/primitives.mjs";
import { t } from "../foundation/i18n.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";

export function createCapabilityExplorer({
  host, changeLens, openObject, openEvidence, serviceQuery, resolvePins,
}) {
  let lens;
  let capabilityId;
  let fixture = false;
  let key = null;
  let evidenceEpoch = 0;
  let evidencePage;
  let evidenceRef;
  let evidenceEntry;
  const query = (request) => fixture ? fixtureQuery(request) : serviceQuery(request);
  const controller = new DossierController(query, () => draw());

  function controlsMarkup() {
    return `<div class="capability-tools" aria-label="${e(t("capability.controls.aria"))}"
      ${testIdAttribute("capability", "controls")}>
      <label>${e(t("capability.controls.source"))}
        <select ${testIdAttribute("capability", "source", "select")}>
          <option value="service" ${!fixture ? "selected" : ""}>${e(t("capability.controls.service"))}</option>
          <option value="fixture" ${fixture ? "selected" : ""}>${e(t("capability.controls.fixture"))}</option>
        </select>
      </label>
      <form class="capability-lens" ${testIdAttribute("capability", "lens", "form")}>
        <label>${e(t("capability.controls.run"))}<input name="run" value="${e(lens.runId)}" required
          ${testIdAttribute("capability", "lens", "run")}></label>
        <label>${e(t("capability.controls.generation"))}<input name="generation" type="number" min="0" step="1"
          value="${lens.generation}" required ${testIdAttribute("capability", "lens", "generation")}></label>
        <label>${e(t("capability.controls.capability"))}<input name="capability" value="${e(capabilityId)}" required
          ${testIdAttribute("capability", "lens", "capability")}></label>
        <button class="${controlClass("primary")}" ${testIdAttribute("capability", "lens", "submit")}>${e(t("capability.controls.inspect"))}</button>
      </form>
      <div class="capability-tool-actions">
        <button type="button" class="${controlClass("secondary")}" data-reload
          ${testIdAttribute("capability", "reload")}>${e(t("capability.controls.reload"))}</button>
        ${controller.state.cursor ? `<button type="button" class="${controlClass("tertiary")}" data-more
          ${testIdAttribute("capability", "more")}>${e(t("capability.controls.more"))}</button>` : ""}
      </div>
    </div>`;
  }

  function bindEvidence(target) {
    target.querySelector("[data-evidence-more]")?.addEventListener("click", () => void showEvidence(evidencePage?.next_cursor));
    target.querySelectorAll("[data-record]").forEach((button) => {
      button.onclick = () => void showEvidence(null, {
        family: button.parentElement.querySelector("[data-family]").value,
        schema_version: null,
        record_id: button.dataset.record,
        reference: null,
        cursor: null,
      });
    });
    target.querySelector("[data-open-evidence]")?.addEventListener("click", (event) => {
      openEvidence?.({ kind: "evidence", id: event.currentTarget.dataset.openEvidence });
    });
  }

  function draw() {
    if (!lens) return;
    host.innerHTML = `<div class="capability-explorer" ${testIdAttribute("capability", "view")}>
      ${controlsMarkup()}
      <div class="capability-dossier-host" ${testIdAttribute("capability", "dossier", "host")}>${renderDossier(controller.state)}</div>
      <section class="capability-evidence-host" aria-live="polite" tabindex="-1"
        aria-label="${e(t("capability.evidence.title"))}" ${testIdAttribute("capability", "evidence", "host")}></section>
    </div>`;
    host.querySelector('[data-test-id="capability-source-select"]').onchange = (event) => {
      fixture = event.target.value === "fixture";
      changeLens({
        runId: fixture ? FIXTURE_RUN : "", generation: fixture ? 3 : 0,
        mode: "HISTORICAL", fixture,
      }, "B.AND");
    };
    host.querySelector('[data-test-id="capability-lens-form"]').onsubmit = (event) => {
      event.preventDefault();
      const data = new FormData(event.target);
      const generation = Number(data.get("generation"));
      if (!Number.isSafeInteger(generation) || generation < 0) return;
      changeLens({
        runId: data.get("run"), generation, mode: "HISTORICAL", fixture,
      }, data.get("capability"));
    };
    host.querySelector("[data-reload]").onclick = () => void controller.load(lens, capabilityId, fixture);
    host.querySelector("[data-more]")?.addEventListener("click", () => void controller.more());
    host.querySelectorAll("[data-section]").forEach((button) => {
      button.onclick = () => {
        const section = host.querySelector(`[data-test-id="capability-section-${button.dataset.section}"]`);
        section.focus();
        section.scrollIntoView({ block: "start" });
      };
    });
    host.querySelectorAll("[data-evidence]").forEach((button) => {
      button.onclick = () => {
        evidenceEntry = controller.state.dossier.entries.find((entry) => entry.entry_id === button.dataset.entry);
        evidenceRef = button.dataset.evidence;
        void showEvidence();
      };
    });
    host.querySelectorAll("[data-related-id]").forEach((button) => {
      button.onclick = () => openObject({ kind: button.dataset.relatedKind, id: button.dataset.relatedId });
    });
    if (controller.state.dossier) resolvePins(controller.state.dossier.meta);
  }

  async function showEvidence(cursor = null, override = null) {
    const epoch = ++evidenceEpoch;
    const target = host.querySelector('[data-test-id="capability-evidence-host"]');
    const request = buildQuery(lens, override ?? {
      family: "reference", schema_version: null, reference: evidenceRef, cursor,
    });
    target.innerHTML = renderEvidence(evidenceRef, evidenceEntry, null);
    bindEvidence(target);
    target.focus();
    target.scrollIntoView({ block: "start" });
    try {
      const page = await query(request);
      if (epoch !== evidenceEpoch || !target.isConnected) return;
      evidencePage = cursor ? { ...page, links: [...(evidencePage?.links ?? []), ...(page.links ?? [])] } : page;
      target.innerHTML = renderEvidence(evidenceRef, evidenceEntry, evidencePage);
      bindEvidence(target);
    } catch (error) {
      if (epoch === evidenceEpoch && target.isConnected) {
        target.innerHTML = renderEvidence(evidenceRef, evidenceEntry, null, error.message);
        bindEvidence(target);
      }
    }
  }

  return {
    update(state) {
      const nextId = state.selected?.kind === "capability" ? state.selected.id : "B.AND";
      const nextKey = JSON.stringify([
        state.context.runId, state.context.generation, state.context.mode, state.context.fixture, nextId,
      ]);
      if (nextKey === key) return;
      evidenceEpoch += 1;
      key = nextKey;
      lens = state.context;
      capabilityId = nextId;
      fixture = Boolean(state.context.fixture);
      void controller.load(lens, capabilityId, fixture);
    },
    hide() {
      evidenceEpoch += 1;
      key = null;
      controller.epoch += 1;
    },
  };
}
