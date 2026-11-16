import { renderSchoolView } from "./school-view.mjs";
import { loadSchoolRows } from "./school-live.mjs";
import { t } from "../foundation/i18n.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";
import { escapeText as esc } from "../frames/frame-model.mjs";

let schoolMode = "matrix";
let schoolSelectedId = null;
let schoolEpoch = 0;
let curriculumModule = null;

export function invalidateSchoolDomainRequests() {
  schoolEpoch += 1;
  curriculumModule?.invalidateCurriculumAtlasRequests?.();
}

function subnav(container, mode, onModeChange) {
  const nav = document.createElement("nav");
  nav.className = "school-subnav";
  nav.setAttribute("aria-label", t("shell.school.subnav"));
  nav.setAttribute("data-test-id", "shell-school-subnav");
  nav.innerHTML =
    '<button type="button" class="ui-control ui-control--peer-tab" data-school-mode="matrix" data-focus-key="school-mode:matrix" ' +
      testIdAttribute("shell", "school-mode", "matrix") + ' aria-current="' +
      (mode === "matrix" ? "page" : "false") + '">' + t("shell.school.matrix") + "</button>" +
    '<button type="button" class="ui-control ui-control--peer-tab" data-school-mode="atlas" data-focus-key="school-mode:atlas" ' +
      testIdAttribute("shell", "school-mode", "atlas") + ' aria-current="' +
      (mode === "atlas" ? "page" : "false") + '">' + t("shell.school.atlas") + "</button>";
  nav.querySelectorAll("[data-school-mode]").forEach((button) => {
    button.addEventListener("click", () => {
      void onModeChange(button.dataset.schoolMode, null, true);
    });
  });
  container.prepend(nav);
}

function value(value, fallback = "school.common.notExposed") {
  return value === null || value === undefined || value === "" ? t(fallback) : value;
}

function scoreQuad(row) {
  return [row.was, row.top, row.now, row.total].map((item) => value(item)).join("/");
}

function matrixInspector(onInspect, id, row) {
  if (!row) return;
  schoolSelectedId = id;
  onInspect({
    kind: "capability",
    id,
    details: {
      [t("school.inspector.scoreQuad")]: scoreQuad(row),
      [t("school.inspector.debt")]: value(row.debt),
      [t("school.inspector.pret")]: value(row.pRet),
      [t("school.inspector.prerequisites")]:
        row.prerequisites?.length ? row.prerequisites : [t("school.common.notExposed")],
      [t("school.inspector.sourceState")]: value(row.sourceState),
      [t("school.inspector.implementationState")]: value(row.implementationState),
      [t("school.inspector.qualificationState")]: value(row.qualificationState),
    },
  });
}

function productionAtlas(container) {
  container.innerHTML = `<section class="school-production-atlas" ${testIdAttribute("school", "atlas", "production")}>
    <header><div><span class="eyebrow">${esc(t("school.atlas.production.eyebrow"))}</span><h2>${esc(t("school.atlas.production.title"))}</h2></div>${contextHelpMarkup({ label: t("school.help.atlas.label"), description: t("school.help.atlas.body"), testId: "school-help-atlas" })}</header>
    <p>${esc(t("school.atlas.production.summary"))}</p>
  </section>`;
}

async function fixtureRows() {
  const fixture = await import("./school-fixture.mjs");
  return fixture.schoolFixtureRows();
}

async function fixtureCurriculum() {
  curriculumModule ??= await import("./curriculum-atlas-view.mjs");
  return curriculumModule;
}

export async function activateSchoolDomain({
  state,
  api,
  onInspect,
  launchMode = "production",
  isActive = () => true,
}) {
  if (state?.view !== "school") return;
  const root = globalThis.document;
  if (!root) return;
  const container = root.querySelector("#domain-view");
  const summary = root.querySelector("#view-summary");
  if (!container || !summary) return;
  const token = ++schoolEpoch;
  if (state.selected?.kind === "capability" && state.selected.id) {
    schoolSelectedId = state.selected.id;
  }

  let matrixState;
  if (launchMode === "fixtures") {
    const rows = await fixtureRows();
    matrixState = Object.freeze({
      rows,
      fixture: true,
      topologyAvailable: true,
      queryState: "FIXTURE",
    });
  } else {
    try {
      const live = await loadSchoolRows(api, state.context);
      matrixState = Object.freeze({
        rows: live.rows,
        fixture: false,
        topologyAvailable: false,
        queryState: live.state,
      });
    } catch (_error) {
      matrixState = Object.freeze({
        rows: Object.freeze([]),
        fixture: false,
        topologyAvailable: false,
        queryState: "UNAVAILABLE",
      });
    }
  }
  if (token !== schoolEpoch || !isActive()) return;

  async function renderMode(mode, requestedSelectedId = null, restoreModeFocus = false) {
    if (token !== schoolEpoch || !isActive()) return;
    schoolMode = mode === "atlas" ? "atlas" : "matrix";
    if (requestedSelectedId) schoolSelectedId = requestedSelectedId;
    if (schoolMode === "atlas") {
      summary.textContent = t("shell.destination.school.atlasPurpose");
      if (launchMode === "fixtures") {
        const curriculum = await fixtureCurriculum();
        if (token !== schoolEpoch || !isActive()) return;
        curriculum.renderCurriculumAtlasView(container, {
          context: state.context,
          api,
          selectedId: schoolSelectedId,
          isActive,
          onInspect: (id, node, binding = null) => {
            schoolSelectedId = id;
            const concept = binding?.state === "PRESENT" ? binding.concepts[0] : null;
            const preferred = concept?.labels?.find((label) => label.role === "prefLabel") ??
              concept?.labels?.[0] ?? null;
            onInspect({
              kind: "capability",
              id,
              details: {
                [t("school.inspector.semanticDisplay")]: concept
                  ? concept.semantic_id + " · " + (preferred?.value ?? node.label) + " · " +
                    t("curriculum.authority.sourceCanonical")
                  : node.semanticId + " · " + t("curriculum.authority.fixtureDisplay"),
                [t("school.inspector.grade")]: node.grade,
                [t("school.inspector.firstIntroduced")]: node.firstIntroducedGrade,
                [t("school.inspector.lifecycleQualification")]:
                  node.lifecycleState + " / " + node.qualificationState,
                [t("school.inspector.nowTopDebt")]:
                  node.now + "/" + node.total + " · " + node.top + "/" + node.total + " · " + node.debt,
                [t("school.inspector.prerequisites")]:
                  node.prerequisites.length ? node.prerequisites : [t("school.common.none")],
                [t("school.inspector.sourceState")]: node.sourceState,
                [t("school.inspector.implementationState")]: node.implementationState,
                [t("school.inspector.sourceRefs")]: node.sourceRefs,
              },
            });
          },
          onModeChange: renderMode,
        });
      } else {
        productionAtlas(container);
        subnav(container, schoolMode, renderMode);
      }
      if (restoreModeFocus) container.querySelector('[data-school-mode="atlas"]')?.focus();
      return;
    }

    curriculumModule?.invalidateCurriculumAtlasRequests?.();
    summary.textContent = t("shell.destination.school.purpose");
    renderSchoolView(container, (id, row) => matrixInspector(onInspect, id, row), {
      ...matrixState,
      selectedId: schoolSelectedId,
    });
    subnav(container, schoolMode, renderMode);
    if (restoreModeFocus) container.querySelector('[data-school-mode="matrix"]')?.focus();
  }

  await renderMode(schoolMode);
}
