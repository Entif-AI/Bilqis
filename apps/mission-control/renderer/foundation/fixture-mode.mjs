const MESSAGES = Object.freeze({
  "en-US": Object.freeze({
    label: "Reference mode",
    detail: "Representative fixture data for interface verification. Production learner evidence is not active in this launch.",
    mode: "REFERENCE",
  }),
});

function copy(document) {
  const locale = document?.documentElement?.lang || "en-US";
  return MESSAGES[locale] ?? MESSAGES["en-US"];
}

export function renderFixtureModePosture(document = globalThis.document) {
  if (!document) return;
  const message = copy(document);
  const shell = document.querySelector("#shell");
  const banner = document.querySelector("#launch-mode-banner");
  const mode = document.querySelector("#mode-badge");
  if (shell) shell.dataset.launchMode = "fixtures";
  if (banner) {
    banner.hidden = false;
    banner.setAttribute("role", "status");
    banner.innerHTML = `<strong>${message.label}</strong><span>${message.detail}</span>`;
  }
  if (mode && !mode.textContent.startsWith(message.mode + " · ")) {
    mode.textContent = message.mode + " · " + mode.textContent;
  }
}
