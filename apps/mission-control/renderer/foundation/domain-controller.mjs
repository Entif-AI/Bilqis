import {
  ensureAtlasOverview,
  ensureAtlasSelection,
  invalidateAtlasRequests,
  renderAtlasDomain,
} from "../atlas/atlas-controller.mjs";
import { deactivateEvidenceView } from "../evidence/evidence-view.mjs";

export function activateDomainViews({
  state, getState, defense, api, homeController, resourceController, operateController,
  capabilityExplorer, onInspect, onNavigate, onAnnounce, schoolDomainSupport = null,
}) {
  if (state?.view !== "evidence") deactivateEvidenceView();
  if (state?.view === "atlas") {
    const context = state.context;
    const isActive = () => getState()?.view === "atlas" && getState().context === context;
    renderAtlasDomain(api, context, isActive);
    if (state.selected?.kind === "semantic" && state.selected.id) {
      void ensureAtlasSelection(api, context, state.selected.id, isActive);
    } else {
      void ensureAtlasOverview(api, context, isActive);
    }
  }
  if (state?.view !== "atlas") invalidateAtlasRequests();
  if (state?.view === "school") {
    if (!schoolDomainSupport || state.context?.fixture !== true) return;
    const context = state.context;
    schoolDomainSupport.activateSchoolDomain({
      state,
      api,
      onInspect,
      isActive: () =>
        getState()?.view === "school" && getState().context === context,
    });
  } else schoolDomainSupport?.invalidateSchoolDomainRequests?.();
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
