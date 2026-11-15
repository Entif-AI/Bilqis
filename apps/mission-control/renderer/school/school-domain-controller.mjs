import { renderSchoolView } from "./school-view.mjs";
import {
  invalidateCurriculumAtlasRequests,
  renderCurriculumAtlasView,
} from "./curriculum-atlas-view.mjs";
import { t } from "../foundation/i18n.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";

let schoolMode = "matrix";
let schoolSelectedId = null;

export function invalidateSchoolDomainRequests() {
  invalidateCurriculumAtlasRequests();
}

function subnav(container, mode, onModeChange) {
  const nav = document.createElement("nav");
  nav.className = "school-subnav";
  nav.setAttribute("aria-label", t("shell.school.subnav"));
  nav.setAttribute("data-test-id", "shell-school-subnav");
  nav.innerHTML =
    '<button type="button" class="ui-control ui-control--peer-tab" data-school-mode="matrix" data-focus-key="school-mode:matrix" ' +
      testIdAttribute("shell", "school-mode", "matrix") + ' aria-current="' +
      (mode === "matrix" ? "page" : "false") + '">' + t("shell.school.matrix") + '</button>' +
    '<button type="button" class="ui-control ui-control--peer-tab" data-school-mode="atlas" data-focus-key="school-mode:atlas" ' +
      testIdAttribute("shell", "school-mode", "atlas") + ' aria-current="' +
      (mode === "atlas" ? "page" : "false") + '">' + t("shell.school.atlas") + '</button>';
  nav.querySelectorAll("[data-school-mode]").forEach((button) => {
    button.addEventListener("click", () => onModeChange(button.dataset.schoolMode, null, true));
  });
  container.prepend(nav);
}

export function activateSchoolDomain({ state, api, onInspect, isActive = () => true }) {
  if (state?.view !== "school") return;
  const root = globalThis.document;
  if (!root) return;
  const container = root.querySelector("#domain-view");
  const summary = root.querySelector("#view-summary");
  if (!container || !summary) return;
  if (state.selected?.kind === "capability" && state.selected.id) {
    schoolSelectedId = state.selected.id;
  }

  function renderMode(mode, requestedSelectedId = null, restoreModeFocus = false) {
    schoolMode = mode === "atlas" ? "atlas" : "matrix";
    if (requestedSelectedId) schoolSelectedId = requestedSelectedId;
    if (schoolMode === "atlas") {
      summary.textContent = t("shell.destination.school.atlasPurpose");
      renderCurriculumAtlasView(container, {
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
              "Semantic display identity": concept
                ? concept.semantic_id + " · " + (preferred?.value ?? node.label) + " · SOURCE CANONICAL"
                : node.semanticId + " · FIXTURE DISPLAY ONLY",
              Grade: node.grade,
              "First introduced": node.firstIntroducedGrade,
              "Lifecycle / qualification": node.lifecycleState + " / " + node.qualificationState,
              "NOW / TOP / debt": node.now + "/" + node.total + " · " +
                node.top + "/" + node.total + " · " + node.debt,
              Prerequisites: node.prerequisites.length ? node.prerequisites : ["none"],
              "Source state": node.sourceState,
              "Implementation state": node.implementationState,
              "Source refs": node.sourceRefs,
            },
          });
        },
        onModeChange: renderMode,
      });
      if (restoreModeFocus) container.querySelector('[data-school-mode="atlas"]')?.focus();
      return;
    }
    invalidateCurriculumAtlasRequests();
    summary.textContent = t("shell.destination.school.purpose");
    renderSchoolView(container, (id, row) => {
      schoolSelectedId = id;
      onInspect({
        kind: "capability",
        id,
        details: {
          "WAS/TOP/NOW/ALL": row.was + "/" + row.top + "/" + row.now + "/" + row.total,
          Debt: row.debt,
          "P(RET)": row.pRet ?? "NOT MEASURED",
          Prerequisites: row.prerequisites.length ? row.prerequisites : ["none"],
          "Source state": row.sourceState,
          "Implementation state": row.implementationState,
          "Qualification state": row.qualificationState,
        },
      });
    }, schoolSelectedId);
    subnav(container, schoolMode, renderMode);
  }

  renderMode(schoolMode);
}
