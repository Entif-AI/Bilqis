"use strict";

const path = require("node:path");
const { app, BrowserWindow, ipcMain, net, protocol } = require("electron");

const { AcceptedControlPlaneAdapter } = require(
  "./electron/accepted-control-plane-adapter.cjs",
);
const {
  LAUNCH_MODE_FIXTURES,
  resolveLaunchMode,
} = require("./electron/launch-mode.cjs");
const { createAcceptedValidators } = require("./electron/accepted-contracts.cjs");
const { ControlPlaneBridge } = require("./electron/control-plane-bridge.cjs");
const { registerMissionControlIpc } = require("./electron/main-ipc.cjs");
const { registerRendererSchemePrivileges } = require("./electron/renderer-location.cjs");
const { registerMissionControlProtocol } = require("./electron/renderer-protocol.cjs");
const { createMissionControlWindow } = require("./electron/window-security.cjs");
const { appUriArgument, rendererHashForAppUri } = require("./electron/app-routing.cjs");
const { rendererEntryUrl } = require("./electron/renderer-location.cjs");

registerRendererSchemePrivileges(protocol);

let missionControlWindow = null;
let pendingAppUri = appUriArgument(process.argv);
const launchMode = resolveLaunchMode(process.argv);

async function openAppUri(raw) {
  const hash = await rendererHashForAppUri(raw);
  if (hash === null) return false;
  if (!missionControlWindow || missionControlWindow.isDestroyed?.()) {
    pendingAppUri = raw;
    return true;
  }
  await missionControlWindow.loadURL(rendererEntryUrl(hash));
  missionControlWindow.restore?.();
  missionControlWindow.show?.();
  return true;
}

async function createWindow() {
  const { assertOperatorView } = await import("./renderer/shell-state.mjs");
  const frameContracts = await import("./renderer/frames/frame-contract.mjs");
  const adapter = launchMode === LAUNCH_MODE_FIXTURES
    ? new (require("./electron/fixture-control-plane-adapter.cjs").FixtureControlPlaneAdapter)()
    : new AcceptedControlPlaneAdapter();
  const bridge = new ControlPlaneBridge(
    adapter,
    createAcceptedValidators(assertOperatorView, frameContracts),
  );
  const { window, loadRenderer } = createMissionControlWindow({
    BrowserWindow,
    preloadPath: path.join(__dirname, "electron", "preload.cjs"),
    browserWindowOptions: {
      width: 1440,
      height: 920,
      minWidth: 760,
      minHeight: 620,
    },
    launchMode,
  });
  const disposeIpc = registerMissionControlIpc({
    ipcMain,
    bridge,
    trustedWebContents: window.webContents,
  });
  const initialHash = pendingAppUri ? await rendererHashForAppUri(pendingAppUri) : "";
  pendingAppUri = null;
  await loadRenderer(initialHash ?? "");
  missionControlWindow = window;
  window.once("closed", () => {
    if (missionControlWindow === window) missionControlWindow = null;
    disposeIpc();
    void bridge.disconnect().finally(() => adapter.close());
  });
  return window;
}

app.setAsDefaultProtocolClient?.("bilqis");
app.on("open-url", (event, raw) => {
  event.preventDefault();
  if (missionControlWindow) void openAppUri(raw);
  else pendingAppUri = raw;
});
app.on("second-instance", (_event, argv) => {
  const raw = appUriArgument(argv);
  if (raw) void openAppUri(raw);
});

app.whenReady().then(async () => {
  registerMissionControlProtocol({
    protocol,
    net,
    assetRoot: path.join(__dirname, "renderer"),
    launchMode,
  });
  await createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      void createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
