import {
  currentMemoryGeneration,
  memoryGeneration,
  pageSummaries,
  priorMemoryGeneration,
  slotByIdentity,
  slotsForPage,
  stableMemoryIdentity,
} from "./memory-model.mjs";
import {
  historicalMemoryMarkup,
  memoryFixtureMarkup,
  MEMORY_TABS,
} from "./memory-fixture-panels.mjs";

export { MEMORY_TABS } from "./memory-fixture-panels.mjs";

const ui = {
  compareGeneration: priorMemoryGeneration().generation,
  selectedPage: 0,
  selectedIdentity: stableMemoryIdentity(currentMemoryGeneration().slots[0]),
  activeTab: "overview",
};

function bindTabs(container) {
  const tabs = [...container.querySelectorAll("[data-memory-tab]")];
  const panels = [...container.querySelectorAll("[data-memory-panel]")];
  const activate = (id, focus = false) => {
    if (!MEMORY_TABS.includes(id)) return;
    ui.activeTab = id;
    tabs.forEach(tab => {
      const selected = tab.dataset.memoryTab === id;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      if (selected && focus) tab.focus?.({ preventScroll: true });
    });
    panels.forEach(panel => { panel.hidden = panel.dataset.memoryPanel !== id; });
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activate(tab.dataset.memoryTab));
    tab.addEventListener("keydown", event => {
      const next = event.key === "ArrowRight" ? (index + 1) % tabs.length
        : event.key === "ArrowLeft" ? (index - 1 + tabs.length) % tabs.length
        : event.key === "Home" ? 0
        : event.key === "End" ? tabs.length - 1
        : null;
      if (next === null) return;
      event.preventDefault();
      activate(tabs[next].dataset.memoryTab, true);
    });
  });
}

function bind(container, inspectMemory, snapshot, context) {
  bindTabs(container);
  container.querySelectorAll("[data-memory-page-step]").forEach(button => button.addEventListener("click", () => {
    const pages = pageSummaries(snapshot);
    const current = pages.findIndex(page => page.pageIndex === ui.selectedPage);
    const next = pages[current + Number(button.dataset.memoryPageStep)];
    if (!next) return;
    ui.selectedPage = next.pageIndex;
    const first = slotsForPage(snapshot, ui.selectedPage)[0];
    if (first) ui.selectedIdentity = stableMemoryIdentity(first);
    renderMemoryView(container, inspectMemory, ui.selectedIdentity, context);
  }));
  container.querySelectorAll("[data-memory-slot]").forEach(button => button.addEventListener("click", () => {
    ui.selectedIdentity = button.dataset.memorySlot;
    renderMemoryView(container, inspectMemory, ui.selectedIdentity, context);
    const slot = slotByIdentity(snapshot, ui.selectedIdentity);
    if (slot) inspectMemory(ui.selectedIdentity, slot);
  }));
  container.querySelector("[data-memory-compare]")?.addEventListener("change", event => {
    ui.compareGeneration = Number(event.currentTarget.value);
    renderMemoryView(container, inspectMemory, ui.selectedIdentity, context);
  });
}

export function renderMemoryView(container, inspectMemory, selectedIdentity = null, context = null) {
  let snapshot = currentMemoryGeneration();
  if (context?.mode === "HISTORICAL") {
    try {
      snapshot = memoryGeneration(context.generation);
    } catch (_error) {
      container.innerHTML = historicalMemoryMarkup(context.generation);
      return;
    }
  }
  if (selectedIdentity && slotByIdentity(snapshot, selectedIdentity)) ui.selectedIdentity = selectedIdentity;
  if (!slotByIdentity(snapshot, ui.selectedIdentity)) ui.selectedIdentity = stableMemoryIdentity(snapshot.slots[0]);
  const selected = slotByIdentity(snapshot, ui.selectedIdentity);
  if (selected) ui.selectedPage = selected.pageIndex;
  container.innerHTML = memoryFixtureMarkup(snapshot, ui, context);
  bind(container, inspectMemory, snapshot, context);
}
