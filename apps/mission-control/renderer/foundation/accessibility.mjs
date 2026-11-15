export const MANUAL_KEYBOARD_SCENARIO = Object.freeze([
  "Tab to Skip to main content and activate it.",
  "Shift+Tab back to Primary navigation, then use ArrowDown to reach School and Enter to open it.",
  "Tab into the capability matrix, activate one capability, and confirm the Global inspector receives focus.",
  "Press Escape to close the inspector and confirm focus returns to the invoking control.",
  "Use the dependency graph with ArrowRight or ArrowDown, activate a node with Space, then inspect the equivalent dependency table.",
  "Press Control+K or Command+K, choose a destination from the command palette, and close the palette with Escape.",
  "While an offline or restart fixture is active, confirm Operate is disabled and retained evidence is labeled inspection-only.",
]);

export function nextRovingIndex(currentIndex, key, count) {
  if (!Number.isInteger(currentIndex) || !Number.isInteger(count) || count <= 0) return -1;
  if (key === "Home") return 0;
  if (key === "End") return count - 1;
  if (key === "ArrowDown" || key === "ArrowRight") return (currentIndex + 1) % count;
  if (key === "ArrowUp" || key === "ArrowLeft") return (currentIndex - 1 + count) % count;
  return currentIndex;
}

export function isActivationKey(key) {
  return key === "Enter" || key === " ";
}

export function focusToken(element) {
  if (!element || typeof element !== "object") return null;
  const key = element.dataset?.focusKey;
  if (typeof key === "string" && key) return `data:${key}`;
  if (typeof element.id === "string" && element.id) return `id:${element.id}`;
  return typeof element.focus === "function" ? Object.freeze({ element }) : null;
}

export function restoreFocus(documentObject, token, fallbackSelector = "#main-content") {
  if (!documentObject || !token) return false;
  let target = null;
  if (typeof token === "object" && token.element?.isConnected !== false &&
      typeof token.element?.focus === "function") {
    target = token.element;
  } else if (typeof token === "string" && token.startsWith("id:")) {
    target = documentObject.getElementById(token.slice(3));
  } else if (typeof token === "string" && token.startsWith("data:")) {
    const key = token.slice(5);
    target = [...documentObject.querySelectorAll("[data-focus-key]")]
      .find((candidate) => candidate.dataset.focusKey === key) ?? null;
  }
  target ??= documentObject.querySelector(fallbackSelector);
  if (!target || typeof target.focus !== "function") return false;
  target.focus();
  return true;
}

export function bindRovingNavigation(container, selector = "button:not(:disabled)") {
  const items = [...container.querySelectorAll(selector)];
  items.forEach((item, index) => item.addEventListener("keydown", (event) => {
    const next = nextRovingIndex(index, event.key, items.length);
    if (next === index) return;
    event.preventDefault();
    items[next]?.focus();
  }));
}
