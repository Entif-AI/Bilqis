import {
  ensureAtlasOverview,
  ensureAtlasSelection,
  invalidateAtlasRequests,
  renderAtlasDomain,
} from "../atlas/atlas-controller.mjs";
import { deactivateEvidenceView } from "../evidence/evidence-view.mjs";
import {
  activateSchoolDomain,
  invalidateSchoolDomainRequests,
} from "../school/school-domain-controller.mjs";

export function activateDomainViews({
  state, getState, defense, api, homeController, resourceController, operateController,
  capabilityExplorer, learningController, onInspect, onSelectionChange, onNavigate, onAnnounce,
  schoolDomainSupport = null, atlasDomainSupport = null,
}) {
  if (state?.view !== "evidence") deactivateEvidenceView();
  if (state?.view === "atlas") {
    const context = state.context;
    const atlasApi = context?.fixture === true ? atlasDomainSupport?.api : api;
    const isActive = () => getState()?.view === "atlas" && getState().context === context;
    if (atlasApi) {
      renderAtlasDomain(atlasApi, context, isActive, onInspect, onSelectionChange);
      if (state.selected?.kind === "semantic" && state.selected.id) {
        void ensureAtlasSelection(atlasApi, context, state.selected.id, isActive, onInspect, onSelectionChange);
      } else {
        void ensureAtlasOverview(atlasApi, context, isActive, onInspect, onSelectionChange);
      }
    }
  }
  if (state?.view !== "atlas") invalidateAtlasRequests();
  if (state?.view === "school") {
    const context = state.context;
    const fixture = state.context?.fixture === true;
    const support = fixture ? schoolDomainSupport : { activateSchoolDomain };
    if (!support?.activateSchoolDomain) return;
    void support.activateSchoolDomain({
      state,
      api,
      onInspect,
      launchMode: fixture ? "fixtures" : "production",
      isActive: () =>
        getState()?.view === "school" && getState().context === context,
    });
  } else {
    invalidateSchoolDomainRequests();
    schoolDomainSupport?.invalidateSchoolDomainRequests?.();
  }
  if (state?.view === "mission-control") {
    void homeController.activate(state.context, {
      host: document.querySelector("#domain-view"),
      onInspect,
      onNavigate,
      defense,
    });
  } else {
    void homeController.deactivate();
  }
  if (state?.view === "resources") {
    void resourceController?.activate(state.context, {
      target: document.querySelector("#domain-view"),
      onInspect,
      defense,
    });
  } else {
    void resourceController?.deactivate();
  }
  if (state?.view === "learning" && state.context?.fixture !== true) {
    void learningController?.activate(state.context, {
      target: document.querySelector("#domain-view"),
      onInspect,
      selection: state.selected,
    });
  } else {
    void learningController?.deactivate();
  }
  if (state?.view === "operate") {
    void operateController?.activate(state.context, {
      target: document.querySelector("#domain-view"),
      onInspect,
      onAnnounce,
      defense,
    });
  } else {
    void operateController?.deactivate();
  }
  if (state?.view === "capability") capabilityExplorer?.update(state);
  else capabilityExplorer?.hide();
}
