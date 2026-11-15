import { compareProductionRefs } from "./compare-production.mjs";
import { buildAppUri } from "./app-uri.mjs";
import { objectRefFromElement } from "./dom-ref.mjs";
import { t } from "../foundation/i18n.mjs";
import {
  createInteractionState,
  explicitHighlightRefs,
  setCompareSide,
  setInteractionPanel,
  stableObjectRef,
} from "./model.mjs";
import {
  addAnnotation,
  loadOperatorMetadata,
  saveOperatorMetadata,
  togglePin,
} from "./operator-metadata.mjs";
import { renderInvestigationMarkup } from "./view.mjs";

function matches(element, ref) {
  return element.dataset.objectKind === ref.kind && element.dataset.objectId === ref.id;
}

function markHighlights(root, ref) {
  const refs = explicitHighlightRefs(ref);
  root.querySelectorAll("[data-object-kind][data-object-id]").forEach((element) => {
    element.removeAttribute("data-global-highlight");
    const matched = refs.find((item) => matches(element, item));
    if (matched) element.dataset.globalHighlight = matched.relation === "selected" ? "selected" : "related";
  });
}

export function createInteractionController({
  document,
  storage,
  getState,
  onTimeLens,
  onCurrentLens,
  canUseCurrent,
  onOpenRef,
  compareRefs = compareProductionRefs,
  copyText = async () => false,
  announce = () => {},
}) {
  let interaction = createInteractionState();
  let metadata = loadOperatorMetadata(storage);
  let hovered = null;

  const currentRef = () => {
    const state = getState();
    return state ? stableObjectRef(state.selected, state.context) : null;
  };

  function save(next) {
    metadata = next;
    if (!saveOperatorMetadata(storage, metadata)) {
      announce(t("investigation.announce.metadataSaveFailed"));
    }
  }

  function render() {
    const state = getState();
    const ref = currentRef();
    const host = document.querySelector("#investigation-strip");
    const comparison = compareRefs(interaction.compare.left, interaction.compare.right);
    host.innerHTML = renderInvestigationMarkup({
      state, interaction, metadata, currentRef: ref, comparison,
      currentAvailable: canUseCurrent(),
    });
    bindDynamic(host);
    updateInspector(ref);
    markHighlights(document, hovered ?? ref);
  }

  function panel(name) {
    interaction = setInteractionPanel(
      interaction,
      interaction.panel === name ? "closed" : name,
    );
    render();
  }

  function bindDynamic(host) {
    host.querySelector("[data-time-lens-form]")?.addEventListener("submit", (event) => {
      event.preventDefault();
      const generation = Number(new FormData(event.currentTarget).get("generation"));
      if (!Number.isSafeInteger(generation) || generation < 0) {
        announce(t("investigation.announce.invalidGeneration"));
        return;
      }
      onTimeLens(generation);
    });
    host.querySelector("[data-use-current]")?.addEventListener("click", () => onCurrentLens());
    host.querySelectorAll("[data-investigation-panel]").forEach((button) => {
      button.addEventListener("click", () => panel(button.dataset.investigationPanel));
    });
    host.querySelectorAll("[data-clear-compare]").forEach((button) => {
      button.addEventListener("click", () => {
        interaction = setCompareSide(interaction, button.dataset.clearCompare, null);
        render();
      });
    });
    host.querySelectorAll("[data-open-pin]").forEach((button) => {
      button.addEventListener("click", () => {
        const pin = metadata.pins[Number(button.dataset.openPin)];
        if (pin) onOpenRef(pin);
      });
    });
    host.querySelectorAll("[data-remove-pin]").forEach((button) => {
      button.addEventListener("click", () => {
        const pin = metadata.pins[Number(button.dataset.removePin)];
        if (!pin) return;
        save(togglePin(metadata, pin));
        render();
      });
    });
    host.querySelector("[data-annotation-form]")?.addEventListener("submit", (event) => {
      event.preventDefault();
      const ref = currentRef();
      const body = new FormData(event.currentTarget).get("body")?.toString() ?? "";
      const next = addAnnotation(metadata, ref, body);
      if (next === metadata) {
        announce(t("investigation.announce.invalidNote"));
        return;
      }
      save(next);
      announce(t("investigation.announce.noteSaved"));
      render();
    });
  }

  function updateInspector(ref) {
    for (const id of ["pin-selection", "compare-left", "compare-right", "annotate-selection"]) {
      const button = document.querySelector("#" + id);
      if (button) button.disabled = !ref;
    }
    const pin = document.querySelector("#pin-selection");
    if (pin) {
      const pinned = ref && metadata.pins.some((item) =>
        item.kind === ref.kind && item.id === ref.id && item.runId === ref.runId &&
        item.generation === ref.generation);
      pin.textContent = t(pinned ? "shell.inspector.unpin" : "shell.inspector.pin");
    }
  }

  function bindStatic() {
    document.querySelector("#pin-selection")?.addEventListener("click", () => {
      const ref = currentRef();
      if (!ref) return;
      save(togglePin(metadata, ref));
      announce(t("investigation.announce.pinUpdated"));
      render();
    });
    document.querySelector("#compare-left")?.addEventListener("click", () => {
      const ref = currentRef();
      if (!ref) return;
      interaction = setCompareSide(interaction, "left", ref);
      render();
    });
    document.querySelector("#compare-right")?.addEventListener("click", () => {
      const ref = currentRef();
      if (!ref) return;
      interaction = setCompareSide(interaction, "right", ref);
      render();
    });
    document.querySelector("#annotate-selection")?.addEventListener("click", () => {
      if (!currentRef()) return;
      interaction = setInteractionPanel(interaction, "annotations");
      render();
      document.querySelector("[data-annotation-form] textarea")?.focus();
    });
    document.querySelector("#copy-deep-link")?.addEventListener("click", async () => {
      const ref = currentRef();
      if (!ref) return;
      const copied = await copyText(buildAppUri(ref));
      announce(t(copied ? "investigation.announce.deepLinkCopied" : "investigation.announce.deepLinkCopyFailed"));
    });
    document.addEventListener("pointerover", (event) => {
      const element = event.target?.closest?.("[data-object-kind][data-object-id]");
      if (!element) return;
      hovered = objectRefFromElement(element, getState()?.context);
      markHighlights(document, hovered);
    });
    document.addEventListener("pointerout", (event) => {
      const element = event.target?.closest?.("[data-object-kind][data-object-id]");
      if (!element || element.contains(event.relatedTarget)) return;
      hovered = null;
      markHighlights(document, currentRef());
    });
  }

  return Object.freeze({
    bindStatic,
    render,
    currentInteraction: () => interaction,
    currentMetadata: () => metadata,
  });
}
